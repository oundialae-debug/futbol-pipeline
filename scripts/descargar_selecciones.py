"""
Datos de 4 selecciones para Inglaterra-España y Chequia-Croacia
(Nations League, 26/09/2026). Tema APARTE del proyecto de ambos marcan
(ver modelos/ambos_marcan/CLAUDE.md "PUNTO DE RETORNO").

Descarga, sin modelo (el análisis viene después):
  1. Los partidos de hoy de la Nations League (liga 5039) -> ids de equipo.
  2. Por selección: /teams/{id}, /teams/statistics/{id} desde 2026-01-01,
     /last-five-games, y TODOS sus partidos de 2025 y 2026 (como local y
     como visitante, cualquier competición: Mundial, Nations League,
     amistosos...).
  3. Por cada partido terminado: /statistics (del equipo), /lineups
     (titulares), /box-score (jugador a jugador: minutos, xG, xA...).
  4. /head-2-head de cada cruce.

Guarda la respuesta ENTERA de cada llamada en data/selecciones/raw/ (lección
de este repo: el box-score del 21/09 se pagó y se tiró). Además, tablas
planas en data/selecciones/*.csv para trabajar. Tope de llamadas.
"""
import os
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
BASE_URL = "https://soccer.highlightly.net"
LIGA_NL = 5039
HOY = datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
CRUCES = [("England", "Spain"), ("Czech Republic", "Croatia")]
TEMPORADAS = (2025, 2026)
DESDE = "2025-01-01"
TOPE = int(os.environ.get("TOPE_LLAMADAS", "700"))
CARPETA = "data/selecciones"
RAW = f"{CARPETA}/raw"
llamadas = [0]


def pedir(path, params=None, nombre=None):
    if llamadas[0] >= TOPE:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] {path} {params or ''}")
            return None
        try:
            j = r.json()
        except Exception:
            return None
        if nombre:
            with open(f"{RAW}/{nombre}.json", "w", encoding="utf-8") as f:
                json.dump(j, f, ensure_ascii=False)
        return j
    return None


