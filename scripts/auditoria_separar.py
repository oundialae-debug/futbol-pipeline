"""
Auditoría externa, punto 1 (29/09/2026): separar modelo futbolístico y mercado.

El modelo oficial mete el precio dentro (7 variables mkt_). No se sabía cuánto
aporta el fútbol por su cuenta en ambos marcan. Fijado ANTES de mirar:

  P_fund  el modelo oficial SIN las 7 variables de precio (solo fútbol)
  P_mkt   el ambos marcan implícito del precio previo (Poisson sobre 1X2 y
          más/menos 2.5, football-data), recalibrado cada mes con los
          meses anteriores (sin recalibrar sale sesgado: -1.97s ya medido)
  P_full  el modelo oficial tal cual
  P_mezcla  logística sobre logit(P_fund) y logit(P_mkt), ajustada cada mes
          SOLO con los meses anteriores (al menos 6). Su peso del fútbol es
          la respuesta: si sale ~0, el fútbol no añade nada al precio.

Mes a mes sep-2024 a sep-2026, 5 semillas. Brier y log loss, sigma emparejado.
Aparte, los 262 partidos con cuota REAL de ambos marcan (Highlightly).
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import modelo_ambos_marcan as A

EPS, MIN_MESES = 1e-4, 6


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sig(d):
    d = np.asarray(d, float)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def brier(p, y):
    return (p - y) ** 2


def ll(p, y):
    p = np.clip(p, EPS, 1 - EPS)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def mercado_real():
    import evaluar_mercados as EM
    c = EM.cargar_cuotas_crudas()
    b = c[c.familia == "Both Teams To Score"]
    piv = b.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
    piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
    piv["p"] = (1 / piv.yes) / (1 / piv.yes + 1 / piv.no)
    return piv.groupby("match_id").p.median().rename("p_real")


def main():
    bt, cols = A.preparar()
    fund = [c for c in cols if c not in A.MKT]
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    filas = []
    for m in meses:
        a = A.predecir_mes(bt, cols, m)[["match_id", "mes", A.OBJETIVO, "p_ambos", "mkt_p_btts_implicito"]]
        f = A.predecir_mes(bt, fund, m)[["match_id", "p_ambos"]].rename(columns={"p_ambos": "p_fund"})
        filas.append(a.rename(columns={"p_ambos": "p_full", "mkt_p_btts_implicito": "p_mkt_crudo"}).merge(f, on="match_id"))
        print(f"  {m} hecho", flush=True)
    t = pd.concat(filas).reset_index(drop=True)
    t = t[t.p_mkt_crudo.notna()].reset_index(drop=True)
    y_all = t[A.OBJETIVO].values
    # mezcla y mercado recalibrado, mes a mes solo con el pasado
    out, pesos = [], []
    for i, m in enumerate(meses):
        if i < MIN_MESES:
            continue
        pas, hoy = t[t.mes < m], t[t.mes == m].copy()
        if hoy.empty:
            continue
        y = pas[A.OBJETIVO].values
        Xp = np.c_[logit(pas.p_fund), logit(pas.p_mkt_crudo)]
        mez = LogisticRegression(C=1e6).fit(Xp, y)
        cal = LogisticRegression(C=1e6).fit(logit(pas.p_mkt_crudo.values).reshape(-1, 1), y)
        hoy["p_mezcla"] = mez.predict_proba(np.c_[logit(hoy.p_fund), logit(hoy.p_mkt_crudo)])[:, 1]
        hoy["p_mkt"] = cal.predict_proba(logit(hoy.p_mkt_crudo.values).reshape(-1, 1))[:, 1]
        pesos.append((m, mez.coef_[0][0], mez.coef_[0][1]))
        out.append(hoy)
    r = pd.concat(out).reset_index(drop=True)
    y = r[A.OBJETIVO].values
    print(f"\n{len(r)} partidos con precio previo, {r.mes.min()}..{r.mes.max()}\n")
    print(f"{'probabilidad':22s} {'Brier':>7s} {'log loss':>9s}   vs P_full (Brier / log loss)")
    for c, n in (("p_full", "P_full (oficial)"), ("p_fund", "P_fund (solo fútbol)"),
                 ("p_mkt", "P_mkt (solo precio)"), ("p_mezcla", "P_mezcla")):
        extra = "" if c == "p_full" else (f"   {sig(brier(r.p_full, y) - brier(r[c], y)):+.2f}s / "
                                          f"{sig(ll(r.p_full, y) - ll(r[c], y)):+.2f}s")
        print(f"{n:22s} {brier(r[c], y).mean():7.4f} {ll(r[c], y).mean():9.4f}{extra}")
    print(f"\nP_mezcla vs P_mkt: {sig(brier(r.p_mkt, y) - brier(r.p_mezcla, y)):+.2f}s (¿añade algo el fútbol al precio?)")
    print(f"P_full  vs P_mkt: {sig(brier(r.p_mkt, y) - brier(r.p_full, y)):+.2f}s")
    w = pd.DataFrame(pesos, columns=["mes", "peso_futbol", "peso_precio"])
    print("\nPeso aprendido cada mes (coeficiente sobre el logit; 1 = se fía entero, 0 = lo ignora):")
    print(w.round(2).to_string(index=False))
    # remuestreo del último ajuste: ¿el peso del fútbol puede ser cero?
    pas = t[t.mes < meses[-1]]
    rng = np.random.default_rng(0)
    bs = []
    for _ in range(300):
        s = pas.sample(len(pas), replace=True, random_state=int(rng.integers(1e9)))
        bs.append(LogisticRegression(C=1e6).fit(np.c_[logit(s.p_fund), logit(s.p_mkt_crudo)], s[A.OBJETIVO]).coef_[0][0])
    bs = np.array(bs)
    print(f"\nPeso del fútbol (ajuste final, {len(pas)} partidos): {np.mean(bs):.2f}, intervalo 95% "
          f"[{np.percentile(bs, 2.5):.2f}, {np.percentile(bs, 97.5):.2f}], <= 0 en el {np.mean(bs <= 0):.0%} de los remuestreos")
    # contra el mercado REAL de ambos marcan
    v = r.merge(mercado_real(), left_on="match_id", right_index=True)
    yv = v[A.OBJETIVO].values
    print(f"\nContra el ambos marcan REAL (Highlightly, {len(v)} partidos):")
    for c, n in (("p_full", "P_full"), ("p_fund", "P_fund"), ("p_mkt", "P_mkt"), ("p_mezcla", "P_mezcla")):
        print(f"  {n:9s} Brier {sig(brier(v.p_real, yv) - brier(v[c], yv)):+.2f}s   log loss {sig(ll(v.p_real, yv) - ll(v[c], yv)):+.2f}s")
    r.to_csv("data/auditoria_separar.csv", index=False)


if __name__ == "__main__":
    main()
