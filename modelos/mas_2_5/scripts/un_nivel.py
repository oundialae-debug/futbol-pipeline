"""
Árboles de UN nivel y calidad sin once = 0 (29/09/2026). En ambos_marcan los
árboles de un nivel ganaron (+1.54s) y el 0 en la calidad sin once fue mejor
que "desconocido" (vacío -1.92s). Se prueba lo mismo aquí, fijado antes:
  (profundidad, nº árboles, calidad sin once)
Elección en 2024/25, prueba una vez en ago 2025 - sep 2026 (modelo oficial).
Antes: ¿Con 9.000 partidos de entrenamiento compensa otra regularización?

Los hiperparámetros del XGBoost (max_depth=2, min_child_weight=20,
reg_lambda=5) se eligieron con ~1.700 partidos. CLAUDE.md del repo padre:
"más partidos de entrenamiento sí podría justificar menos regularización".
Ahora hay ~9.000 (desde 2022/23).

  ELECCIÓN: 12 combinaciones (max_depth 2/3/4, min_child_weight 5/20,
  reg_lambda 1/5), mes a mes en 2024/25 (cada mes entrenado con lo anterior),
  2 semillas, solo el XGBoost 28. Gana el menor Brier medio.
  PRUEBA, una vez: ago 2025 - sep 2026, modelo oficial completo (XGBoost +
  logística) con la actual y con la elegida, 5 semillas, contra la casa.
"""
import sys, io, contextlib, itertools, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import rasgos_mas25 as R
from modelo_oficial import rasgos, SUMAS, cargar_hist

hist = cargar_hist()
bc = rasgos(hist)
fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(
    fd[["match_id", "p_mercado", "Avg>2.5", "Avg<2.5"]], on="match_id", how="left")
bc["f"] = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = bc.f.dt.strftime("%Y-%m")
C28 = R.columnas_produccion(bc)
CP = [c for c in C28 if "_cp_" in c]
ACTUAL = (2, 400, "vacío")
REJILLA = [(2, 400, "vacío"), (1, 400, "vacío"), (1, 800, "vacío"),
           (2, 400, "cero"), (1, 400, "cero"), (1, 800, "cero")]


def xgb(params, ent, val, semillas):
    md, n, cp = params
    if cp == "cero":
        ent, val = ent.copy(), val.copy()
        ent[CP], val[CP] = ent[CP].fillna(0), val[CP].fillna(0)
    y = ent.mas_2_5.values.astype(int)
    return np.mean([XGBClassifier(n_estimators=n, max_depth=md, learning_rate=0.03, subsample=0.8,
                                  colsample_bytree=0.8, min_child_weight=20, reg_lambda=5.0,
                                  random_state=s, n_jobs=4, eval_metric="logloss", tree_method="hist")
                    .fit(ent[C28].values, y).predict_proba(val[C28].values)[:, 1] for s in semillas], axis=0)


def meses(desde, hasta):
    return sorted(bc.loc[(bc.f >= desde) & (bc.f < hasta) & bc.p_mercado.notna(), "mes"].unique())


# ---- elección en 2024/25 ----
brier = {p: [] for p in REJILLA}
for mes in meses("2024-08-01", "2025-07-01"):
    val = bc[(bc.mes == mes) & bc.p_mercado.notna()]
    ent = bc[bc.f < pd.Timestamp(mes + "-01", tz="UTC")]
    for p in REJILLA:
        brier[p].append(2 * (xgb(p, ent, val, (0, 1)) - val.mas_2_5.values) ** 2)
tabla = sorted(((np.concatenate(b).mean(), p) for p, b in brier.items()))
print("ELECCIÓN (2024/25, Brier del XGBoost 28; menor es mejor):")
for b, p in tabla:
    print(f"  profundidad={p[0]} árboles={p[1]} calidad sin once={p[2]:5s}  Brier {b:.4f}"
          f"{'  <- actual' if p == ACTUAL else ''}")
elegida = tabla[0][1]
print(f"Elegida: {elegida}\n")

# ---- prueba, una vez ----
res = []
for mes in meses("2025-08-01", "2026-10-01"):
    val = bc[(bc.mes == mes) & bc.p_mercado.notna()]
    ent = bc[bc.f < pd.Timestamp(mes + "-01", tz="UTC")]
    e = ent.dropna(subset=SUMAS)
    sc = StandardScaler().fit(e[SUMAS])
    pl = LogisticRegression().fit(sc.transform(e[SUMAS]), e.mas_2_5.astype(int)) \
        .predict_proba(sc.transform(val[SUMAS].fillna(e[SUMAS].mean())))[:, 1]
    r = pd.DataFrame({"y": val.mas_2_5.values, "pm": val.p_mercado.values})
    r["actual"] = (xgb(ACTUAL, ent, val, range(5)) + pl) / 2
    for p in REJILLA:
        r[str(p)] = (xgb(p, ent, val, range(5)) + pl) / 2 if p != ACTUAL else r["actual"]
    r["elegida"] = r[str(elegida)]
    res.append(r)
d = pd.concat(res, ignore_index=True)
sig = lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
bm, ba, be = (2 * (d[c] - d.y) ** 2 for c in ("pm", "actual", "elegida"))
print(f"PRUEBA ({len(d)} partidos, ago 2025 - sep 2026), modelo oficial completo:")
print(f"  actual  {ACTUAL}: vs casa {sig(bm - ba):+.2f}s")
print(f"  elegida {elegida}: vs casa {sig(bm - be):+.2f}s | elegida vs actual "
      f"{sig(ba - be) if elegida != ACTUAL else 0:+.2f}s")
print("\nInformativo (NO decide; elegir mirando esto sería contaminar la prueba):")
for p in REJILLA:
    b = 2 * (d[str(p)] - d.y) ** 2
    print(f"  {p}: vs casa {sig(bm - b):+.2f}s | vs actual {sig(ba - b) if p != ACTUAL else 0:+.2f}s")
