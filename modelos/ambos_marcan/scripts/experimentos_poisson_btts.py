import sys
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

hist = M.cargar()
base_completa = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
grupos = rasgos.grupos_rasgo(base_completa)
cuotas = EM.cargar_cuotas_crudas()

# Poisson simple: lambda de cada equipo = media de (su propio ataque, la
# defensa del rival), P(marca>=1) = 1-exp(-lambda), P(BTTS) = producto
# asumiendo independencia. No es dato nuevo -- combina m_goles/m_goles_contra
# ya existentes con una formula explicita de futbol.
lam_local = (base_completa['loc_m_goles'] + base_completa['vis_m_goles_contra']) / 2
lam_visit = (base_completa['vis_m_goles'] + base_completa['loc_m_goles_contra']) / 2
p_local = 1 - np.exp(-lam_local.clip(lower=0))
p_visit = 1 - np.exp(-lam_visit.clip(lower=0))
base_completa['poisson_lambda_local'] = lam_local
base_completa['poisson_lambda_visit'] = lam_visit
base_completa['poisson_p_btts'] = p_local * p_visit
poisson_cols = ['poisson_lambda_local', 'poisson_lambda_visit', 'poisson_p_btts']

prod = sum((grupos[g] for g in ['arbitro','h2h','h2h_profundo','tabla','calidad_plantilla']), [])

def evaluar(nombre_cfg, cols_extra, solo_ambos=False):
    cols = sum((grupos[g] for g in ['base','elo']), []) + cols_extra
    base = base_completa[base_completa[cols].notna().all(axis=1)].reset_index(drop=True)
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent = base.iloc[:corte]
    fecha_corte = pd.to_datetime(ent.fecha.max())
    print(f"=== {nombre_cfg} ({len(cols)} rasgos, {len(base)} partidos) ===")
    mercados = {'ambos_marcan': EM.MERCADOS['ambos_marcan']} if solo_ambos else EM.MERCADOS
    suma_sigmas = suma_acierto = 0.0
    for nombre, cfg in mercados.items():
        r = EM.evaluar_uno(nombre, cfg, base, cols, ent, fecha_corte, cuotas)
        if not r["evaluable"]:
            print(f"  {nombre:20s} NO EVALUABLE -- {r['motivo']}")
            continue
        pmer_todos = EM.mercado_por_partido(cuotas, cfg)
        val = base[pd.to_datetime(base.fecha) > fecha_corte]
        val = val[val.match_id.isin(pmer_todos.index)]
        y = val[nombre].values.astype(int)
        y_ent = ent[nombre].values.astype(int)
        preds = []
        for s in EM.SEMILLAS:
            modelo = M.entrenar(ent[cols].values, y_ent, cfg['n_clases'], semilla=s)
            p = M.probabilidades(modelo, val[cols].values, cfg['n_clases'])
            preds.append(p if cfg['n_clases']==3 else p[:,1])
        pn = np.mean(preds, axis=0)
        pm = pmer_todos.loc[val.match_id].values
        am = ((pn > 0.5).astype(int) == y).mean(); amk = ((pm > 0.5).astype(int) == y).mean()
        ad = am - amk
        suma_sigmas += r['sigmas']; suma_acierto += ad
        print(f"  {nombre:20s} n={r['partidos']:4d}  {r['sigmas']:+.2f}s  acierto {am*100:5.1f}% vs {amk*100:5.1f}% ({ad*100:+.1f}pp)")
    if not solo_ambos:
        print(f"  SUMA sigmas: {suma_sigmas:+.2f}   SUMA acierto_dif: {suma_acierto*100:+.1f}pp")
    print()

# Primero, correlacion con el objetivo real -- comprobacion rapida de si
# la senal cruda ya sirve antes de meterla en el modelo
c = base_completa[['poisson_p_btts','ambos_marcan']].dropna()
print(f"Correlacion poisson_p_btts vs ambos_marcan real: {c.corr().iloc[0,1]:.3f} (n={len(c)})\n")

evaluar("base+elo", [], solo_ambos=True)
evaluar("base+elo+poisson_btts (sola)", poisson_cols, solo_ambos=True)
evaluar("produccion", prod, solo_ambos=True)
evaluar("produccion+poisson_btts", prod + poisson_cols, solo_ambos=True)
