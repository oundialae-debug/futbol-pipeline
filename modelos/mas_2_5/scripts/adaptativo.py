"""
Modelo que se AJUSTA SOLO mes a mes (idea del usuario, 26/09/2026).

Para cada mes M desde ago 2024 hasta hoy:
  1. Ventana de ajuste = los 3 meses anteriores a M. Cada configuración se
     entrena con lo anterior a esa ventana y se mide en ella (Brier).
     Configuraciones: 7 conjuntos de variables x 2 niveles de poda
     (regularización fuerte / suave).
  2. En la misma ventana se eligen dos pesos:
       - mezcla con el Poisson-xG (0, 25, 50, 75%)
       - confianza en la casa (0, 25, 50, 75, 100%): p = w·casa + (1-w)·modelo
  3. Con lo elegido se reentrena con TODO lo anterior a M y se predice M.
Nunca se mira M para decidir. Referencia: XGBoost 28 fijo, mismos meses.
"""
import sys, io, time, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
from scipy.stats import poisson
from scipy.sparse import csr_matrix, hstack
from sklearn.linear_model import PoissonRegressor
from xgboost import XGBClassifier
import modelo_xgboost as M, rasgos_mas25 as R

t0 = time.time()
fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"), pd.read_csv("data/historico_h2h_profundo.csv"))
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(
    fd[["match_id", "p_mercado", "Avg>2.5", "Avg<2.5"]], on="match_id", how="left")
bc["f"] = pd.to_datetime(bc.fecha, utc=True)
bc = bc.sort_values("f").reset_index(drop=True)
bc["mes"] = bc.f.dt.strftime("%Y-%m")
G = R.grupos(bc)
C28 = R.columnas_produccion(bc)
SIN_PASES = [c for c in C28 if "total_passes" not in c]
CONJ = {"28": C28, "28+elo": C28 + G["elo"], "28+tabla": C28 + G["tabla"],
        "28+h2h": C28 + G["h2h_reciente"], "28+calidad": C28 + G["calidad_plantilla_vieja"],
        "28-pases": SIN_PASES, "73 (clasica+elo+g/a)": R.columnas_produccion(bc, ["base_clasica", "elo", "cp_ataque"])}
PODA = {"fuerte": dict(min_child_weight=20, reg_lambda=5.0), "suave": dict(min_child_weight=8, reg_lambda=1.0)}
print(f"{len(bc)} partidos; construido en {time.time()-t0:.0f}s")


def xgb_pred(cols, poda, ent, val, semillas):
    y = ent.mas_2_5.values.astype(int)
    out = []
    for s in semillas:
        m = XGBClassifier(n_estimators=400, max_depth=2, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
                          random_state=s, n_jobs=4, eval_metric="logloss", tree_method="hist", **PODA[poda])
        out.append(m.fit(ent[cols].values, y).predict_proba(val[cols].values)[:, 1])
    return np.mean(out, axis=0)


# ---- Poisson-xG (igual que poisson_dc_xg.py, sin Dixon-Coles: ρ≈0) ----
h = hist.dropna(subset=["goles_l", "goles_v"]).copy()
h["f"] = pd.to_datetime(h.fecha, format="mixed", utc=True)
for lado, g in (("l", "goles_l"), ("v", "goles_v")):
    x = pd.to_numeric(h.get(f"{lado}_expected_goals"), errors="coerce")
    h[f"xg_{lado}"] = x.where(x.notna(), h[g])
EQ = {e: i for i, e in enumerate(pd.unique(h[["local_id", "visitante_id"]].values.ravel()))}
LG = {l: i for i, l in enumerate(h.liga_id.unique())}
hi = h.set_index("match_id")


def dis(att, dfn, liga, casa):
    n = len(att); r = np.arange(n)
    return hstack([csr_matrix((np.ones(n), (r, [EQ[e] for e in att])), shape=(n, len(EQ))),
                   csr_matrix((np.ones(n), (r, [EQ[e] for e in dfn])), shape=(n, len(EQ))),
                   csr_matrix((np.ones(n), (r, [LG[x] for x in liga])), shape=(n, len(LG))),
                   csr_matrix(np.asarray(casa, float).reshape(-1, 1))]).tocsr()


def poisson_pred(hasta, ids):
    ent = h[h.f < hasta]
    X = dis(np.r_[ent.local_id, ent.visitante_id], np.r_[ent.visitante_id, ent.local_id],
            np.r_[ent.liga_id, ent.liga_id], np.r_[np.ones(len(ent)), np.zeros(len(ent))])
    w = 0.5 ** (np.r_[(hasta - ent.f).dt.days, (hasta - ent.f).dt.days] / 365.0)
    m = PoissonRegressor(alpha=0.01, max_iter=1000).fit(X, np.r_[ent.xg_l, ent.xg_v], sample_weight=w)
    v = hi.loc[ids]
    ll = m.predict(dis(v.local_id, v.visitante_id, v.liga_id, np.ones(len(v))))
    lv = m.predict(dis(v.visitante_id, v.local_id, v.liga_id, np.zeros(len(v))))
    return 1 - poisson.cdf(2, ll + lv)


