"""
CALIDAD DE PLANTILLA: temporada ANTERIOR de cada jugador, hecho histórico
fijo, sin riesgo de fuga

POR QUÉ LA TEMPORADA ANTERIOR Y NO LA ACTUAL
-----------------------------------------------
Comprobado (sondeo_jugador_stats.py, 24/09): /players/{id}/statistics
rompe limpio por temporada ("25/26", "24/25"...), pero la temporada EN
CURSO sigue acumulando partidos cada semana -- usarla para un partido de
hace meses metería resultados posteriores a ese partido. La temporada
ANTERIOR ya está cerrada: es un número fijo, no cambia según cuándo se
pida. Nuestro histórico tiene dos temporadas (columna `temporada`: 2025 y
2026, que en el formato de esta API son "25/26" y "26/27"), así que hace
falta la stats de "24/25" para los partidos de temporada=2025 y de
"25/26" para los de temporada=2026.

3478 JUGADORES ÚNICOS -- LA MAYOR PASADA DE API DEL PROYECTO
----------------------------------------------------------------
Por eso: tope pequeño por defecto (500) para validar el patrón y que la
variable aporte algo antes de comprometer el resto. Reanudable, mismo
patrón de detección de cuota agotada que el resto.

QUÉ SE GUARDA
--------------
Todo lo que devuelve perCompetition, sin filtrar por temporada aquí --
eso se decide en rasgos.py, igual que el resto de variables cronológicas.
"""
import os
import csv
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

RUTA_LINEUPS = "data/historico_lineups.csv"
RUTA_SALIDA = "data/historico_jugador_stats.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "500"))
COLUMNAS = ["jugador_id", "temporada", "liga", "club", "partidos", "goles",
           "asistencias", "minutos", "amarillas", "rojas"]

llamadas = [0]
fallos_seguidos = [0]
CUOTA_AGOTADA = [False]
TOPE_FALLOS_SEGUIDOS = 8


def pedir(jugador_id):
    if llamadas[0] >= TOPE_LLAMADAS or CUOTA_AGOTADA[0]:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}/players/{jugador_id}/statistics",
                            headers=HEADERS, timeout=25)
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


def jugadores_unicos():
    df = pd.read_csv(RUTA_LINEUPS)
    ids = set()
    for col in ("local_ids", "visitante_ids"):
        for s in df[col].dropna():
            ids.update(int(x) for x in s.split("|"))
    return sorted(ids)


def ya_tengo():
    if not os.path.exists(RUTA_SALIDA):
        return set()
    with open(RUTA_SALIDA, newline="", encoding="utf-8") as f:
        return {int(fila["jugador_id"]) for fila in csv.DictReader(f)}


def main():
    if not os.path.exists(RUTA_LINEUPS):
        print(f"Falta {RUTA_LINEUPS}. Lanza antes backfill_lineups.py.")
        return
    todos = jugadores_unicos()
    vistos = ya_tengo()
    pendientes = [j for j in todos if j not in vistos]
    print(f"Jugadores únicos: {len(todos)}. Ya tenía: {len(vistos)}. "
          f"Pendientes: {len(pendientes)}.")
    print(f"Tope de esta pasada: {TOPE_LLAMADAS} llamadas.\n")

    nuevo_fichero = not os.path.exists(RUTA_SALIDA)
    f = open(RUTA_SALIDA, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=COLUMNAS)
    if nuevo_fichero:
        w.writeheader()

    guardados = sin_datos = filas_totales = 0
    try:
        for jid in pendientes:
            if llamadas[0] >= TOPE_LLAMADAS:
                break
            j = pedir(jid)
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas han "
                      f"fallado del todo -- probablemente la cuota diaria "
                      f"esta agotada. Paro aqui.")
                break
            d = (j[0] if isinstance(j, list) else j) if j else None
            per_comp = (d or {}).get("perCompetition") or []
            if not per_comp:
                w.writerow({"jugador_id": jid, "temporada": "", "liga": "",
                           "club": "", "partidos": "", "goles": "",
                           "asistencias": "", "minutos": "", "amarillas": "",
                           "rojas": ""})
                sin_datos += 1
                continue
            for c in per_comp:
                w.writerow({
                    "jugador_id": jid,
                    "temporada": c.get("season"),
                    "liga": c.get("league"),
                    "club": c.get("club"),
                    "partidos": c.get("gamesPlayed"),
                    "goles": c.get("goals"),
                    "asistencias": c.get("assists"),
                    "minutos": c.get("minutesPlayed"),
                    "amarillas": c.get("yellowCards"),
                    "rojas": c.get("redCards"),
                })
                filas_totales += 1
            guardados += 1
            if guardados % 100 == 0:
                f.flush()
                print(f"  {guardados} jugadores guardados  (llamadas {llamadas[0]})")
    finally:
        f.close()

    print(f"\n{guardados} jugadores nuevos ({filas_totales} filas de "
          f"temporada/liga), {sin_datos} sin datos utilizables.")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
