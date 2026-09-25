"""
H2H PROFUNDO: /head-2-head da las ÚLTIMAS 10 confrontaciones REALES entre
dos equipos, no solo lo que hay dentro de nuestro propio histórico

POR QUÉ ESTO Y NO SOLO calcular_h2h()
---------------------------------------
calcular_h2h() en rasgos.py solo ve enfrentamientos dentro de
historico_partidos.csv (13 meses). Comprobado (sondeo_h2h.py, 24/09) con
Real Madrid-Barcelona: de las 10 confrontaciones que da la API, 7 son de
ANTES de nuestra ventana (hasta abril 2024, año y medio más atrás). La
mayoría de pares de equipos (52%) no se habían enfrentado nunca dentro de
nuestra ventana -- esto puede arreglar justo esa escasez.

POR PAR DE EQUIPOS, NO POR PARTIDO
------------------------------------
1218 pares únicos de equipos sobre 2539 partidos -- la mitad de llamadas
que un backfill por partido. El resultado de /head-2-head no depende de
qué partido concreto se esté evaluando, solo del par.

CUIDADO CON LA FUGA: "últimas 10 A DÍA DE HOY" no es lo mismo que
"últimas 10 antes de un partido concreto del histórico"
---------------------------------------------------------------------
Si un partido del histórico es de hace 13 meses y ese par se ha enfrentado
varias veces DESPUÉS, usar sin filtrar el "últimas 10 de hoy" metería
información del futuro respecto a ese partido. Por eso este script solo
GUARDA lo crudo (todas las confrontaciones que devuelve la API, con
fecha); el FILTRADO por fecha < partido se hace en rasgos.py, igual que
con el resto de variables cronológicas (Elo, H2H propio, tabla, árbitro).

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
RUTA_SALIDA = "data/historico_h2h_profundo.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "3000"))
COLUMNAS = ["par", "fecha", "local_id", "goles_l", "goles_v"]

llamadas = [0]
fallos_seguidos = [0]
CUOTA_AGOTADA = [False]
TOPE_FALLOS_SEGUIDOS = 8


def pedir(params):
    if llamadas[0] >= TOPE_LLAMADAS or CUOTA_AGOTADA[0]:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}/head-2-head", headers=HEADERS,
                            params=params, timeout=25)
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


def clave_par(id1, id2):
    a, b = sorted((int(id1), int(id2)))
    return f"{a}_{b}"


def ya_tengo():
    if not os.path.exists(RUTA_SALIDA):
        return set()
    with open(RUTA_SALIDA, newline="", encoding="utf-8") as f:
        return {fila["par"] for fila in csv.DictReader(f)}


def main():
    if not os.path.exists(RUTA_HIST):
        print(f"Falta {RUTA_HIST}. Lanza antes el backfill del histórico.")
        return
    # Temporada más reciente primero: si la cuota se acaba a mitad, que
    # quede COMPLETA la temporada nueva en vez de dos a medias.
    hist = pd.read_csv(RUTA_HIST).sort_values("temporada", ascending=False, kind="stable")
    pares = {}
    for _, fila in hist.iterrows():
        clave = clave_par(fila["local_id"], fila["visitante_id"])
        pares[clave] = (int(fila["local_id"]), int(fila["visitante_id"]))

    vistos = ya_tengo()
    pendientes = [p for p in pares if p not in vistos]
    print(f"Pares únicos: {len(pares)}. Ya tenía: {len(vistos)}. "
          f"Pendientes: {len(pendientes)}.")
    print(f"Tope de esta pasada: {TOPE_LLAMADAS} llamadas.\n")

    nuevo_fichero = not os.path.exists(RUTA_SALIDA)
    f = open(RUTA_SALIDA, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=COLUMNAS)
    if nuevo_fichero:
        w.writeheader()

    # Un par sin ningún cruce previo real (nunca se han visto) tambien hay
    # que marcarlo como "ya intentado" o se reintentaria cada pasada -- se
    # guarda una fila centinela con fecha vacia.
    guardados = pares_sin_historial = 0
    try:
        for clave in pendientes:
            if llamadas[0] >= TOPE_LLAMADAS:
                break
            id1, id2 = pares[clave]
            j = pedir({"teamIdOne": id1, "teamIdTwo": id2})
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas han "
                      f"fallado del todo -- probablemente la cuota diaria "
                      f"esta agotada, no un bache de red. Paro aqui.")
                break
            partidos = j if isinstance(j, list) else (j.get("data", []) if j else [])
            if not partidos:
                w.writerow({"par": clave, "fecha": "", "local_id": "",
                           "goles_l": "", "goles_v": ""})
                pares_sin_historial += 1
                continue
            for p in partidos:
                estado = (p.get("state") or {})
                marcador = (estado.get("score") or {}).get("current")
                gl = gv = ""
                if marcador and " - " in marcador:
                    try:
                        gl, gv = marcador.split(" - ")
                        gl, gv = int(gl), int(gv)
                    except ValueError:
                        gl = gv = ""
                w.writerow({
                    "par": clave,
                    "fecha": p.get("date"),
                    "local_id": (p.get("homeTeam") or {}).get("id"),
                    "goles_l": gl,
                    "goles_v": gv,
                })
            guardados += 1
            if guardados % 50 == 0:
                f.flush()
                print(f"  {guardados} pares guardados  (llamadas {llamadas[0]})")
    finally:
        f.close()

    print(f"\n{guardados} pares nuevos con historial, "
          f"{pares_sin_historial} sin ningún cruce previo.")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
