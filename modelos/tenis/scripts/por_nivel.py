"""
¿Una mezcla (cuota + Elo + puntos) por circuito y nivel de torneo, o una
para todo? Pregunta del usuario (30/09/2026): son torneos distintos. Las
puntuaciones de jugador siguen usando todos los niveles (un jugador que sube
de Challenger es el mismo jugador); solo se separa la capa de mezcla.

Fijado antes de mirar: (1) una para todo, (2) una por circuito, (3) una por
circuito x nivel (Grand Slam; 1000 con Finals; 500; 250 y resto). Cada una
se ajusta con todos los años anteriores al juzgado; se juzgan 2023-2026
contra el mercado recalibrado con la MISMA partición. Apuestas valor > 0.
Escribe data/tenis/por_nivel.md.
"""
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/tenis/scripts")
import evaluar_elo as V  # noqa: E402
import evaluar_puntos as EP  # noqa: E402
import ventanas as W  # noqa: E402

COLS = ["l_p_mkt", "l_p_elo", "l_p_puntos"]


def nivel(s):
    s = str(s)
    if "Grand Slam" in s:
        return "GS"
    if any(k in s for k in ("1000", "Masters", "Mandatory", "Championships", "Finals")):
        return "1000"
    if "500" in s or s == "Premier":
        return "500"
    return "250"


def main():
    d = EP.construir()
    a = np.random.default_rng(3).random(len(d)) < 0.5
    d["y"] = a.astype(int)
    for c in ("p_mkt", "p_puntos", "p_elo"):
        d[f"l_{c}"] = V.logit(np.where(a, d[c], 1 - d[c]))
    d["nivel"] = d["Series"].where(d["circuito"] == "atp", d.get("Tier")).map(nivel)
    d["g_todo"] = "todo"
    d["g_circ"] = d["circuito"]
    d["g_nivel"] = d["circuito"] + " " + d["nivel"]
    out = ["# Mezcla por circuito y nivel de torneo, o una para todo\n",
           "Generado por `modelos/tenis/scripts/por_nivel.py`. Juzgado 2023-2026. Log-loss: negativo = mejora",
           "al mercado recalibrado (con la misma partición).\n",
           f"Partidos 2023-2026 por grupo: {d[d.año >= 2023].g_nivel.value_counts().to_dict()}\n",
           "| partición | mezcla - mercado recalibrado | apuestas valor>0: n / rendimiento (sigmas) |", "|---|---|---|"]
    detalle = ["\n## Por grupo (partición circuito x nivel)\n", "| grupo | partidos | mezcla - mercado (sigmas) | "
               "pesos medios cuota / Elo / puntos | apuestas: n / rendimiento |", "|---|---|---|---|---|"]
    for nombre, g in (("una para todo", "g_todo"), ("por circuito", "g_circ"), ("por circuito y nivel", "g_nivel")):
        xs, rs, grupos = [], [], {}
        for año in range(2023, 2027):
            for k, sub in d[d["año"] <= año].groupby(g):
                tr, te = sub[sub["año"] < año], sub[sub["año"] == año]
                if len(te) == 0 or len(tr) < 100:
                    continue
                y = te["y"].values
                base = LogisticRegression(C=1e6).fit(tr[["l_p_mkt"]], tr["y"]).predict_proba(te[["l_p_mkt"]])[:, 1]
                m = LogisticRegression(C=1e6).fit(tr[COLS], tr["y"])
                p = m.predict_proba(te[COLS])[:, 1]
                ll = lambda q: -(y * np.log(q) + (1 - y) * np.log(1 - q))  # noqa: E731
                x = ll(p) - ll(base)
                r = W.apuestas(te, p)
                xs.append(x)
                rs += r
                gg = grupos.setdefault(k, {"x": [], "r": [], "c": []})
                gg["x"].append(x)
                gg["r"] += r
                gg["c"].append(m.coef_[0])
        x, r = np.concatenate(xs), np.array(rs)
        out.append(f"| {nombre} | {x.mean():+.5f} ({x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f}) | "
                   f"{len(r)} / {r.mean():+.2%} ({r.mean() / (r.std(ddof=1) / np.sqrt(len(r))):+.2f}) |")
        if g == "g_nivel":
            for k, gg in sorted(grupos.items()):
                x, r, c = np.concatenate(gg["x"]), np.array(gg["r"]), np.mean(gg["c"], axis=0)
                detalle.append(f"| {k} | {len(x)} | {x.mean():+.5f} ({x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f}) | "
                               f"{c[0]:+.2f} / {c[1]:+.2f} / {c[2]:+.2f} | {len(r)} / {r.mean():+.2%} |")
    open("data/tenis/por_nivel.md", "w").write("\n".join(out + detalle) + "\n")
    print("\n".join(out + detalle))


if __name__ == "__main__":
    main()
