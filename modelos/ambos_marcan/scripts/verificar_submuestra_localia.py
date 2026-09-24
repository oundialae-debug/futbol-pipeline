"""
Verificacion de que el "mejor combo" del barrido de 42 combinaciones no
era tal -- comparaba contra el numero de produccion en la muestra
equivocada (2239 partidos) en vez de en la propia submuestra que usan
los combos con "localia" (2090 partidos, porque esa variable exige mas
historial especifico de casa/fuera). Ver CLAUDE.md "Las 42
combinaciones" para el resultado completo.
"""
import sys
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

hist = M.cargar()
base_completa = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
grupos = rasgos.grupos_rasgo(base_completa)
cuotas = EM.cargar_cuotas_crudas()
prod = sum((grupos[g] for g in ['arbitro','h2h','h2h_profundo','tabla','calidad_plantilla']), [])
cols_prod = sum((grupos[g] for g in ['base','elo']), []) + prod

largo0 = rasgos.a_largo(hist).sort_values(['equipo','en_casa','fecha']).reset_index(drop=True)
g5 = largo0.groupby(['equipo','en_casa'], sort=False)
largo0['loca_goles'] = g5['goles'].transform(lambda s: s.shift(1).rolling(rasgos.VENTANA, min_periods=3).mean())
loc5 = largo0[largo0.en_casa==1][['match_id','loca_goles']]
vis5 = largo0[largo0.en_casa==0][['match_id','loca_goles']]
loca_ids = set(loc5.dropna().match_id) & set(vis5.dropna().match_id)

base = base_completa[base_completa[cols_prod].notna().all(axis=1)].reset_index(drop=True)
base = base[base.match_id.isin(loca_ids)].reset_index(drop=True)
print(f'{len(base)} partidos (misma submuestra que localia)')
corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
ent = base.iloc[:corte]
fecha_corte = pd.to_datetime(ent.fecha.max())
cfgm = EM.MERCADOS['ambos_marcan']
r = EM.evaluar_uno('ambos_marcan', cfgm, base, cols_prod, ent, fecha_corte, cuotas)
pmer_todos = EM.mercado_por_partido(cuotas, cfgm)
val = base[pd.to_datetime(base.fecha) > fecha_corte]
val = val[val.match_id.isin(pmer_todos.index)]
y = val['ambos_marcan'].values.astype(int)
y_ent = ent['ambos_marcan'].values.astype(int)
preds = []
for s in EM.SEMILLAS:
    modelo = M.entrenar(ent[cols_prod].values, y_ent, 2, semilla=s)
    p = M.probabilidades(modelo, val[cols_prod].values, 2)
    preds.append(p[:,1])
pn = np.mean(preds, axis=0)
pm = pmer_todos.loc[val.match_id].values
am = ((pn>0.5).astype(int)==y).mean(); amk = ((pm>0.5).astype(int)==y).mean()
print(f'produccion SOLA en submuestra localia: {r["sigmas"]:+.2f}s  acierto {am*100:.1f}% vs {amk*100:.1f}%')
