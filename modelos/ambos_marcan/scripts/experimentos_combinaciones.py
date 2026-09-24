import sys, time, itertools
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
from collections import defaultdict, deque
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

t0 = time.time()
hist = M.cargar()
base_completa = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
grupos = rasgos.grupos_rasgo(base_completa)
cuotas = EM.cargar_cuotas_crudas()
prod = sum((grupos[g] for g in ['arbitro','h2h','h2h_profundo','tabla','calidad_plantilla']), [])

# ---------- reconstruir las 6 variables (arbitro en su mejor version: ventana 20) ----------
def calcular_arbitro_ventana(hist, ventana=20):
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
            v_tarj.append(media_t_actual); v_gol.append(media_g_actual); v_n.append(0)
        tarjetas = None
        if all(pd.notna(fila.get(c)) for c in ('l_yellow_cards','l_red_cards','v_yellow_cards','v_red_cards')):
            tarjetas = fila['l_yellow_cards']+fila['l_red_cards']+fila['v_yellow_cards']+fila['v_red_cards']
        gl, gv = fila.get('goles_l'), fila.get('goles_v')
        goles = (gl+gv) if pd.notna(gl) and pd.notna(gv) else None
        if tarjetas is not None: media_t_num += tarjetas; media_t_den += 1
        if goles is not None: media_g_num += goles; media_g_den += 1
        if pd.notna(arb):
            if arb not in tarj_dq:
                tarj_dq[arb] = deque(maxlen=ventana); gol_dq[arb] = deque(maxlen=ventana)
            if tarjetas is not None: tarj_dq[arb].append(tarjetas)
            if goles is not None: gol_dq[arb].append(goles)
    return pd.DataFrame({'match_id': orden['match_id'].values,
                         'arbitrov20_tarjetas_media': v_tarj,
                         'arbitrov20_goles_media': v_gol,
                         'arbitrov20_partidos_previos': v_n})

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
            n_prev.append(0); pts_local.append(0.5); gd_local.append(0.0); continue
        previos = grupo[(grupo['fecha'] < fecha_partido) & (grupo['fecha'] >= limite)]
        previos = previos.sort_values('fecha', ascending=False).head(max_partidos)
        pts, gd, pesos = [], [], []
        for _, m in previos.iterrows():
            if pd.isna(m['goles_l']) or pd.isna(m['goles_v']): continue
            mi_g, su_g = ((m['goles_l'], m['goles_v']) if m['local_id']==l else (m['goles_v'], m['goles_l']))
            p = 3.0 if mi_g>su_g else (1.0 if mi_g==su_g else 0.0)
            reciente = (fecha_partido - m['fecha']).days <= 365*ventana_peso_anios
            pts.append(p); gd.append(mi_g-su_g); pesos.append(peso_extra if reciente else 1.0)
        if not pts:
            n_prev.append(0); pts_local.append(0.5); gd_local.append(0.0)
        else:
            pa = np.array(pesos)
            n_prev.append(len(pts))
            pts_local.append(float(np.average(pts, weights=pa))/3.0)
            gd_local.append(float(np.average(gd, weights=pa)))
    return pd.DataFrame({'match_id': orden['match_id'].values,
                         'h2hr_partidos_previos': n_prev, 'h2hr_pts_local_norm': pts_local, 'h2hr_gd_local': gd_local})

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
        gfpg_l.append(gf_l0/pj_l0 if pj_l0 else 0.0); gfpg_v.append(gf_v0/pj_v0 if pj_v0 else 0.0)
        gcpg_l.append(gc_l0/pj_l0 if pj_l0 else 0.0); gcpg_v.append(gc_v0/pj_v0 if pj_v0 else 0.0)
        gl, gv = fila['goles_l'], fila['goles_v']
        if pd.notna(gl) and pd.notna(gv):
            pl3 = 3 if gl>gv else (1 if gl==gv else 0)
            pv3 = 3 if gv>gl else (1 if gl==gv else 0)
            tabla[l] = (pts_l0+pl3, gf_l0+gl, gc_l0+gv, pj_l0+1)
            tabla[v] = (pts_v0+pv3, gf_v0+gv, gc_v0+gl, pj_v0+1)
    return pd.DataFrame({'match_id': orden['match_id'].values,
                         'loc_tabla_gfpg': gfpg_l, 'vis_tabla_gfpg': gfpg_v,
                         'loc_tabla_gcpg': gcpg_l, 'vis_tabla_gcpg': gcpg_v})

