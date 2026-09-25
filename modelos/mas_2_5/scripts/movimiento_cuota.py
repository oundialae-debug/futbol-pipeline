"""
Movimiento de la cuota de Más/Menos 2.5 (25/09/2026). Sin modelo, solo
football-data: foto "previa" (días antes) y "cierre" (C).

Pregunta: ¿el movimiento previa -> cierre predice el resultado MÁS ALLÁ de
la cuota de cierre? Si sí, al cierre se podría apostar en la dirección del
movimiento (o contra ella, si el mercado se pasa). Utilizable de verdad: al
cierre ya se sabe cómo se ha movido.

1. Control de datos: el cierre debe predecir mejor que la previa.
2. Regresión logística y ~ logit(p_cierre) + movimiento, por temporada.
3. Apuesta al cierre en la dirección del movimiento, con cuota media de
   cierre (AvgC) y máxima (MaxC, optimista), por temporada.
Se hace con la media de casas (más cobertura) y con Pinnacle.
"""
import glob
import numpy as np, pandas as pd

DIV = {"E0": "Premier", "SP1": "La Liga", "SP2": "Segunda", "I1": "Serie A", "D1": "Bundesliga", "F1": "Ligue 1"}
filas = []
for f in sorted(glob.glob("data/football_data/*.csv")):
    d = pd.read_csv(f, encoding="utf-8-sig", on_bad_lines="skip").dropna(subset=["FTHG", "FTAG"])
    div, t = f.split("/")[-1][:-4].split("_")
    d = d.assign(liga=DIV[div], temporada=f"20{t[:2]}/{t[2:]}")
    filas.append(d.copy())
d = pd.concat(filas, ignore_index=True).copy()
d["y"] = (d.FTHG + d.FTAG > 2.5).astype(int)
justa = lambda o, u: (1 / o) / (1 / o + 1 / u)
logit = lambda p: np.log(p / (1 - p))


def logistica(X, y, iters=50):
    """Regresión logística por Newton; devuelve coeficientes y z (coef/error)."""
    X = np.column_stack([np.ones(len(X)), X])
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b))
        H = X.T @ (X * (p * (1 - p))[:, None])
        b += np.linalg.solve(H, X.T @ (y - p))
    return b, b / np.sqrt(np.diag(np.linalg.inv(H)))


def sig(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


for fuente, pre, cie in (("MEDIA DE CASAS", "Avg", "AvgC"), ("PINNACLE", "P", "PC")):
    g0 = d.dropna(subset=[f"{pre}>2.5", f"{pre}<2.5", f"{cie}>2.5", f"{cie}<2.5"]).copy()
    g0["p_pre"] = justa(g0[f"{pre}>2.5"], g0[f"{pre}<2.5"])
    g0["p_cie"] = justa(g0[f"{cie}>2.5"], g0[f"{cie}<2.5"])
    g0["mov"] = g0.p_cie - g0.p_pre
    malas = ~(g0.p_pre.between(0.02, 0.98) & g0.p_cie.between(0.02, 0.98))
    g0 = g0[~malas]                      # cuotas absurdas en la fuente (p.ej. 1.0)
    print(f"=== {fuente}: {malas.sum()} filas con cuotas imposibles descartadas ===")
    print(f"=== {fuente}: {len(g0)} partidos ===")
    for temp in sorted(g0.temporada.unique()) + ["todas"]:
        g = g0 if temp == "todas" else g0[g0.temporada == temp]
        if len(g) < 200:
            print(f"  {temp}: {len(g)} partidos, pocos"); continue
        bp, bc = 2 * (g.p_pre - g.y) ** 2, 2 * (g.p_cie - g.y) ** 2
        coef, z = logistica(np.column_stack([logit(g.p_cie), g.mov * 10]), g.y.values.astype(float))
        print(f"  {temp:8s} n={len(g):4d}  mov. medio {g.mov.abs().mean()*100:.1f} pts | cierre mejor que previa "
              f"{sig(bp - bc):+.2f}s | efecto del movimiento {coef[2]:+.3f} (z={z[2]:+.2f})")
    print()

# 3. apostar al cierre en la dirección del movimiento (media de casas como señal)
g0 = d.dropna(subset=["Avg>2.5", "Avg<2.5", "AvgC>2.5", "AvgC<2.5", "MaxC>2.5", "MaxC<2.5"]).copy()
g0["mov"] = justa(g0["AvgC>2.5"], g0["AvgC<2.5"]) - justa(g0["Avg>2.5"], g0["Avg<2.5"])
print("=== Apuesta al CIERRE en la dirección del movimiento (señal: media de casas) ===")
print(f"{'cuota':6s} {'mov. mín':>8s} {'temporada':>9s} {'apuestas':>8s} {'rentab.':>8s} {'±':>6s} {'sigmas':>7s}")
for cuota in ("AvgC", "MaxC"):
    for umbral in (0.01, 0.03, 0.05):
        for temp in sorted(g0.temporada.unique()) + ["todas"]:
            g = g0 if temp == "todas" else g0[g0.temporada == temp]
            over, under = g.mov > umbral, g.mov < -umbral
            ret = np.concatenate([(g.y[over] * g[f"{cuota}>2.5"][over] - 1).values,
                                  ((1 - g.y[under]) * g[f"{cuota}<2.5"][under] - 1).values])
            if len(ret) < 30:
                print(f"{cuota:6s} {umbral*100:7.0f}p {temp:>9s} {len(ret):8d}  (pocas)"); continue
            print(f"{cuota:6s} {umbral*100:7.0f}p {temp:>9s} {len(ret):8d} {ret.mean()*100:+7.2f}% "
                  f"{ret.std(ddof=1)/np.sqrt(len(ret))*100:5.2f} {sig(ret):+6.2f}s")
        print()
