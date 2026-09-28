"""NBA fase 1: lista de partidos (resultado y marcador por cuartos) de varias temporadas.

Plan gratuito: 100 llamadas/dia, cuota APARTE de la de futbol. /matches pagina de
100 en 100, asi que una temporada (~1.230 partidos + playoffs) son ~15 llamadas.
Guarda cada pagina CRUDA (para mirar la respuesta entera) y un CSV plano.
Reanudable: una pagina ya guardada y llena no se vuelve a pedir.
"""
import csv
import json
import os
import sys
from pathlib import Path

import requests

URL = "https://nba.highlightly.net/matches"
H = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}
TEMPORADAS = [int(t) for t in os.environ.get("TEMPORADAS", "2026,2025,2024,2023,2022").split(",")]
TOPE = int(os.environ.get("TOPE_LLAMADAS", "70"))
RESERVA = 10  # no bajar de aqui en la cuota diaria
CRUDO = Path("data/nba/partidos_crudo")
CRUDO.mkdir(parents=True, exist_ok=True)

llamadas = 0
quedan = None
for temporada in TEMPORADAS:
    offset = 0
    while True:
        f = CRUDO / f"{temporada}_{offset:05d}.json"
        if f.exists():
            j = json.loads(f.read_text())
            if len(j.get("data", [])) == 100:  # pagina llena: ya esta
                offset += 100
                continue
        if llamadas >= TOPE:
            print(f"Tope de {TOPE} llamadas alcanzado"); break
        r = requests.get(URL, headers=H, timeout=30,
                         params={"league": "NBA", "season": temporada, "limit": 100, "offset": offset})
        llamadas += 1
        quedan = r.headers.get("x-ratelimit-requests-remaining")
        print(f"temporada {temporada} offset {offset}: HTTP {r.status_code}, quedan {quedan}")
        if not r.ok:
            print(r.text[:300]); sys.exit(1)
        j = r.json()
        f.write_text(json.dumps(j, ensure_ascii=False))
        n = len(j.get("data", []))
        total = (j.get("pagination") or {}).get("totalCount")
        print(f"   {n} partidos (total temporada: {total})")
        if quedan is not None and int(quedan) <= RESERVA:
            print("Cuota diaria casi agotada, paro"); break
        if n < 100:
            break
        offset += 100
    else:
        continue
    if llamadas >= TOPE or (quedan is not None and int(quedan) <= RESERVA):
        break

# CSV plano con todo lo guardado
filas = {}
for f in sorted(CRUDO.glob("*.json")):
    for p in json.loads(f.read_text()).get("data", []):
        st = p.get("state") or {}
        sc = st.get("score") or {}
        filas[p["id"]] = {
            "id": p["id"], "liga": p.get("league"), "temporada": p.get("season"), "fecha": p.get("date"),
            "local_id": p["homeTeam"]["id"], "local": p["homeTeam"].get("displayName") or p["homeTeam"]["name"],
            "visitante_id": p["awayTeam"]["id"], "visitante": p["awayTeam"].get("displayName") or p["awayTeam"]["name"],
            "estado": st.get("description"), "periodo": st.get("period"),
            "cuartos_local": json.dumps(sc.get("homeTeam")), "cuartos_visitante": json.dumps(sc.get("awayTeam")),
        }
with open("data/nba/partidos.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(next(iter(filas.values())).keys()) if filas else ["id"])
    w.writeheader()
    for k in sorted(filas, key=lambda k: filas[k]["fecha"] or ""):
        w.writerow(filas[k])
print(f"\n{llamadas} llamadas. data/nba/partidos.csv: {len(filas)} partidos")