def calcular_impacto_jugador(hist):
    if 'local_ids' not in hist.columns or 'visitante_ids' not in hist.columns:
        return pd.DataFrame({'match_id': hist['match_id'].values})
    orden = hist.sort_values('fecha').reset_index(drop=True)
    historial = defaultdict(list)
    filas = []
    for _, fila in orden.iterrows():
        def medias(ids_str):
            if pd.isna(ids_str): return 0.0, 0.0, 0
            gfs, gcs = [], []
            for jid_s in ids_str.split('|'):
                hx = historial.get(int(jid_s))
                if hx:
                    gfs.append(np.mean([h[0] for h in hx])); gcs.append(np.mean([h[1] for h in hx]))
            n = len(gfs)
            if n == 0: return 0.0, 0.0, 0
            return float(np.mean(gfs)), float(np.mean(gcs)), n
        gf_l, gc_l, n_l = medias(fila.get('local_ids'))
        gf_v, gc_v, n_v = medias(fila.get('visitante_ids'))
        filas.append({'match_id': fila['match_id'], 'loc_impacto_gf': gf_l, 'vis_impacto_gf': gf_v,
                      'loc_impacto_gc': gc_l, 'vis_impacto_gc': gc_v, 'loc_impacto_n': n_l, 'vis_impacto_n': n_v})
        gl, gv = fila.get('goles_l'), fila.get('goles_v')
        if pd.notna(gl) and pd.notna(gv):
            if pd.notna(fila.get('local_ids')):
                for jid_s in fila['local_ids'].split('|'): historial[int(jid_s)].append((gl, gv))
            if pd.notna(fila.get('visitante_ids')):
                for jid_s in fila['visitante_ids'].split('|'): historial[int(jid_s)].append((gv, gl))
    return pd.DataFrame(filas)

largo0 = rasgos.a_largo(hist).sort_values(['equipo','en_casa','fecha']).reset_index(drop=True)
g5 = largo0.groupby(['equipo','en_casa'], sort=False)
largo0['loca_goles'] = g5['goles'].transform(lambda s: s.shift(1).rolling(rasgos.VENTANA, min_periods=3).mean())
largo0['loca_goles_contra'] = g5['goles_contra'].transform(lambda s: s.shift(1).rolling(rasgos.VENTANA, min_periods=3).mean())
loc5 = largo0[largo0.en_casa==1][['match_id','loca_goles','loca_goles_contra']].rename(
    columns={'loca_goles':'loc_loca_goles','loca_goles_contra':'loc_loca_goles_contra'})
vis5 = largo0[largo0.en_casa==0][['match_id','loca_goles','loca_goles_contra']].rename(
    columns={'loca_goles':'vis_loca_goles','loca_goles_contra':'vis_loca_goles_contra'})
loca = loc5.merge(vis5, on='match_id', how='inner')

largo6 = rasgos.a_largo(hist).sort_values(['equipo','fecha']).reset_index(drop=True)
g6 = largo6.groupby('equipo', sort=False)
largo6['r5_goles'] = g6['goles'].transform(lambda s: s.shift(1).rolling(5, min_periods=2).mean())
pts6 = np.where(largo6.goles > largo6.goles_contra, 3, np.where(largo6.goles==largo6.goles_contra, 1, 0))
largo6['_pts6'] = pts6
largo6['r5_puntos'] = g6['_pts6'].transform(lambda s: s.shift(1).rolling(5, min_periods=2).mean())
loc6 = largo6[largo6.en_casa==1][['match_id','r5_goles','r5_puntos']].rename(columns={'r5_goles':'loc_r5_goles','r5_puntos':'loc_r5_puntos'})
vis6 = largo6[largo6.en_casa==0][['match_id','r5_goles','r5_puntos']].rename(columns={'r5_goles':'vis_r5_goles','r5_puntos':'vis_r5_puntos'})
r5 = loc6.merge(vis6, on='match_id', how='inner')

arb_v20 = calcular_arbitro_ventana(hist, ventana=20)
h2h_crudo = pd.read_csv('data/historico_h2h_profundo.csv')
h2hr = calcular_h2h_reciente(hist, h2h_crudo)
tg = calcular_tabla_goles(hist)
ij = calcular_impacto_jugador(hist)

bc = base_completa.merge(arb_v20, on='match_id', how='left') \
                  .merge(h2hr, on='match_id', how='left') \
                  .merge(tg, on='match_id', how='left') \
                  .merge(ij, on='match_id', how='left') \
                  .merge(loca, on='match_id', how='left') \
                  .merge(r5, on='match_id', how='left')
