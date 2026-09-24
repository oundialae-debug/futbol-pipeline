import sys
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

hist = M.cargar()
base_completa = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
grupos = rasgos.grupos_rasgo(base_completa)
cuotas = EM.cargar_cuotas_crudas()

for lado in ('loc', 'vis'):
    base_completa[f'{lado}_momentum_puntos'] = base_completa[f'{lado}_r_puntos'] - base_completa[f'{lado}_m_puntos']
    base_completa[f'{lado}_momentum_goles'] = base_completa[f'{lado}_r_goles'] - base_completa[f'{lado}_m_goles']
base_completa['dif_momentum_puntos'] = base_completa['loc_momentum_puntos'] - base_completa['vis_momentum_puntos']
base_completa['dif_momentum_goles'] = base_completa['loc_momentum_goles'] - base_completa['vis_momentum_goles']
momentum_cols = ['loc_momentum_puntos','vis_momentum_puntos','dif_momentum_puntos',
                'loc_momentum_goles','vis_momentum_goles','dif_momentum_goles']
prod = sum((grupos[g] for g in ['arbitro','h2h','h2h_profundo','tabla','calidad_plantilla']), [])

for nombre_cfg, cols_extra in [("produccion", prod), ("produccion+momentum", prod+momentum_cols)]:
    cols = sum((grupos[g] for g in ['base','elo']), []) + cols_extra
    base = base_completa[base_completa[cols].notna().all(axis=1)].reset_index(drop=True)
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent = base.iloc[:corte]
    fecha_corte = pd.to_datetime(ent.fecha.max())
    print(f"--- {nombre_cfg} ---")
    for nombre, cfg in EM.MERCADOS.items():
        r = EM.evaluar_uno(nombre, cfg, base, cols, ent, fecha_corte, cuotas)
        if not r["evaluable"]: continue
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
        if cfg['n_clases'] == 3:
            pm = pmer_todos.loc[val.match_id][[f'p_{l}' for l in cfg['lados']]].values
            am = (pn.argmax(axis=1) == y).mean(); amk = (pm.argmax(axis=1) == y).mean()
        else:
            pm = pmer_todos.loc[val.match_id].values
            am = ((pn > 0.5).astype(int) == y).mean(); amk = ((pm > 0.5).astype(int) == y).mean()
        print(f"  {nombre:20s} {r['sigmas']:+.2f}s  acierto {am*100:5.1f}% vs {amk*100:5.1f}% ({(am-amk)*100:+.1f}pp)")
