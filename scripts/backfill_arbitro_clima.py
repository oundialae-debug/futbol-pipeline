"""
ÁRBITRO Y CLIMA DE /matches/{id}, DOS VARIABLES EN UNA SOLA LLAMADA

POR QUÉ ESTAS DOS
------------------
Comprobado contra 5 partidos reales repartidos por fecha (sondeo_matches.py,
23/09), incluido el más viejo del histórico (13+ meses): las dos vienen
pobladas con valores reales y variados, no un relleno fijo.

  arbitro   nombre del colegiado. pipeline_diario.py ya lo usa con éxito
            (88% de cobertura) para un histórico más pequeño de la
            temporada en curso; aquí se trae para los ~2500 partidos del
            histórico principal. Distintos árbitros pitan distinto número
            de tarjetas de media -- es justo el mercado donde peor va el
            modelo (mas_4_5_tarjetas).
  clima     status ("clear day", "cloudy", "wind"...) y temperatura. Lluvia
            y viento afectan a goles y córners en la literatura de
            análisis de fútbol; nunca se había probado aquí.

Ninguna de las dos depende del RESULTADO del partido -- son condiciones
conocidas ANTES o EN el pitido inicial, no estadísticas post-partido. Eso
las distingue de box-score (que si son estadisticas del propio partido, y
por eso su rasgo se calcula con cuidado de que sea el histórico PREVIO del
equipo, no el propio partido): aquí el dato crudo en sí mismo no filtra
nada, es la condición del partido, no su desenlace.

UNA SOLA LLAMADA PARA LAS DOS
-------------------------------
/matches/{id} ya trae referee Y forecast en la misma respuesta -- la mitad
de llamadas que si fueran dos backfills separados.

REANUDABLE, con la misma detección de cuota agotada que backfill_boxscore.py
(21/09): si N llamadas seguidas fallan del todo, es la cuota diaria, no un
bache de red, y se para en vez de reintentar durante horas.
"""
import os
import csv
import re
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

RUTA_HIST = "data/historico_partidos.csv"
RUTA_SALIDA = "data/historico_arbitro_clima.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "3000"))
COLUMNAS = ["match_id", "arbitro", "clima_status", "clima_temp"]

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


def parsear_temp(temp_str):
    """'33.42°C' -> 33.42. Si viene vacío o con otro formato, None."""
    if not temp_str:
        return None
    m = re.search(r"-?\d+\.?\d*", str(temp_str))
    return float(m.group()) if m else None


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
    print(f"Ya tenía árbitro/clima de {len(vistos)} partidos de {len(hist)}.")
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
            j = pedir(f"/matches/{fila['match_id']}")
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas han "
                      f"fallado del todo -- probablemente la cuota diaria "
                      f"esta agotada, no un bache de red. Paro aqui en vez "
                      f"de reintentar el resto uno a uno.")
                break
            if not j:
                sin_datos += 1
                continue
            datos = j[0] if isinstance(j, list) else j
            arbitro = (datos.get("referee") or {}).get("name")
            clima = datos.get("forecast") or {}
            w.writerow({
                "match_id": mid,
                "arbitro": arbitro,
                "clima_status": clima.get("status"),
                "clima_temp": parsear_temp(clima.get("temperature")),
            })
            guardados += 1
            if guardados % 50 == 0:
                f.flush()
                print(f"  {guardados} guardados  (llamadas {llamadas[0]})")
    finally:
        f.close()

    print(f"\n{guardados} partidos nuevos con árbitro/clima. "
          f"{sin_datos} sin datos utilizables.")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
