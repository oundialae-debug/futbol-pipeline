"""NBA totales: modelo con ritmo, eficiencia, descanso, bajas y arbitros, contra el cierre de MGM.

Datos: Kaggle eoinamoore (box-score por equipo y jugador, 2021-22..2025-26; cruzado con
nuestra API: marcador identico en el 99.97% de 6.921 partidos) + cierre MGM (Kaggle).
Sin gastar API.

Regla anti-fuga: todo rasgo de un partido sale SOLO de partidos anteriores (shift antes
de acumular). Las bajas usan quien jugo de verdad: en la NBA las bajas se conocen antes
del salto (lista de inactivos) y el cierre ya las lleva dentro, asi que es la misma
informacion que tiene el precio contra el que se compara.

Prueba: reentreno MENSUAL (lo que funciono en futbol), prueba 2024-25 y 2025-26.
"""
import os
import numpy as np
import pandas as pd
import xgboost as xgb

D = "data/nba/kaggle"
JUEGO = ["Regular Season", "Playoffs", "Play-in Tournament", "NBA Emirates Cup",
         "Emirates NBA Cup", "NBA Cup", "in-season-knockout"]

# ---------------- partidos y equipos ----------------
g = pd.read_csv(f"{D}/partidos.csv.gz")
g = g[g.gameType.isin(JUEGO)].copy()
g["fecha"] = pd.to_datetime(g.gameDateTimeEst, format="mixed")
g["temp"] = np.where(g.fecha.dt.month >= 8, g.fecha.dt.year + 1, g.fecha.dt.year)
t = pd.read_csv(f"{D}/equipos_partido.csv.gz")
t = t[t.gameId.isin(g.gameId)].copy()
t["fecha"] = pd.to_datetime(t.gameDateTimeEst, format="mixed")
t["temp"] = np.where(t.fecha.dt.month >= 8, t.fecha.dt.year + 1, t.fecha.dt.year)
t["pos"] = t.fieldGoalsAttempted + 0.44 * t.freeThrowsAttempted - t.reboundsOffensive + t.turnovers
riv = t[["gameId", "teamId", "pos"]].rename(columns={"teamId": "opponentTeamId", "pos": "pos_riv"})
t = t.merge(riv, on=["gameId", "opponentTeamId"])
t["ritmo"] = (t.pos + t.pos_riv) / 2 * 48 / (t.numMinutes / 5).clip(lower=48)
t["ortg"] = 100 * t.teamScore / t.pos
t["drtg"] = 100 * t.opponentScore / t.pos_riv
t["tasa3"] = t.threePointersAttempted / t.fieldGoalsAttempted
t["tasa_tl"] = t.freeThrowsAttempted / t.fieldGoalsAttempted
t["total"] = t.teamScore + t.opponentScore
t = t.sort_values(["teamId", "fecha"]).reset_index(drop=True)
BASE = ["ritmo", "ortg", "drtg", "tasa3", "tasa_tl", "total"]
gr = t.groupby(["teamId", "temp"])
for c in BASE:
    t[f"{c}_temp"] = gr[c].transform(lambda s: s.shift(1).expanding().mean())
    t[f"{c}_10"] = gr[c].transform(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
t["jugados"] = gr.cumcount()
t["descanso"] = t.groupby("teamId").fecha.diff().dt.total_seconds().div(86400).clip(upper=7)
t["b2b"] = (t.descanso < 1.6).astype(float)

# ---------------- bajas ----------------
j = pd.read_csv(f"{D}/jugadores_partido.csv.gz")
j = j[j.gameId.isin(g.gameId)].copy()
j["fecha"] = pd.to_datetime(j.gameDate)
j["jugo"] = (j.numMinutes.fillna(0) > 0).astype(float)
j["min"] = j.numMinutes.fillna(0)
j = j.sort_values(["personId", "playerteamId", "fecha"])
gj = j.groupby(["personId", "playerteamId"])
# media de minutos y puntos en sus ultimos 15 partidos del equipo (con los que no jugo como 0)
j["min_prev"] = gj["min"].transform(lambda s: s.shift(1).rolling(15, min_periods=5).mean())
j["pts_prev"] = gj["points"].transform(lambda s: s.fillna(0).shift(1).rolling(15, min_periods=5).mean())
fijo = j.min_prev >= 20
j["baja_pts"] = np.where(fijo & (j.jugo == 0), j.pts_prev, 0.0)
j["baja_min"] = np.where(fijo & (j.jugo == 0), j.min_prev, 0.0)
j["baja_fijos"] = (fijo & (j.jugo == 0)).astype(float)
bajas = j.groupby(["gameId", "playerteamId"])[["baja_pts", "baja_min", "baja_fijos"]].sum().reset_index()
t = t.merge(bajas, left_on=["gameId", "teamId"], right_on=["gameId", "playerteamId"], how="left")
for c in ["baja_pts", "baja_min", "baja_fijos"]:
    t[c] = t[c].fillna(0)

# ---------------- arbitros ----------------
g = g.sort_values("fecha")
g["total"] = g.homeScore + g.awayScore
media = g.total.expanding().mean().shift(1)
g["desvio"] = g.total - media
arb = g[["gameId", "fecha", "officials", "desvio"]].dropna(subset=["officials"]).copy()
arb["arbitro"] = arb.officials.str.split(r",\s*")
arb = arb.explode("arbitro")
arb = arb.sort_values("fecha")
ga = arb.groupby("arbitro").desvio
arb["arb_prev"] = ga.transform(lambda s: s.shift(1).expanding(min_periods=10).mean())
g = g.merge(arb.groupby("gameId").arb_prev.mean().rename("arbitros"), on="gameId", how="left")

# ---------------- tabla por partido ----------------
R = [f"{c}_{v}" for c in BASE for v in ["temp", "10"]] + \
    ["jugados", "descanso", "b2b", "baja_pts", "baja_min", "baja_fijos"]
L = t[t.home == 1].set_index("gameId")[R].add_prefix("l_")
V = t[t.home == 0].set_index("gameId")[R].add_prefix("v_")
x = g.set_index("gameId").join(L, how="inner").join(V, how="inner").reset_index()
x["dia"] = x.fecha.dt.date.astype(str)
x["local"] = x.hometeamCity + " " + x.hometeamName

k = pd.read_csv("data/nba/cuotas_kaggle/all_odds.csv").drop_duplicates("game_id")
k["dia"] = k.game_date.str[:10]
nombres = sorted(set(x.local))
alias = {"LA Clippers": "LA Clippers", "LA Lakers": "Los Angeles Lakers"}
k["local"] = k.home_team.map(lambda c: alias.get(c) or next(n for n in nombres if n.startswith(c + " ")))
x = x.merge(k[["dia", "local", "total_over_points", "total_over_decimal_odds",
               "total_under_decimal_odds", "spread_home_points", "spread_home_decimal_odds",
               "spread_away_decimal_odds"]], on=["dia", "local"], how="inner")
x = x[(x.l_jugados >= 5) & (x.v_jugados >= 5)].sort_values("fecha").reset_index(drop=True)
MERCADO = os.environ.get("MERCADO", "totales")
if MERCADO == "totales":
    x["linea"] = x.total_over_points
    x["total"] = x.homeScore + x.awayScore
    x["cuota_mas"], x["cuota_menos"] = x.total_over_decimal_odds, x.total_under_decimal_odds
else:  # handicap: "total" = diferencia local-visitante; "linea" = diferencia que da la casa
    x = x.dropna(subset=["spread_home_points"]).reset_index(drop=True)
    x["linea"] = -x.spread_home_points
    x["total"] = x.homeScore - x.awayScore
    x["cuota_mas"], x["cuota_menos"] = x.spread_home_decimal_odds, x.spread_away_decimal_odds
x["resto"] = x.total - x.linea
print(f"MERCADO: {MERCADO}")
print(f"partidos con linea y rasgos: {len(x)} | con arbitros: {x.arbitros.notna().mean():.0%}")

F_SIN = ["l_" + r for r in R] + ["v_" + r for r in R] + ["arbitros"]
CONFIGS = {
    "base (ritmo, eficiencia, descanso)": [f for f in F_SIN if "baja" not in f and f != "arbitros"],
    "+bajas": [f for f in F_SIN if f != "arbitros"],
    "+bajas+arbitros": F_SIN,
}
PARAMS = dict(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.8,
              colsample_bytree=0.8, min_child_weight=20, reg_lambda=5)


def walk_forward(feats, objetivo, con_linea):
    cols = feats + (["linea"] if con_linea else [])
    x["mes"] = x.fecha.dt.to_period("M")
    pru = x[x.temp >= 2025]
    preds = pd.Series(index=pru.index, dtype=float)
    for mes in sorted(pru.mes.unique()):
        ent = x[x.fecha < mes.start_time]
        idx = pru.index[pru.mes == mes]
        ps = []
        for semilla in range(5):
            m = xgb.XGBRegressor(**PARAMS, random_state=semilla)
            m.fit(ent[cols], ent[objetivo])
            ps.append(m.predict(x.loc[idx, cols]))
        preds[idx] = np.mean(ps, axis=0)
    return preds


def evaluar(nombre, dif):
    """dif = prediccion de (total - linea). >0 apuesta over."""
    s = x.loc[dif.index]
    c = np.corrcoef(dif, s.resto)[0, 1]
    print(f"\n{nombre}: corr(pred, real-linea) {c:+.3f} ({c*np.sqrt(len(s)):+.2f}s), n={len(s)}")
    for u in [0, 1, 2, 3, 4]:
        k = dif.abs() > u
        ss, dd = s[k], dif[k]
        over = dd > 0
        gana = np.where(over, ss.total > ss.linea, ss.total < ss.linea)
        empate = ss.total == ss.linea
        cuota = np.where(over, ss.cuota_mas, ss.cuota_menos)
        gan = np.where(empate, 0, np.where(gana, cuota - 1, -1.0))
        if len(gan) < 30:
            continue
        print(f"   |pred| > {u}: n={len(gan):4d} acierto {gana[~empate].mean():.1%} "
              f"roi {gan.mean():+.2%} ({gan.mean()/gan.std(ddof=1)*np.sqrt(len(gan)):+.2f}s)")


rmse = lambda e: float(np.sqrt(np.mean(e ** 2)))
pru = x[x.temp >= 2025]
print(f"prueba (2024-25 y 2025-26): {len(pru)} partidos | RMSE de la linea {rmse(pru.resto):.2f}")
for nombre, feats in CONFIGS.items():
    p_total = walk_forward(feats, "total", con_linea=False)
    print(f"\n### {nombre} ({len(feats)} rasgos)  RMSE modelo {rmse(p_total - pru.total):.2f}")
    evaluar("  A) modelo sin linea: pred_total - linea", p_total - pru.linea)
    p_resto = walk_forward(feats, "resto", con_linea=True)
    evaluar("  B) modelo con linea, predice (real - linea)", p_resto)
