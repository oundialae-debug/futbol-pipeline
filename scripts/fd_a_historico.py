"""Respaldo SIN API de Highlightly: completa data/historico_partidos.csv con football-data.co.uk.

Usuario 13/10/2026: se acabaron las llamadas (100/día en total) y la API devolvió listas vacías. football-data.co.uk
publica gratis, por liga, resultados + xG (HxG/AxG) + tiros (HS/HST) + corners, faltas y tarjetas de la temporada en curso.
Validado el 13/10 contra Highlightly (Premier y Serie A, 10-12/10): goles y tiros iguales, xG igual o ±0.3.

Qué hace (en GitHub Actions: desde el contenedor de Claude esa web está bloqueada):
  1. Baja E0, SP1, I1, D1, F1 de la temporada actual a data/football_data/<temp>_<liga>.csv.
  2. Por cada partido TERMINADO que no esté ya en historico_partidos.csv (mismo liga_id, mismos clubes, +-1 día)
     añade una fila con las columnas que da football-data (el resto queda vacío) y match_id NEGATIVO
     (crc32 de fecha+clubes). Nunca toca filas reales de Highlightly.
  3. Si Highlightly trae después ese partido, la fila negativa se borra (sin duplicados).
Los clubes se emparejan con los ids que ya hay en el histórico (norm/parecido de cuotas_football_data.py); lo que no
empareja se lista y se salta (nunca se inventa un id).

Uso:  python3 scripts/fd_a_historico.py          (baja y fusiona)
      FD_LOCAL=1 python3 scripts/fd_a_historico.py   (no baja; usa los CSV que ya hay en data/football_data, para pruebas)
"""
import csv
import os
import sys
import time
import zlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from difflib import SequenceMatcher  # noqa: E402
import unicodedata  # noqa: E402
from cuotas_football_data import COD  # noqa: E402

HIST = os.environ.get("FD_HIST", "data/historico_partidos.csv")
CARPETA = os.environ.get("FD_CARPETA", "data/football_data")
TEMP = os.environ.get("FD_TEMP", "2627")
LIGAS = {"E0": "Premier League", "SP1": "La Liga", "I1": "Serie A", "D1": "Bundesliga", "F1": "Ligue 1"}
MIN_PARECIDO = 0.78
# nombres de football-data que el texto no empareja solo (revisados a mano)
ALIAS = {"man city": "manchester city", "man united": "manchester united", "nott'm forest": "nottingham forest",
         "hull": "hull city", "m'gladbach": "borussia monchengladbach", "milan": "ac milan", "roma": "as roma",
         "paris sg": "paris saint germain", "ath madrid": "atletico madrid", "ath bilbao": "athletic club",
         "sociedad": "real sociedad", "betis": "real betis", "vallecano": "rayo vallecano", "bayern munich": "bayern munich",
         "dortmund": "borussia dortmund", "leverkusen": "bayer leverkusen", "ein frankfurt": "eintracht frankfurt",
         "stuttgart": "vfb stuttgart", "hoffenheim": "1899 hoffenheim", "mainz": "fsv mainz 05", "augsburg": "fc augsburg",
         "köln": "fc koln", "koln": "fc koln", "st pauli": "fc st pauli", "freiburg": "sc freiburg", "union berlin": "union berlin",
         "wolfsburg": "vfl wolfsburg", "bremen": "werder bremen", "heidenheim": "fc heidenheim", "brest": "stade brestois 29",
         "st etienne": "saint etienne", "paris fc": "paris fc", "le havre": "le havre ac", "troyes": "estac troyes",
         "rennes": "rennes fc", "tottenham": "tottenham", "wolves": "wolverhampton wanderers", "leeds": "leeds united",
         "newcastle": "newcastle united", "hamburg": "hamburger sv", "paderborn": "sc paderborn 07", "celta": "celta de vigo", "la coruna": "deportivo la coruna", "santander": "racing santander", "west ham": "west ham united", "brighton": "brighton and hove albion", "internazionale": "inter", "sport club freiburg": "sc freiburg",
         "fc bayern munchen": "bayern munich"}


