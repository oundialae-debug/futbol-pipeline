"""
¿Cuánto mejora el modelo con MUCHA más historia? (25/09/2026)

Solo football-data.co.uk (gratis, sin API): 2016/17 -> 2026/27, 6 ligas,
~23.000 partidos con goles, tiros, tiros a puerta, córners y cuotas.
Antes de 2019/20 la media de casas se llama BbAv; después, Avg.

Variables (lo que da la fuente): medias de los 8 partidos anteriores de
goles, tiros a puerta, tiros fuera, córners (propios y del rival) y puntos,
loc/vis/dif; Elo; liga. Sin pases ni g/a (no están en esta fuente).

Fijado ANTES de mirar:
  - mismas variables, entrenando con historia de 1, 3 y 10 temporadas
  - versión "parte de la cuota" (base_margin) con 10 temporadas
  - evaluación mes a mes en ago 2025 - sep 2026 (los mismos meses de siempre)
"""
import glob, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from xgboost import XGBClassifier

DIV = {"E0": 1, "SP1": 2, "SP2": 3, "I1": 4, "D1": 5, "F1": 6}
filas = []
for f in sorted(glob.glob("data/football_data/*.csv")):
    d = pd.read_csv(f, encoding="utf-8-sig", on_bad_lines="skip", encoding_errors="ignore")
    d = d.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
    div, t = f.split("/")[-1][:-4].split("_")
    d["liga"], d["temporada"] = DIV[div], int(t[:2])
    d["fecha"] = pd.to_datetime(d.Date, dayfirst=True, errors="coerce")
    o = d["Avg>2.5"] if "Avg>2.5" in d else d.get("BbAv>2.5")
    u = d["Avg<2.5"] if "Avg<2.5" in d else d.get("BbAv<2.5")
    d["cuota_o"], d["cuota_u"] = o, u
    for c in ("HS", "AS", "HST", "AST", "HC", "AC", "PC>2.5", "PC<2.5"):
        if c not in d:
            d[c] = np.nan
    filas.append(d[["fecha", "liga", "temporada", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "HS", "AS",
                    "HST", "AST", "HC", "AC", "cuota_o", "cuota_u", "PC>2.5", "PC<2.5"]])
p = pd.concat(filas, ignore_index=True).dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)
p["pid"] = np.arange(len(p))
p["y"] = (p.FTHG + p.FTAG > 2.5).astype(int)
justa = lambda o, u: (1 / o) / (1 / o + 1 / u)
p["p_mercado"] = justa(p.cuota_o, p.cuota_u)
p["p_pc"] = justa(p["PC>2.5"], p["PC<2.5"])
print(f"{len(p)} partidos, {p.fecha.min().date()} a {p.fecha.max().date()}; con cuota {p.p_mercado.notna().sum()}")

def rasgos(p):
    """Medias de 8 partidos (shift antes de rolling) y Elo (se lee antes de actualizar)."""
    p = p.copy()
    # ---- formato largo: una fila por equipo y partido ----
    L = []
    for lado, riv, pre in (("Home", "Away", ("FTHG", "FTAG", "HS", "AS", "HST", "AST", "HC", "AC")),
                           ("Away", "Home", ("FTAG", "FTHG", "AS", "HS", "AST", "HST", "AC", "HC"))):
        gf, gc, s, sc, st, stc, c, cc = pre
        L.append(pd.DataFrame({"pid": p.pid, "fecha": p.fecha, "equipo": p[f"{lado}Team"] + "_" + p.liga.astype(str),
                               "casa": int(lado == "Home"), "gf": p[gf], "gc": p[gc],
                               "tp": p[st], "tp_c": p[stc], "tf": p[s] - p[st], "tf_c": p[sc] - p[stc],
                               "co": p[c], "co_c": p[cc]}))
    L = pd.concat(L).sort_values(["equipo", "fecha"]).reset_index(drop=True)
    L["pts"] = np.where(L.gf > L.gc, 3, np.where(L.gf == L.gc, 1, 0))
    MED = ["gf", "gc", "tp", "tp_c", "tf", "tf_c", "co", "co_c", "pts"]
    g = L.groupby("equipo")
    for m in MED:
        L[f"m_{m}"] = g[m].shift(1).groupby(L.equipo).rolling(8, min_periods=3).mean().reset_index(level=0, drop=True)

    # ---- Elo (cronológico, se lee antes de actualizar) ----
    elo, e_l, e_v = {}, [], []
    for r in p.itertuples(index=False):
        a, b = f"{r.HomeTeam}_{r.liga}", f"{r.AwayTeam}_{r.liga}"
        ea, eb = elo.get(a, 1500.0), elo.get(b, 1500.0)
        e_l.append(ea); e_v.append(eb)
        esp = 1 / (1 + 10 ** ((eb - ea - 60) / 400))
        res = 1.0 if r.FTHG > r.FTAG else (0.5 if r.FTHG == r.FTAG else 0.0)
        elo[a], elo[b] = ea + 20 * (res - esp), eb - 20 * (res - esp)
    p["loc_elo"], p["vis_elo"] = e_l, e_v
    p["dif_elo"] = p.loc_elo - p.vis_elo

    loc = L[L.casa == 1].set_index("pid"); vis = L[L.casa == 0].set_index("pid")
    for m in MED:
        p[f"loc_{m}"], p[f"vis_{m}"] = loc[f"m_{m}"].reindex(p.pid).values, vis[f"m_{m}"].reindex(p.pid).values
        p[f"dif_{m}"] = p[f"loc_{m}"] - p[f"vis_{m}"]
    global COLS
    COLS = [f"{s}_{m}" for m in MED for s in ("loc", "vis", "dif")] + ["loc_elo", "vis_elo", "dif_elo", "liga"]


    return p


