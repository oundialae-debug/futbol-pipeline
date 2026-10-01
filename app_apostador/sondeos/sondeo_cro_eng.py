"""Llamadas para la previa Croacia–Inglaterra (03/10/2026).

Permiso del usuario el 01/10/2026: «todas las llamadas que necesites, no tienes
límite para esta vez». Sin vídeos (/highlights): el usuario duda de que sea
legal ponerlos. /lineups no se pide: la API solo las da desde 40' antes.

  1   /head-2-head Croacia (3337) – Inglaterra (9294): últimos 10 reales
  1   /matches/1301122767: el partido del sábado (sede, árbitro, tiempo, noticias)
  1   /matches/1267466568: Mundial, Inglaterra 4-2 Croacia (eventos y tiros)
  22  /players/{id}: perfil de los 22 titulares probables (lesiones, club, valor)
  22  /players/{id}/statistics: su temporada en todas las competiciones
Total: 47 como mucho. Guarda la respuesta ENTERA en raw/cro_eng/ y no repite
lo que ya está guardado.
"""
import json
import os
from pathlib import Path

import requests

BASE = "https://soccer.highlightly.net"
RAW = Path(__file__).resolve().parent / "raw" / "cro_eng"
RAW.mkdir(parents=True, exist_ok=True)
CLAVE = os.environ["HIGHLIGHTLY_API_KEY"]
JUGADORES = [33481, 41999419, 20774467, 56061159, 29372028, 382207, 210259, 369005, 2367015, 2296980, 174678,   # Croacia
             29778, 235214, 22364342, 3086524, 45803366, 10943485, 45717, 22344861, 3175074, 26160883, 50432599]  # Inglaterra
PEDIDOS = [("h2h_3337_9294", "/head-2-head", {"teamIdOne": 3337, "teamIdTwo": 9294}),
           ("match_1301122767", "/matches/1301122767", {}),
           ("match_1267466568", "/matches/1267466568", {})]
PEDIDOS += [(f"player_{j}", f"/players/{j}", {}) for j in JUGADORES]
PEDIDOS += [(f"player_stats_{j}", f"/players/{j}/statistics", {}) for j in JUGADORES]

llamadas = 0
for nombre, ruta, params in PEDIDOS[:47]:
    f = RAW / f"{nombre}.json"
    if f.exists():
        print(nombre, "ya guardado")
        continue
    r = requests.get(BASE + ruta, params=params, headers={"x-rapidapi-key": CLAVE}, timeout=30)
    llamadas += 1
    print(nombre, "HTTP", r.status_code, len(r.content), "bytes")
    if r.status_code == 200:
        f.write_text(json.dumps(r.json(), ensure_ascii=False, indent=1))
print("llamadas hechas:", llamadas)
