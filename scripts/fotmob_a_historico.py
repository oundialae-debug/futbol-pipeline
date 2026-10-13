"""Fuente SIN cuota de Highlightly: FotMob (partidos, estadísticas por equipo con xG, jugadores con minutos/rating/xG,
mapa de tiros) -> historico + Champions + jugadores. Se ejecuta en GitHub Actions (fotmob_datos.yml).

Usuario 13/10/2026: se acabaron las llamadas a Highlightly (100/día en total) y hay que seguir con previos, post-partidos
y XI. Sondeo del 13/10: FotMob responde desde el runner sin clave (`/api/data/matches?date=` y `/api/data/matchDetails`).

Qué hace, para las fechas dadas (por defecto ayer y hoy, UTC):
  1. Lista los partidos de Premier (47), LaLiga (87), Serie A (55), Bundesliga (54), Ligue 1 (53) y Champions (42).
  2. Champions: escribe data/redes/ucl_calendario.csv (los que aún no han terminado, hoy y 3 días siguientes) con los
     nombres de los clubes de las 5 grandes tal y como los usa el histórico (el resto con el nombre de FotMob).
  3. Partidos terminados: baja matchDetails y
       - 5 ligas: sustituye/añade la fila (match_id NEGATIVO = crc32 de fecha+clubes, como fd_a_historico.py) en
         data/historico_partidos.csv con las columnas que da FotMob (xG, tiros, corners, faltas, posesión, pases...).
       - Champions: fila en data/redes/ucl_historico.csv (liga "Champions League", id 2486).
       - jugadores (todas las competiciones anteriores): data/fotmob_jugadores.csv, una fila por jugador y partido, con
         todas las estadísticas que da FotMob (minutos, rating, goles, asistencias, xG, xA, tiros, pases clave...).
  4. Guarda un ejemplo crudo (data/fotmob_ejemplo.json) y los títulos de estadística que no supo mapear
     (data/fotmob_titulos.md) para ampliar el mapa sin adivinar.
Nunca toca filas reales (id positivo) de Highlightly.

Uso: python3 scripts/fotmob_a_historico.py [AAAA-MM-DD ...]
"""
import csv
import json
import os
import re
import sys
import time
import zlib
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(__file__))
from fd_a_historico import parecido  # noqa: E402

HIST = os.environ.get("FM_HIST", "data/historico_partidos.csv")
UCL_H = os.environ.get("FM_UCL_H", "data/redes/ucl_historico.csv")
UCL_C = os.environ.get("FM_UCL_C", "data/redes/ucl_calendario.csv")
JUG = os.environ.get("FM_JUG", "data/fotmob_jugadores.csv")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
LIGAS = {47: ("Premier League", 33973), 87: ("La Liga", 119924), 55: ("Serie A", 115669),
         54: ("Bundesliga", 67162), 53: ("Ligue 1", 52695), 42: ("Champions League", 2486)}
MIN_PARECIDO = 0.78
TITULOS_SIN_MAPA = set()

# título FotMob (minúsculas) -> sufijo de columna del histórico (se usa l_<sufijo> / v_<sufijo>)
MAPA = {"expected goals (xg)": "expected_goals", "ball possession": "possession", "corners": "corners",
        "fouls committed": "fouls", "yellow cards": "yellow_cards", "red cards": "red_cards",
        "shots on target": "shots_on_target", "blocked shots": "blocked_shots", "shots off target": "shots_off_target",
        "offsides": "offsides", "interceptions": "interceptions", "clearances": "clearances", "key chances": "key_passes",
        "big chances": "big_chances_created", "tackles won": "successful_tackles", "total passes": "total_passes",
        "accurate passes": "successful_passes", "crosses": "crosses", "aerial duels won": "successful_aerial_duels",
        "dribbles": "dribbles", "xg open play": None, "xg set play": None, "xgot": None}


def get(url, intentos=3):
    for i in range(intentos):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (403, 404):
                return None
        except Exception:
            pass
        time.sleep(2 * (i + 1))
    return None


def num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?\d+(?:\.\d+)?", str(x))
    return float(m.group()) if m else None