bc['dif_impacto_gf'] = bc['loc_impacto_gf'] - bc['vis_impacto_gf']
bc['dif_impacto_gc'] = bc['loc_impacto_gc'] - bc['vis_impacto_gc']
bc['dif_loca_goles'] = bc['loc_loca_goles'] - bc['vis_loca_goles']
bc['dif_loca_goles_contra'] = bc['loc_loca_goles_contra'] - bc['vis_loca_goles_contra']
bc['loc_momentum5_puntos'] = bc['loc_r5_puntos'] - bc['loc_m_puntos']
bc['vis_momentum5_puntos'] = bc['vis_r5_puntos'] - bc['vis_m_puntos']
bc['loc_momentum5_goles'] = bc['loc_r5_goles'] - bc['loc_m_goles']
bc['vis_momentum5_goles'] = bc['vis_r5_goles'] - bc['vis_m_goles']
bc['dif_momentum5_puntos'] = bc['loc_momentum5_puntos'] - bc['vis_momentum5_puntos']
bc['dif_momentum5_goles'] = bc['loc_momentum5_goles'] - bc['vis_momentum5_goles']

VARS = {
    1: ['arbitrov20_tarjetas_media','arbitrov20_goles_media','arbitrov20_partidos_previos'],
    2: ['h2hr_partidos_previos','h2hr_pts_local_norm','h2hr_gd_local'],
    3: ['loc_tabla_gfpg','vis_tabla_gfpg','loc_tabla_gcpg','vis_tabla_gcpg'],
    4: ['loc_impacto_gf','vis_impacto_gf','loc_impacto_gc','vis_impacto_gc','loc_impacto_n','vis_impacto_n','dif_impacto_gf','dif_impacto_gc'],
    5: ['loc_loca_goles','loc_loca_goles_contra','vis_loca_goles','vis_loca_goles_contra','dif_loca_goles','dif_loca_goles_contra'],
    6: ['loc_momentum5_puntos','vis_momentum5_puntos','dif_momentum5_puntos','loc_momentum5_goles','vis_momentum5_goles','dif_momentum5_goles'],
}
NOMBRES = {1:'arbitro_v20', 2:'h2h_reciente', 3:'tabla_goles', 4:'impacto_jugador', 5:'localia', 6:'momentum5'}

print(f"Carga y preparacion: {time.time()-t0:.0f}s\n")

# prod SIN arbitro (para no duplicar cuando metemos la variante ventana 20)
prod_sin_arb = sum((grupos[g] for g in ['h2h','h2h_profundo','tabla','calidad_plantilla']), [])

def evaluar(cols_extra):
    cols = sum((grupos[g] for g in ['base','elo']), []) + prod_sin_arb + cols_extra
    base = bc[bc[cols].notna().all(axis=1)].reset_index(drop=True)
    if len(base) < 300:
        return None
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent = base.iloc[:corte]
    fecha_corte = pd.to_datetime(ent.fecha.max())
    cfgm = EM.MERCADOS['ambos_marcan']
    r = EM.evaluar_uno('ambos_marcan', cfgm, base, cols, ent, fecha_corte, cuotas)
    if not r["evaluable"]:
        return None
    pmer_todos = EM.mercado_por_partido(cuotas, cfgm)
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
    return {'n': len(base), 'sigmas': r['sigmas'], 'acierto': am, 'acierto_mercado': amk}

filas = []
combos = []
for tam in (3, 4, 5, 6):
    combos.extend(itertools.combinations(range(1,7), tam))
print(f"{len(combos)} combinaciones de tamano >=3 a probar\n")

for i, combo in enumerate(combos):
    cols_extra = sum((VARS[v] for v in combo), [])
    nombre = "+".join(NOMBRES[v] for v in combo)
    res = evaluar(cols_extra)
    if res is None:
        print(f"[{i+1}/{len(combos)}] {nombre}: NO EVALUABLE")
        continue
    filas.append({'combo': nombre, 'n_vars': len(combo), **res})
    print(f"[{i+1}/{len(combos)}] {nombre:55s} n={res['n']:4d}  {res['sigmas']:+.2f}s  "
          f"acierto {res['acierto']*100:5.1f}% vs {res['acierto_mercado']*100:5.1f}%")

tabla = pd.DataFrame(filas)
tabla.to_csv('data/combinaciones_seis_variables.csv', index=False)
print(f"\nEscrito data/combinaciones_seis_variables.csv ({time.time()-t0:.0f}s totales)\n")
print("=== TOP 10 por sigmas ===")
print(tabla.sort_values('sigmas', ascending=False).head(10)[['combo','n','sigmas','acierto']].to_string(index=False))
print("\n=== TOP 10 por acierto ===")
print(tabla.sort_values('acierto', ascending=False).head(10)[['combo','n','sigmas','acierto']].to_string(index=False))
