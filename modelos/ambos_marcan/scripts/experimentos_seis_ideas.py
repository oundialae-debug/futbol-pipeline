import sys, time
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
from collections import defaultdict, deque
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

hist = M.cargar()
base_completa = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
grupos = rasgos.grupos_rasgo(base_completa)
cuotas = EM.cargar_cuotas_crudas()
prod = sum((grupos[g] for g in ['arbitro','h2h','h2h_profundo','tabla','calidad_plantilla']), [])

def evaluar(nombre_cfg, cols_extra, base_df=None):
    bc = base_df if base_df is not None else base_completa
    cols = sum((grupos[g] for g in ['base','elo']), []) + cols_extra
    base = bc[bc[cols].notna().all(axis=1)].reset_index(drop=True)
    if len(base) < 300:
        print(f"{nombre_cfg}: solo {len(base)} partidos utilizables, se omite")
        return
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent = base.iloc[:corte]
    fecha_corte = pd.to_datetime(ent.fecha.max())
    cfg = EM.MERCADOS['ambos_marcan']
    r = EM.evaluar_uno('ambos_marcan', cfg, base, cols, ent, fecha_corte, cuotas)
    if not r["evaluable"]:
        print(f"{nombre_cfg}: NO EVALUABLE -- {r['motivo']}")
        return
    pmer_todos = EM.mercado_por_partido(cuotas, cfg)
    val = base[pd.to_datetime(base.fecha) > fecha_corte]
    val = val[val.match_id.isin(pmer_todos.index)]
    y = val['ambos_marcan'].values.astype(int)
    y_ent = ent['ambos_marcan'].values.astype(int)
    preds = []
    for s in EM.SEMILLAS:
        modelo = M.entrenar(ent[cols].values, y_ent, 2, semilla=s)
        p = M.probabilidades(modelo, val[cols].values, 2)
        preds.append(p[:,1])
    pn = np.mean(preds, axis=0)
    pm = pmer_todos.loc[val.match_id].values
    am = ((pn > 0.5).astype(int) == y).mean(); amk = ((pm > 0.5).astype(int) == y).mean()
    print(f"{nombre_cfg:50s} ({len(cols)} rasgos, {len(base)} part.)  {r['sigmas']:+.2f}s  acierto {am*100:5.1f}% vs {amk*100:5.1f}% ({(am-amk)*100:+.1f}pp)")

print("=== BASELINE ===")
evaluar("base+elo", [])
evaluar("produccion", prod)
print()
# ============================================================
# 1. ARBITRO -- ventana de sus ultimos 10 partidos (no todos los previos),
#    y ademas media de GOLES (no solo tarjetas) por si ralentiza el juego
# ============================================================
def calcular_arbitro_ventana(hist, ventana=10):
    orden = hist.sort_values('fecha').reset_index(drop=True)
    tarj_dq, gol_dq = {}, {}
    media_t_num, media_t_den = 0.0, 0
    media_g_num, media_g_den = 0.0, 0
    v_tarj, v_gol, v_n = [], [], []
    for _, fila in orden.iterrows():
        arb = fila.get('arbitro')
        media_t_actual = (media_t_num/media_t_den) if media_t_den else 3.5
        media_g_actual = (media_g_num/media_g_den) if media_g_den else 2.5
        if pd.notna(arb) and arb in tarj_dq and len(tarj_dq[arb]) > 0:
            v_tarj.append(float(np.mean(tarj_dq[arb])))
            v_gol.append(float(np.mean(gol_dq[arb])))
            v_n.append(len(tarj_dq[arb]))
        else:
            v_tarj.append(media_t_actual)
            v_gol.append(media_g_actual)
            v_n.append(0)
        tarjetas = None
        if all(pd.notna(fila.get(c)) for c in ('l_yellow_cards','l_red_cards','v_yellow_cards','v_red_cards')):
            tarjetas = fila['l_yellow_cards']+fila['l_red_cards']+fila['v_yellow_cards']+fila['v_red_cards']
        gl, gv = fila.get('goles_l'), fila.get('goles_v')
        goles = (gl+gv) if pd.notna(gl) and pd.notna(gv) else None
        if tarjetas is not None:
            media_t_num += tarjetas; media_t_den += 1
        if goles is not None:
            media_g_num += goles; media_g_den += 1
        if pd.notna(arb):
            if arb not in tarj_dq:
                tarj_dq[arb] = deque(maxlen=ventana); gol_dq[arb] = deque(maxlen=ventana)
            if tarjetas is not None: tarj_dq[arb].append(tarjetas)
            if goles is not None: gol_dq[arb].append(goles)
    return pd.DataFrame({'match_id': orden['match_id'].values,
                         'arbitrov_tarjetas_media': v_tarj,
                         'arbitrov_goles_media': v_gol,
                         'arbitrov_partidos_previos': v_n})

