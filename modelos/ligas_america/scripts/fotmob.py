"""
Descarga de FotMob (api interna de su web, sin clave) para ARG (112),
BRA (268) y MEX (230). Pedido el 29/09/2026: la API de Highlightly estaba sin
cuota y el usuario señaló que webs como FotMob/FootyStats dan xG y xA.

Por partido terminado (/api/data/matchDetails):
  fotmob_partidos.csv  una fila: fecha, equipos, marcador, árbitro, tiempo,
                       estadio, y por lado: xG, xGOT, xG de jugada/balón
                       parado/sin penalti, remates (total, a puerta, dentro del
                       área), ocasiones claras (y falladas), toques en el área
                       rival, posesión, pases, córners, faltas, tarjetas, nota
                       FotMob del equipo, edad media y valor de mercado del once.
  fotmob_jugadores.csv una fila por jugador con estadísticas: titular o no,
                       minutos, nota, goles, asistencias, xG, xA, xGOT, remates,
                       y en porteros paradas y goles evitados.

OJO (fuga): el bloque del árbitro en infoBox trae sus medias A DÍA DE HOY;
no se guarda. El valor de mercado del once es el de FotMob hoy para ese
jugador, no el de la fecha del partido: se guarda pero es sospechoso de
fuga hasta comprobarlo (no usar en el modelo sin probarlo aparte).

Una petición por segundo, reanudable (no repite partidos ya guardados), y
cuenta en voz alta los partidos sin xG (en temporadas viejas puede faltar).
Uso: LIGAS=ARG,BRA,MEX python3 modelos/ligas_america/scripts/fotmob.py
"""
import os
import csv
import sys
import time
import json
import urllib.parse
import requests

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
R_PART = os.path.join(CARPETA, "fotmob_partidos.csv")
R_JUG = os.path.join(CARPETA, "fotmob_jugadores.csv")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
PAUSA = float(os.environ.get("PAUSA", "1.0"))

LIGAS = {"ARG": 112, "BRA": 268, "MEX": 230}
# temporadas por liga: las que devuelve allAvailableSeasons desde 2023
DESDE = "2023"

ESTAD = {  # título exacto de FotMob -> columna
    "Expected goals (xG)": "xg", "xG on target (xGOT)": "xgot", "xG open play": "xg_jugada",
    "xG set play": "xg_parado", "xG non-penalty": "xg_sinpen", "Total shots": "remates",
    "Shots on target": "remates_puerta", "Shots inside box": "remates_area",
    "Big chances": "ocasiones", "Big chances missed": "ocasiones_falladas",
    "Touches in opposition box": "toques_area", "Ball possession": "posesion",
    "Passes": "pases", "Corners": "corners", "Fouls committed": "faltas",
    "Yellow cards": "amarillas", "Red cards": "rojas", "Keeper saves": "paradas",
    "Offsides": "fueras_juego",
}
JUG = {"rating_title": "nota", "minutes_played": "minutos", "goals": "goles", "assists": "asistencias",
       "expected_goals": "xg", "expected_assists": "xa", "expected_goals_on_target": "xgot",
       "total_shots": "remates", "saves": "paradas", "goals_prevented": "goles_evitados",
       "expected_goals_on_target_faced": "xgot_recibido", "chances_created": "pases_clave"}

C_PART = (["match_id", "liga", "temporada", "ronda", "fecha_utc", "local_id", "local", "visitante_id",
           "visitante", "goles_l", "goles_v", "arbitro", "arbitro_id", "estadio", "temp", "lluvia"]
          + [f"{l}_{c}" for l in ("l", "v") for c in list(ESTAD.values())
             + ["nota_equipo", "edad_once", "valor_once", "formacion"]])
C_JUG = ["match_id", "fecha_utc", "equipo_id", "jugador_id", "nombre", "titular", "portero"] + list(JUG.values())

sesion = requests.Session()
peticiones = [0]


def pedir(url):
    for intento in range(3):
        time.sleep(PAUSA)
        peticiones[0] += 1
        try:
            r = sesion.get(url, headers=UA, timeout=30)
            if r.status_code == 200:
                return r.json()
            print(f"  [HTTP {r.status_code}] {url}", flush=True)
            if r.status_code in (403, 429):
                time.sleep(30 * (intento + 1))
        except Exception as e:
            print(f"  [{type(e).__name__}] {url}", flush=True)
            time.sleep(5)
    return None


def num(v):
    if v is None:
        return None
    s = str(v).split(" ")[0].replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None


