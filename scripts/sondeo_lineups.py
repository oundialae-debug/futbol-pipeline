"""
SONDEO: esquema COMPLETO de /lineups/{id} en un partido viejo.

sondeo_matches.py (23/09) solo miró las claves de nivel superior
(homeTeam/awayTeam) para confirmar que había datos en partidos antiguos.
Antes de construir el backfill de rotación hace falta ver la estructura
entera -- si hay formation, initialLineup/starters, substitutes, y cómo se
identifica a cada jugador -- para saber qué se puede calcular de verdad
(un índice de rotación necesita poder comparar la alineación titular de
HOY contra la de su partido anterior, jugador a jugador).
"""
import os
import json
import requests

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

MATCH_ID = 1183862626  # partido real del histórico, 2026-04-21 (75%)


def main():
    r = requests.get(f"{BASE_URL}/lineups/{MATCH_ID}", headers=HEADERS, timeout=25)
    print(f"HTTP {r.status_code}")
    if r.status_code != 200:
        print(r.text[:2000])
        return
    j = r.json()
    d = j[0] if isinstance(j, list) else j
    print(json.dumps(d, indent=2, ensure_ascii=False)[:6000])


if __name__ == "__main__":
    main()
