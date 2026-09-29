"""
Resultados de una liga de FotMob en el formato de football-data
(Country, League, Season, Date, Time, Home, Away, HG, AG, Res, AvgC*), para
ligas que football-data NO cubre. Una petición por temporada (la lista de
partidos de la liga ya trae el marcador). Sin cuotas: AvgC* quedan vacías.

Primer uso (29/09/2026): Colombia Primera B (FotMob 9125) -> data/football_data/COLB.csv
(football-data no tiene Colombia: su COL.csv redirige a la liga polaca).
Uso: python3 fotmob_resultados.py 9125 COLB Colombia "Primera B" 2019
"""
import os
import sys
import time
import urllib.parse
from datetime import datetime
import requests

UA = {"User-Agent": "Mozilla/5.0"}
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "football_data")


def main(lid, cod, pais, nombre, desde):
    base = f"https://www.fotmob.com/api/data/leagues?id={lid}"
    d = requests.get(base, headers=UA, timeout=30).json()
    filas, futuros = [], 0
    for t in [t for t in d["allAvailableSeasons"] if t[:4] >= desde]:
        time.sleep(1)
        dd = requests.get(f"{base}&season={urllib.parse.quote(t)}", headers=UA, timeout=30).json()
        n = 0
        for m in dd["fixtures"]["allMatches"]:
            s = m["status"]
            if not s.get("finished") or s.get("cancelled") or "scoreStr" not in s:
                continue
            try:
                hg, ag = (int(x) for x in s["scoreStr"].replace(" ", "").split("-"))
            except ValueError:
                continue
            f = datetime.strptime(s["utcTime"][:16], "%Y-%m-%dT%H:%M")
            filas.append([pais, nombre, t, f.strftime("%d/%m/%Y"), f.strftime("%H:%M"), m["home"]["name"],
                          m["away"]["name"], hg, ag, "H" if hg > ag else "A" if ag > hg else "D"] + [""] * 3)
            n += 1
        print(f"  {cod} {t}: {n} partidos terminados")
    os.makedirs(FD, exist_ok=True)
    with open(os.path.join(FD, f"{cod}.csv"), "w", encoding="utf-8") as fh:
        fh.write("Country,League,Season,Date,Time,Home,Away,HG,AG,Res,AvgCH,AvgCD,AvgCA\n")
        for r in filas:
            fh.write(",".join(str(x).replace(",", " ") for x in r) + "\n")
    print(f"{len(filas)} partidos -> {cod}.csv")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