def partidos_de_liga(cod, lid):
    d = pedir(f"https://www.fotmob.com/api/data/leagues?id={lid}")
    temps = [t for t in d["allAvailableSeasons"] if t[:4] >= DESDE]
    out = []
    for t in temps:
        dd = d if t == d["details"].get("selectedSeason") else pedir(
            f"https://www.fotmob.com/api/data/leagues?id={lid}&season={urllib.parse.quote(t)}")
        if not dd:
            continue
        am = dd["fixtures"]["allMatches"]
        fin = [m for m in am if m["status"].get("finished") and not m["status"].get("cancelled")]
        print(f"  {cod} {t}: {len(am)} partidos, {len(fin)} terminados", flush=True)
        out += [(m["id"], t) for m in fin]
    return out


def extraer(cod, temporada, mid, d):
    c, g = d["content"], d["general"]
    ib = c["matchFacts"].get("infoBox") or {}
    h = d["header"]["teams"]
    fila = {"match_id": mid, "liga": cod, "temporada": temporada, "ronda": g.get("leagueRoundName"),
            "fecha_utc": g.get("matchTimeUTCDate"), "local_id": h[0]["id"], "local": h[0]["name"],
            "visitante_id": h[1]["id"], "visitante": h[1]["name"], "goles_l": h[0].get("score"),
            "goles_v": h[1].get("score"), "arbitro": (ib.get("Referee") or {}).get("text"),
            "arbitro_id": (ib.get("Referee") or {}).get("id"), "estadio": (ib.get("Stadium") or {}).get("name"),
            "temp": (c.get("weather") or {}).get("temperature"), "lluvia": (c.get("weather") or {}).get("precipitation")}
    for grp in (((c.get("stats") or {}).get("Periods") or {}).get("All") or {}).get("stats") or []:
        for s in grp.get("stats") or []:
            col = ESTAD.get(s.get("title"))
            v = s.get("stats") or [None, None]
            if col and v[0] is not None:
                fila[f"l_{col}"], fila[f"v_{col}"] = num(v[0]), num(v[1])
    lu = c.get("lineup") or {}
    for lado, k in (("l", "homeTeam"), ("v", "awayTeam")):
        t = lu.get(k) or {}
        fila[f"{lado}_nota_equipo"] = t.get("rating")
        fila[f"{lado}_edad_once"] = t.get("averageStarterAge")
        fila[f"{lado}_valor_once"] = t.get("totalStarterMarketValue")
        fila[f"{lado}_formacion"] = t.get("formation")
    titulares = {str(p["id"]) for k in ("homeTeam", "awayTeam") for p in ((lu.get(k) or {}).get("starters") or [])}
    jug = []
    for pid, p in (c.get("playerStats") or {}).items():
        if not p.get("stats"):
            continue
        fj = {"match_id": mid, "fecha_utc": fila["fecha_utc"], "equipo_id": p.get("teamId"), "jugador_id": pid,
              "nombre": p.get("name"), "titular": int(str(pid) in titulares), "portero": int(bool(p.get("isGoalkeeper")))}
        for grp in p["stats"]:
            for s in (grp.get("stats") or {}).values():
                col = JUG.get(s.get("key"))
                if col and col not in fj:
                    fj[col] = (s.get("stat") or {}).get("value")
        jug.append(fj)
    return fila, jug


def ya():
    if not os.path.exists(R_PART):
        return set()
    with open(R_PART, newline="", encoding="utf-8") as f:
        return {r["match_id"] for r in csv.DictReader(f)}


def main():
    os.makedirs(CARPETA, exist_ok=True)
    hechos = ya()
    fp = open(R_PART, "a", newline="", encoding="utf-8")
    fj = open(R_JUG, "a", newline="", encoding="utf-8")
    wp, wj = csv.DictWriter(fp, C_PART), csv.DictWriter(fj, C_JUG)
    if not hechos:
        wp.writeheader(); wj.writeheader()
    for cod in os.environ.get("LIGAS", "ARG,BRA,MEX").split(","):
        lista = [(m, t) for m, t in partidos_de_liga(cod, LIGAS[cod]) if m not in hechos]
        # lo más reciente primero: si se corta, que quede lo que más pesa
        lista.sort(key=lambda x: x[1], reverse=True)
        print(f"{cod}: {len(lista)} partidos por descargar", flush=True)
        sin_xg = 0
        for i, (mid, t) in enumerate(lista):
            d = pedir(f"https://www.fotmob.com/api/data/matchDetails?matchId={mid}")
            if not d:
                continue
            try:
                fila, jug = extraer(cod, t, mid, d)
            except Exception as e:
                print(f"  [no se pudo leer {mid}: {type(e).__name__} {e}]", flush=True)
                continue
            sin_xg += fila.get("l_xg") is None
            wp.writerow(fila); wj.writerows(jug)
            if i % 25 == 0:
                fp.flush(); fj.flush()
                print(f"  {cod} {i+1}/{len(lista)} ({t}) sin xG hasta ahora: {sin_xg}  peticiones {peticiones[0]}", flush=True)
        print(f"{cod} terminado. Partidos sin xG: {sin_xg} de {len(lista)}", flush=True)
    fp.close(); fj.close()


if __name__ == "__main__":
    main()
