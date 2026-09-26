"""
SONDEO: ¿desde cuándo da la API xG y xA POR JUGADOR? (26/09/2026)

/box-score/{matchId} trae, jugador a jugador, expectedGoals y
expectedAssists (esquema PlayerBoxScoreStatisticsDto de la spec). El
backfill de box-score del 21/09 los recibió en 2.537 partidos y los tiró:
solo guardó 7 agregados de equipo. Antes de volver a pagarlos, se mira en
qué temporadas existen de verdad -- UN partido no mide una temporada (ya
engañó dos veces: xG de 2024/25 y alineaciones de 2023/24), así que se
piden 2 partidos por mes muestreado, repartidos de ago-2023 a sep-2026.

~24 llamadas. Escribe sondeo_xg_jugador.md.
"""
import os
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
BASE_URL = "https://soccer.highlightly.net"
MESES = ["2023-09", "2023-12", "2024-03", "2024-05", "2024-09", "2024-12",
         "2025-02", "2025-04", "2025-09", "2026-01", "2026-04", "2026-09"]
POR_MES = 2


def pedir(path):
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            return None, r.status_code
        try:
            return r.json(), 200
        except Exception:
            return None, "no-json"
    return None, "sin respuesta"


def main():
    h = pd.read_csv("data/historico_partidos.csv")
    h["mes"] = h.fecha.str[:7]
    lineas = ["# Sondeo: xG y xA por jugador en /box-score\n",
              "| mes | liga | partido | estado | jugadores | con xG | con xA | suma xG (ambos) |",
              "|---|---|---|---|---|---|---|---|"]
    ejemplo = None
    for mes in MESES:
        # ligas grandes primero; un partido de liga distinta por cada toma
        cand = h[(h.mes == mes)].sort_values("liga_id").drop_duplicates("liga").head(POR_MES)
        for _, f in cand.iterrows():
            j, est = pedir(f"/box-score/{f.match_id}")
            equipos = (j.get("data") if isinstance(j, dict) else j) or []
            jug = [p for e in equipos if isinstance(e, dict) for p in (e.get("players") or [])]
            st = [p.get("statistics") or {} for p in jug]
            con_xg = sum(s.get("expectedGoals") is not None for s in st)
            con_xa = sum(s.get("expectedAssists") is not None for s in st)
            suma = sum(float(s.get("expectedGoals") or 0) for s in st)
            if ejemplo is None and con_xg:
                ejemplo = sorted(st[0].keys())
            fila = (f"| {mes} | {f.liga} | {f.local} - {f.visitante} | {est} | {len(jug)} | "
                    f"{con_xg} | {con_xa} | {suma:.2f} |")
            print(fila)
            lineas.append(fila)
    if ejemplo:
        lineas += ["\n## Campos de estadística de un jugador (respuesta entera)\n", ", ".join(ejemplo)]
    open("sondeo_xg_jugador.md", "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("\nEscrito sondeo_xg_jugador.md")


if __name__ == "__main__":
    main()
