"""
SONDEO: ¿tiene la API temporadas anteriores a la 2025/26?

El histórico solo tiene una temporada completa (2025/26, 2.223 partidos) y
el arranque de la 2026/27. Todas las pruebas del 23-24/09 apuntan a que el
límite del modelo es la CANTIDAD de partidos de entrenamiento (~1.700).
backfill_historico.py nunca pidió season=2024 o anteriores -- que nadie lo
haya pedido no prueba que no exista (regla de CLAUDE.md).

Comprueba, con ~35 llamadas:
  1. Cuántos partidos devuelve /matches por liga y temporada (2024, 2023, 2022).
  2. Para un partido terminado de La Liga de cada temporada, si hay datos en
     las rutas que usa el modelo: /statistics (córners, xG...), /matches/{id}
     (árbitro), /lineups (alineaciones, necesarias para calidad_plantilla).
"""
import os
import time
import requests

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}
LIGAS = {33973: "Premier League", 119924: "La Liga", 115669: "Serie A",
         67162: "Bundesliga", 52695: "Ligue 1", 120775: "Segunda"}
TEMPORADAS = (2024, 2023, 2022)
RUTA_INFORME = "sondeo_temporadas_antiguas.md"


def pedir(path, params=None):
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1))
            continue
        if r.status_code == 429:
            time.sleep(5)
            continue
        if r.status_code != 200:
            return None, r.status_code
        try:
            return r.json(), 200
        except Exception:
            return None, "no-json"
    return None, "sin respuesta"


def lista(j):
    if isinstance(j, dict):
        return j.get("data") or []
    return j or []


def terminado(p):
    return "finish" in str((p.get("state") or {}).get("description", "")).lower()


def main():
    lineas = ["# Sondeo: temporadas anteriores a la 2025/26\n",
              "## Partidos por liga y temporada (/matches, hasta 100 por página)\n",
              "| temporada | liga | 1ª página | terminados | total (paginación) |",
              "|---|---|---|---|---|"]
    muestra = {}
    for temporada in TEMPORADAS:
        for liga_id, liga in LIGAS.items():
            j, estado = pedir("/matches", {"leagueId": liga_id, "season": temporada,
                                           "limit": 100, "offset": 0})
            lote = lista(j)
            fin = [p for p in lote if terminado(p)]
            total = (j.get("pagination") or {}).get("totalCount") if isinstance(j, dict) else None
            print(f"{temporada} {liga:16s} estado={estado} 1a pagina={len(lote)} terminados={len(fin)} total={total}")
            lineas.append(f"| {temporada} | {liga} | {len(lote)} | {len(fin)} | {total} |")
            if liga_id == 119924 and fin:
                muestra[temporada] = fin[0]

    lineas += ["\n## Profundidad de datos: un partido terminado de La Liga por temporada\n",
               "| temporada | partido | /statistics | árbitro (/matches/{id}) | /lineups |",
               "|---|---|---|---|---|"]
    for temporada, p in muestra.items():
        mid = p["id"]
        nombre = f"{(p.get('homeTeam') or {}).get('name')} vs {(p.get('awayTeam') or {}).get('name')} ({str(p.get('date'))[:10]})"
        est, _ = pedir(f"/statistics/{mid}")
        n_est, tiene_corners = 0, False
        for bloque in lista(est) if not isinstance(est, list) else est:
            for s in (bloque.get("statistics") or []):
                n_est += 1
                tiene_corners |= str(s.get("displayName", "")).lower() == "corners"
        det, _ = pedir(f"/matches/{mid}")
        d = (det[0] if isinstance(det, list) and det else det) or {}
        arbitro = (d.get("referee") or {}).get("name") if isinstance(d.get("referee"), dict) else d.get("referee")
        lu, _ = pedir(f"/lineups/{mid}")
        titulares = 0
        if isinstance(lu, dict):
            for lado in ("homeTeam", "awayTeam"):
                for linea in ((lu.get(lado) or {}).get("initialLineup") or []):
                    titulares += len(linea) if isinstance(linea, list) else 0
        print(f"{temporada} {nombre}: estadisticas={n_est} corners={tiene_corners} arbitro={arbitro} titulares={titulares}")
        lineas.append(f"| {temporada} | {nombre} | {n_est} stats, córners={tiene_corners} | {arbitro} | {titulares} titulares |")

    with open(RUTA_INFORME, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"\nEscrito {RUTA_INFORME}")


if __name__ == "__main__":
    main()
