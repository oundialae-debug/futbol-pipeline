"""
Revisión a fondo, antes de confirmarlo: árboles de 1 nivel contra 2 en ambos
marcan (petición del usuario, 29/09/2026: "que salga mejor pero apostando no
me gusta").

Fijado antes de mirar:
  1. Los 21 meses (sep-2024..sep-2026), los dos modelos, con DOS juegos de
     semillas (0-4 y 10-14): ¿la mejora aguanta o es azar del entrenamiento?
  2. Por liga y por temporada: ¿sale de un solo sitio?
  3. Mercado y apuestas en los partidos con cuota real de ambos marcan:
     Brier contra el mercado, apuestas con VE>0 y VE>2% (cuota mediana), y la
     diferencia de beneficio entre los dos modelos con remuestreo por partido
     (2.000 veces): ¿es real o suerte?
  4. Calibración de los dos.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
import modelo_ambos_marcan as A
import evaluar_mercados as EM

BASE = dict(n_estimators=400, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
            min_child_weight=20, reg_lambda=5.0)
MODELOS = {"1 nivel": dict(BASE, max_depth=1), "2 niveles": dict(BASE, max_depth=2)}
SEMILLAS = {"semillas 0-4": (0, 1, 2, 3, 4), "semillas 10-14": (10, 11, 12, 13, 14)}


def predecir(bt, cols, mes, params, semillas):
    pasado, test = bt[bt.mes < mes], bt[bt.mes == mes]
    y = pasado[A.OBJETIVO].values.astype(int)
    p = np.mean([XGBClassifier(objective="binary:logistic", random_state=s, n_jobs=2, eval_metric="logloss",
                               tree_method="hist", **params).fit(pasado[cols].values, y)
                 .predict_proba(test[cols].values)[:, 1] for s in semillas], axis=0)
    return p


def sig(d):
    d = np.asarray(d, float)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def main():
    bt, cols = A.preparar()
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    h = pd.read_csv("data/historico_partidos.csv", usecols=["match_id", "liga", "temporada"])
    t = bt[bt.mes.isin(meses)][["match_id", "mes", A.OBJETIVO]].merge(h, on="match_id", how="left")
    for ns, sem in SEMILLAS.items():
        for nm, par in MODELOS.items():
            t[f"{nm}|{ns}"] = np.concatenate([predecir(bt, cols, m, par, sem) for m in meses])
            print(f"  hecho {nm}, {ns}", flush=True)
    t.to_csv("data/revision_profundidad.csv", index=False)
    y = t[A.OBJETIVO].values
    br = lambda c: (t[c].values - y) ** 2
    print(f"\n1. 21 meses, {len(t)} partidos: 1 nivel contra 2 niveles")
    for ns in SEMILLAS:
        d = br(f"2 niveles|{ns}") - br(f"1 nivel|{ns}")
        pos = sum((br(f"2 niveles|{ns}")[t.mes == m].mean() > br(f"1 nivel|{ns}")[t.mes == m].mean()) for m in meses)
        print(f"   {ns}: {sig(d):+.2f}s, mejor en {pos}/{len(meses)} meses")
    d2 = br("2 niveles|semillas 10-14") - br("2 niveles|semillas 0-4")
    print(f"   ruido de proceso (2 niveles, semillas 0-4 contra 10-14): {sig(d2):+.2f}s")
    # promedio de los dos juegos de semillas para lo demás
    for nm in MODELOS:
        t[nm] = t[[f"{nm}|{ns}" for ns in SEMILLAS]].mean(axis=1)
    d = br("2 niveles") - br("1 nivel")
    print("\n2. Por liga y por temporada (1 nivel contra 2; positivo = mejor 1 nivel)")
    for col in ("liga", "temporada"):
        for k, g in t.assign(d=d).groupby(col):
            print(f"   {str(k):16s} n={len(g):5d}  {sig(g.d):+.2f}s")
    # 3. mercado y apuestas
    c = EM.cargar_cuotas_crudas()
    b = c[c.familia == "Both Teams To Score"]
    piv = b.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
    piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
    piv["pm"] = (1 / piv.yes) / (1 / piv.yes + 1 / piv.no)
    med = piv.groupby("match_id").agg(pm=("pm", "median"), yes=("yes", "median"), no=("no", "median"))
    v = t.merge(med, left_on="match_id", right_index=True)
    yv = v[A.OBJETIVO].values
    print(f"\n3. Partidos con cuota real de ambos marcan: {len(v)}")
    ben = {}
    for nm in MODELOS:
        p = v[nm].values
        print(f"   {nm}: contra el mercado {sig((v.pm.values - yv) ** 2 - (p - yv) ** 2):+.2f}s")
        vs, vn = p * v.yes - 1, (1 - p) * v.no - 1
        si = vs >= vn
        ve = np.where(si, vs, vn)
        gana = np.where(si, yv == 1, yv == 0)
        res = np.where(gana, np.where(si, v.yes, v.no) - 1, -1.0)
        for u in (0.0, 0.02):
            m = ve > u
            print(f"      VE>{u:.0%}: {m.sum()} apuestas, acierto {gana[m].mean():.1%}, beneficio {res[m].mean():+.1%} "
                  f"({sig(res[m]):+.2f}s)")
        ben[nm] = np.where(ve > 0, res, 0.0)       # beneficio por partido (0 si no apuesta)
    dif = ben["1 nivel"] - ben["2 niveles"]
    rng = np.random.default_rng(0)
    bs = [dif[rng.integers(0, len(dif), len(dif))].sum() for _ in range(2000)]
    print(f"   diferencia de beneficio total (1 nivel - 2 niveles, VE>0): {dif.sum():+.1f} unidades; "
          f"intervalo 95% [{np.percentile(bs, 2.5):+.1f}, {np.percentile(bs, 97.5):+.1f}]; "
          f"1 nivel peor en el {np.mean(np.array(bs) < 0):.0%} de los remuestreos")
    solo = (ben["1 nivel"] != 0) != (ben["2 niveles"] != 0)
    print(f"   partidos donde solo apuesta uno de los dos: {solo.sum()}")
    print("\n4. Calibración (21 meses)")
    for nm in MODELOS:
        p = t[nm].values
        lado = np.where(p >= .5, p, 1 - p)
        gana = np.where(p >= .5, y == 1, y == 0)
        tr = "  ".join(f"{a:.0%}-{b:.0%}: dice {lado[(lado >= a) & (lado < b)].mean():.1%} pasa "
                       f"{gana[(lado >= a) & (lado < b)].mean():.1%} (n={((lado >= a) & (lado < b)).sum()})"
                       for a, b in ((.5, .55), (.55, .6), (.6, .65), (.65, 1.01)) if ((lado >= a) & (lado < b)).sum())
        print(f"   {nm}: {tr}")


if __name__ == "__main__":
    main()
