"""
Cuota + Elo + modelo de puntos juntos (30/09/2026, pregunta del usuario: "en
fútbol metíamos la cuota como variable"). Ventana móvil: cada año 2021-2026
con una logística ajustada solo con los años anteriores. Comparador: el
mercado recalibrado (logística solo con la cuota, misma ventana). Apuestas
de la mezcla al lado con valor > 0 a la cuota de cierre de la referencia.
Escribe data/tenis/mezcla_tres.md.
"""
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/tenis/scripts")
import evaluar_elo as V  # noqa: E402
import evaluar_puntos as EP  # noqa: E402


def main():
    d = EP.construir()
    a = np.random.default_rng(3).random(len(d)) < 0.5
    d["y"] = a.astype(int)
    for c in ("p_mkt", "p_puntos", "p_elo"):
        d[f"l_{c}"] = V.logit(np.where(a, d[c], 1 - d[c]))
    out = ["# Cuota + Elo + modelo de puntos (ventana móvil)\n",
           "Generado por `modelos/tenis/scripts/mezcla_tres.py`. Log-loss: negativo = mejora al mercado recalibrado.\n",
           "| año | partidos | mezcla - mercado recalibrado | pesos cuota / Elo / puntos | apuestas valor>0: n / rendimiento |",
           "|---|---|---|---|---|"]
    todas, rets = [], []
    cols = ["l_p_mkt", "l_p_elo", "l_p_puntos"]
    for año in range(2021, 2027):
        tr, te = d[d["año"] < año], d[d["año"] == año]
        y = te["y"].values
        base = LogisticRegression(C=1e6).fit(tr[["l_p_mkt"]], tr["y"]).predict_proba(te[["l_p_mkt"]])[:, 1]
        m = LogisticRegression(C=1e6).fit(tr[cols], tr["y"])
        p = m.predict_proba(te[cols])[:, 1]
        ll = lambda q: -(y * np.log(q) + (1 - y) * np.log(1 - q))  # noqa: E731
        x = ll(p) - ll(base)
        todas.append(x)
        # apuestas: lado A = el que ganó si a; cuotas de la referencia de cada partido
        r = []
        for (_, f), pa in zip(te.iterrows(), p):
            casa = "PS" if f["fuente_mkt"] == "Pinnacle" else "BFE"
            cw, cl = f[f"cuota_w_{casa}"], f[f"cuota_l_{casa}"]
            ca, cb = (cw, cl) if f["y"] == 1 else (cl, cw)
            va, vb = pa * ca - 1, (1 - pa) * cb - 1
            if max(va, vb) > 0:
                r.append((ca - 1 if f["y"] == 1 else -1.0) if va >= vb else (cb - 1 if f["y"] == 0 else -1.0))
        rets += r
        out.append(f"| {año} | {len(te)} | {x.mean():+.4f} ({x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f}) | "
                   f"{m.coef_[0][0]:+.2f} / {m.coef_[0][1]:+.2f} / {m.coef_[0][2]:+.2f} | {len(r)} / {np.mean(r):+.2%} |")
    x, r = np.concatenate(todas), np.array(rets)
    out.append(f"| **2021-2026** | {len(x)} | {x.mean():+.4f} ({x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f}) | | "
               f"{len(r)} / {r.mean():+.2%} ({r.mean() / (r.std(ddof=1) / np.sqrt(len(r))):+.2f} sigmas) |")
    open("data/tenis/mezcla_tres.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
