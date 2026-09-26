"""
Alineaciones reales de Inglaterra-España y Chequia-Croacia (26/09/2026),
para rehacer los pronósticos con el once de verdad en vez del probable.
Solo /lineups de los 2 partidos (2 llamadas). Tema aparte de ambos marcan.
"""
import os, json, requests
import pandas as pd

HEADERS = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}   # nunca se imprime
eq = json.load(open("data/selecciones/equipos.json"))
filas = []
for loc, vis, mid in eq["cruces"]:
    r = requests.get(f"https://soccer.highlightly.net/lineups/{mid}", headers=HEADERS, timeout=30)
    print(f"{loc} - {vis}: HTTP {r.status_code}")
    if r.status_code != 200:
        continue
    j = r.json()
    json.dump(j, open(f"data/selecciones/raw/lineups_hoy_{mid}.json", "w"), ensure_ascii=False)
    j = j[0] if isinstance(j, list) and j else j
    for lado in ("homeTeam", "awayTeam"):
        t = (j or {}).get(lado) or {}
        for linea in t.get("initialLineup") or []:
            for p in (linea if isinstance(linea, list) else [linea]):
                if isinstance(p, dict):
                    filas.append({"match_id": mid, "equipo": t.get("name"), "equipo_id": t.get("id"),
                                  "formacion": t.get("formation"), "jugador_id": p.get("id"),
                                  "jugador": p.get("name"), "posicion": p.get("position")})
d = pd.DataFrame(filas)
d.to_csv("data/selecciones/alineaciones_hoy.csv", index=False)
print(d.groupby("equipo").size().to_dict() if len(d) else "sin alineaciones todavía")
