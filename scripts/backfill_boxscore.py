"""
SIETE VARIABLES NUEVAS DE /box-score, NINGUNA DUPLICA /statistics

POR QUÉ ESTAS SIETE
--------------------
/statistics ya nos da 33 estadísticas de EQUIPO (faltas cometidas, tarjetas,
posesión...). /box-score da 37 estadísticas POR JUGADOR. La mayoría, sumadas,
reproducen lo que /statistics ya da (sumar goalsScored de los 11 jugadores es
el mismo número que ya tenemos). Elegidas solo las que NO se pueden sacar de
/statistics, agregadas a nivel de equipo:

  faltas_recibidas      suma de fouledByOthers -- faltas que le HACEN al
                         equipo, no las que comete. /statistics solo da
                         faltas cometidas.
  segundas_amarillas    suma de cardsSecondYellow -- roja por doble amarilla,
                         distinto de una roja directa. /statistics junta
                         todas las rojas en un solo número.
  duelos_totales        suma de duelsTotal -- intensidad física del partido.
                         No existe en /statistics en ninguna forma.
  duelos_ganados_pct    duelsWon / duelsTotal del equipo.
  falta_max_jugador     el MÁXIMO de fouledOthers entre los 11-23 jugadores.
                         Esto es lo que /statistics no puede dar NUNCA: un
                         equipo con 14 faltas repartidas entre seis jugadores
                         no es el mismo perfil que 14 faltas con un jugador
                         concentrando 6. Solo lo por-jugador lo distingue.
  jugadores_2mas_faltas  cuántos jugadores llegan a 2+ faltas -- lo mismo
                         desde el otro lado: reparto ancho de la agresividad.
  xg_evitado_portero     suma de expectedGoalsPrevented -- calidad del
                         portero PARANDO, independiente de los goles
                         encajados. /statistics solo da el xG ofensivo del
                         equipo, nunca el defensivo del portero.

ESQUEMA COMPROBADO CONTRA UN PARTIDO REAL (sondeo_boxscore.py, 21/09)
-----------------------------------------------------------------------
Los nombres de arriba son los EXACTOS que devuelve la API. La respuesta es
una lista de dos objetos {team, players}; el equipo se identifica emparejando
team.id contra local_id/visitante_id, igual que ya hace backfill_historico.py
con /statistics -- nunca por posición en la lista, que no está garantizada.

REANUDABLE
----------
Lee los match_id de data/historico_partidos.csv, salta los que ya tiene en
data/historico_boxscore.csv, y se puede relanzar tantas veces como haga falta.
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
RUTA_SALIDA = "data/historico_boxscore.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "3000"))

VARIABLES = ["faltas_recibidas", "segundas_amarillas", "duelos_totales",
            "duelos_ganados_pct", "falta_max_jugador",
            "jugadores_2mas_faltas", "xg_evitado_portero"]
COLUMNAS = ["match_id"] + [f"{lado}_{v}" for v in VARIABLES for lado in ("l", "v")]

llamadas = [0]
fallos_seguidos = [0]
CUOTA_AGOTADA = [False]
# Si esto son N llamadas seguidas que agotan sus 3 reintentos, no es un bache
# de red: es la cuota diaria agotada. Sin esto, la pasada del 21/09 se quedo
# reintentando 3 veces con 5s de espera CADA UNO de ~2.500 partidos -- mas de
# diez horas para no traer nada, y encima sin guardar lo poco que si
# consiguio porque el workflow tampoco tenia if: always() en el paso de
# guardar. Los dos fallos juntos perdieron la pasada entera.
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
    # agoto los 3 reintentos: probablemente cuota agotada, no red intermitente
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


def agregar_equipo(jugadores):
    """Los siete numeros de un equipo, a partir de sus jugadores."""
    fouled_others = [j.get("statistics", {}).get("fouledOthers") for j in jugadores]
    fouled_others = [x for x in fouled_others if x is not None]
    fouled_by = [j.get("statistics", {}).get("fouledByOthers") for j in jugadores]
    fouled_by = [x for x in fouled_by if x is not None]
    segundas = sum(j.get("statistics", {}).get("cardsSecondYellow") or 0
                  for j in jugadores)
    duelos_t = sum(j.get("statistics", {}).get("duelsTotal") or 0 for j in jugadores)
    duelos_g = sum(j.get("statistics", {}).get("duelsWon") or 0 for j in jugadores)
    xg_evitado = sum(j.get("statistics", {}).get("expectedGoalsPrevented") or 0
                     for j in jugadores)
    return {
        "faltas_recibidas": sum(fouled_by) if fouled_by else None,
        "segundas_amarillas": segundas,
        "duelos_totales": duelos_t,
        "duelos_ganados_pct": (duelos_g / duelos_t) if duelos_t else None,
        "falta_max_jugador": max(fouled_others) if fouled_others else None,
        "jugadores_2mas_faltas": sum(1 for x in fouled_others if x >= 2),
        "xg_evitado_portero": xg_evitado,
    }


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
    print(f"Ya tenía box-score de {len(vistos)} partidos de {len(hist)}.")
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
            j = pedir(f"/box-score/{fila['match_id']}")
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas han "
                      f"fallado del todo -- probablemente la cuota diaria "
                      f"esta agotada, no un bache de red. Paro aqui en vez "
                      f"de reintentar el resto uno a uno.")
                break
            equipos = desempaquetar(j) if j else []
            if len(equipos) != 2:
                sin_datos += 1
                continue
            por_id = {}
            for eq in equipos:
                tid = (eq.get("team") or {}).get("id")
                jugadores = eq.get("players") or []
                if tid is not None and jugadores:
                    por_id[tid] = agregar_equipo(jugadores)
            local_id, visitante_id = fila["local_id"], fila["visitante_id"]
            if local_id not in por_id or visitante_id not in por_id:
                sin_datos += 1
                continue
            salida = {"match_id": mid}
            for v in VARIABLES:
                salida[f"l_{v}"] = por_id[local_id][v]
                salida[f"v_{v}"] = por_id[visitante_id][v]
            w.writerow(salida)
            guardados += 1
            if guardados % 50 == 0:
                f.flush()
                print(f"  {guardados} guardados  (llamadas {llamadas[0]})")
    finally:
        f.close()

    print(f"\n{guardados} partidos nuevos con box-score. "
          f"{sin_datos} sin datos utilizables (normal en partidos muy "
          f"antiguos o con cobertura mínima).")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
