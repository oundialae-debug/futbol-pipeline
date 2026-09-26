"""
Forma de club reciente para la nota justa de los jugadores de selecciones
(26/09/2026). Tema aparte del proyecto de ambos marcan.

data/historico_xg_jugador.csv (la nota de club de cada jugador) solo crece
cuando alguien lanza a mano backfill_historico + backfill_xg_jugador: se quedó
en el 20/09. Esto mantiene aparte, SIN tocar los CSV del proyecto principal,
data/selecciones/club_reciente.csv: el box-score por jugador de los partidos
terminados de las 6 ligas en los últimos DIAS días que aún no estén en
ninguno de los dos ficheros. Mismas columnas que historico_xg_jugador + fecha.

Coste: 6 ligas x DIAS llamadas a /matches + 1 /box-score por partido nuevo.
"""
import os
import json
import time
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd

HEADERS = {"x-rapidapi-key": os.environ.get("HIGHLIGHTLY_API_KEY", "")}   # nunca se imprime
BASE_URL = "https://soccer.highlightly.net"
DIAS = int(os.environ.get("DIAS", "4"))
TOPE = int(os.environ.get("TOPE_LLAMADAS", "200"))
SALIDA = "data/selecciones/club_reciente.csv"
llamadas = [0]


def pedir(path, params=None):
    if llamadas[0] >= TOPE or not HEADERS["x-rapidapi-key"]:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        return r.json() if r.status_code == 200 else None
    return None


def lista(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def main():
    import sys
    sys.path.insert(0, "scripts")
    from backfill_xg_jugador import COLUMNAS, ESTADISTICAS
    ligas = sorted(pd.read_csv("data/historico_partidos.csv").liga_id.unique())
    vistos = set(pd.read_csv("data/historico_xg_jugador.csv", usecols=["match_id"]).match_id.astype(str))
    previo = pd.read_csv(SALIDA) if os.path.exists(SALIDA) else pd.DataFrame(columns=COLUMNAS + ["fecha"])
    vistos |= set(previo.match_id.astype(str))
    hoy = datetime.now(timezone.utc).date()
    nuevos = []
    for liga in ligas:
        for d in range(1, DIAS + 1):
            fecha = (hoy - timedelta(days=d)).isoformat()
            for p in lista(pedir("/matches", {"leagueId": int(liga), "date": fecha})):
                estado = (p.get("state") or {}).get("description", "") if isinstance(p, dict) else ""
                if isinstance(p, dict) and "finish" in str(estado).lower() and str(p.get("id")) not in vistos:
                    nuevos.append((p["id"], fecha))
                    vistos.add(str(p["id"]))
    filas = []
    for mid, fecha in nuevos:
        j = pedir(f"/box-score/{mid}")
        for eq in lista(j) if j else []:
            tid = (eq.get("team") or {}).get("id") if isinstance(eq, dict) else None
            for pl in (eq.get("players") or []) if isinstance(eq, dict) else []:
                st = pl.get("statistics") or {}
                st = (st[0] if st else {}) if isinstance(st, list) else st
                filas.append({"match_id": mid, "equipo_id": tid, "jugador_id": pl.get("id"),
                              "posicion": pl.get("position"), "minutos": pl.get("minutesPlayed"),
                              "suplente": pl.get("isSubstitute"), "nota": pl.get("matchRating"),
                              "fueras_de_juego": pl.get("offsides"), "fecha": fecha,
                              **{k: st.get(k) for k in ESTADISTICAS}})
    out = pd.concat([previo, pd.DataFrame(filas)]) if filas else previo
    out.to_csv(SALIDA, index=False)
    print(f"Forma de clubes: {len(nuevos)} partidos nuevos de {len(ligas)} ligas en {DIAS} días, "
          f"{len(filas)} filas de jugador. Total en {SALIDA}: {len(out)}. Llamadas {llamadas[0]} de {TOPE}.")


if __name__ == "__main__":
    main()
