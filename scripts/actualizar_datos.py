"""
Se ejecuta automáticamente cada día vía GitHub Actions. Descarga los
partidos recientes de La Liga (resultados, tarjetas, árbitro) y los añade
al histórico acumulado en data/historico_tarjetas.csv, sin duplicar
partidos que ya estuvieran guardados.
"""
import os
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}
LIGA_ID = 119924  # La Liga
RUTA_CSV = "data/historico_tarjetas.csv"

# IDs de los 20 equipos de La Liga 2026-27 (recopilados durante esta sesión)
EQUIPOS_LA_LIGA = [
    463728, 451814, 452665, 461175, 450963, 456920, 460324, 467132, 462877,
    454367, 620312, 3970699, 462026, 453516, 456069, 459473, 679031, 458622,
    619461, 465430,
]


def obtener_partidos_recientes(team_id: int) -> list[dict]:
    r = requests.get(f"{BASE_URL}/last-five-games", headers=HEADERS, params={"teamId": team_id})
    if r.status_code != 200:
        print(f"  [aviso] fallo al pedir equipo {team_id}: {r.status_code}")
        return []
    return [p for p in r.json() if p["league"]["id"] == LIGA_ID and p["state"]["description"] == "Finished"]


def obtener_detalle_partido(match_id: int) -> dict | None:
    r = requests.get(f"{BASE_URL}/matches/{match_id}", headers=HEADERS)
    if r.status_code != 200:
        return None
    datos = r.json()[0] if isinstance(r.json(), list) else r.json()

    tarjetas = {"local": {"amarillas": 0, "rojas": 0}, "visitante": {"amarillas": 0, "rojas": 0}}
    for evento in datos.get("events", []):
        lado = "local" if evento["team"]["id"] == datos["homeTeam"]["id"] else "visitante"
        if evento["type"] == "Yellow Card":
            tarjetas[lado]["amarillas"] += 1
        elif evento["type"] == "Red Card":
            tarjetas[lado]["rojas"] += 1

    return {
        "match_id": match_id, "fecha": datos["date"], "ronda": datos["round"],
        "equipo_local": datos["homeTeam"]["name"], "equipo_visitante": datos["awayTeam"]["name"],
        "goles_local": datos["state"]["score"]["current"].split(" - ")[0],
        "goles_visitante": datos["state"]["score"]["current"].split(" - ")[1],
        "arbitro": datos.get("referee", {}).get("name", "desconocido"),
        "amarillas_local": tarjetas["local"]["amarillas"], "rojas_local": tarjetas["local"]["rojas"],
        "amarillas_visitante": tarjetas["visitante"]["amarillas"], "rojas_visitante": tarjetas["visitante"]["rojas"],
    }


def main():
    historico = pd.read_csv(RUTA_CSV) if os.path.exists(RUTA_CSV) else pd.DataFrame()
    ids_conocidos = set(historico["match_id"]) if not historico.empty else set()

    ids_encontrados = {}
    for team_id in EQUIPOS_LA_LIGA:
        for partido in obtener_partidos_recientes(team_id):
            ids_encontrados[partido["id"]] = partido
        time.sleep(1)

    ids_nuevos = [i for i in ids_encontrados if i not in ids_conocidos]
    print(f"Partidos encontrados: {len(ids_encontrados)} | Nuevos por añadir: {len(ids_nuevos)}")

    filas_nuevas = []
    for match_id in ids_nuevos:
        detalle = obtener_detalle_partido(match_id)
        if detalle:
            filas_nuevas.append(detalle)
        time.sleep(1)

    if filas_nuevas:
        historico = pd.concat([historico, pd.DataFrame(filas_nuevas)], ignore_index=True)
        os.makedirs("data", exist_ok=True)
        historico.to_csv(RUTA_CSV, index=False)
        print(f"Guardados {len(filas_nuevas)} partidos nuevos. Total histórico: {len(historico)}")
    else:
        print("No hay partidos nuevos que añadir.")


if __name__ == "__main__":
    main()