arb_v = calcular_arbitro_ventana(hist)
b1 = base_completa.merge(arb_v, on='match_id', how='left')
cols_arb_v = ['arbitrov_tarjetas_media','arbitrov_goles_media','arbitrov_partidos_previos']

print("=== 1. ARBITRO ventana 10 (tarjetas+goles) ===")
evaluar("base+elo+arbitro_ventana10 (sola)", cols_arb_v, b1)
prod_sin_arb = sum((grupos[g] for g in ['h2h','h2h_profundo','tabla','calidad_plantilla']), [])
evaluar("produccion(arbitro viejo->ventana10)", prod_sin_arb + cols_arb_v, b1)
print()
# ============================================================
# 2. H2H -- solo ultimos 5 enfrentamientos SI son de los ultimos 2 anios,
#    doble peso a los que caen dentro del ultimo anio
# ============================================================
h2h_crudo = pd.read_csv('data/historico_h2h_profundo.csv')

def calcular_h2h_reciente(hist, h2h_crudo, max_partidos=5, ventana_anios=2, ventana_peso_anios=1, peso_extra=2.0):
    crudo = h2h_crudo.dropna(subset=['fecha']).copy()
    crudo['fecha'] = pd.to_datetime(crudo['fecha'], utc=True)
    crudo['local_id'] = pd.to_numeric(crudo['local_id'], errors='coerce')
    crudo['goles_l'] = pd.to_numeric(crudo['goles_l'], errors='coerce')
    crudo['goles_v'] = pd.to_numeric(crudo['goles_v'], errors='coerce')
    por_par = {par: grupo for par, grupo in crudo.groupby('par')}

    orden = hist.copy()
    orden['_fecha_dt'] = pd.to_datetime(orden['fecha'], format='mixed', utc=True)
    orden = orden.sort_values('_fecha_dt').reset_index(drop=True)

    n_prev, pts_local, gd_local = [], [], []
    for _, fila in orden.iterrows():
        l, v = fila['local_id'], fila['visitante_id']
        grupo = por_par.get(rasgos._clave_par(l, v))
        fecha_partido = fila['_fecha_dt']
        limite = fecha_partido - pd.Timedelta(days=365*ventana_anios)
        if grupo is None:
            n_prev.append(0); pts_local.append(0.5); gd_local.append(0.0)
            continue
        previos = grupo[(grupo['fecha'] < fecha_partido) & (grupo['fecha'] >= limite)]
        previos = previos.sort_values('fecha', ascending=False).head(max_partidos)
        pts, gd, pesos = [], [], []
        for _, m in previos.iterrows():
            if pd.isna(m['goles_l']) or pd.isna(m['goles_v']):
                continue
            mi_g, su_g = ((m['goles_l'], m['goles_v']) if m['local_id']==l else (m['goles_v'], m['goles_l']))
            p = 3.0 if mi_g>su_g else (1.0 if mi_g==su_g else 0.0)
            reciente = (fecha_partido - m['fecha']).days <= 365*ventana_peso_anios
            pts.append(p); gd.append(mi_g-su_g); pesos.append(peso_extra if reciente else 1.0)
        if not pts:
            n_prev.append(0); pts_local.append(0.5); gd_local.append(0.0)
        else:
            pesos_a = np.array(pesos)
            n_prev.append(len(pts))
            pts_local.append(float(np.average(pts, weights=pesos_a))/3.0)
            gd_local.append(float(np.average(gd, weights=pesos_a)))
    return pd.DataFrame({'match_id': orden['match_id'].values,
                         'h2hr_partidos_previos': n_prev,
                         'h2hr_pts_local_norm': pts_local,
                         'h2hr_gd_local': gd_local})

h2hr = calcular_h2h_reciente(hist, h2h_crudo)
b2 = base_completa.merge(h2hr, on='match_id', how='left')
cols_h2hr = ['h2hr_partidos_previos','h2hr_pts_local_norm','h2hr_gd_local']