def lista(fecha):
    j = get(f"https://www.fotmob.com/api/data/matches?date={fecha.replace('-', '')}")
    out = []
    for lg in (j or {}).get("leagues", []):
        pid = lg.get("primaryId") or lg.get("id")
        if pid in LIGAS and (lg.get("ccode") in ("ENG", "ESP", "ITA", "GER", "FRA", "INT") or pid == 42):
            for m in lg["matches"]:
                out.append((pid, m))
    return out


def catalogo(h):
    c = {}
    for r in h:
        if r["match_id"].startswith("-"):
            pass
        for n, i in ((r["local"], r["local_id"]), (r["visitante"], r["visitante_id"])):
            if i:
                c[n] = int(float(i))
    return c


def club(nombre, cat):
    ord_ = sorted(cat, key=lambda n: -parecido(nombre, n))
    if ord_ and parecido(nombre, ord_[0]) >= MIN_PARECIDO and (
            len(ord_) < 2 or parecido(nombre, ord_[0]) - parecido(nombre, ord_[1]) >= 0.05):
        return ord_[0], cat[ord_[0]]
    return nombre, None


def estadisticas(det):
    """{sufijo: (local, visitante)} de la pestaña 'All'."""
    out = {}
    grupos = (((det.get("content") or {}).get("stats") or {}).get("Periods") or {}).get("All", {}).get("stats", [])
    for g in grupos:
        for s in g.get("stats", []):
            t = str(s.get("title", "")).lower()
            v = s.get("stats")
            if not isinstance(v, list) or len(v) != 2:
                continue
            if t in MAPA:
                if MAPA[t]:
                    out[MAPA[t]] = (num(v[0]), num(v[1]))
            else:
                TITULOS_SIN_MAPA.add(str(s.get("title")))
    return out


def jugadores(det, fecha, liga, mid_fm):
    filas = []
    for pid, p in ((det.get("content") or {}).get("playerStats") or {}).items():
        f = {"fecha": fecha, "liga": liga, "fotmob_match_id": mid_fm, "fotmob_jugador_id": p.get("id"),
             "jugador": p.get("name"), "equipo": p.get("teamName"), "equipo_id_fotmob": p.get("teamId"),
             "portero": int(bool(p.get("isGoalkeeper")))}
        for grupo in p.get("stats", []):
            for etiqueta, d in (grupo.get("stats") or {}).items():
                st = (d or {}).get("stat") or {}
                f[(d or {}).get("key") or etiqueta] = st.get("value")
        filas.append(f)
    return filas


def escribir_filas(ruta, cols, filas):
    nuevo = not os.path.exists(ruta)
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if nuevo:
            w.writeheader()
        w.writerows(filas)


