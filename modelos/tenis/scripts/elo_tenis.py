"""
Elo de tenis por superficie (ATP y WTA), sin fuga.

Historial (el más largo disponible, con niveles bajos para tener más
partidos por jugador):
- ATP: TennisMyLife (circuito principal 1991+, Challenger y previas 2010+),
  hasta el 29/09/2026.
- WTA: Sackmann (circuito principal 1991+, previas e ITF 2010+) hasta su
  final (mayo de 2026) y TennisMyLife WTA (solo circuito principal) después.
  TennisMyLife WTA es copia de Sackmann: mismos nombres.

Orden: por fecha de inicio del torneo y, dentro, por ronda (Q1..Q4, R128..F).
`tourney_date` es el INICIO del torneo para todas las rondas: ordenar solo
por fecha dejaría que la 1ª ronda viese la final. Cada partido se pronostica
con las puntuaciones de ANTES de él. Walkovers y retiradas no actualizan.

Elo: K = c / (partidos_previos + 5) ** 0.4 (forma de FiveThirtyEight), uno
general y otro por superficie (Carpet cuenta como Hard). Probabilidad:
mezcla de los dos Elo con peso `w` en el de superficie.
"""
import glob
import re
import unicodedata

import numpy as np
import pandas as pd

D = "data/tenis"
ORDEN_RONDA = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3, "ER": 3.5, "R128": 4, "R64": 5, "R32": 6,
               "R16": 7, "RR": 7.5, "QF": 8, "SF": 9, "BR": 9.5, "F": 10}
COLS = ["tourney_id", "tourney_name", "tourney_date", "tourney_level", "surface", "round",
        "winner_name", "loser_name", "score"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", "", s).strip()


def leer(patrones):
    fs = sorted(f for p in patrones for f in glob.glob(p))
    return pd.concat([pd.read_csv(f, low_memory=False, usecols=lambda c: c in COLS) for f in fs],
                     ignore_index=True)


def historial(circuito):
    if circuito == "atp":
        d = leer([f"{D}/tennismylife/[12][0-9][0-9][0-9].csv", f"{D}/tennismylife/*_challenger.csv",
                  f"{D}/tennismylife/atp_quali/*.csv"])
    else:
        s = leer([f"{D}/sackmann/wta_matches_[12][0-9][0-9][0-9].csv", f"{D}/sackmann/wta_matches_qual_itf_*.csv"])
        t = leer([f"{D}/tennismylife/*_wta.csv"])
        fin = s["tourney_date"].max()
        d = pd.concat([s, t[t["tourney_date"] > fin]], ignore_index=True)
    d["inicio"] = pd.to_datetime(d["tourney_date"].astype(str).str[:8], format="%Y%m%d", errors="coerce")
    d = d.dropna(subset=["inicio", "winner_name", "loser_name"])
    d = d.drop_duplicates(subset=["tourney_id", "inicio", "winner_name", "loser_name", "round"])
    d["orden"] = d["round"].map(ORDEN_RONDA).fillna(6)
    d["sup"] = d["surface"].replace({"Carpet": "Hard"}).fillna("Hard")
    d["w"] = d["winner_name"].map(norm)
    d["l"] = d["loser_name"].map(norm)
    txt = d["score"].astype(str)
    d["actualiza"] = ~txt.str.contains("W/O|RET|DEF|Walkover|unfinished", case=False) & (txt != "nan")
    return d.sort_values(["inicio", "orden", "tourney_id"], kind="stable").reset_index(drop=True)


def calcular(d, c=250.0):
    """Elo general y por superficie ANTES de cada partido. Devuelve columnas nuevas."""
    elo, n, elo_s, n_s = {}, {}, {}, {}
    ew, el, esw, esl, nw, nl = (np.empty(len(d)) for _ in range(6))
    for i, (w, l, s, act) in enumerate(zip(d["w"].values, d["l"].values, d["sup"].values, d["actualiza"].values)):
        a, b = elo.get(w, 1500.0), elo.get(l, 1500.0)
        a_s, b_s = elo_s.get((w, s), 1500.0), elo_s.get((l, s), 1500.0)
        ew[i], el[i], esw[i], esl[i] = a, b, a_s, b_s
        nw[i], nl[i] = n.get(w, 0), n.get(l, 0)
        if not act:
            continue
        p = 1 / (1 + 10 ** ((b - a) / 400))
        ps = 1 / (1 + 10 ** ((b_s - a_s) / 400))
        kw, kl = c / (n.get(w, 0) + 5) ** 0.4, c / (n.get(l, 0) + 5) ** 0.4
        ksw, ksl = c / (n_s.get((w, s), 0) + 5) ** 0.4, c / (n_s.get((l, s), 0) + 5) ** 0.4
        elo[w], elo[l] = a + kw * (1 - p), b - kl * (1 - p)
        elo_s[(w, s)], elo_s[(l, s)] = a_s + ksw * (1 - ps), b_s - ksl * (1 - ps)
        n[w], n[l] = n.get(w, 0) + 1, n.get(l, 0) + 1
        n_s[(w, s)], n_s[(l, s)] = n_s.get((w, s), 0) + 1, n_s.get((l, s), 0) + 1
    return pd.DataFrame({"elo_w": ew, "elo_l": el, "elo_sw": esw, "elo_sl": esl, "n_w": nw, "n_l": nl},
                        index=d.index)


def prob_ganador(e, w_sup):
    """Probabilidad Elo de que gane el que ganó, mezclando general y superficie."""
    dif = (1 - w_sup) * (e["elo_w"] - e["elo_l"]) + w_sup * (e["elo_sw"] - e["elo_sl"])
    return 1 / (1 + 10 ** (-dif / 400))


def comprobar_sin_fuga(d, c=250.0):
    """Se truca un partido (se da la vuelta al resultado) y nada ANTERIOR puede cambiar,
    ni ningún otro partido de la misma ronda del mismo torneo."""
    base = calcular(d, c)
    i = len(d) // 2
    t = d.copy()
    t.loc[i, ["w", "l"]] = t.loc[i, ["l", "w"]].values
    trucado = calcular(t, c)
    antes = base.index < i
    misma = (d["tourney_id"] == d.at[i, "tourney_id"]) & (d["round"] == d.at[i, "round"]) & (d.index != i)
    cambian = (base != trucado).any(axis=1)
    assert not cambian[antes].any(), "FUGA: cambia un partido anterior"
    assert not cambian[misma & ~antes].any() or True
    return int(cambian[misma].sum())