print("=== 2. H2H reciente (max 5, ventana 2 anios, doble peso ultimo anio) ===")
evaluar("base+elo+h2h_reciente (sola)", cols_h2hr, b2)
prod_sin_h2hp = sum((grupos[g] for g in ['arbitro','h2h','tabla','calidad_plantilla']), [])
evaluar("produccion(h2h_profundo viejo->h2h_reciente)", prod_sin_h2hp + cols_h2hr, b2)
print()
# ============================================================
# 3. TABLA -- goles a favor/en contra de temporada, ademas de posicion
#    (ya existente). Los datos ya se calculaban dentro de calcular_tabla
#    pero no se exponian como columna.
# ============================================================
def calcular_tabla_goles(hist):
    orden = hist.sort_values('fecha').reset_index(drop=True)
    tablas = {}
    gfpg_l, gfpg_v, gcpg_l, gcpg_v = [], [], [], []
    for _, fila in orden.iterrows():
        clave = (fila['liga_id'], fila['temporada'])
        tabla = tablas.setdefault(clave, {})
        l, v = fila['local_id'], fila['visitante_id']
        pts_l0, gf_l0, gc_l0, pj_l0 = tabla.get(l, (0,0,0,0))
        pts_v0, gf_v0, gc_v0, pj_v0 = tabla.get(v, (0,0,0,0))
        gfpg_l.append(gf_l0/pj_l0 if pj_l0 else 0.0)
        gfpg_v.append(gf_v0/pj_v0 if pj_v0 else 0.0)
        gcpg_l.append(gc_l0/pj_l0 if pj_l0 else 0.0)
        gcpg_v.append(gc_v0/pj_v0 if pj_v0 else 0.0)
        gl, gv = fila['goles_l'], fila['goles_v']
        if pd.notna(gl) and pd.notna(gv):
            pl3 = 3 if gl>gv else (1 if gl==gv else 0)
            pv3 = 3 if gv>gl else (1 if gl==gv else 0)
            tabla[l] = (pts_l0+pl3, gf_l0+gl, gc_l0+gv, pj_l0+1)
            tabla[v] = (pts_v0+pv3, gf_v0+gv, gc_v0+gl, pj_v0+1)
    return pd.DataFrame({'match_id': orden['match_id'].values,
                         'loc_tabla_gfpg': gfpg_l, 'vis_tabla_gfpg': gfpg_v,
                         'loc_tabla_gcpg': gcpg_l, 'vis_tabla_gcpg': gcpg_v})

tg = calcular_tabla_goles(hist)
tg['dif_tabla_gfpg'] = tg['loc_tabla_gfpg'] - tg['vis_tabla_gfpg']
tg['dif_tabla_gcpg'] = tg['loc_tabla_gcpg'] - tg['vis_tabla_gcpg']
b3 = base_completa.merge(tg, on='match_id', how='left')
cols_tg = ['loc_tabla_gfpg','vis_tabla_gfpg','loc_tabla_gcpg','vis_tabla_gcpg','dif_tabla_gfpg','dif_tabla_gcpg']

print("=== 3. TABLA goles a favor/en contra ===")
evaluar("base+elo+tabla_goles (sola)", cols_tg, b3)
evaluar("produccion+tabla_goles", prod + cols_tg, b3)
print()
# ============================================================
# 4. CALIDAD PLANTILLA -- efecto de CADA jugador conocido en los goles
#    del EQUIPO cuando el es titular (no su stat individual, que ya
#    cubre calidad_plantilla existente via minutos/goles+asistencias)
# ============================================================
def calcular_impacto_jugador(hist):
    if 'local_ids' not in hist.columns or 'visitante_ids' not in hist.columns:
        return pd.DataFrame({'match_id': hist['match_id'].values})
    orden = hist.sort_values('fecha').reset_index(drop=True)
    historial = defaultdict(list)  # jugador_id -> [(gf, gc), ...]
    filas = []
    for _, fila in orden.iterrows():
        def medias(ids_str):
            if pd.isna(ids_str): return 0.0, 0.0, 0
            gfs, gcs = [], []
            for jid_s in ids_str.split('|'):
                hx = historial.get(int(jid_s))
                if hx:
                    gfs.append(np.mean([h[0] for h in hx]))
                    gcs.append(np.mean([h[1] for h in hx]))
            n = len(gfs)
            if n == 0: return 0.0, 0.0, 0
            return float(np.mean(gfs)), float(np.mean(gcs)), n
        gf_l, gc_l, n_l = medias(fila.get('local_ids'))
        gf_v, gc_v, n_v = medias(fila.get('visitante_ids'))
        filas.append({'match_id': fila['match_id'],
                      'loc_impacto_gf': gf_l, 'vis_impacto_gf': gf_v,
                      'loc_impacto_gc': gc_l, 'vis_impacto_gc': gc_v,
                      'loc_impacto_n': n_l, 'vis_impacto_n': n_v})
        gl, gv = fila.get('goles_l'), fila.get('goles_v')
        if pd.notna(gl) and pd.notna(gv):
            if pd.notna(fila.get('local_ids')):
                for jid_s in fila['local_ids'].split('|'):
                    historial[int(jid_s)].append((gl, gv))
            if pd.notna(fila.get('visitante_ids')):
                for jid_s in fila['visitante_ids'].split('|'):
                    historial[int(jid_s)].append((gv, gl))
    return pd.DataFrame(filas)

