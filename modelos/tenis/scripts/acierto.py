"""
Objetivo del usuario (30/09/2026): ACERTAR MÁS, no ganar al mercado. Tabla de
acierto del ganador y calidad de la probabilidad (log-loss, Brier) de cada
opción, ventana móvil (cada año 2021-2026 con capas ajustadas solo con los
anteriores). Con cuota: mercado solo, mercado recalibrado, cuota+Elo+puntos.
Sin cuota: Elo, puntos, Elo+puntos (mezcla ajustada). Por circuito y nivel.
Escribe data/tenis/acierto.md.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/tenis/scripts")
import evaluar_elo as V  # noqa: E402
import evaluar_puntos as EP  # noqa: E402
import por_nivel as PN  # noqa: E402

OPCIONES = {"mercado (cuota sin margen)": None, "mercado recalibrado": ["l_p_mkt"],
            "cuota + Elo + puntos": ["l_p_mkt", "l_p_elo", "l_p_puntos"],
            "Elo solo": "p_elo_A", "puntos solo": "p_puntos_A", "Elo + puntos (sin cuota)": ["l_p_elo", "l_p_puntos"]}


def main():
    d = EP.construir()
    a = np.random.default_rng(3).random(len(d)) < 0.5
    d["y"] = a.astype(int)
    for c in ("p_mkt", "p_puntos", "p_elo"):
        d[f"{c}_A"] = np.where(a, d[c], 1 - d[c])
        d[f"l_{c}"] = V.logit(d[f"{c}_A"])
    d["nivel"] = d["circuito"].str.upper() + " " + d["Series"].where(d["circuito"] == "atp", d.get("Tier")).map(PN.nivel)
    pred = {k: pd.Series(np.nan, index=d.index) for k in OPCIONES}
    for año in range(2021, 2027):
        tr, te = d[d["año"] < año], d[d["año"] == año]
        for k, v in OPCIONES.items():
            if v is None:
                pred[k][te.index] = te["p_mkt_A"]
            elif isinstance(v, str):
                pred[k][te.index] = te[v]
            else:
                pred[k][te.index] = LogisticRegression(C=1e6).fit(tr[v], tr["y"]).predict_proba(te[v])[:, 1]
    x = d[d["año"] >= 2021]
    y = x["y"].values
    out = ["# Acierto del ganador: qué opción acierta más (ventana móvil 2021-2026)\n",
           "Generado por `modelos/tenis/scripts/acierto.py`. Acierto = el lado con prob. > 50% gana.",
           "Log-loss y Brier: más bajo es mejor.\n",
           "| opción | acierto | log-loss | Brier |", "|---|---|---|---|"]
    for k in OPCIONES:
        p = pred[k][x.index].values
        out.append(f"| {k} | {((p > 0.5) == (y == 1)).mean():.2%} | "
                   f"{np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p))):.4f} | {np.mean((p - y) ** 2):.4f} |")
    out += ["\n## Acierto por circuito y nivel\n", "| grupo | partidos | " + " | ".join(OPCIONES) + " |",
            "|---|---|" + "---|" * len(OPCIONES)]
    for g, sub in x.groupby("nivel"):
        ys = sub["y"].values
        out.append(f"| {g} | {len(sub)} | " + " | ".join(
            f"{((pred[k][sub.index].values > 0.5) == (ys == 1)).mean():.1%}" for k in OPCIONES) + " |")
    # diferencia de acierto cuota+Elo+puntos vs mercado, emparejada
    a1 = ((pred["cuota + Elo + puntos"][x.index].values > 0.5) == (y == 1)).astype(float)
    a0 = ((pred["mercado (cuota sin margen)"][x.index].values > 0.5) == (y == 1)).astype(float)
    dd = a1 - a0
    out.append(f"\nAcierto cuota+Elo+puntos - mercado: {dd.mean():+.2%} "
               f"({dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):+.2f} sigmas; partidos donde discrepan: "
               f"{int((dd != 0).sum())}).")
    open("data/tenis/acierto.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
