"""
¿El modelo exagera los juegos también ANTES del partido y en miles de partidos, o solo en el directo
de un día? (30/09/2026, pregunta del usuario: "que aprenda también del previo, no solo del directo").

Historial Sackmann (fuerza de cada jugador ANTES de cada partido, modelo de puntos, sin mirar el
resultado) + marcador final -> juegos totales reales. Para cada partido: juegos esperados por el
modelo y P(más de L) en líneas fijas. Mide el sesgo por circuito, nivel y año, y prueba una
recalibración aprendida con 2021-2023 sobre 2024-2026 (partidos que no vio). Sin cuotas: el
precio previo de juegos solo lo tenemos de Kalshi (kalshi_puntos.py).
Partidos completos (sin RET, W/O ni DEF). Escribe data/tenis/historico_juegos.md.
"""
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import markov_tenis as K  # noqa: E402
import modelo_puntos as P  # noqa: E402

SAL = "data/tenis/historico_juegos.md"
COEF = "data/tenis/correccion_juegos_historica.json"
NIVEL = {"G": "Grand Slam", "M": "Masters/1000", "A": "ATP/WTA 250-500", "P": "WTA 500-1000", "PM": "WTA 500-1000",
         "I": "WTA 250", "F": "Finales", "C": "Challenger/125", "D": "Copa Davis/BJK", "S": "ITF", "15": "ITF", "25": "ITF"}


def juegos(score):
    s = str(score)
    if any(x in s for x in ("RET", "W/O", "DEF", "Def", "unfinished", "?")) or not s.strip():
        return np.nan
    tot = 0
    for a, b in re.findall(r"(\d+)-(\d+)", re.sub(r"\(\d+\)", "", s)):
        a, b = int(a), int(b)
        if a > 7 or b > 7:           # super tie-break a 10 como set decisivo: cuenta como 1 juego
            tot += 1
        else:
            tot += a + b
    return tot or np.nan


def main():
    cache, filas = {}, []
    for circ in ("atp", "wta"):
        d, _ = P.calcular(circ, P.PARAMS[circ])
        d = d[d.inicio >= "2021-01-01"].copy()
        d["juegos"] = d.score.map(juegos)
        d = d.dropna(subset=["juegos", "p_w", "p_l"])
        for r in d.itertuples():
            bo = int(r.best_of) if r.best_of in (3, 5) else 3
            k = (K.redondear(r.p_w), K.redondear(r.p_l), bo)
            if k not in cache:
                cache[k] = K.partido(*k)[1]
            tot = cache[k]
            filas.append({"circ": circ, "nivel": NIVEL.get(str(r.tourney_level), str(r.tourney_level)), "bo": bo,
                          "anio": str(r.inicio)[:4], "juegos": r.juegos, "esperado": sum(g * p for g, p in tot.items()),
                          **{f"p{L}": sum(p for g, p in tot.items() if g > L) for L in (19.5, 21.5, 23.5, 36.5, 38.5)}})
    h = pd.DataFrame(filas)
    h3 = h[h.bo == 3]
    lin = ["# Juegos totales antes del partido: ¿exagera el modelo? (historial 2021-2026)\n",
           f"{len(h):,} partidos completos (al mejor de 3: {len(h3):,}). Modelo de puntos con la fuerza de cada jugador "
           "ANTES del partido.\n", "## Juegos esperados por el modelo frente a los reales (al mejor de 3)\n",
           "| circuito | nivel | partidos | modelo espera | reales | diferencia |", "|---|---|---|---|---|---|"]
    for (c, n), g in h3.groupby(["circ", "nivel"]):
        if len(g) >= 200:
            lin.append(f"| {c.upper()} | {n} | {len(g):,} | {g.esperado.mean():.2f} | {g.juegos.mean():.2f} | "
                       f"{g.esperado.mean() - g.juegos.mean():+.2f} |")
    lin += ["", "## Por año (al mejor de 3, todos los niveles)\n", "| año | partidos | modelo espera | reales | diferencia |",
            "|---|---|---|---|---|"]
    for a, g in h3.groupby("anio"):
        lin.append(f"| {a} | {len(g):,} | {g.esperado.mean():.2f} | {g.juegos.mean():.2f} | {g.esperado.mean() - g.juegos.mean():+.2f} |")
    lin += ["", "## P(más de la línea): dice el modelo / pasa de verdad (al mejor de 3)\n",
            "| línea | modelo | real | sesgo |", "|---|---|---|---|"]
    for L in (19.5, 21.5, 23.5):
        m, r = h3[f"p{L}"].mean(), (h3.juegos > L).mean()
        lin.append(f"| {L} | {m:.1%} | {r:.1%} | {m - r:+.1%} |")
    # recalibración aprendida con 2021-2023, juzgada en 2024-2026
    tr, te = h3[h3.anio <= "2023"], h3[h3.anio >= "2024"]
    lin += ["", "## Recalibración aprendida con 2021-2023, juzgada en 2024-2026 (partidos que no vio)\n",
            "| línea | Brier modelo | Brier recalibrado | mejora |", "|---|---|---|---|"]
    from sklearn.linear_model import LogisticRegression

    def lg(p):
        return np.log(np.clip(p, .01, .99) / (1 - np.clip(p, .01, .99))).reshape(-1, 1)
    for L in (19.5, 21.5, 23.5):
        m = LogisticRegression(C=1e6).fit(lg(tr[f"p{L}"].values), (tr.juegos > L).values)
        y = (te.juegos > L).values
        b0 = np.mean((te[f"p{L}"].values - y) ** 2)
        b1 = np.mean((m.predict_proba(lg(te[f"p{L}"].values))[:, 1] - y) ** 2)
        lin.append(f"| {L} | {b0:.4f} | {b1:.4f} | {(b0 - b1) / b0:+.1%} |")
    # corrección para el PREVIO, por circuito, con todo el historial al mejor de 3 (las tres líneas apiladas):
    # p_corregida = sig(a + b·logit(p_modelo) + c·(línea − 21.5)). La usa evaluar_juegos.py con los previos.
    import json
    coef = {}
    for c, g in h3.groupby("circ"):
        X = np.vstack([np.column_stack([lg(g[f"p{L}"].values)[:, 0], np.full(len(g), L - 21.5)]) for L in (19.5, 21.5, 23.5)])
        y = np.concatenate([(g.juegos > L).values for L in (19.5, 21.5, 23.5)])
        m = LogisticRegression(C=1e6).fit(X, y)
        coef[c] = [float(m.intercept_[0]), float(m.coef_[0][0]), float(m.coef_[0][1])]
    json.dump(coef, open(COEF, "w"), indent=1)
    lin += ["", f"Corrección guardada en `{COEF}` (por circuito): {coef}"]
    open(SAL, "w").write("\n".join(lin) + "\n")
    print("\n".join(lin))


if __name__ == "__main__":
    main()
