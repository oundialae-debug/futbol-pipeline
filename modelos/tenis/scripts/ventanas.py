"""
¿Ventana corta o todo el pasado para la capa de mezcla (cuota + Elo +
puntos)? Pregunta del usuario (30/09/2026). Las puntuaciones de jugador
(Elo, puntos) no cambian: ya olvidan solas. Solo cambia con qué años se
ajustan los 3 pesos de la mezcla.

Fijado antes de mirar: ventanas de 1, 2 y 3 años frente a "todo lo
anterior"; se juzgan 2023-2026 (años en que todas tienen sus datos). Log-loss
contra el mercado recalibrado con la MISMA ventana, y apuestas con valor > 0.
Escribe data/tenis/ventanas.md.
"""
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/tenis/scripts")
import evaluar_elo as V  # noqa: E402
import evaluar_puntos as EP  # noqa: E402

COLS = ["l_p_mkt", "l_p_elo", "l_p_puntos"]


def apuestas(te, p):
    r = []
    for (_, f), pa in zip(te.iterrows(), p):
        casa = "PS" if f["fuente_mkt"] == "Pinnacle" else "BFE"
        cw, cl = f[f"cuota_w_{casa}"], f[f"cuota_l_{casa}"]
        ca, cb = (cw, cl) if f["y"] == 1 else (cl, cw)
        va, vb = pa * ca - 1, (1 - pa) * cb - 1
        if max(va, vb) > 0:
            r.append((ca - 1 if f["y"] == 1 else -1.0) if va >= vb else (cb - 1 if f["y"] == 0 else -1.0))
    return r


def main():
    d = EP.construir()
    a = np.random.default_rng(3).random(len(d)) < 0.5
    d["y"] = a.astype(int)
    for c in ("p_mkt", "p_puntos", "p_elo"):
        d[f"l_{c}"] = V.logit(np.where(a, d[c], 1 - d[c]))
    out = ["# Ventana de ajuste de la mezcla: corta o todo el pasado\n",
           "Generado por `modelos/tenis/scripts/ventanas.py`. Juzgado 2023-2026. Log-loss: negativo = mejora",
           "al mercado recalibrado. Mezcla = cuota + Elo + puntos.\n",
           "| ventana | mezcla - mercado recalibrado (2023-2026) | por año | apuestas valor>0: n / rendimiento (sigmas) |",
           "|---|---|---|---|"]
    for nombre, anos in (("todo lo anterior", None), ("3 años", 3), ("2 años", 2), ("1 año", 1)):
        xs, rs, por = [], [], []
        for año in range(2023, 2027):
            tr = d[(d["año"] < año) & ((d["año"] >= año - anos) if anos else True)]
            te = d[d["año"] == año]
            y = te["y"].values
            base = LogisticRegression(C=1e6).fit(tr[["l_p_mkt"]], tr["y"]).predict_proba(te[["l_p_mkt"]])[:, 1]
            p = LogisticRegression(C=1e6).fit(tr[COLS], tr["y"]).predict_proba(te[COLS])[:, 1]
            ll = lambda q: -(y * np.log(q) + (1 - y) * np.log(1 - q))  # noqa: E731
            x = ll(p) - ll(base)
            xs.append(x)
            por.append(f"{año}: {x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f}")
            rs += apuestas(te, p)
        x, r = np.concatenate(xs), np.array(rs)
        out.append(f"| {nombre} | {x.mean():+.5f} ({x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f}) | "
                   f"{', '.join(por)} | {len(r)} / {r.mean():+.2%} ({r.mean() / (r.std(ddof=1) / np.sqrt(len(r))):+.2f}) |")
        print(out[-1], flush=True)
    open("data/tenis/ventanas.md", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
