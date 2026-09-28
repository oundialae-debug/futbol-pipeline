"""NBA: construccion de rasgos por partido (sin fuga) + cierre de MGM.

Sacado de modelo_totales.py para compartirlo con modelo_ganador.py.
Todo rasgo de un partido sale SOLO de partidos anteriores (shift antes de acumular).
"""
import numpy as np
import pandas as pd


def construir():
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
    # FALLO SILENCIOSO de Kaggle: playerteamId vacio en el 99.9% de 2021-22 y ~7% del resto.
    # Se recupera con (partido, local/visitante): coincide en el 99.9% donde si venia.
    eq = t[["gameId", "home", "teamId"]].rename(columns={"teamId": "_eq"})
    j = j.merge(eq, on=["gameId", "home"], how="left")
    j["playerteamId"] = j.playerteamId.fillna(j._eq)
    j = j.drop(columns="_eq").dropna(subset=["playerteamId"])
    j["fecha"] = pd.to_datetime(j.gameDate)
    j["jugo"] = (j.numMinutes.fillna(0) > 0).astype(float)
    j["min"] = j.numMinutes.fillna(0)
    j = j.sort_values(["personId", "playerteamId", "fecha"])
    gj = j.groupby(["personId", "playerteamId"])
    # media de minutos y puntos en sus ultimos 15 partidos del equipo (con los que no jugo como 0)
    j["min_prev"] = gj["min"].transform(lambda s: s.shift(1).rolling(15, min_periods=5).mean())
    j["pts_prev"] = gj["points"].transform(lambda s: s.fillna(0).shift(1).rolling(15, min_periods=5).mean())
    fijo = j.min_prev >= 20
    # baja = marcado de baja ANTES del partido (lesion, liga, personal), no "no jugo":
    # un "no jugo" puede ser decision del entrenador durante el partido
    de_baja = j.comment.fillna("").str.match(r"^(DND|NWT|DNP - Injury|DNP - League|DNP - Personal)")
    j["baja_pts"] = np.where(fijo & de_baja, j.pts_prev, 0.0)
    j["baja_min"] = np.where(fijo & de_baja, j.min_prev, 0.0)
    j["baja_fijos"] = (fijo & de_baja).astype(float)
    bajas = j.groupby(["gameId", "playerteamId"])[["baja_pts", "baja_min", "baja_fijos"]].sum().reset_index()
    t = t.merge(bajas, left_on=["gameId", "teamId"], right_on=["gameId", "playerteamId"], how="left")
    for c in ["baja_pts", "baja_min", "baja_fijos"]:
        t[c] = t[c].fillna(0)

    # ---------------- calidad de los DISPONIBLES ----------------
    # OJO: NO usar "quien jugo": eso se decide en parte durante el partido (minutos de la
    # basura en una paliza, prorrogas) y es fuga. Probado el 28/09: con "quien jugo" la
    # correlacion con (total - linea) salia +0.113 (+4.95s) sin mejorar el acierto: sintoma.
    # Disponible = tiene fila y no esta de baja (DND/NWT/DNP por lesion o liga). "DNP - Coach's
    # Decision" cuenta como disponible: el entrenador lo decide en el partido.
    # Por jugador (en cualquier equipo), medias de sus ultimos 30 partidos JUGADOS antes de
    # este: minutos, produccion por minuto y +/- por minuto. Fuerza = suma sobre disponibles
    # de minutos_previos x ritmo. Los lesionados largos no tienen fila (Embiid 2024-25): no suman.
    j = j.sort_values(["personId", "fecha"]).reset_index(drop=True)
    j["prod"] = (j.points.fillna(0) + 0.4 * j.reboundsTotal.fillna(0) + 0.7 * j.assists.fillna(0)
                 - j.turnovers.fillna(0) - 0.4 * j.fieldGoalsAttempted.fillna(0)
                 - 0.2 * j.freeThrowsAttempted.fillna(0))
    jug = j[j.jugo == 1]
    gp = jug.groupby("personId")
    acum = pd.DataFrame(index=jug.index)
    for c in ["min", "prod", "plusMinusPoints"]:
        acum[c] = gp[c].transform(lambda s: s.fillna(0).rolling(30, min_periods=5).sum())
    acum["n"] = gp["min"].transform(lambda s: s.rolling(30, min_periods=5).count())
    # valor INCLUYENDO el partido jugado -> se arrastra y se desplaza una fila: cada fila ve
    # solo lo acumulado hasta su ultimo partido jugado ANTERIOR
    for c in acum:
        j[f"_{c}"] = acum[c]
        j[f"_{c}"] = j.groupby("personId")[f"_{c}"].transform(lambda s: s.ffill().shift(1))
    j["mpg"] = j._min / j._n
    baja = j.comment.fillna("").str.match(r"^(DND|NWT|DNP - Injury|DNP - League|DNP - Personal)")
    disp = j[~baja].copy()
    disp["f_prod"] = disp.mpg * disp._prod / disp._min
    disp["f_pm"] = disp.mpg * disp._plusMinusPoints / disp._min
    disp["min_conocidos"] = disp.mpg
    fz = disp.groupby(["gameId", "playerteamId"])[["f_prod", "f_pm", "min_conocidos"]].sum(min_count=1).reset_index()
    t = t.merge(fz, left_on=["gameId", "teamId"], right_on=["gameId", "playerteamId"], how="left",
                suffixes=("", "_fz"))

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

    # ---------------- Elo con margen de victoria (estilo 538) ----------------
    # Valor ANTES de cada partido. Entre temporadas se acerca 1/4 a la media.
    elo, pre_l, pre_v, temp_ant = {}, [], [], None
    for r in g.itertuples():
        if temp_ant is not None and r.temp != temp_ant:
            elo = {k: 0.75 * v + 0.25 * 1505 for k, v in elo.items()}
        temp_ant = r.temp
        el, ev = elo.get(r.hometeamId, 1500.0), elo.get(r.awayteamId, 1500.0)
        pre_l.append(el); pre_v.append(ev)
        dif = el + 70 - ev
        esperado = 1 / (1 + 10 ** (-dif / 400))
        margen = r.homeScore - r.awayScore
        gana = 1.0 if margen > 0 else 0.0
        favorito_gana = dif if gana else -dif
        mult = (abs(margen) + 3) ** 0.8 / (7.5 + 0.006 * favorito_gana)
        cambio = 20 * mult * (gana - esperado)
        elo[r.hometeamId], elo[r.awayteamId] = el + cambio, ev - cambio
    g["elo_l"], g["elo_v"] = pre_l, pre_v
    el = g[["gameId", "hometeamId", "elo_l"]].rename(columns={"hometeamId": "teamId", "elo_l": "elo"})
    ev = g[["gameId", "awayteamId", "elo_v"]].rename(columns={"awayteamId": "teamId", "elo_v": "elo"})
    t = t.merge(pd.concat([el, ev]), on=["gameId", "teamId"], how="left")

    # ---------------- tabla por partido ----------------
    R = [f"{c}_{v}" for c in BASE for v in ["temp", "10"]] + \
        ["jugados", "descanso", "b2b", "baja_pts", "baja_min", "baja_fijos",
         "f_prod", "f_pm", "min_conocidos", "elo"]
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
                   "spread_away_decimal_odds", "money_home_decimal_odds",
                   "money_away_decimal_odds"]], on=["dia", "local"], how="inner")
    x = x[(x.l_jugados >= 5) & (x.v_jugados >= 5)].sort_values("fecha").reset_index(drop=True)
    return x, R