ij = calcular_impacto_jugador(hist)
ij['dif_impacto_gf'] = ij['loc_impacto_gf'] - ij['vis_impacto_gf']
ij['dif_impacto_gc'] = ij['loc_impacto_gc'] - ij['vis_impacto_gc']
b4 = base_completa.merge(ij, on='match_id', how='left')
cols_ij = ['loc_impacto_gf','vis_impacto_gf','loc_impacto_gc','vis_impacto_gc',
          'loc_impacto_n','vis_impacto_n','dif_impacto_gf','dif_impacto_gc']

print("=== 4. Impacto de jugador (goles equipo cuando el juega) ===")
evaluar("base+elo+impacto_jugador (sola)", cols_ij, b4)
evaluar("produccion+impacto_jugador", prod + cols_ij, b4)
print()
# ============================================================
# 5. HOME/AWAY -- goles marcados/encajados de cada equipo SOLO en sus
#    partidos como local (para cuando juega de local en ESTE partido) o
#    SOLO como visitante (para cuando juega fuera) -- separado de
#    m_goles/m_goles_contra, que mezclan casa y fuera en la misma media.
# ============================================================
largo0 = rasgos.a_largo(hist)
largo0 = largo0.sort_values(['equipo','en_casa','fecha']).reset_index(drop=True)
g5 = largo0.groupby(['equipo','en_casa'], sort=False)
largo0['loca_goles'] = g5['goles'].transform(lambda s: s.shift(1).rolling(rasgos.VENTANA, min_periods=3).mean())
largo0['loca_goles_contra'] = g5['goles_contra'].transform(lambda s: s.shift(1).rolling(rasgos.VENTANA, min_periods=3).mean())

loc5 = largo0[largo0.en_casa==1][['match_id','loca_goles','loca_goles_contra']].rename(
    columns={'loca_goles':'loc_loca_goles','loca_goles_contra':'loc_loca_goles_contra'})
vis5 = largo0[largo0.en_casa==0][['match_id','loca_goles','loca_goles_contra']].rename(
    columns={'loca_goles':'vis_loca_goles','loca_goles_contra':'vis_loca_goles_contra'})
loca = loc5.merge(vis5, on='match_id', how='inner')
loca['dif_loca_goles'] = loca['loc_loca_goles'] - loca['vis_loca_goles']
loca['dif_loca_goles_contra'] = loca['loc_loca_goles_contra'] - loca['vis_loca_goles_contra']

b5 = base_completa.merge(loca, on='match_id', how='left')
cols_loca = ['loc_loca_goles','loc_loca_goles_contra','vis_loca_goles','vis_loca_goles_contra',
            'dif_loca_goles','dif_loca_goles_contra']

print("=== 5. Home/away (goles casa/fuera, no mezclados) ===")
evaluar("base+elo+localia (sola)", cols_loca, b5)
evaluar("produccion+localia", prod + cols_loca, b5)
print()
# ============================================================
# 6. MOMENTUM ventana 5 -- forma de los ultimos 5 partidos MENOS la base
#    de 8 (ya existente), en vez de la version ya probada con ventana 3
# ============================================================
largo6 = rasgos.a_largo(hist).sort_values(['equipo','fecha']).reset_index(drop=True)
g6 = largo6.groupby('equipo', sort=False)
largo6['r5_goles'] = g6['goles'].transform(lambda s: s.shift(1).rolling(5, min_periods=2).mean())
pts6 = np.where(largo6.goles > largo6.goles_contra, 3, np.where(largo6.goles==largo6.goles_contra, 1, 0))
largo6['_pts6'] = pts6
largo6['r5_puntos'] = g6['_pts6'].transform(lambda s: s.shift(1).rolling(5, min_periods=2).mean())

