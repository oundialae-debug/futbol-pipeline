"""
Corregir el defecto de fábrica del modelo de puntos (06/10/2026, "mejora el modelo").

historico_juegos.py mostró que el modelo espera +1 a +5 juegos de más en TODOS los niveles: ve a los
dos jugadores demasiado igualados (fuerzas encogidas). Arreglo en la raíz, antes del cálculo de Markov:
    m = (pa + pb)/2,  d = pa − pb
    pa' = m + c + k·d/2,   pb' = m + c − k·d/2
k > 1 separa a los jugadores (más diferencia de nivel -> menos juegos y favorito más claro);
c mueve el nivel medio de saque (más saque -> más juegos ganados al saque -> más juegos).
(k, c) se eligen por circuito y nivel con 2021-2023 (log-verosimilitud del total de juegos real) y se
juzgan en 2024-2026, partidos que no vieron: juegos (error medio, Brier en 19,5/21,5/23,5) y ganador
(acierto, log-loss). Resultado: data/tenis/ajuste_separacion.md y .json (lo lee pronosticos_api).
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import historico_juegos as H  # noqa: E402
import markov_tenis as K  # noqa: E402
import modelo_puntos as P  # noqa: E402

SAL, JS = "data/tenis/ajuste_separacion.md", "data/tenis/ajuste_separacion.json"
KS = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
CS = [-0.10, -0.08, -0.06, -0.04, -0.02, 0.0]
N = 3000
CACHE = {}


def grupo(nivel):
    n = str(nivel)
    if n in ("C",):
        return "challenger"
    if n in ("S", "15", "25") or n.isdigit():
        return "itf"
    return "circuito"


def dist(pw, pl, bo):
    """Media de los dos órdenes de saque: K.partido pone a A sacando primero, y como en el historial A es
    siempre el GANADOR, sin simetrizar el acierto medía en parte "quién saca primero" (salía 50,9% en ITF)."""
    k = (K.redondear(pw), K.redondear(pl), bo)
    if k not in CACHE:
        g1, t1, _ = K.partido(*k)
        g2, t2, _ = K.partido(k[1], k[0], bo)
        CACHE[k] = ((g1 + 1 - g2) / 2, {x: (t1.get(x, 0) + t2.get(x, 0)) / 2 for x in set(t1) | set(t2)})
    return CACHE[k]


def aplicar(pw, pl, k, c):
    m, d = (pw + pl) / 2, pw - pl
    return float(np.clip(m + c + k * d / 2, .3, .92)), float(np.clip(m + c - k * d / 2, .3, .92))


def medir(g, k, c):
    ll, gana, esp, bri = 0.0, [], [], {L: [] for L in (19.5, 21.5, 23.5)}
    for r in g.itertuples():
        pw, pl = aplicar(r.p_w, r.p_l, k, c)
        pg, tot = dist(pw, pl, r.bo)
        ll += np.log(max(tot.get(int(r.juegos), 0), 1e-6))
        gana.append(pg)
        esp.append(sum(x * p for x, p in tot.items()))
        for L in bri:
            bri[L].append((sum(p for x, p in tot.items() if x > L) - (r.juegos > L)) ** 2)
    gana = np.array(gana)
    return {"ll_juegos": ll / len(g), "dif_juegos": float(np.mean(esp) - g.juegos.mean()),
            "brier": {L: float(np.mean(v)) for L, v in bri.items()},
            "acierto": float((gana > .5).mean()), "logloss_ganador": float(-np.mean(np.log(np.clip(gana, 1e-6, 1))))}


def main():
    filas = []
    for circ in ("atp", "wta"):
        d, _ = P.calcular(circ, P.PARAMS[circ])
        d = d[d.inicio >= "2021-01-01"].copy()
        d["juegos"] = d.score.map(H.juegos)
        d = d.dropna(subset=["juegos", "p_w", "p_l"])
        d = d[d.best_of == 3]
        d["bo"] = 3
        d["grupo"] = d.tourney_level.map(grupo)
        d["circ"] = circ
        filas.append(d[["circ", "grupo", "inicio", "p_w", "p_l", "bo", "juegos"]])
    h = pd.concat(filas)
    res, lin = {}, ["# Separar a los jugadores: corrección del modelo de puntos (elegida en 2021-23, juzgada en 2024-26)\n",
                    "Al mejor de 3. k separa a los jugadores, c mueve el nivel de saque. Muestra de "
                    f"{N} partidos por grupo y periodo.\n",
                    "| grupo | k | c | juegos de más (antes → después) | Brier 21,5 (antes → después) | acierto ganador (antes → después) | log-loss ganador |",
                    "|---|---|---|---|---|---|---|"]
    for (circ, gr), g in h.groupby(["circ", "grupo"]):
        tr = g[g.inicio < "2024-01-01"]
        te = g[g.inicio >= "2024-01-01"]
        if len(tr) < 500 or len(te) < 500:
            continue
        tr, te = tr.sample(min(N, len(tr)), random_state=1), te.sample(min(N, len(te)), random_state=1)
        mejor = max(((k, c) for k in KS for c in CS), key=lambda kc: medir(tr, *kc)["ll_juegos"])
        a, b = medir(te, 1.0, 0.0), medir(te, *mejor)
        res[f"{circ}|{gr}"] = {"k": mejor[0], "c": mejor[1]}
        lin.append(f"| {circ.upper()} {gr} | {mejor[0]} | {mejor[1]:+.2f} | {a['dif_juegos']:+.2f} → {b['dif_juegos']:+.2f} | "
                   f"{a['brier'][21.5]:.4f} → {b['brier'][21.5]:.4f} | {a['acierto']:.1%} → {b['acierto']:.1%} | "
                   f"{a['logloss_ganador']:.4f} → {b['logloss_ganador']:.4f} |")
        print(lin[-1], flush=True)
    json.dump(res, open(JS, "w"), indent=1)
    open(SAL, "w").write("\n".join(lin) + "\n")


if __name__ == "__main__":
    main()
