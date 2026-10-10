"""
La IA del no favorito (ia_no_favorito.py) en PAPEL con partidos de verdad, desde el 10/10/2026.
El usuario: ranking y puntos están online (API-Tennis get_standings, con player_key), la IA mejoró año a
año (2025: +7,9% en 659 apuestas) y 2-3 apuestas al día no es poco. Hay que verla en partidos que no vio.

Cada hora (desde previa_juegos.registrar, la misma llamada get_odds): para cada partido ATP/WTA de
CIRCUITO aún sin empezar (la IA solo se entrenó con circuito: Challenger e ITF fuera), mismas variables que
en el historial: bet365 y Pinnacle (Pncl) sin margen del no favorito de bet365, mejor cuota del mercado,
ranking y puntos (get_standings, 2 peticiones al día, guardado en ranking_<fecha>.json), superficie, nivel,
ronda, al mejor de 5, WTA. Si p_IA × cuota bet365 − 1 > 3%: apuesta en papel (una por partido, la primera
vez que cumple) en data/tenis/api_tennis/ia_no_favorito/<fecha>.csv, con la mejor cuota blanda al lado.
La IA se entrena con TODO tennis-data (2020-2026) al arrancar cada pasada (unos segundos).
"""
import csv
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import api_tennis as A  # noqa: E402

DIR = "data/tenis/api_tennis/ia_no_favorito"
UMBRAL = 0.03
BLANDAS = ("bet365", "1xBet", "Marathon", "Sbo", "WilliamHill", "BetVictor", "Betano")
SLAMS = ("australian open", "roland garros", "french open", "wimbledon", "us open")
M1000 = ("shanghai", "paris", "indian wells", "miami", "madrid", "rome", "monte carlo", "toronto", "montreal",
         "cincinnati", "canada")
A500 = ("tokyo", "beijing", "basel", "vienna", "dubai", "rotterdam", "acapulco", "barcelona", "hamburg",
        "washington", "halle", "queen", "rio de janeiro", "doha", "dallas")
W1000 = ("beijing", "wuhan", "doha", "dubai", "indian wells", "miami", "madrid", "rome", "toronto", "montreal",
         "cincinnati", "canada")
W500 = ("tokyo", "ningbo", "brisbane", "adelaide", "abu dhabi", "linz", "stuttgart", "charleston", "berlin",
        "eastbourne", "washington", "seoul", "san diego", "guadalajara")
CAMPOS = ["hora", "event_key", "tipo", "torneo", "ronda", "no_favorito", "lado", "p_ia", "p_bet365", "p_pinnacle",
          "cuota_bet365", "mejor_cuota", "mejor_casa", "valor"]


def modelo():
    import ia_no_favorito as I
    from sklearn.ensemble import HistGradientBoostingClassifier
    d = I.datos()
    m = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, l2_regularization=1.0,
                                       min_samples_leaf=200, random_state=0).fit(d[I.X], d.y)
    return m, I.X


def ranking(ahora):
    ruta = f"{DIR}/ranking_{ahora:%Y-%m-%d}.json"
    if os.path.exists(ruta):
        return json.load(open(ruta))
    rk = {}
    for t in ("ATP", "WTA"):
        for r in A._pedir("get_standings", event_type=t):
            try:
                rk[str(r["player_key"])] = (int(r["place"]), float(r["points"]))
            except (KeyError, ValueError, TypeError):
                pass
    os.makedirs(DIR, exist_ok=True)
    json.dump(rk, open(ruta, "w"))
    return rk


def nivel(tipo, torneo):
    t = str(torneo).lower()
    if any(s in t for s in SLAMS):
        return 3
    wta = "wta" in str(tipo).lower()
    if any(s in t for s in (W1000 if wta else M1000)):
        return 2
    if any(s in t for s in (W500 if wta else A500)):
        return 1
    return 0


def ronda(texto):
    t = str(texto).lower()
    if "final" in t and "1/" not in t and "semi" not in t and "quarter" not in t:
        return 7
    m = re.search(r"1/(\d+)", t)
    return {2: 6, 4: 5, 8: 4, 16: 3, 32: 2, 64: 1}.get(int(m.group(1)), 1) if m else 4


def _med(d):
    v = [float(x) for x in (d or {}).values() if x not in (None, "")]
    return v


