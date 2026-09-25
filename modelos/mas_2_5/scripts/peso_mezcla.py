"""
Peso de la mezcla Poisson-xG / XGBoost 28 (25/09/2026). Se elige el peso en
ago 2025 - ene 2026 y se comprueba en feb - sep 2026 (no participa).
Peso = % de Poisson-xG; el resto es XGBoost 28.
"""
import numpy as np, pandas as pd
d = pd.read_csv("data/poisson_dc_xg.csv")
elige, prueba = d[d.mes < "2026-02"], d[d.mes >= "2026-02"]
sig = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def evalua(g, w):
    p = w * g.p_xg + (1 - w) * g.p_28
    b, bm = 2 * (p - g.y) ** 2, 2 * (g.p_mercado - g.y) ** 2
    vo, vu = p * g["Avg>2.5"] - 1, (1 - p) * g["Avg<2.5"] - 1
    o, u = (vo > 0) & (vo >= vu), (vu > 0) & (vu > vo)
    ret = np.r_[(g.y[o] * g["Avg>2.5"][o] - 1).values, ((1 - g.y[u]) * g["Avg<2.5"][u] - 1).values]
    return b.mean(), sig(bm - b), ret.mean() * 100, len(ret)


print(f"elegir: {len(elige)} partidos | comprobar: {len(prueba)}")
print(f"{'% Poisson':>9s} | {'Brier (elegir)':>14s} | {'vs casa (comprobar)':>19s} {'apostando (comprobar)':>22s}")
filas = []
for w in np.arange(0, 1.01, 0.1):
    be, _, _, _ = evalua(elige, w)
    bp, sp, rp, n = evalua(prueba, w)
    filas.append((w, be))
    print(f"{w*100:8.0f}% | {be:14.4f} | {sp:+18.2f}s {rp:+12.2f}% ({n} ap.)")
w_best = min(filas, key=lambda x: x[1])[0]
print(f"\nPeso elegido con la primera mitad: {w_best*100:.0f}% Poisson-xG / {(1-w_best)*100:.0f}% XGBoost")