p = rasgos(p)
# ---- comprobación de fuga: trucar el marcador de UN partido no mueve SUS rasgos,
#      y sí los de partidos posteriores (si no, la prueba no prueba nada) ----
obj = p.pid.iloc[len(p) * 3 // 4]
tr = p.copy(); tr.loc[tr.pid == obj, ["FTHG", "FTAG", "HST", "AST", "HS", "AS"]] = [9, 0, 20, 0, 30, 0]
p2 = rasgos(tr)
propio = np.allclose(p.loc[p.pid == obj, COLS].fillna(-9).values, p2.loc[p2.pid == obj, COLS].fillna(-9).values)
despues = (p.loc[p.fecha > p.loc[p.pid == obj, "fecha"].iloc[0], COLS].fillna(-9).values !=
           p2.loc[p2.fecha > p2.loc[p2.pid == obj, "fecha"].iloc[0], COLS].fillna(-9).values).any(axis=1).sum()
print(f"FUGA: {'pasa' if propio and despues > 0 else 'FALLA'} (propio partido igual: {propio}; "
      f"partidos posteriores que cambian: {despues})")
assert propio and despues > 0

logit = lambda x: np.log(x / (1 - x))


def xgb(s):
    return XGBClassifier(n_estimators=400, max_depth=2, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
                         min_child_weight=20, reg_lambda=5.0, random_state=s, n_jobs=2, eval_metric="logloss",
                         tree_method="hist")


def predecir(ent, val, base=False):
    ps = []
    for s in range(5):
        if base:
            m = xgb(s).fit(ent[COLS].values, ent.y.values, base_margin=logit(ent.p_mercado.values))
            ps.append(m.predict_proba(val[COLS].values, base_margin=logit(val.p_mercado.values))[:, 1])
        else:
            m = xgb(s).fit(ent[COLS].values, ent.y.values)
            ps.append(m.predict_proba(val[COLS].values)[:, 1])
    return np.mean(ps, axis=0)


p["mes"] = p.fecha.dt.strftime("%Y-%m")
ev = p[(p.fecha >= "2025-08-01") & p.p_mercado.notna()]
VERS = {"1 temporada": 1, "3 temporadas": 3, "10 temporadas": 10}
out = []
for mes in sorted(ev.mes.unique()):
    hoy = pd.Timestamp(mes + "-01")
    val = ev[ev.mes == mes]
    r = val[["pid", "mes", "y", "p_mercado", "p_pc", "cuota_o", "cuota_u"]].copy()
    for n, anios in VERS.items():
        ent = p[(p.fecha < hoy) & (p.fecha >= hoy - pd.DateOffset(years=anios))]
        r[f"p_{anios}"] = predecir(ent, val)
    entb = p[(p.fecha < hoy) & p.p_mercado.notna() & p.p_mercado.between(0.02, 0.98)]
    r["p_B10"] = predecir(entb, val, base=True)
    out.append(r)
d = pd.concat(out)
d.to_csv("data/historia_larga.csv", index=False)


def sig(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


bm = 2 * (d.p_mercado - d.y) ** 2
gp = d.dropna(subset=["p_pc"])
print(f"\n{len(d)} partidos evaluados mes a mes ({d.mes.min()} a {d.mes.max()}). Positivo = el modelo es mejor.")
print(f"{'modelo':34s} {'vs media casas':>15s} {'vs Pinnacle':>12s} {'acierto':>8s} {'apuesta (cuota media)':>22s}")
for c, n in [(f"p_{a}", f"historia {k}") for k, a in VERS.items()] + [("p_B10", "parte de la cuota, 10 temporadas")]:
    b = 2 * (d[c] - d.y) ** 2
    vo, vu = d[c] * d.cuota_o - 1, (1 - d[c]) * d.cuota_u - 1
    o, u = (vo > 0) & (vo >= vu), (vu > 0) & (vu > vo)
    ret = np.r_[(d.y[o] * d.cuota_o[o] - 1).values, ((1 - d.y[u]) * d.cuota_u[u] - 1).values]
    print(f"{n:34s} {sig(bm - b):+14.2f}s {sig(2*(gp.p_pc-gp.y)**2 - 2*(gp[c]-gp.y)**2):+11.2f}s "
          f"{((d[c] > .5) == d.y).mean()*100:7.1f}% {ret.mean()*100:+9.2f}% ({len(ret)} ap.)")
print(f"{'media de casas':34s} {'':15s} {sig(2*(gp.p_pc-gp.y)**2 - bm[gp.index]):+11.2f}s "
      f"{((d.p_mercado > .5) == d.y).mean()*100:7.1f}%")
