"""
¿Con 9.000 partidos de entrenamiento compensa otra regularización? (29/09/2026)

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
ACTUAL = (2, 20, 5.0)
REJILLA = list(itertools.product((2, 3, 4), (5, 20), (1.0, 5.0)))


def xgb(params, ent, val, semillas):
    md, mcw, lam = params
    y = ent.mas_2_5.values.astype(int)
    return np.mean([XGBClassifier(n_estimators=400, max_depth=md, learning_rate=0.03, subsample=0.8,
                                  colsample_bytree=0.8, min_child_weight=mcw, reg_lambda=lam,
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
    print(f"  max_depth={p[0]} min_child_weight={p[1]:2d} reg_lambda={p[2]:.0f}  Brier {b:.4f}"
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
    r["elegida"] = (xgb(elegida, ent, val, range(5)) + pl) / 2 if elegida != ACTUAL else r["actual"]
    res.append(r)
d = pd.concat(res, ignore_index=True)
sig = lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
bm, ba, be = (2 * (d[c] - d.y) ** 2 for c in ("pm", "actual", "elegida"))
print(f"PRUEBA ({len(d)} partidos, ago 2025 - sep 2026), modelo oficial completo:")
print(f"  actual  {ACTUAL}: vs casa {sig(bm - ba):+.2f}s")
print(f"  elegida {elegida}: vs casa {sig(bm - be):+.2f}s | elegida vs actual "
      f"{sig(ba - be) if elegida != ACTUAL else 0:+.2f}s")
