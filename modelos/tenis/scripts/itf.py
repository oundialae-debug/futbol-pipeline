"""
Entrenar en ITF (30/09/2026, petición del usuario).

Historial de ITF:
- Sackmann (copia de archivo): ITF masculino (futures) 2010-jun 2026, con
  estadísticas de saque en 2025-2026; ITF femenino (qual_itf) hasta jun 2026.
- Después de junio de 2026: resultados de los mercados cerrados de Kalshi
  (ganador y nombres completos: cada partido tiene un mercado por jugador;
  fecha = cierre del mercado; torneo y ronda del texto "2026 M15 Luan Round
  of 32"). Sin estadísticas. Superficie: la de la última edición del mismo
  torneo en Sackmann; si no hay, pista dura.
- Todo junto con ATP/Challenger (o WTA): los jugadores de ITF también juegan
  Challengers.

Prueba (fijada antes de mirar): en los partidos de ITF de Kalshi posteriores
al final de Sackmann que tienen precio (foto a cierre - 4 h), acierto y
log-loss del Elo y del modelo de puntos (parámetros fijos, ya elegidos) contra
el precio de Kalshi. Escribe data/tenis/itf.md.
"""
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import calibracion_kalshi as CK  # noqa: E402
import elo_tenis as E  # noqa: E402
import markov_tenis as K  # noqa: E402
import modelo_puntos as P  # noqa: E402

D = "data/tenis"
RONDA = {"round of 128": "R128", "round of 64": "R64", "round of 32": "R32", "round of 16": "R16",
         "quarterfinal": "QF", "semifinal": "SF", "final": "F"}
TEXTO = re.compile(r"in the 2026 (.+?) (Round [Oo]f \d+|Quarterfinals?|Semifinals?|Finals?|Qualifying.*?) after")
C_ELO = {"atp": 250.0, "wta": 350.0}
# nota de partida de un debutante en ITF, elegida con los partidos de ITF de 2025 de Sackmann
# (antes de todo lo de Kalshi): ATP plana entre 1000 y 1100, WTA plana entre 1300 y 1400
INICIAL_ITF = {"atp": 1100.0, "wta": 1300.0}


def resultados_kalshi(serie, circuito, desde):
    m = pd.read_csv(f"{D}/kalshi/mercados_{serie}.csv")
    m = m[m["result"].isin(["yes", "no"])]
    g = m.groupby("event_ticker")
    filas = []
    for ev, x in g:
        if len(x) != 2 or (x["result"] == "yes").sum() != 1:
            continue
        gan, per = x[x["result"] == "yes"].iloc[0], x[x["result"] == "no"].iloc[0]
        t = TEXTO.search(str(gan["rules_primary"]))
        cierre = pd.Timestamp(gan["close_time"]).tz_convert(None)
        if cierre < desde:
            continue
        torneo = t.group(1) if t else "ITF"
        ronda = RONDA.get(t.group(2).lower().rstrip("s"), "Q1") if t else "R32"
        filas.append({"tourney_id": f"k-{torneo}-{cierre:%Y%W}", "tourney_name": torneo,
                      "tourney_date": int(cierre.strftime("%Y%m%d")), "tourney_level": "ITF",
                      "round": ronda, "winner_name": gan["yes_sub_title"], "loser_name": per["yes_sub_title"],
                      "score": "kalshi", "event_ticker": ev})
    k = pd.DataFrame(filas)
    # superficie: la de la última edición del mismo torneo en Sackmann
    pat = f"{D}/sackmann/atp_matches_futures_202[45]*.csv" if circuito == "atp" else \
        f"{D}/sackmann/wta_matches_qual_itf_202[456].csv"
    import glob
    s = pd.concat([pd.read_csv(f, usecols=["tourney_name", "surface"], low_memory=False) for f in glob.glob(pat)])
    sup = s.dropna().drop_duplicates("tourney_name", keep="last").set_index("tourney_name")["surface"]
    k["surface"] = k["tourney_name"].map(sup).fillna("Hard")
    k["sup_conocida"] = k["tourney_name"].isin(sup.index)
    return k


def main():
    out = ["# Entrenar en ITF: Elo y modelo de puntos contra el precio de Kalshi\n",
           "Generado por `modelos/tenis/scripts/itf.py`. Partidos de ITF de Kalshi posteriores al final de Sackmann,",
           "con precio a cierre - 4 h. Acierto = el lado con prob. > 50% gana. Log-loss: más bajo es mejor.\n",
           "| serie | partidos de Kalshi añadidos al historial | con superficie conocida | evaluados | acierto Kalshi | "
           "acierto Elo | acierto puntos | log-loss Kalshi | log-loss Elo | log-loss puntos |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for serie, circuito in (("KXITFMATCH", "atp"), ("KXITFWMATCH", "wta")):
        base = E.historial(circuito, itf=(circuito == "atp"))
        fin_sack = base.loc[base["tourney_level"].astype(str).isin(["15", "25", "35", "50", "75", "100", "S", "F"]),
                            "inicio"].max()
        k = resultados_kalshi(serie, circuito, fin_sack + pd.Timedelta(days=7))
        d = E.historial(circuito, itf=(circuito == "atp"), extra=k.drop(columns=["sup_conocida"]))
        elo = E.calcular(d, C_ELO[circuito], INICIAL_ITF[circuito])
        d["p_elo"] = E.prob_ganador(elo, 0.25).values
        r = P.pasar(d, *P.PARAMS[circuito])
        d["p_w"], d["p_l"] = P.prob_punto(r["th_w"], r["v_w"]), P.prob_punto(r["th_l"], r["v_l"])
        dk = d[d["event_ticker"].notna()] if "event_ticker" in d else d.iloc[0:0]
        precios = CK.cargar(serie).dropna(subset=["p"])
        precios = precios[(precios.p > 0) & (precios.p < 1)]
        x = dk.merge(precios[["event_ticker", "yes_sub_title", "p", "y"]], on="event_ticker")
        # p de Kalshi es del jugador "sí" del mercado guardado; orientarla al ganador
        si_gana = x["yes_sub_title"] == x["winner_name"]
        x["p_k"] = np.where(si_gana, x["p"], 1 - x["p"])
        x["p_puntos"] = [K.partido(K.redondear(a), K.redondear(b), 3)[0] for a, b in zip(x["p_w"], x["p_l"])]
        ac = lambda p: (p > 0.5).mean()  # noqa: E731
        ll = lambda p: np.mean(-np.log(np.clip(p, 1e-6, 1)))  # noqa: E731
        out.append(f"| {serie} | {len(k)} | {k['sup_conocida'].mean():.0%} | {len(x)} | {ac(x.p_k):.1%} | "
                   f"{ac(x.p_elo):.1%} | {ac(x.p_puntos):.1%} | {ll(x.p_k):.4f} | {ll(x.p_elo):.4f} | "
                   f"{ll(x.p_puntos):.4f} |")
        print(out[-1], flush=True)
    open(f"{D}/itf.md", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