def main(fechas):
    with open(HIST, newline="", encoding="utf-8") as f:
        lect = csv.DictReader(f)
        cols = lect.fieldnames
        filas = list(lect)
    cat = catalogo(filas)
    claves = {}
    for i, r in enumerate(filas):
        claves.setdefault((r["liga_id"], r["local_id"], r["visitante_id"]), []).append((r["fecha"][:10], i, r["match_id"]))
    ucl_rows, ucl_exist = [], set()
    if os.path.exists(UCL_H):
        for r in csv.DictReader(open(UCL_H, newline="", encoding="utf-8")):
            ucl_exist.add((r["local"], r["visitante"], r["fecha"][:10]))
    jug_rows, futuros, nuevas, ejemplo = [], [], 0, False
    borrar = set()
    for fecha in fechas:
        for pid, m in lista(fecha):
            liga, lid = LIGAS[pid]
            st = m.get("status") or {}
            t_utc = st.get("utcTime") or m.get("time")
            home, away = m["home"]["name"], m["away"]["name"]
            a, b = club(home, cat), club(away, cat)
            if not st.get("finished"):
                if pid == 42 and not st.get("cancelled"):
                    futuros.append({"match_id": -int(m["id"]), "liga": liga, "liga_id": lid, "fecha": str(t_utc)[:10],
                                    "saque_utc": str(t_utc)[11:16], "local": a[0], "visitante": b[0],
                                    "ronda": f"FotMob {m['id']}"})
                continue
            det = get(f"https://www.fotmob.com/api/data/matchDetails?matchId={m['id']}")
            if not det:
                print(f"[!] sin detalle {home}-{away}")
                continue
            if not ejemplo:
                json.dump(det, open("data/fotmob_ejemplo.json", "w"), ensure_ascii=False)
                ejemplo = True
            dia = str(t_utc)[:10]
            est = estadisticas(det)
            fila = {c: "" for c in cols}
            fila.update({"fecha": str(t_utc)[:19].replace(" ", "T") + ".000Z" if "T" in str(t_utc) else str(t_utc),
                         "liga_id": lid, "liga": liga, "temporada": 2026, "local": a[0], "visitante": b[0],
                         "local_id": a[1] or "", "visitante_id": b[1] or "",
                         "goles_l": m["home"].get("score"), "goles_v": m["away"].get("score")})
            for suf, (x, y) in est.items():
                if f"l_{suf}" in fila:
                    fila[f"l_{suf}"], fila[f"v_{suf}"] = ("" if x is None else x), ("" if y is None else y)
            if "possession" in est:      # histórico: fracción (0.43)
                fila["l_possession"], fila["v_possession"] = est["possession"][0] / 100, est["possession"][1] / 100
            jug_rows += jugadores(det, dia, liga, m["id"])
            if pid == 42:
                if (a[0], b[0], dia) in ucl_exist:
                    continue
                fila["match_id"] = str(-zlib.crc32(f"{dia}|{a[0]}|{b[0]}".encode()))
                ucl_rows.append(fila)
                ucl_exist.add((a[0], b[0], dia))
                continue
            if not a[1] or not b[1]:
                print(f"[!] sin id de club: {home}/{away}")
                continue
            fila["match_id"] = str(-zlib.crc32(f"{dia}|{a[1]}|{b[1]}".encode()))
            previas = claves.get((str(lid), str(a[1]), str(b[1])), [])
            if any(abs((pd.Timestamp(d) - pd.Timestamp(dia)).days) <= 1 and not mid.startswith("-") for d, _, mid in previas):
                continue              # Highlightly ya lo trae
            for d, i, mid in previas:    # fila negativa previa (football-data): se sustituye por la de FotMob
                if mid.startswith("-") and abs((pd.Timestamp(d) - pd.Timestamp(dia)).days) <= 1:
                    borrar.add(i)
            filas.append(fila)
            nuevas += 1
    if nuevas or borrar:
        filas = [r for i, r in enumerate(filas) if i not in borrar]
        with open(HIST, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(filas)
    if ucl_rows:
        escribir_filas(UCL_H, cols, ucl_rows)
    if futuros:
        pd.DataFrame(futuros).drop_duplicates(["fecha", "local", "visitante"]).sort_values(["fecha", "saque_utc"]).to_csv(UCL_C, index=False)
    if jug_rows:
        antes = pd.read_csv(JUG, low_memory=False) if os.path.exists(JUG) else pd.DataFrame()
        todo = pd.concat([antes, pd.DataFrame(jug_rows)], ignore_index=True).drop_duplicates(["fotmob_match_id", "fotmob_jugador_id"], keep="last")
        todo.to_csv(JUG, index=False)
    open("data/fotmob_titulos.md", "w").write("# Títulos de estadística de FotMob sin mapear\n\n" + "\n".join(f"- {t}" for t in sorted(TITULOS_SIN_MAPA)) + "\n")
    print(f"Ligas: +{nuevas} filas (sustituidas {len(borrar)}); Champions: +{len(ucl_rows)} jugadas, {len(futuros)} por jugar; jugadores: {len(jug_rows)}")


if __name__ == "__main__":
    hoy = datetime.now(timezone.utc).date()
    fs = sys.argv[1:] or [(hoy - timedelta(days=k)).isoformat() for k in (2, 1, 0)] + [(hoy + timedelta(days=k)).isoformat() for k in (1, 2, 3)]
    main(fs)
