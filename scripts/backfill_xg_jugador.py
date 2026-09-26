"""
xG, xA y el resto de estadísticas POR JUGADOR de /box-score (26/09/2026)

El backfill de box-score del 21/09 (backfill_boxscore.py) recibió estas
estadísticas en 2.537 partidos y solo guardó 7 agregados de equipo: el xG y
el xA de cada jugador se tiraron. Esta vez se guarda la respuesta ENTERA de
cada jugador (los 37 campos de PlayerBoxScoreStatisticsDto de la spec más
posición, minutos, titular/suplente y nota), una fila por jugador y partido.
Lo que se decida usar después sale de aquí sin volver a pagar llamadas.

COBERTURA (sondeo_xg_jugador.md): xG/xA por jugador solo desde abril de
2025. Antes, /box-score devuelve los jugadores pero sin xG: se saltan.

ORDEN: fecha más reciente primero. Si la cuota se acaba a mitad, queda
completa la temporada más nueva, no dos a medias.

REANUDABLE: salta los match_id ya guardados. Un partido sin jugadores se
apunta con una fila vacía (jugador_id en blanco) para no repedirlo.
"""
import os
import csv
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_HIST = "data/historico_partidos.csv"
RUTA_SALIDA = "data/historico_xg_jugador.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "3100"))
INICIO_COBERTURA = "2025-04-01"

# Nombres EXACTOS de la spec (components.schemas.PlayerBoxScoreStatisticsDto),
# no adivinados.
ESTADISTICAS = [
    "goalsScored", "goalsSaved", "goalsConceded", "assists", "dribblesTotal",
    "dribblesSuccessful", "dribblesFailed", "dribbleSuccessRate",
    "fouledByOthers", "fouledOthers", "tacklesTotal", "interceptionsTotal",
    "duelsTotal", "duelsWon", "duelsLost", "duelSuccessRate", "cardsRed",
    "cardsYellow", "cardsSecondYellow", "passesAccuracy", "passesSuccessful",
    "passesFailed", "passesTotal", "passesKey", "penaltiesScored",
    "penaltiesMissed", "penaltiesTotal", "penaltiesAccuracy", "shotsOnTarget",
    "shotsOffTarget", "shotsTotal", "shotsAccuracy", "expectedGoals",
    "expectedAssists", "expectedGoalsOnTarget", "expectedGoalsOnTargetConceded",
    "expectedGoalsPrevented"]
COLUMNAS = (["match_id", "equipo_id", "jugador_id", "posicion", "minutos",
             "suplente", "nota", "fueras_de_juego"] + ESTADISTICAS)

llamadas = [0]
fallos_seguidos = [0]
TOPE_FALLOS_SEGUIDOS = 8
CUOTA_AGOTADA = [False]


def pedir(path):
    if llamadas[0] >= TOPE_LLAMADAS or CUOTA_AGOTADA[0]:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            fallos_seguidos[0] += 1
            if fallos_seguidos[0] >= TOPE_FALLOS_SEGUIDOS:
                CUOTA_AGOTADA[0] = True
            return None
        try:
            j = r.json()
            fallos_seguidos[0] = 0
            return j
        except Exception:
            return None
    fallos_seguidos[0] += 1
    if fallos_seguidos[0] >= TOPE_FALLOS_SEGUIDOS:
        CUOTA_AGOTADA[0] = True
    return None


def desempaquetar(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def estadisticas_de(jugador):
    """La spec dice lista de DTO; en la práctica llega un dict. Acepta las dos."""
    s = jugador.get("statistics")
    if isinstance(s, list):
        s = s[0] if s else {}
    return s or {}


def ya_tengo():
    if not os.path.exists(RUTA_SALIDA):
        return set()
    with open(RUTA_SALIDA, newline="", encoding="utf-8") as f:
        return {fila["match_id"] for fila in csv.DictReader(f)}


def main():
    hist = pd.read_csv(RUTA_HIST)
    hist = hist[hist.fecha.astype(str).str[:10] >= INICIO_COBERTURA]
    hist = hist.sort_values("fecha", ascending=False)
    vistos = ya_tengo()
    pendientes = [m for m in hist.match_id.astype(str) if m not in vistos]
    print(f"{len(hist)} partidos desde {INICIO_COBERTURA}. Ya tenía {len(vistos)}. "
          f"Pendientes {len(pendientes)}. Tope {TOPE_LLAMADAS} llamadas.\n")

    nuevo = not os.path.exists(RUTA_SALIDA)
    f = open(RUTA_SALIDA, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=COLUMNAS)
    if nuevo:
        w.writeheader()

    guardados = sin_datos = filas = con_xg = 0
    try:
        for mid in pendientes:
            if llamadas[0] >= TOPE_LLAMADAS:
                break
            j = pedir(f"/box-score/{mid}")
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas fallidas: "
                      f"probablemente cuota agotada. Paro aquí.")
                break
            jugadores = []
            for eq in (desempaquetar(j) if j else []):
                tid = (eq.get("team") or {}).get("id") if isinstance(eq, dict) else None
                for p in (eq.get("players") or []) if isinstance(eq, dict) else []:
                    jugadores.append((tid, p))
            if not jugadores:
                if j is not None:   # respuesta válida pero vacía: apuntar para no repedir
                    w.writerow({"match_id": mid})
                sin_datos += 1
                continue
            for tid, p in jugadores:
                s = estadisticas_de(p)
                fila = {"match_id": mid, "equipo_id": tid, "jugador_id": p.get("id"),
                        "posicion": p.get("position"), "minutos": p.get("minutesPlayed"),
                        "suplente": p.get("isSubstitute"), "nota": p.get("matchRating"),
                        "fueras_de_juego": p.get("offsides")}
                for k in ESTADISTICAS:
                    fila[k] = s.get(k)
                con_xg += s.get("expectedGoals") is not None
                w.writerow(fila)
                filas += 1
            guardados += 1
            if guardados % 100 == 0:
                f.flush()
                print(f"  {guardados} partidos  (llamadas {llamadas[0]})")
    finally:
        f.close()

    print(f"\n{guardados} partidos nuevos, {filas} filas de jugador "
          f"({con_xg} con xG). {sin_datos} sin jugadores.")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if guardados and con_xg == 0:
        print("[!] NINGÚN jugador con xG: algo va mal (nombre de campo o cobertura).")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