def lista(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def terminado(p):
    e = p.get("state")
    d = (e.get("description") if isinstance(e, dict) else e) or ""
    return "finish" in str(d).lower()


def marcador(p):
    s = ((p.get("state") or {}).get("score") or {}).get("current") if isinstance(p.get("state"), dict) else None
    try:
        a, b = str(s).split("-")
        return int(a), int(b)
    except Exception:
        return None, None


def main():
    os.makedirs(RAW, exist_ok=True)
    hoy = lista(pedir("/matches", {"leagueId": LIGA_NL, "date": HOY, "timezone": "Europe/Madrid"},
                      f"nations_league_{HOY}"))
    equipos, cruces_ids = {}, []
    for loc, vis in CRUCES:
        p = next((x for x in hoy if (x.get("homeTeam") or {}).get("name") == loc
                  and (x.get("awayTeam") or {}).get("name") == vis), None)
        if not p:
            print(f"[!] No encuentro {loc} - {vis} hoy en la Nations League"); continue
        equipos[loc], equipos[vis] = p["homeTeam"]["id"], p["awayTeam"]["id"]
        cruces_ids.append((loc, vis, p["id"]))
        print(f"{loc} ({p['homeTeam']['id']}) - {vis} ({p['awayTeam']['id']})  partido {p['id']}")

    partidos = {}
    for nombre, tid in equipos.items():
        clave = nombre.replace(" ", "_").lower()
        pedir(f"/teams/{tid}", nombre=f"equipo_{clave}")
        pedir(f"/teams/statistics/{tid}", {"fromDate": "2026-01-01"}, f"estadisticas_2026_{clave}")
        pedir("/last-five-games", {"teamId": tid}, f"ultimos5_{clave}")
        for temp in TEMPORADAS:
            for lado in ("homeTeamId", "awayTeamId"):
                offset = 0
                while True:
                    j = pedir("/matches", {lado: tid, "season": temp, "limit": 100, "offset": offset},
                              f"partidos_{clave}_{temp}_{lado}_{offset}")
                    lote = lista(j) if j else []
                    for p in lote:
                        if isinstance(p, dict) and p.get("id") and str(p.get("date", ""))[:10] >= DESDE:
                            partidos[p["id"]] = p
                    if len(lote) < 100:
                        break
                    offset += 100
    for loc, vis, _ in cruces_ids:
        pedir("/head-2-head", {"teamIdOne": equipos[loc], "teamIdTwo": equipos[vis]},
              f"h2h_{loc}_{vis}".replace(" ", "_").lower())

    filas_p, filas_est, filas_lu, filas_box = [], [], [], []
    for mid, p in sorted(partidos.items(), key=lambda kv: str(kv[1].get("date"))):
        gl, gv = marcador(p)
        filas_p.append({"match_id": mid, "fecha": str(p.get("date"))[:10],
                        "competicion": (p.get("league") or {}).get("name"),
                        "local_id": (p.get("homeTeam") or {}).get("id"), "local": (p.get("homeTeam") or {}).get("name"),
                        "visitante_id": (p.get("awayTeam") or {}).get("id"), "visitante": (p.get("awayTeam") or {}).get("name"),
                        "goles_l": gl, "goles_v": gv, "terminado": terminado(p)})
        if not terminado(p):
            continue
        for eq in lista(pedir(f"/statistics/{mid}", nombre=f"statistics_{mid}")):
            if isinstance(eq, dict):
                for s in eq.get("statistics") or []:
                    filas_est.append({"match_id": mid, "equipo_id": (eq.get("team") or {}).get("id"),
                                      "estadistica": s.get("displayName"), "valor": s.get("value")})
        lu = pedir(f"/lineups/{mid}", nombre=f"lineups_{mid}")
        lu = lu[0] if isinstance(lu, list) and lu else lu
        if isinstance(lu, dict):
            for lado in ("homeTeam", "awayTeam"):
                t = lu.get(lado) or {}
                for linea in t.get("initialLineup") or []:
                    for j in (linea if isinstance(linea, list) else [linea]):
                        if isinstance(j, dict):
                            filas_lu.append({"match_id": mid, "equipo_id": t.get("id"), "formacion": t.get("formation"),
                                             "jugador_id": j.get("id"), "jugador": j.get("name"),
                                             "posicion": j.get("position")})
        for eq in lista(pedir(f"/box-score/{mid}", nombre=f"boxscore_{mid}")):
            if not isinstance(eq, dict):
                continue
            tid = (eq.get("team") or {}).get("id")
            for j in eq.get("players") or []:
                st = j.get("statistics") or {}
                st = (st[0] if st else {}) if isinstance(st, list) else st
                filas_box.append({"match_id": mid, "equipo_id": tid, "jugador_id": j.get("id"),
                                  "jugador": j.get("name"), "posicion": j.get("position"),
                                  "minutos": j.get("minutesPlayed"), "suplente": j.get("isSubstitute"),
                                  "nota": j.get("matchRating"), **st})

    pd.DataFrame(filas_p).to_csv(f"{CARPETA}/partidos.csv", index=False)
    pd.DataFrame(filas_est).to_csv(f"{CARPETA}/estadisticas_partido.csv", index=False)
    pd.DataFrame(filas_lu).to_csv(f"{CARPETA}/alineaciones.csv", index=False)
    pd.DataFrame(filas_box).to_csv(f"{CARPETA}/jugadores_partido.csv", index=False)
    json.dump({"equipos": equipos, "cruces": cruces_ids}, open(f"{CARPETA}/equipos.json", "w"))
    dp = pd.DataFrame(filas_p)
    print(f"\n{len(dp)} partidos desde {DESDE} ({dp.terminado.sum() if len(dp) else 0} terminados). "
          f"Filas: estadísticas {len(filas_est)}, alineaciones {len(filas_lu)}, jugadores {len(filas_box)}. "
          f"Llamadas {llamadas[0]} de {TOPE}.")
    if len(dp):
        for nombre, tid in equipos.items():
            m = dp[(dp.local_id == tid) | (dp.visitante_id == tid)]
            print(f"  {nombre:15s} {len(m):3d} partidos, competiciones: {m.competicion.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
