"""
Segunda auditoría externa, puntos 1-3 (29/09/2026), reproducidos con XGBoost real.

La auditoría (con un modelo scikit-learn) dijo: (1) el precio solo supera al
modelo de 102 variables (+3.0s, 16/23 meses); (2) partir del precio y añadir
árboles de fútbol no mejora al precio; (3) ampliar el modelo de precio con más
de 2.5, empate y lambdas mejora (+1.55s) y la liga no aporta.

Mes a mes sep-2024..sep-2026, cada mes entrenado solo con lo anterior, en los
partidos con precio previo (los mismos para todos):
  A      oficial (XGBoost, 102 variables, semillas 0-4)
  A2     oficial con semillas 10-14 (ruido de entrenamiento)
  B      logística sobre logit(mkt_p_btts_implicito)
  C      logística sobre logit(btts impl.), logit(más 2.5), logit(empate), lambda_l, lambda_v
  C_liga C + liga (one-hot)
  D      XGBoost solo con las 7 variables de precio (semillas 0-4)
  E120/E300  base = logit de B; árboles SOLO con variables de fútbol (120/300)

Reglas FIJADAS ANTES: punto 1 se confirma si B o C superan a A en >= +2s en
Brier Y log loss y por encima de |A2 vs A|; punto 2 si ninguna E supera a B
en +2s; punto 3 si C supera a B en >= +2s (C_liga vs C mide la liga). Unas 6
comparaciones: un sí por debajo de ~+2.4s se marca como dudoso. Contra el
ambos marcan REAL en los partidos con cuota cosechada. No cambia el oficial.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import modelo_ambos_marcan as A

EPS = 1e-4
Y = A.OBJETIVO


def logit(p):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def brier(p, y):
    return (np.asarray(p) - y) ** 2


def ll(p, y):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def sig(d):
    d = np.asarray(d, float)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def x_precio(d, liga=None):
    X = np.c_[logit(d.mkt_p_btts_implicito), logit(d.mkt_p_mas_2_5), logit(d.mkt_p_empate),
              d.mkt_lambda_l, d.mkt_lambda_v]
    if liga is not None:
        X = np.c_[X, (d.liga_id.values[:, None] == np.array(liga)[None, :]).astype(float)]
    return X


def xgb(semilla, n=400):
    p = dict(A.PARAMS)
    p["n_estimators"] = n
    return XGBClassifier(objective="binary:logistic", random_state=semilla, n_jobs=2,
                         eval_metric="logloss", tree_method="hist", **p)


def main():
    bt, cols = A.preparar()
    mkt = list(A.MKT)
    fund = [c for c in cols if c not in mkt]
    ligas = sorted(bt.liga_id.dropna().unique())
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    tiene = bt[mkt].notna().all(axis=1)
    out = []
    for m in meses:
        pas, hoy = bt[bt.mes < m], bt[(bt.mes == m) & tiene].copy()
        if hoy.empty:
            continue
        ya, yp = pas[Y].values.astype(int), None
        pp = pas[tiene.loc[pas.index]]
        yp = pp[Y].values.astype(int)
        r = hoy[["match_id", "mes", "liga_id", Y]].copy()
        r["A"] = np.mean([xgb(s).fit(pas[cols].values, ya).predict_proba(hoy[cols].values)[:, 1]
                          for s in (0, 1, 2, 3, 4)], axis=0)
        r["A2"] = np.mean([xgb(s).fit(pas[cols].values, ya).predict_proba(hoy[cols].values)[:, 1]
                           for s in (10, 11, 12, 13, 14)], axis=0)
        lb = LogisticRegression(C=1e6).fit(logit(pp.mkt_p_btts_implicito).reshape(-1, 1), yp)
        r["B"] = lb.predict_proba(logit(hoy.mkt_p_btts_implicito).reshape(-1, 1))[:, 1]
        r["C"] = make_pipeline(StandardScaler(), LogisticRegression(C=1e6)).fit(
            x_precio(pp), yp).predict_proba(x_precio(hoy))[:, 1]
        r["C_liga"] = make_pipeline(StandardScaler(), LogisticRegression(C=1e6)).fit(
            x_precio(pp, ligas), yp).predict_proba(x_precio(hoy, ligas))[:, 1]
        r["D"] = np.mean([xgb(s).fit(pas[mkt].values, ya).predict_proba(hoy[mkt].values)[:, 1]
                          for s in (0, 1, 2, 3, 4)], axis=0)
        base_tr = logit(lb.predict_proba(logit(pp.mkt_p_btts_implicito).reshape(-1, 1))[:, 1])
        base_te = logit(r["B"].values)
        for n in (120, 300):
            r[f"E{n}"] = np.mean([xgb(s, n).fit(pp[fund].values, yp, base_margin=base_tr)
                                  .predict_proba(hoy[fund].values, base_margin=base_te)[:, 1]
                                  for s in (0, 1, 2, 3, 4)], axis=0)
        out.append(r)
        print(f"  {m}: {len(r)} partidos", flush=True)
    t = pd.concat(out).reset_index(drop=True)
    t.to_csv("data/auditoria2_precio.csv", index=False)
    y = t[Y].values
    brazos = ["A", "A2", "B", "C", "C_liga", "D", "E120", "E300"]
    print(f"\n{len(t)} partidos, {t.mes.nunique()} meses ({t.mes.min()}..{t.mes.max()})\n")
    print(f"{'brazo':8s} {'Brier':>7s} {'logloss':>8s}")
    for b in brazos:
        print(f"{b:8s} {brier(t[b], y).mean():7.4f} {ll(t[b], y).mean():8.4f}")

    def comp(nuevo, ref, texto):
        db, dl = brier(t[ref], y) - brier(t[nuevo], y), ll(t[ref], y) - ll(t[nuevo], y)
        mes = sum(brier(g[ref], g[Y]).mean() > brier(g[nuevo], g[Y]).mean() for _, g in t.groupby("mes"))
        print(f"{texto:44s} Brier {sig(db):+.2f}s  log loss {sig(dl):+.2f}s  mejor en {mes}/{t.mes.nunique()} meses")
    print()
    comp("A2", "A", "ruido: A (semillas 10-14) vs A (0-4)")
    comp("B", "A", "P1: solo precio (B) vs oficial (A)")
    comp("C", "A", "P1: precio ampliado (C) vs oficial (A)")
    comp("D", "A", "XGBoost solo precio (D) vs oficial (A)")
    comp("E120", "B", "P2: residual 120 árboles vs solo precio (B)")
    comp("E300", "B", "P2: residual 300 árboles vs solo precio (B)")
    comp("C", "B", "P3: precio ampliado (C) vs solo precio (B)")
    comp("C_liga", "C", "P3: C + liga vs C")
    print("\nCalibración (lado elegido: dice / pasa / n):")
    for b in ("A", "B", "C"):
        p = t[b].values
        lado = np.where(p >= .5, p, 1 - p)
        g = np.where(p >= .5, y == 1, y == 0)
        tr = []
        for a, c in ((.5, .55), (.55, .6), (.6, .65), (.65, 1.01)):
            k = (lado >= a) & (lado < c)
            if k.sum():
                tr.append(f"{a:.0%}+: {lado[k].mean():.1%}/{g[k].mean():.1%}/{k.sum()}")
        print(f"  {b}: " + "  ".join(tr))
    import evaluar_mercados as EM
    c = EM.cargar_cuotas_crudas()
    b = c[c.familia == "Both Teams To Score"]
    piv = b.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
    piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
    piv["p"] = (1 / piv.yes) / (1 / piv.yes + 1 / piv.no)
    v = t.merge(piv.groupby("match_id").p.median().rename("real"), left_on="match_id", right_index=True)
    yv = v[Y].values
    print(f"\nContra el ambos marcan REAL ({len(v)} partidos con cuota cosechada; + = mejor que el mercado):")
    for b in brazos:
        print(f"  {b:8s} Brier {sig(brier(v.real, yv) - brier(v[b], yv)):+.2f}s  "
              f"log loss {sig(ll(v.real, yv) - ll(v[b], yv)):+.2f}s")


if __name__ == "__main__":
    main()
