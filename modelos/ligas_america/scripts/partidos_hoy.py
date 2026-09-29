"""
Partidos de HOY (hora de Buenos Aires) en Argentina, Brasil y México, por liga.
Pocas llamadas: /leagues de Argentina (para ver IDs) y /matches por país y día.
Escribe modelos/ligas_america/partidos_hoy.md y data/partidos_hoy.csv (solo
en esta carpeta). No elige liga sola: imprime y se decide mirando.
"""
import os
import csv
import time
from datetime import datetime, timedelta, timezone
import requests

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
CARPETA = "modelos/ligas_america"
TZ = "America/Argentina/Buenos_Aires"
FECHA = os.environ.get("FECHA") or (datetime.now(timezone.utc) - timedelta(hours=3)).date().isoformat()
PAISES = ("Argentina", "Brazil", "Mexico")


def pedir(path, params=None):
    print(f"  GET {path} {params}", flush=True)
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] {path} {params}"); return None
        return r.json()
    return None


def lista(j):
    if isinstance(j, dict):
        return j.get("data") or []
    return j or []


def main():
    out = [f"# Partidos del {FECHA} (hora de Buenos Aires)\n"]
    filas = []
    ligas = lista(pedir("/leagues", {"countryName": "Argentina", "limit": 100}))
    out.append("## Ligas de Argentina en la API\n\n| id | nombre | temporadas |\n|---|---|---|")
    for l in ligas:
        temps = sorted({s.get("season") for s in (l.get("seasons") or []) if isinstance(s, dict)})
        out.append(f"| {l.get('id')} | {l.get('name')} | {', '.join(map(str, temps[-5:]))} |")
    for pais in PAISES:
        # tope de 5 páginas y corte si una página no trae ids nuevos: la
        # primera versión se quedó en bucle (la API repetía la página)
        todos, vistos = [], set()
        for pagina in range(5):
            lote = lista(pedir("/matches", {"countryName": pais, "date": FECHA, "timezone": TZ,
                                            "limit": 100, "offset": 100 * pagina}))
            nuevos = [p for p in lote if isinstance(p, dict) and p.get("id") not in vistos]
            print(f"  {pais} página {pagina}: {len(lote)} partidos, {len(nuevos)} nuevos", flush=True)
            vistos |= {p.get("id") for p in nuevos}
            todos += nuevos
            if len(lote) < 100 or not nuevos:
                break
        out.append(f"\n## {pais}: {len(todos)} partidos\n\n| liga_id | liga | temporada | hora | partido | estado |\n|---|---|---|---|---|---|")
        for p in sorted(todos, key=lambda p: ((p.get("league") or {}).get("id") or 0, str(p.get("date")))):
            lg = p.get("league") or {}
            est = p.get("state") or {}
            est = est.get("description") if isinstance(est, dict) else est
            loc, vis = (p.get("homeTeam") or {}), (p.get("awayTeam") or {})
            out.append(f"| {lg.get('id')} | {lg.get('name')} | {lg.get('season')} | {str(p.get('date'))[11:16]} UTC "
                       f"| {loc.get('name')} - {vis.get('name')} | {est} |")
            filas.append({"match_id": p.get("id"), "pais": pais, "liga_id": lg.get("id"), "liga": lg.get("name"),
                          "temporada": lg.get("season"), "fecha_utc": p.get("date"),
                          "local_id": loc.get("id"), "local": loc.get("name"),
                          "visitante_id": vis.get("id"), "visitante": vis.get("name"), "estado": est})
    os.makedirs(f"{CARPETA}/data", exist_ok=True)
    with open(f"{CARPETA}/data/partidos_hoy.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas else ["match_id"])
        w.writeheader(); w.writerows(filas)
    open(f"{CARPETA}/partidos_hoy.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
