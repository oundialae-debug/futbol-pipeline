"""Sondeo de 3 partidos TERMINADOS en /matches/{id} (permiso del usuario el 01/10/2026: 3 llamadas).

Pregunta: ¿vienen rellenos después del pitido los tiros (shots), los eventos
(goles, cambios, VAR) y las predicciones en directo (predictions.live)? Lo
guardado hasta ahora era de antes de empezar y no lo dice.

Guarda la respuesta ENTERA en app_apostador/sondeos/raw/match_<id>.json.
Si el fichero ya existe, no vuelve a pedirlo: nunca más de 3 llamadas.
"""
import json
import os
from pathlib import Path

import requests

IDS = [1301103194,   # Chequia 0-2 Inglaterra, 29/09/2026 (Nations League)
       1301102343,   # España 4-1 Croacia, 29/09/2026 (Nations League)
       1336406078]   # Atlético 2-1 Real Madrid, 20/09/2026 (LaLiga)
RAW = Path(__file__).resolve().parent / "raw"
RAW.mkdir(exist_ok=True)
CLAVE = os.environ["HIGHLIGHTLY_API_KEY"]
llamadas = 0
for mid in IDS[:3]:
    f = RAW / f"match_{mid}.json"
    if f.exists():
        print(mid, "ya guardado, no se pide")
        continue
    r = requests.get(f"https://soccer.highlightly.net/matches/{mid}", headers={"x-rapidapi-key": CLAVE}, timeout=30)
    llamadas += 1
    print(mid, "HTTP", r.status_code)
    if r.status_code != 200:
        continue
    f.write_text(json.dumps(r.json(), ensure_ascii=False, indent=1))
    d = r.json()
    d = d[0] if isinstance(d, list) else d
    pr = d.get("predictions") or {}
    print("   estado:", d.get("state"))
    print("   events:", len(d.get("events") or []), sorted({e.get("type") for e in d.get("events") or []}))
    for t in ("homeTeam", "awayTeam"):
        print(f"   {t} shots:", len(d.get(t, {}).get("shots") or []))
    print("   predictions prematch/live:", len(pr.get("prematch") or []), len(pr.get("live") or []))
    print("   news:", len(d.get("news") or []), "venue:", d.get("venue"))
print("llamadas hechas:", llamadas)