def limpio(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace(".", " ").replace("-", " ")
    return " ".join(s.split())


def parecido(a, b):
    a0, b = limpio(a), limpio(b)
    ta, tb = set(a0.split()), set(b.split())
    mejor = 0.9 if (ta and tb and (ta <= tb or tb <= ta) and min(len(a0), len(b)) >= 4) else 0.0   # "Coventry" / "Coventry City"
    for a in {a0, ALIAS.get(a0, a0)}:          # con y sin alias: el alias solo ayuda, nunca rompe un nombre que ya coincide
        mejor = max(mejor, 1.0 if a == b else SequenceMatcher(None, a, b).ratio())
    return mejor
DESDE = "2026-08-01"
LON = ZoneInfo("Europe/London")


def bajar():
    import requests
    os.makedirs(CARPETA, exist_ok=True)
    for cod in LIGAS:
        url = f"https://www.football-data.co.uk/mmz4281/{TEMP}/{cod}.csv"
        r = None
        for i in range(3):
            try:
                r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 2yellow-fd"})
                if r.status_code == 200 and r.content:
                    break
            except Exception:
                pass
            time.sleep(3 * (i + 1))
        if r is None or r.status_code != 200 or not r.content:
            print(f"FALLO {cod}: {getattr(r, 'status_code', 'sin respuesta')}")
            continue
        open(f"{CARPETA}/{TEMP}_{cod}.csv", "wb").write(r.content)


def num(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def utc_iso(fecha, hora):
    """football-data da la hora local del Reino Unido (dd/mm/yyyy, hh:mm)."""
    d = datetime.strptime(f"{fecha} {hora if isinstance(hora, str) and ':' in hora else '12:00'}", "%d/%m/%Y %H:%M")
    return d.replace(tzinfo=LON).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:00.000Z")


def main():
    if os.environ.get("FD_LOCAL") != "1":
        bajar()
    with open(HIST, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        cols = lector.fieldnames
        filas = list(lector)
    reales = [r for r in filas if not r["match_id"].startswith("-")]
    # clubes de cada liga: nombre -> id (el último que aparezca)
    clubes = {}
    for r in reales:
        c = clubes.setdefault(int(r["liga_id"]), {})
        c[r["local"]] = int(r["local_id"])
        c[r["visitante"]] = int(r["visitante_id"])
    claves = {}   # (liga_id, local_id, visitante_id) -> lista de fechas de filas reales
    for r in reales:
        claves.setdefault((int(r["liga_id"]), int(r["local_id"]), int(r["visitante_id"])), []).append(r["fecha"][:10])

    def hay_real(lid, a, b, dia):
        d0 = pd.Timestamp(dia)
        return any(abs((pd.Timestamp(x) - d0).days) <= 1 for x in claves.get((lid, a, b), []))

    # 1) fuera las filas negativas que Highlightly ya trae
    antes = len(filas)
    filas = [r for r in filas if not r["match_id"].startswith("-") or not hay_real(
        int(r["liga_id"]), int(r["local_id"]), int(r["visitante_id"]), r["fecha"][:10])]
    quitadas = antes - len(filas)
    existentes = {(int(r["liga_id"]), int(r["local_id"]), int(r["visitante_id"]), r["fecha"][:10])
                  for r in filas if r["match_id"].startswith("-")}

    nuevas, sin_club, ultima = [], {}, {}
    for cod, liga in LIGAS.items():
        ruta = f"{CARPETA}/{TEMP}_{cod}.csv"
        if not os.path.exists(ruta):
            print(f"{liga}: sin fichero")
            continue
        d = pd.read_csv(ruta, encoding="latin-1")
        d.columns = [c.replace("﻿", "").replace("ï»¿", "") for c in d.columns]
        d = d[d.FTHG.notna() & d.Date.notna()]
        lid = COD[cod]
        catalogo = clubes.get(lid, {})

        def club(nombre):
            if not catalogo:
                return None
            ordenados = sorted(catalogo, key=lambda n: -parecido(nombre, n))
            mejor = ordenados[0]
            ok = parecido(nombre, mejor) >= MIN_PARECIDO and (
                len(ordenados) < 2 or parecido(nombre, mejor) - parecido(nombre, ordenados[1]) >= 0.05)   # sin empates
            if ok and os.environ.get("FD_MAPA"):
                print(f"   {liga}: {nombre} -> {mejor}")
            return (mejor, catalogo[mejor]) if ok else None
        if len(d):
            ultima[liga] = d.Date.iloc[-1]
        for x in d.itertuples():
            fecha = utc_iso(x.Date, getattr(x, "Time", None))
            if fecha[:10] < DESDE:
                continue
            a, b = club(x.HomeTeam), club(x.AwayTeam)
            if not a or not b:
                for n, c in ((x.HomeTeam, a), (x.AwayTeam, b)):
                    if not c:
                        sin_club.setdefault(liga, set()).add(n)
                continue
            if hay_real(lid, a[1], b[1], fecha[:10]) or (lid, a[1], b[1], fecha[:10]) in existentes:
                continue
            hs, as_ = num(getattr(x, "HS", None)), num(getattr(x, "AS", None))
            hst, ast = num(getattr(x, "HST", None)), num(getattr(x, "AST", None))
            fila = {c: "" for c in cols}
            fila.update({"match_id": str(-zlib.crc32(f"{fecha[:10]}|{a[1]}|{b[1]}".encode())), "fecha": fecha,
                         "liga_id": lid, "liga": liga, "temporada": 2026, "local_id": a[1], "local": a[0],
                         "visitante_id": b[1], "visitante": b[0], "goles_l": int(x.FTHG), "goles_v": int(x.FTAG)})
            mapa = {"l_corners": "HC", "v_corners": "AC", "l_fouls": "HF", "v_fouls": "AF", "l_yellow_cards": "HY",
                    "v_yellow_cards": "AY", "l_red_cards": "HR", "v_red_cards": "AR", "l_expected_goals": "HxG",
                    "v_expected_goals": "AxG", "l_shots_on_target": "HST", "v_shots_on_target": "AST"}
            for dest, orig in mapa.items():
                v = num(getattr(x, orig, None))
                if dest in fila and v is not None:
                    fila[dest] = v
            if hs is not None and hst is not None and "l_shots_off_target" in fila:
                fila["l_shots_off_target"] = hs - hst      # fuera + bloqueados (football-data no los separa)
            if as_ is not None and ast is not None and "v_shots_off_target" in fila:
                fila["v_shots_off_target"] = as_ - ast
            nuevas.append(fila)
            existentes.add((lid, a[1], b[1], fecha[:10]))
    if nuevas or quitadas:
        with open(HIST, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(filas + nuevas)
    for liga, f in ultima.items():
        print(f"{liga}: último partido en football-data {f}")
    print(f"Filas añadidas: {len(nuevas)}; filas de football-data sustituidas por Highlightly: {quitadas}")
    for liga, s in sin_club.items():
        print(f"[!] {liga}: sin emparejar -> {sorted(s)}")
    for n in nuevas[-12:]:
        print(f"  + {n['fecha'][:10]} {n['local']} {n['goles_l']}-{n['goles_v']} {n['visitante']} xG {n['l_expected_goals']}-{n['v_expected_goals']}")


if __name__ == "__main__":
    main()
