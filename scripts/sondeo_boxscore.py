"""
SONDEO: ¿QUE TRAE /box-score DE VERDAD?

Antes de construir nada sobre esto, comprobar el esquema EXACTO contra un
partido real -- la regla de CLAUDE.md que ya costo una semana una vez
("First Team To Score" con T mayuscula, nadie lo miro antes de usarlo).

Imprime las claves de la respuesta y las estadisticas de un jugador de
muestra, para verificar los nombres exactos antes de escribir el backfill.
"""
import os
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}


def pedir(path, params=None):
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    return r.status_code, (r.json() if r.status_code == 200 else None)


def desempaquetar(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def main():
    hoy = datetime.now(timezone.utc).date()
    mid = None
    for dd in range(1, 15):
        fecha = (hoy - timedelta(days=dd)).isoformat()
        _, j = pedir("/matches", {"leagueId": 119924, "date": fecha, "limit": 10})
        for p in desempaquetar(j) if j else []:
            desc = str((p.get("state") or {}).get("description", ""))
            if "finish" in desc.lower():
                mid = p["id"]
                break
        if mid:
            break

    print(f"partido probado: {mid}")
    if not mid:
        print("no se encontro partido terminado")
        return

    status, j = pedir(f"/box-score/{mid}")
    print(f"status /box-score: {status}")
    equipos = desempaquetar(j) if j else []
    print(f"equipos en la respuesta: {len(equipos)}")
    if not equipos:
        return
    eq = equipos[0]
    print(f"claves del equipo: {list(eq.keys())}")
    jugadores = eq.get("players")
    if jugadores is None:
        for k, v in eq.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                jugadores = v
                print(f"  (lista de jugadores encontrada en la clave '{k}')")
                break
    if not jugadores:
        print("no se encontro lista de jugadores")
        return
    print(f"\njugadores: {len(jugadores)}")
    jug = jugadores[0]
    print(f"claves de un jugador: {list(jug.keys())}")
    stats = jug.get("statistics")
    print(f"\nestadisticas del jugador (claves EXACTAS):")
    if isinstance(stats, dict):
        for k, v in stats.items():
            print(f"  {k} = {v}")
    else:
        print(f"  (no es un dict, es: {type(stats)}) -> {stats}")


if __name__ == "__main__":
    main()
