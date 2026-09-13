"""
BACKFILL histórico completo (ejecución puntual, no diaria).
Trae los ~380 partidos de La Liga 2025-26 con: resultado, árbitro,
tarjetas, faltas, y cuota de mercado "Total Cards" si está disponible
para partidos históricos.

Distinto del script diario (actualizar_datos.py) -- este se lanza a mano
una sola vez para tener la base histórica completa lista para entrenar.
"""
import os
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}
LIGA_ID = 119924
TEMPORADA = 2025  # La Liga 2025-26
RUTA_CSV = "data/historico_completo_2025_26.csv"

# Rivalidades reales de La Liga -- usado para el factor de derbi
DERBIS = {
    frozenset(["Real Madrid", "Barcelona"]),        # El Clásico
    frozenset(["Real Madrid", "Atlético Madrid"]),  # Derbi madrileño
    frozenset(["Atlético Madrid", "Barcelona"]),
    frozenset(["Athletic Club", "Real Sociedad"]),  # Derbi vasco
    frozenset(["Sevilla FC", "Real Betis"]),         # Derbi sevillano
    frozenset(["Celta de Vigo", "Deportivo La Coruña"]),  # Derbi gallego
    frozenset(["Espanyol", "Barcelona"]),
    frozenset(["Valencia", "Villarreal"]),
}


def es_derbi(local: str, visitante: str) -> bool:
    return frozenset([local, visitante]) in DERBIS


def obtener_pagina_partidos(offset: int, intentos: int = 3) -> list[dict]:
    for intento in range(intentos):
        r = requests.get(f"{BASE_URL}/matches", headers=HEADERS,
                          params={"leagueId": LIGA_ID, "season": TEMPORADA, "limit": 100, "offset": offset})
        if r.status_code == 200:
            return r.json()["data"]
        if r.status_code == 429:
            time.sleep(5 * (intento + 1))
            continue
        print(f"  [aviso] fallo en offset {offset}: {r.status_code}")
        return []
    return []


def obtener_detalle_completo(match_id: int) -> tuple[dict | None, list[dict]]:
    """Devuelve (fila_resumen_partido, lista_eventos_de_tarjeta_por_jugador).
    Los eventos por jugador alimentan las variables 7 (alineación real) y
    8 (acumulación de amonestaciones) -- validado hoy que son fiables."""
    r_stats = requests.get(f"{BASE_URL}/statistics/{match_id}", headers=HEADERS)
    r_match = requests.get(f"{BASE_URL}/matches/{match_id}", headers=HEADERS)
    if r_stats.status_code != 200 or r_match.status_code != 200:
        return None, []

    stats_por_equipo = r_stats.json()
    datos = r_match.json()[0] if isinstance(r_match.json(), list) else r_match.json()

    def extraer(bloque):
        s = {x["displayName"]: x["value"] for x in bloque["statistics"]}
        return s.get("Yellow cards", 0), s.get("Red cards", 0), s.get("Fouls", None), s.get("Corners", None)

    home_id = datos["homeTeam"]["id"]
    bloque_local = next(b for b in stats_por_equipo if b["team"]["id"] == home_id)
    bloque_visitante = next(b for b in stats_por_equipo if b["team"]["id"] != home_id)
    am_l, roj_l, faltas_l, corners_l = extraer(bloque_local)
    am_v, roj_v, faltas_v, corners_v = extraer(bloque_visitante)
    local_nombre, visitante_nombre = datos["homeTeam"]["name"], datos["awayTeam"]["name"]

    # -- eventos de tarjeta por jugador (variables 7 y 8) --
    eventos_tarjeta = []
    for e in datos.get("events", []):
        if e["type"] in ("Yellow Card", "Red Card"):
            eventos_tarjeta.append({
                "match_id": match_id, "fecha": datos["date"], "equipo": e["team"]["name"],
                "jugador": e["player"], "jugador_id": e["playerId"], "tipo": e["type"], "minuto": e["time"],
            })

    cuota_total_cards = None
    try:
        r_odds = requests.get(f"{BASE_URL}/odds", headers=HEADERS, params={"matchId": match_id})
        if r_odds.status_code == 200:
            for mercado in r_odds.json().get("data", []):
                if "Total Cards" in mercado.get("name", ""):
                    cuota_total_cards = mercado
                    break
    except Exception:
        pass

    fila = {
        "match_id": match_id, "fecha": datos["date"], "ronda": datos["round"],
        "equipo_local": local_nombre, "equipo_visitante": visitante_nombre,
        "goles_local": datos["state"]["score"]["current"].split(" - ")[0],
        "goles_visitante": datos["state"]["score"]["current"].split(" - ")[1],
        "arbitro": datos.get("referee", {}).get("name", "desconocido"),
        "amarillas_local": am_l, "rojas_local": roj_l, "faltas_local": faltas_l, "corners_local": corners_l,
        "amarillas_visitante": am_v, "rojas_visitante": roj_v, "faltas_visitante": faltas_v, "corners_visitante": corners_v,
        "es_derbi": es_derbi(local_nombre, visitante_nombre),
        "tiene_cuota_total_cards": cuota_total_cards is not None,
    }
    return fila, eventos_tarjeta


def main():
    print("Fase 1: listando todos los partidos de la temporada...")
    todos_los_partidos = {}
    offset = 0
    while True:
        pagina = obtener_pagina_partidos(offset)
        if not pagina:
            break
        for p in pagina:
            if p["league"]["id"] == LIGA_ID and p["state"]["description"] == "Finished":
                todos_los_partidos[p["id"]] = p
        if len(pagina) < 100:
            break
        offset += 100
        time.sleep(2)

    print(f"Partidos finalizados encontrados: {len(todos_los_partidos)}")

    print("Fase 2: trayendo el detalle de cada partido (tarjetas, árbitro, faltas, eventos por jugador)...")
    filas = []
    todos_los_eventos = []
    for i, match_id in enumerate(todos_los_partidos):
        detalle, eventos = obtener_detalle_completo(match_id)
        if detalle:
            filas.append(detalle)
            todos_los_eventos.extend(eventos)
        if (i + 1) % 20 == 0:
            print(f"  ...{i+1}/{len(todos_los_partidos)} procesados")
        time.sleep(1)

    df = pd.DataFrame(filas)
    os.makedirs("data", exist_ok=True)
    df.to_csv(RUTA_CSV, index=False)
    print(f"\nGuardado: {len(df)} partidos completos en {RUTA_CSV}")

    df_eventos = pd.DataFrame(todos_los_eventos)
    df_eventos.to_csv("data/eventos_tarjetas_jugadores_2025_26.csv", index=False)
    print(f"Guardado: {len(df_eventos)} eventos de tarjeta por jugador en data/eventos_tarjetas_jugadores_2025_26.csv")


if __name__ == "__main__":
    main()
