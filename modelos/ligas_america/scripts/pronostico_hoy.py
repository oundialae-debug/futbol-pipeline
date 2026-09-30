"""
Pronóstico de ambos marcan, más/menos 2.5, 1X2 y marcador más probable para
los partidos de HOY que salen en la portada de Promiedos, en las ligas que
este modelo conoce (LIGA_PROMIEDOS). Sin API de Highlightly.

  - Cuota 1X2 de hoy: la que publica Promiedos (una casa, ahora).
  - Modelo "completo" (precio 1X2 + juego) entrenado con las ligas que SÍ
    tienen cuota histórica (ARG, BRA, MEX, USA, football-data); en ligas sin
    cuota histórica (Colombia, Uruguay) se aplica igual, porque el precio de
    hoy sí existe. Aviso: esas ligas no están en el entreno de ese brazo.
  - Brazo "juego" (sin precio) entrenado con todas.
Nombres Promiedos -> histórico: tabla ALIAS; si falta alguno, se PARA y se
listan los nombres del histórico de esa liga (nunca "por parecido").
"""
import os
import re
import sys
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelo_goles as G

LIGA_PROMIEDOS = {"Liga BetPlay Dimayor": "COLA", "Liga AUF Uruguaya": "URU", "MLS": "USA",
                  "Liga Profesional Argentina": "ARG", "Brasileirao": "BRA", "Liga MX": "MEX"}
ALIAS = {
    # MLS
    "New York Red Bulls": "New York Red Bulls", "St. Louis City SC": "St. Louis City",
    # Colombia (nombres de FotMob)
    "Atlético Nacional": "Atlético Nacional", "Junior FC": "Junior FC",
    # Uruguay
    "Montevideo City Torque": "Montevideo City Torque", "Peñarol": "Club Atletico Peñarol",
}
MKT_LIGAS = ("ARG", "BRA", "MEX", "USA")


def hoy():
    html = requests.get("https://www.promiedos.com.ar/", headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
    d = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))
    for l in d["props"]["pageProps"]["data"]["leagues"]:
        cod = LIGA_PROMIEDOS.get(l["name"])
        if not cod:
            continue
        for g in l["games"]:
            if g["status"]["enum"] != 1:
                continue
            o = [float(x["value"]) for x in ((g.get("main_odds") or {}).get("options") or [])]
            yield cod, g["start_time"], g["teams"][0]["name"], g["teams"][1]["name"], (o if len(o) == 3 else [np.nan] * 3)


def main():
    hist = G.cargar()
    filas, faltan = [], []
    for cod, hora, h, a, o in hoy():
        nom = [ALIAS.get(x, x) for x in (h, a)]
        eq = set(hist[hist.liga == cod].Home) | set(hist[hist.liga == cod].Away)
        f = [x for x in nom if x not in eq]
        if f:
            faltan.append((cod, f, sorted(eq)))
            continue
        filas.append({"liga": cod, "fecha": pd.Timestamp(datetime.now(timezone.utc).replace(tzinfo=None)),
                      "hora": hora, "Home": nom[0], "Away": nom[1], "AvgCH": o[0], "AvgCD": o[1], "AvgCA": o[2],
                      "futuro": 1})
    if faltan:
        for cod, f, eq in faltan:
            print(f"[{cod}] sin pareja: {f}\n   nombres del histórico: {eq}")
        raise SystemExit("Añadir a ALIAS (no emparejar por parecido).")
    if not filas:
        print("Hoy no hay partidos programados en estas ligas."); return
    fut = pd.DataFrame(filas)
    fut["temporada"] = fut.liga.map(hist.groupby("liga").temporada.max())
    todo = pd.concat([hist.assign(futuro=0), fut], ignore_index=True).sort_values(["fecha", "liga"]).reset_index(drop=True)
    todo = G.elo(G.añadir_mercado(todo))
    todo = G.forma(todo)
    cj = G.columnas_juego(todo)
    pasado, futuro = todo[todo.futuro == 0], todo[todo.futuro == 1].copy()
    con_mkt = pasado[pasado.liga.isin(MKT_LIGAS) & pasado.m_pl.notna()]
    for obj, y in G.OBJETIVOS.items():
        futuro[f"{obj}_completo"] = G.predecir(con_mkt, futuro, G.MKT + cj, y)
        futuro[f"{obj}_juego"] = G.predecir(pasado, futuro, cj, y)
    lin = [f"# Partidos de hoy ({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC; hora según Promiedos)\n",
           "| liga | hora | partido | 1X2 casa (sin margen) | ambos marcan sí | más de 2.5 | marcador más probable |",
           "|---|---|---|---|---|---|---|"]
    for _, r in futuro.iterrows():
        pb, po = r.ambos_marcan_completo, r.mas_2_5_completo
        # marcador: el par de Poisson que reproduce ESAS p de ambos marcan y más de 2.5,
        # orientado según el 1X2 de la casa (favorito = el de más goles esperados)
        from scipy.optimize import fsolve
        def ecs(x):
            m = G.poisson_1x2(abs(x[0]), abs(x[1]))[3]
            tot = np.add.outer(np.arange(len(m)), np.arange(len(m)))
            return [1 - m[0, :].sum() - m[:, 0].sum() + m[0, 0] - pb, m[tot > 2].sum() - po]
        l1, l2 = sorted(np.abs(fsolve(ecs, (1.4, 1.0))), reverse=True)
        ll, lv = (l1, l2) if r.m_pl >= r.m_pv else (l2, l1)
        m = G.poisson_1x2(ll, lv)[3]
        i, j = np.unravel_index(m[:6, :6].argmax(), (6, 6))
        c = f"{r.m_pl*100:.0f}/{r.m_pe*100:.0f}/{r.m_pv*100:.0f}%" if pd.notna(r.m_pl) else "sin cuota"
        lin.append(f"| {G.LIGAS[r.liga]} | {r.hora} | {r.Home} - {r.Away} | {c} | {pb*100:.0f}% (sin precio {r.ambos_marcan_juego*100:.0f}%) | "
                   f"{po*100:.0f}% (sin precio {r.mas_2_5_juego*100:.0f}%) | {i}-{j} ({m[i, j]*100:.0f}%) |")
    txt = "\n".join(lin) + "\n"
    open(os.path.join(G.CARPETA, "pronosticos_hoy.md"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