def registrar(ahora, partidos, odds, superficie):
    tour = [p for p in partidos if not p.get("event_status") and p.get("event_type_type") in ("Atp Singles", "Wta Singles")]
    if not tour:
        return
    os.makedirs(DIR, exist_ok=True)
    ruta = f"{DIR}/{ahora:%Y-%m-%d}.csv"
    hechos = {r["event_key"] for r in csv.DictReader(open(ruta))} if os.path.exists(ruta) else set()
    rk = ranking(ahora)
    m, X = modelo()
    nuevas = []
    for p in tour:
        k = str(p.get("event_key"))
        o = odds.get(k) if isinstance(odds, dict) else None
        if k in hechos or not o:
            continue
        ha = o.get("Home/Away", {})
        h, w = ha.get("Home", {}), ha.get("Away", {})
        try:
            b1, b2, p1, p2 = float(h["bet365"]), float(w["bet365"]), float(h["Pncl"]), float(w["Pncl"])
        except (KeyError, TypeError, ValueError):
            continue
        ud = 1 if b1 > b2 else 2                         # no favorito de bet365
        c_ud, c_fav = (b1, b2) if ud == 1 else (b2, b1)
        ps_ud, ps_fav = (p1, p2) if ud == 1 else (p2, p1)
        lado_ud = h if ud == 1 else w
        cuotas = {c: float(x) for c, x in lado_ud.items() if x not in (None, "")}
        k_ud = str(p.get("first_player_key" if ud == 1 else "second_player_key"))
        k_fav = str(p.get("second_player_key" if ud == 1 else "first_player_key"))
        if k_ud not in rk or k_fav not in rk:
            continue                                     # sin ranking no hay dato: no se inventa
        sup = superficie(p)
        f = {"p365": (1 / c_ud) / (1 / c_ud + 1 / c_fav), "pps": (1 / ps_ud) / (1 / ps_ud + 1 / ps_fav),
             "max_rel": max(cuotas.values()) / c_ud,
             "log_rk": np.log(max(rk[k_ud][0], 1)) - np.log(max(rk[k_fav][0], 1)),
             "log_pt": np.log(max(rk[k_ud][1], 1)) - np.log(max(rk[k_fav][1], 1)),
             "sup_Hard": int(sup == "Hard"), "sup_Clay": int(sup == "Clay"), "sup_Grass": int(sup == "Grass"),
             "nivel": nivel(p.get("event_type_type"), p.get("tournament_name")),
             "ronda": ronda(p.get("tournament_round")),
             "bo5": int(A.mejor_de(p) == 5), "wta": int("wta" in str(p.get("event_type_type")).lower())}
        f["dif_ps"] = f["pps"] - f["p365"]
        p_ia = float(m.predict_proba(pd.DataFrame([f])[X])[:, 1][0])
        v = p_ia * c_ud - 1
        if v > UMBRAL:
            blandas = {c: x for c, x in cuotas.items() if c in BLANDAS}
            mc, mx = max(blandas.items(), key=lambda z: z[1])
            nuevas.append({"hora": f"{ahora:%Y-%m-%d %H:%M}", "event_key": k, "tipo": p.get("event_type_type"),
                           "torneo": p.get("tournament_name"), "ronda": p.get("tournament_round"),
                           "no_favorito": p.get("event_first_player" if ud == 1 else "event_second_player"),
                           "lado": f"jugador{ud}", "p_ia": round(p_ia, 4), "p_bet365": round(f["p365"], 4),
                           "p_pinnacle": round(f["pps"], 4), "cuota_bet365": c_ud, "mejor_cuota": mx,
                           "mejor_casa": mc, "valor": round(v, 4)})
    nuevo = not os.path.exists(ruta)
    with open(ruta, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerows(nuevas)
    print(f"IA no favorito: {len(nuevas)} apuestas nuevas en papel")


def tabla():
    import glob
    fs = sorted(f for f in glob.glob(f"{DIR}/*.csv"))
    lin = ["## IA del no favorito, en papel (circuito ATP/WTA, desde el 10/10)", ""]
    if not fs:
        return lin + ["Todavía sin apuestas."]
    v = pd.concat(pd.read_csv(f) for f in fs)
    r = pd.concat(pd.read_csv(f) for f in glob.glob("data/tenis/api_tennis/resultados/*.csv")).drop_duplicates(
        "event_key", keep="last")
    r = r[r.estado.isin(["Finished", "Retired"])].copy()     # retirada: gana quien avanza (como en el historial)
    s = r.sets.astype(str).str.split("-", expand=True)
    r["s1"], r["s2"] = pd.to_numeric(s[0], errors="coerce"), pd.to_numeric(s[1], errors="coerce")
    v = v.merge(r[["event_key", "s1", "s2"]], on="event_key")
    if v.empty:
        return lin + [f"{len(pd.concat(pd.read_csv(f) for f in fs))} apuestas apuntadas, ninguna resuelta todavía."]
    v["gana"] = np.where(v.lado == "jugador1", v.s1 > v.s2, v.s2 > v.s1)
    lin += ["| cuota | apuestas | aciertos | hacen falta | beneficio | sigmas |", "|---|---|---|---|---|---|"]
    for nombre, c in (("bet365", "cuota_bet365"), ("mejor casa blanda", "mejor_cuota")):
        b = np.where(v.gana, v[c] - 1, -1.0)
        sig = b.mean() / (b.std(ddof=1) / np.sqrt(len(b))) if len(b) > 1 else float("nan")
        lin.append(f"| {nombre} | {len(v)} | {v.gana.mean():.0%} | {np.mean(1 / v[c]):.0%} | {b.mean():+.1%} | {sig:+.2f} |")
    return lin
