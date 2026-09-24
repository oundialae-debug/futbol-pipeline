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

def entrenar_pesado(X, y, n_clases, semilla, pesos):
    m = XGBClassifier(
        n_estimators=400, max_depth=2, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8,
        min_child_weight=20, reg_lambda=5.0,
        objective="multi:softprob" if n_clases > 2 else "binary:logistic",
        num_class=n_clases if n_clases > 2 else None,
        random_state=semilla, n_jobs=2, eval_metric="mlogloss",
        tree_method="hist",
    )
    m.fit(X, y, sample_weight=pesos)
    return m

fechas_ent = pd.to_datetime(ent.fecha)
dias_antes = (fecha_corte - fechas_ent).dt.days.values.astype(float)

VIDAS_MEDIAS = [None, 730, 365, 180]  # None = sin decaimiento (peso uniforme)

for vida_media in VIDAS_MEDIAS:
    if vida_media is None:
        pesos = np.ones(len(ent))
        etiqueta = "sin decaimiento (actual)"
    else:
        pesos = 0.5 ** (dias_antes / vida_media)
        etiqueta = f"vida media {vida_media}d (min peso {pesos.min():.2f})"
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
            modelo = entrenar_pesado(ent[cols].values, y_ent, cfg['n_clases'], s, pesos)
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
    print(f"  {etiqueta:35s}  sigmas={suma_sigmas:+.2f}  acierto_dif={suma_acierto*100:+.1f}pp")
