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

cfg = EM.MERCADOS['ambos_marcan']
pmer_todos = EM.mercado_por_partido(cuotas, cfg)  # match_id -> prob mercado

# Solo los partidos donde SI hay cuota real -- 251 con resultado conocido.
base = base_completa[base_completa[cols_prod].notna().all(axis=1)].reset_index(drop=True)
base = base[base.match_id.isin(pmer_todos.index)].sort_values('fecha').reset_index(drop=True)
base['cuota_mercado'] = pmer_todos.loc[base.match_id].values
print(f"{len(base)} partidos con TODOS los rasgos de produccion Y cuota real de ambos_marcan")
print(f"rango de fechas: {base.fecha.min()} a {base.fecha.max()}\n")

# Corte temporal DENTRO de esta ventana pequenya -- 70/30, no el 75/25 estandar
# (con tan pocos partidos, mas vale dejar un poco mas de validacion)
corte = int(len(base) * 0.70)
ent, val = base.iloc[:corte], base.iloc[corte:]
print(f"AVISO: muestra pequenya. entreno={len(ent)} valido={len(val)} "
      f"(el resto del proyecto usa ~1679/212 -- esto es 10-20x menos)\n")

y_ent = ent['ambos_marcan'].values.astype(int)
y_val = val['ambos_marcan'].values.astype(int)
pm_val = val['cuota_mercado'].values

def evaluar_config(nombre, cols):
    preds = []
    for s in EM.SEMILLAS:
        modelo = M.entrenar(ent[cols].values, y_ent, 2, semilla=s)
        p = M.probabilidades(modelo, val[cols].values, 2)
        preds.append(p[:,1])
    pn = np.mean(preds, axis=0)
    b_modelo = EM.brier(pn, y_val, 2).mean()
    b_mercado = EM.brier(pm_val, y_val, 2).mean()
    dif = EM.brier(np.column_stack([pm_val]*0 or [pm_val]), y_val, 2) if False else None
    # Brier pareado partido a partido para sigmas (mismo patron que evaluar_uno)
    b_modelo_partido = ((np.column_stack([1-pn,pn]) - np.eye(2)[y_val])**2).sum(axis=1)
    b_mercado_partido = ((np.column_stack([1-pm_val,pm_val]) - np.eye(2)[y_val])**2).sum(axis=1)
    dif = b_mercado_partido - b_modelo_partido
    ee = dif.std(ddof=1)/np.sqrt(len(dif)) if len(dif)>1 else np.nan
    sigmas = dif.mean()/ee if ee else 0.0
    am = ((pn>0.5).astype(int)==y_val).mean()
    amk = ((pm_val>0.5).astype(int)==y_val).mean()
    print(f"{nombre:35s} ({len(cols)} rasgos)  Brier {b_modelo:.4f} vs mercado {b_mercado:.4f}  "
          f"{sigmas:+.2f}s  acierto {am*100:.1f}% vs {amk*100:.1f}%")

evaluar_config("produccion (sin cuota)", cols_prod)
evaluar_config("produccion + cuota_mercado", cols_prod + ['cuota_mercado'])

print("\n=== Con regularizacion ligera (min_child_weight=5, ajustada a 148 filas) ===")
def entrenar_ligero(X, y, semilla):
    from xgboost import XGBClassifier
    m = XGBClassifier(n_estimators=200, max_depth=2, learning_rate=0.05,
                      subsample=0.8, colsample_bytree=0.8,
                      min_child_weight=5, reg_lambda=5.0,
                      objective="binary:logistic", random_state=semilla,
                      n_jobs=2, eval_metric="logloss", tree_method="hist")
    m.fit(X, y)
    return m

def evaluar_ligero(nombre, cols):
    preds = []
    for s in EM.SEMILLAS:
        modelo = entrenar_ligero(ent[cols].values, y_ent, s)
        p = modelo.predict_proba(val[cols].values)
        preds.append(p[:,1])
    pn = np.mean(preds, axis=0)
    b_modelo_partido = ((np.column_stack([1-pn,pn]) - np.eye(2)[y_val])**2).sum(axis=1)
    b_mercado_partido = ((np.column_stack([1-pm_val,pm_val]) - np.eye(2)[y_val])**2).sum(axis=1)
    dif = b_mercado_partido - b_modelo_partido
    ee = dif.std(ddof=1)/np.sqrt(len(dif)) if len(dif)>1 else np.nan
    sigmas = dif.mean()/ee if ee else 0.0
    am = ((pn>0.5).astype(int)==y_val).mean()
    print(f"{nombre:35s} ({len(cols)} rasgos)  Brier {b_modelo_partido.mean():.4f} "
          f"{sigmas:+.2f}s  acierto {am*100:.1f}%")

evaluar_ligero("produccion (sin cuota)", cols_prod)
evaluar_ligero("produccion + cuota_mercado", cols_prod + ['cuota_mercado'])