brier = lambda p, y: np.mean(2 * (p - y) ** 2)
W_P, W_M = [0, .25, .5, .75], [0, .25, .5, .75, 1.0]
meses = sorted(bc.loc[(bc.f >= "2024-08-01") & bc.p_mercado.notna(), "mes"].unique())
res, elecciones = [], []
for mes in meses:
    hoy = pd.Timestamp(mes + "-01", tz="UTC")
    ini_v = hoy - pd.DateOffset(months=3)
    ventana = bc[(bc.f >= ini_v) & (bc.f < hoy) & bc.p_mercado.notna()]
    ent_v = bc[bc.f < ini_v]
    val = bc[(bc.mes == mes) & bc.p_mercado.notna()]
    yv = ventana.mas_2_5.values
    # 1. variables + poda, medidas en la ventana
    puntos = {(c, p): brier(xgb_pred(CONJ[c], p, ent_v, ventana, (0, 1)), yv) for c in CONJ for p in PODA}
    c_best, p_best = min(puntos, key=puntos.get)
    # 2. pesos de mezcla, en la misma ventana
    px_v = xgb_pred(CONJ[c_best], p_best, ent_v, ventana, (0, 1))
    pp_v = poisson_pred(ini_v, ventana.match_id.values)
    pm_v = ventana.p_mercado.values
    grid = {(a, b): brier(b * pm_v + (1 - b) * (a * pp_v + (1 - a) * px_v), yv) for a in W_P for b in W_M}
    wp, wm = min(grid, key=grid.get)
    # 3. predecir el mes con todo lo anterior
    ent = bc[bc.f < hoy]
    px = xgb_pred(CONJ[c_best], p_best, ent, val, range(5))
    pp = poisson_pred(hoy, val.match_id.values)
    p_final = wm * val.p_mercado.values + (1 - wm) * (wp * pp + (1 - wp) * px)
    p_fijo = xgb_pred(C28, "fuerte", ent, val, range(5))
    res.append(pd.DataFrame({"match_id": val.match_id.values, "mes": mes, "y": val.mas_2_5.values,
                             "p_mercado": val.p_mercado.values, "o": val["Avg>2.5"].values,
                             "u": val["Avg<2.5"].values, "p_adaptativo": p_final,
                             "p_modelo_sin_casa": wp * pp + (1 - wp) * px, "p_28_fijo": p_fijo}))
    elecciones.append({"mes": mes, "n": len(val), "variables": c_best, "poda": p_best,
                       "peso_poisson": wp, "peso_casa": wm})
    print(f"{mes}: {c_best:22s} poda {p_best:6s} poisson {wp:.0%} casa {wm:.0%}  (n={len(val)}, {time.time()-t0:.0f}s)")

d = pd.concat(res, ignore_index=True)
d.to_csv("data/adaptativo.csv", index=False)
pd.DataFrame(elecciones).to_csv("data/adaptativo_elecciones.csv", index=False)
sig = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
bm = 2 * (d.p_mercado - d.y) ** 2
d["temp"] = np.where(d.mes < "2025-07", "2024/25", np.where(d.mes < "2026-07", "2025/26", "2026/27"))
print(f"\n{len(d)} partidos evaluados ({meses[0]} a {meses[-1]}). Positivo = mejor que la casa.")
for c in ("p_28_fijo", "p_modelo_sin_casa", "p_adaptativo"):
    b = 2 * (d[c] - d.y) ** 2
    vo, vu = d[c] * d.o - 1, (1 - d[c]) * d.u - 1
    ov, un = (vo > 0) & (vo >= vu), (vu > 0) & (vu > vo)
    ret = np.r_[(d.y[ov] * d.o[ov] - 1).values, ((1 - d.y[un]) * d.u[un] - 1).values]
    por_t = "  ".join(f"{t} {sig(bm[g.index] - b[g.index]):+.2f}s" for t, g in d.groupby("temp"))
    print(f"  {c:18s} vs casa {sig(bm - b):+.2f}s | {por_t} | acierto {((d[c]>.5)==d.y).mean()*100:.1f}% "
          f"| apostando {ret.mean()*100:+.2f}% (±{ret.std(ddof=1)/np.sqrt(max(len(ret),2))*100:.2f}, {len(ret)} ap.)")
print(f"  casa: acierto {((d.p_mercado>.5)==d.y).mean()*100:.1f}%")
print(f"\nAdaptativo frente al 28 fijo: {sig(2*(d.p_28_fijo-d.y)**2 - 2*(d.p_adaptativo-d.y)**2):+.2f}s")
e = pd.DataFrame(elecciones)
print("\nQué eligió (meses):", e.variables.value_counts().to_dict(), "| poda:", e.poda.value_counts().to_dict())
print("peso casa medio", round(e.peso_casa.mean(), 2), "| peso Poisson medio", round(e.peso_poisson.mean(), 2))
