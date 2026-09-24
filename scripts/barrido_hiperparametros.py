import sys, time
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM
from xgboost import XGBClassifier

hist = M.cargar()
base_completa = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
cols = rasgos.columnas_rasgo_default(base_completa)
base = base_completa[base_completa[cols].notna().all(axis=1)].reset_index(drop=True)
corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
ent = base.iloc[:corte]
fecha_corte = pd.to_datetime(ent.fecha.max())
cuotas = EM.cargar_cuotas_crudas()
print(f"{len(base)} partidos utilizables, {len(cols)} rasgos, entreno {len(ent)}\n")

def entrenar_param(X, y, n_clases, semilla, max_depth, min_child_weight, reg_lambda):
    m = XGBClassifier(
        n_estimators=400, max_depth=max_depth, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8,
        min_child_weight=min_child_weight, reg_lambda=reg_lambda,
        objective="multi:softprob" if n_clases > 2 else "binary:logistic",
        num_class=n_clases if n_clases > 2 else None,
        random_state=semilla, n_jobs=2, eval_metric="mlogloss",
        tree_method="hist",
    )
    m.fit(X, y)
    return m

GRID = [(d, mcw, rl) for d in (2, 3) for mcw in (20, 30, 50) for rl in (5, 10, 20)]
print(f"{len(GRID)} configuraciones de hiperparametros\n")

filas = []
t0 = time.time()
for max_depth, mcw, rl in GRID:
    suma_sigmas = 0.0
    suma_acierto = 0.0
    for nombre, cfg in EM.MERCADOS.items():
        pmer_todos = EM.mercado_por_partido(cuotas, cfg)
        if pmer_todos is None: continue
        val = base[pd.to_datetime(base.fecha) > fecha_corte]
        val = val[val.match_id.isin(pmer_todos.index)]
        if len(val) < 20: continue
        y = val[nombre].values.astype(int)
        y_ent = ent[nombre].values.astype(int)
        if len(np.unique(y_ent)) < cfg['n_clases']: continue
        preds = []
        for s in EM.SEMILLAS:
            modelo = entrenar_param(ent[cols].values, y_ent, cfg['n_clases'], s, max_depth, mcw, rl)
            p = M.probabilidades(modelo, val[cols].values, cfg['n_clases'])
            preds.append(p if cfg['n_clases']==3 else p[:,1])
        pn = np.mean(preds, axis=0)
        if cfg['n_clases'] == 3:
            pm = pmer_todos.loc[val.match_id][[f'p_{l}' for l in cfg['lados']]].values
            acierto_modelo = (pn.argmax(axis=1) == y).mean()
            acierto_mercado = (pm.argmax(axis=1) == y).mean()
        else:
            pm = pmer_todos.loc[val.match_id].values
            acierto_modelo = ((pn > 0.5).astype(int) == y).mean()
            acierto_mercado = ((pm > 0.5).astype(int) == y).mean()
        b_modelo = EM.brier(pn, y, cfg['n_clases'])
        b_mercado = EM.brier(pm, y, cfg['n_clases'])
        dif = b_mercado - b_modelo
        ee = dif.std(ddof=1) / np.sqrt(len(dif)) if len(dif) > 1 else np.nan
        sigmas = float(dif.mean() / ee) if ee else 0.0
        suma_sigmas += sigmas
        suma_acierto += (acierto_modelo - acierto_mercado)
    filas.append({'max_depth': max_depth, 'min_child_weight': mcw, 'reg_lambda': rl,
                  'suma_sigmas': suma_sigmas, 'suma_acierto_dif': suma_acierto})
    print(f"  depth={max_depth} mcw={mcw:3d} lambda={rl:3d}  sigmas={suma_sigmas:+.2f}  acierto_dif={suma_acierto*100:+.1f}pp  ({time.time()-t0:.0f}s)")

tabla = pd.DataFrame(filas).sort_values('suma_sigmas', ascending=False)
tabla.to_csv('data/barrido_hiperparametros.csv', index=False)
print("\n=== Mejores por sigmas ===")
print(tabla.head(5).to_string(index=False))
print("\n=== Mejores por acierto ===")
print(tabla.sort_values('suma_acierto_dif', ascending=False).head(5).to_string(index=False))
print(f"\nReferencia actual (depth=2, mcw=20, lambda=5): sigmas -7.93, acierto -13.8pp")
