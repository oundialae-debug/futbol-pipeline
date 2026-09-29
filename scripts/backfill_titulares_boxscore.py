"""
TITULARES DE 2023/24 DESDE /box-score (29/09/2026)

/lineups no tiene nada antes de abril de 2024 (ver CLAUDE.md). El sondeo
sondeo_titulares_boxscore.md (16 partidos, ago-2023 a mar-2024, 5 ligas +
Segunda) mostró que /box-score SÍ marca isSubstitute: 11 titulares por
equipo en 16 de 16, con posición y minutos, y en los dos controles coincide
al 100% con /lineups.

Escribe en data/historico_lineups.csv, MISMO formato que backfill_lineups.py,
para que todos los modelos lo usen sin cambios:
  - IDs ordenados portero, defensas, medios, delanteros (rasgos.py asigna la
    posición por el orden y la formación: primer ID portero, primera línea
    defensas, última línea delanteros)
  - formación reconstruida contando posiciones ("4-3-3"); el box-score no la da
Solo partidos de 2023/24 anteriores a 2024-04-01 (lo posterior ya viene de
/lineups). Reanudable: salta los match_id que ya están en el fichero.
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
RUTA_SALIDA = "data/historico_lineups.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "2000"))
TEMPORADA = 2023
HASTA = "2024-04-01"
COLUMNAS = ["match_id", "local_formacion", "local_ids", "visitante_formacion", "visitante_ids"]
ORDEN = {"Goalkeeper": 0, "Defender": 1, "Midfielder": 2, "Forward": 3}

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


def once(bloque):
    """(ids ordenados por posición, formación) o None si no hay 11 titulares con posición."""
    tit = [p for p in (bloque.get("players") or []) if p.get("isSubstitute") is False and p.get("id") is not None]
    if len(tit) != 11 or any(p.get("position") not in ORDEN for p in tit):
        return None
    tit.sort(key=lambda p: ORDEN[p["position"]])
    n = {k: sum(p["position"] == k for p in tit) for k in ORDEN}
    if n["Goalkeeper"] != 1:
        return None
    lineas = [n["Defender"], n["Midfielder"], n["Forward"]]
    formacion = "-".join(str(x) for x in lineas if x > 0)
    return "|".join(str(p["id"]) for p in tit), formacion


def ya_tengo():
    if not os.path.exists(RUTA_SALIDA):
        return set()
    with open(RUTA_SALIDA, newline="", encoding="utf-8") as f:
        return {fila["match_id"] for fila in csv.DictReader(f)}


def main():
    hist = pd.read_csv(RUTA_HIST)
    obj = hist[(hist.temporada == TEMPORADA) & (hist.fecha.astype(str).str[:10] < HASTA)]
    vistos = ya_tengo()
    pendientes = obj[~obj.match_id.astype(str).isin(vistos)]
    print(f"2023/24 anterior a {HASTA}: {len(obj)} partidos; ya en el fichero {len(obj) - len(pendientes)}; "
          f"pendientes {len(pendientes)}. Tope: {TOPE_LLAMADAS} llamadas.\n")

    f = open(RUTA_SALIDA, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=COLUMNAS)
    guardados = sin_datos = 0
    try:
        for _, fila in pendientes.iterrows():
            if llamadas[0] >= TOPE_LLAMADAS:
                break
            j = pedir(f"/box-score/{fila['match_id']}")
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas fallidas: probablemente cuota agotada. Paro.")
                break
            equipos = (j.get("data") if isinstance(j, dict) else j) or []
            por_equipo = {}
            for e in equipos:
                if isinstance(e, dict) and isinstance(e.get("team"), dict):
                    por_equipo[str(e["team"].get("id"))] = once(e)
            l = por_equipo.get(str(int(fila["local_id"])))
            v = por_equipo.get(str(int(fila["visitante_id"])))
            if not l or not v:
                sin_datos += 1
                continue
            w.writerow({"match_id": str(fila["match_id"]), "local_formacion": l[1], "local_ids": l[0],
                        "visitante_formacion": v[1], "visitante_ids": v[0]})
            guardados += 1
            if guardados % 50 == 0:
                f.flush()
                print(f"  {guardados} guardados  (llamadas {llamadas[0]})")
    finally:
        f.close()
    print(f"\n{guardados} partidos nuevos con titulares. {sin_datos} sin 11+11 titulares utilizables.")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if guardados + sin_datos < len(pendientes):
        print("[!] Quedan pendientes: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
