"""
¿Necesita la liga pesar más en ambos marcan? (pregunta del usuario, 29/09/2026,
tras ver que el modelo de 1 nivel empeoraba en LaLiga y apostando).

Barato, sobre las predicciones ya guardadas del oficial (2 niveles, media de
10 semillas, data/revision_profundidad.csv). Fijado antes: cada mes, para cada
liga, un ajuste con SOLO los meses anteriores de esa liga (al menos 6):
  A  desplazamiento: logit(p) + b_liga        (la liga sube o baja el nivel)
  B  Platt por liga: a_liga * logit(p) + b_liga (además, cuánto fiarse en esa liga)
Contra el oficial sin tocar, Brier emparejado, y por liga. 2 intentos: ~+2.2s.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

EPS, MIN_MESES = 1e-4, 6


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def main():
    t = pd.read_csv("data/revision_profundidad.csv")
    t["p"] = t[["2 niveles|semillas 0-4", "2 niveles|semillas 10-14"]].mean(axis=1)
    meses = sorted(t.mes.unique())
    out = []
    for i, m in enumerate(meses):
        if i < MIN_MESES:
            continue
        for liga, hoy in t[t.mes == m].groupby("liga"):
            pas = t[(t.mes < m) & (t.liga == liga)]
            x, y = logit(pas.p.values), pas.ambos_marcan.values
            xh = logit(hoy.p.values)
            # A: solo desplazamiento (pendiente fija en 1): regresión con offset vía ajuste de b
            bs = np.linspace(-1, 1, 401)
            ll = [-(y * np.log(1 / (1 + np.exp(-(x + bb)))) + (1 - y) * np.log(1 - 1 / (1 + np.exp(-(x + bb))))).mean() for bb in bs]
            bA = bs[int(np.argmin(ll))]
            pl = LogisticRegression(C=1e6).fit(x.reshape(-1, 1), y)
            out.append(hoy.assign(pA=1 / (1 + np.exp(-(xh + bA))),
                                  pB=pl.predict_proba(xh.reshape(-1, 1))[:, 1], bA=bA))
    r = pd.concat(out)
    y = r.ambos_marcan.values
    b0 = (r.p - y) ** 2
    print(f"{len(r)} partidos, {r.mes.min()}..{r.mes.max()}")
    for c, n in (("pA", "A desplazamiento por liga"), ("pB", "B Platt por liga")):
        d = b0 - (r[c] - y) ** 2
        print(f"{n:28s} {sig(d):+.2f}s  (Brier {((r[c]-y)**2).mean():.4f} vs {b0.mean():.4f})")
        print("   por liga: " + "  ".join(f"{l} {sig(g):+.2f}" for l, g in pd.Series(d.values, index=r.liga.values).groupby(level=0)))
    print("\nDesplazamiento medio aprendido por liga (logit; + = el oficial se queda corto en ambos marcan):")
    print("   " + "  ".join(f"{l} {v:+.3f}" for l, v in r.groupby("liga").bA.mean().items()))
    r.to_csv("data/ajuste_por_liga.csv", index=False)


if __name__ == "__main__":
    main()
