"""
ALINEACIONES CRUDAS, PARA CALCULAR UN ÍNDICE DE ROTACIÓN DESPUÉS

ESQUEMA COMPROBADO CONTRA UN PARTIDO REAL (sondeo_lineups.py, 23/09)
-----------------------------------------------------------------------
/lineups/{id} devuelve {homeTeam, awayTeam}, cada uno con `formation`
("4-3-3"), `initialLineup` (lista de líneas -- portero, defensas, medios,
delanteros -- cada jugador con `id` numérico ESTABLE) y `substitutes`.
Confirmado con partidos viejos (sondeo_matches.py, mismo día): HTTP 200
también en el más antiguo del histórico.

QUÉ SE GUARDA AQUÍ, QUÉ SE CALCULA DESPUÉS
--------------------------------------------
Este script solo guarda lo crudo: los 11 IDs de titulares de cada equipo y
la formación. El ÍNDICE DE ROTACIÓN (cuántos titulares cambian respecto al
partido anterior del mismo equipo) se calcula en rasgos.py, con la misma
regla anti-fuga que Elo y H2H: la alineación que ve el partido X es la de
X mismo (no es un resultado, es la condición del partido, conocida antes
del pitido), pero la alineación ANTERIOR contra la que se compara tiene
que ser estrictamente de una fecha previa.

REANUDABLE, mismo patrón de detección de cuota agotada que el resto.
"""
import os
import csv
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

RUTA_HIST = "data/historico_partidos.csv"
RUTA_SALIDA = "data/historico_lineups.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "3000"))
COLUMNAS = ["match_id", "local_formacion", "local_ids", "visitante_formacion", "visitante_ids"]

llamadas = [0]
fallos_seguidos = [0]
CUOTA_AGOTADA = [False]
TOPE_FALLOS_SEGUIDOS = 8


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


def ids_titulares(bloque):
    """Aplana initialLineup (lista de líneas) a una lista plana de IDs."""
    lineas = bloque.get("initialLineup") or []
    ids = []
    for linea in lineas:
        for jugador in linea:
            if jugador.get("id") is not None:
                ids.append(str(jugador["id"]))
    return ids


def ya_tengo():
    if not os.path.exists(RUTA_SALIDA):
        return set()
    with open(RUTA_SALIDA, newline="", encoding="utf-8") as f:
        return {fila["match_id"] for fila in csv.DictReader(f)}


def main():
    if not os.path.exists(RUTA_HIST):
        print(f"Falta {RUTA_HIST}. Lanza antes el backfill del histórico.")
        return
    hist = pd.read_csv(RUTA_HIST)
    vistos = ya_tengo()
    print(f"Ya tenía lineups de {len(vistos)} partidos de {len(hist)}.")
    print(f"Tope de esta pasada: {TOPE_LLAMADAS} llamadas.\n")

    nuevo_fichero = not os.path.exists(RUTA_SALIDA)
    f = open(RUTA_SALIDA, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=COLUMNAS)
    if nuevo_fichero:
        w.writeheader()

    guardados = sin_datos = 0
    try:
        for _, fila in hist.iterrows():
            if llamadas[0] >= TOPE_LLAMADAS:
                break
            mid = str(fila["match_id"])
            if mid in vistos:
                continue
            j = pedir(f"/lineups/{fila['match_id']}")
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas han "
                      f"fallado del todo -- probablemente la cuota diaria "
                      f"esta agotada, no un bache de red. Paro aqui en vez "
                      f"de reintentar el resto uno a uno.")
                break
            if not j:
                sin_datos += 1
                continue
            d = j[0] if isinstance(j, list) else j
            home, away = d.get("homeTeam") or {}, d.get("awayTeam") or {}
            ids_l, ids_v = ids_titulares(home), ids_titulares(away)
            if len(ids_l) < 5 or len(ids_v) < 5:
                # una alineacion real tiene 11; menos de 5 es un partido sin
                # datos utilizables, no un equipo que jugo con pocos jugadores
                sin_datos += 1
                continue
            w.writerow({
                "match_id": mid,
                "local_formacion": home.get("formation"),
                "local_ids": "|".join(ids_l),
                "visitante_formacion": away.get("formation"),
                "visitante_ids": "|".join(ids_v),
            })
            guardados += 1
            if guardados % 50 == 0:
                f.flush()
                print(f"  {guardados} guardados  (llamadas {llamadas[0]})")
    finally:
        f.close()

    print(f"\n{guardados} partidos nuevos con lineups. "
          f"{sin_datos} sin datos utilizables.")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
