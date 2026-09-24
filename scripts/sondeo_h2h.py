"""
SONDEO: esquema real de /head-2-head, y si va MÁS ALLÁ de los ~13 meses
que ya tenemos en el histórico propio.

La spec dice "últimas 10 confrontaciones", sin decir hasta cuándo. El H2H
calculado del propio historico_partidos.csv (calcular_h2h en rasgos.py)
solo ve partidos dentro de esa ventana -- 52% de los pares no se habían
enfrentado nunca ahí. Si la API guarda historial más profundo (temporadas
anteriores, no solo lo que nosotros hemos cosechado), esto podría arreglar
justo esa debilidad. Si NO va más allá de lo que ya tenemos, no merece la
pena otro backfill de ~2500 llamadas.

Un par de equipos real del histórico, elegido porque son de la misma
liga desde hace años (más probable que tengan historial profundo real).
"""
import os
import json
import requests

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

# Real Madrid vs Barcelona -- clásico, décadas de historial si la API lo
# guarda. IDs reales tomados de historico_partidos.csv.
CASOS = [
    ("Real Madrid vs Barcelona", 461175, 450963),
]


def main():
    for etiqueta, id1, id2 in CASOS:
        r = requests.get(f"{BASE_URL}/head-2-head",
                         headers=HEADERS, params={"teamIdOne": id1, "teamIdTwo": id2},
                         timeout=25)
        print(f"[{etiqueta}] HTTP {r.status_code}")
        if r.status_code != 200:
            print(r.text[:1000])
            continue
        j = r.json()
        partidos = j if isinstance(j, list) else j.get("data", [])
        print(f"  {len(partidos)} partidos devueltos")
        for p in partidos[:12]:
            print(f"    {p.get('date')}  {(p.get('homeTeam') or {}).get('name')} "
                  f"{(p.get('state') or {}).get('score', {}).get('current')} "
                  f"{(p.get('awayTeam') or {}).get('name')}  "
                  f"liga={(p.get('league') or {}).get('name')} "
                  f"temporada={(p.get('league') or {}).get('season')}")
        if partidos:
            print("\n  claves de un partido completo:")
            print(json.dumps(partidos[0], indent=2, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