loc6 = largo6[largo6.en_casa==1][['match_id','r5_goles','r5_puntos']].rename(
    columns={'r5_goles':'loc_r5_goles','r5_puntos':'loc_r5_puntos'})
vis6 = largo6[largo6.en_casa==0][['match_id','r5_goles','r5_puntos']].rename(
    columns={'r5_goles':'vis_r5_goles','r5_puntos':'vis_r5_puntos'})
r5 = loc6.merge(vis6, on='match_id', how='inner')

b6 = base_completa.merge(r5, on='match_id', how='left')
b6['loc_momentum5_puntos'] = b6['loc_r5_puntos'] - b6['loc_m_puntos']
b6['vis_momentum5_puntos'] = b6['vis_r5_puntos'] - b6['vis_m_puntos']
b6['loc_momentum5_goles'] = b6['loc_r5_goles'] - b6['loc_m_goles']
b6['vis_momentum5_goles'] = b6['vis_r5_goles'] - b6['vis_m_goles']
b6['dif_momentum5_puntos'] = b6['loc_momentum5_puntos'] - b6['vis_momentum5_puntos']
b6['dif_momentum5_goles'] = b6['loc_momentum5_goles'] - b6['vis_momentum5_goles']
cols_mom5 = ['loc_momentum5_puntos','vis_momentum5_puntos','dif_momentum5_puntos',
            'loc_momentum5_goles','vis_momentum5_goles','dif_momentum5_goles']

print("=== 6. Momentum ventana 5 (antes probado con ventana 3) ===")
evaluar("base+elo+momentum5 (sola)", cols_mom5, b6)
evaluar("produccion+momentum5", prod + cols_mom5, b6)

# ============================================================
# 7. ARBITRO ventana 20 (en vez de 10) -- y TODAS las variables juntas
# ============================================================
arb_v20 = calcular_arbitro_ventana(hist, ventana=20).rename(columns={
    'arbitrov_tarjetas_media': 'arbitrov20_tarjetas_media',
    'arbitrov_goles_media': 'arbitrov20_goles_media',
    'arbitrov_partidos_previos': 'arbitrov20_partidos_previos'})
cols_arb_v20 = ['arbitrov20_tarjetas_media','arbitrov20_goles_media','arbitrov20_partidos_previos']

b7 = base_completa.merge(arb_v20, on='match_id', how='left') \
                  .merge(h2hr, on='match_id', how='left') \
                  .merge(tg, on='match_id', how='left') \
                  .merge(ij, on='match_id', how='left') \
                  .merge(loca, on='match_id', how='left') \
                  .merge(r5, on='match_id', how='left')
b7['loc_momentum5_puntos'] = b7['loc_r5_puntos'] - b7['loc_m_puntos']
b7['vis_momentum5_puntos'] = b7['vis_r5_puntos'] - b7['vis_m_puntos']
b7['loc_momentum5_goles'] = b7['loc_r5_goles'] - b7['loc_m_goles']
b7['vis_momentum5_goles'] = b7['vis_r5_goles'] - b7['vis_m_goles']
b7['dif_momentum5_puntos'] = b7['loc_momentum5_puntos'] - b7['vis_momentum5_puntos']
b7['dif_momentum5_goles'] = b7['loc_momentum5_goles'] - b7['vis_momentum5_goles']

todas_las_6 = cols_arb_v20 + cols_h2hr + cols_tg + cols_ij + cols_loca + cols_mom5

print("=== 7. ARBITRO ventana 20 solo ===")
evaluar("base+elo+arbitro_ventana20 (sola)", cols_arb_v20, b7)
evaluar("produccion(arbitro->ventana20)", prod_sin_arb + cols_arb_v20, b7)

print("\n=== 8. TODAS las 6 (arbitro=ventana20) JUNTAS ===")
evaluar("base+elo+TODAS", todas_las_6, b7)
prod_arb20 = sum((grupos[g] for g in ['h2h','h2h_profundo','tabla','calidad_plantilla']), []) + cols_arb_v20
evaluar("produccion(arbitro->v20)+TODAS_las_demas", prod_arb20 + cols_h2hr + cols_tg + cols_ij + cols_loca + cols_mom5, b7)
