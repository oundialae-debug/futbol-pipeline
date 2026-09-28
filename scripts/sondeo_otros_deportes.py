"""Sondeo minimo: sirve nuestra clave para otros deportes? (28/09/2026)

Como mucho 2 llamadas: host propio de la NBA y, solo si falla, la All Sports API.
Nunca imprime la clave.
"""
import os
import requests

H = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}
PRUEBAS = [
    ("nba.highlightly.net", "https://nba.highlightly.net/matches"),
    ("sports.highlightly.net/nba", "https://sports.highlightly.net/nba/matches"),
]
for nombre, url in PRUEBAS:
    r = requests.get(url, headers=H, params={"date": "2026-03-15", "limit": 3}, timeout=30)
    print(f"\n== {nombre}: HTTP {r.status_code}")
    for k in ("x-ratelimit-requests-limit", "x-ratelimit-requests-remaining"):
        print(f"  {k}: {r.headers.get(k)}")
    try:
        j = r.json()
    except ValueError:
        print("  cuerpo no JSON:", r.text[:300])
        continue
    if r.ok and isinstance(j, dict):
        print("  plan:", j.get("plan"), "| total partidos ese dia:", (j.get("pagination") or {}).get("totalCount"))
        for p in j.get("data", [])[:3]:
            print("  ", p.get("league"), p.get("season"), p["homeTeam"]["name"], "-", p["awayTeam"]["name"],
                  (p.get("state") or {}).get("description"))
        break
    print("  respuesta:", str(j)[:300])
