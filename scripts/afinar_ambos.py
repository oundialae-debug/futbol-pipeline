"""
Ajuste interno (hiperparámetros) del modelo oficial de ambos marcan (29/09/2026).

Por qué ahora: los valores actuales (max_depth=2, min_child_weight=20,
reg_lambda=5) se eligieron el 21-24/09 con ~1.700 partidos de entrenamiento.
Hoy entrena con ~9.000 (2022/23 a hoy). El CLAUDE.md ya dejó escrito que más
partidos podrían justificar menos regularización.

Protocolo FIJADO ANTES, para no engañarse con muchas combinaciones:
  1. Selección: rejilla de 12 combinaciones (max_depth 2/3/4 x
     min_child_weight 5/20 x reg_lambda 1/5), mes a mes de sep-2024 a
     ago-2025, 2 semillas. Gana la de menor Brier.
  2. Confirmación: la ganadora contra los valores actuales en sep-2025 a
     sep-2026, meses que la selección NO ha mirado, 5 semillas. Un solo
     intento: listón +2s.
Si la ganadora es la actual, no hay nada que confirmar.
"""
import os
import sys
import itertools
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
import modelo_ambos_marcan as A

ACTUAL = dict(max_depth=2, min_child_weight=20, reg_lambda=5.0)
REJILLA = [dict(max_depth=d, min_child_weight=w, reg_lambda=l)
           for d, w, l in itertools.product((2, 3, 4), (5, 20), (1.0, 5.0))]
# Ronda 2 (29/09): la ronda 1 dio ganadora a la actual, en el BORDE de la
# rejilla (lo más simple). Se mira más allá, hacia modelos aún más simples.
# Misma selección y misma confirmación (esta sigue sin mirarse).
if os.environ.get("RONDA") == "2":
    REJILLA = [dict(max_depth=d, min_child_weight=w, reg_lambda=l)
               for d, w, l in itertools.product((1, 2), (20, 50), (5.0, 20.0))]


def entrenar(X, y, semilla, p):
    return XGBClassifier(n_estimators=400, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
                         objective="binary:logistic", random_state=semilla, n_jobs=2,
                         eval_metric="logloss", tree_method="hist", **p).fit(X, y)


def predecir(bt, cols, mes, p, semillas):
    pasado, test = bt[bt.mes < mes], bt[bt.mes == mes]
    y = pasado[A.OBJETIVO].values.astype(int)
    pr = np.mean([entrenar(pasado[cols].values, y, s, p).predict_proba(test[cols].values)[:, 1]
                  for s in semillas], axis=0)
    return test[["match_id", "mes", A.OBJETIVO]].assign(p=pr)


def correr(bt, cols, meses, p, semillas):
    return pd.concat([predecir(bt, cols, m, p, semillas) for m in meses])


def nombre(p):
    return f"prof {p['max_depth']}, hoja {p['min_child_weight']}, lambda {p['reg_lambda']:g}"


def main():
    bt, cols = A.preparar()
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    sel = [m for m in meses if m <= "2025-08"]
    conf = [m for m in meses if m >= "2025-09"]
    print(f"Selección: {sel[0]}..{sel[-1]} ({len(sel)} meses). Confirmación: {conf[0]}..{conf[-1]} ({len(conf)} meses)\n")
    filas = []
    for p in REJILLA:
        r = correr(bt, cols, sel, p, (0, 1))
        brier = ((r.p - r[A.OBJETIVO]) ** 2).mean()
        filas.append({**p, "brier": brier})
        print(f"  {nombre(p):32s} Brier {brier:.5f}{'   <- actual' if p == ACTUAL else ''}", flush=True)
    t = pd.DataFrame(filas).sort_values("brier")
    t.to_csv(f"data/afinar_ambos_seleccion{'_r2' if os.environ.get('RONDA') == '2' else ''}.csv", index=False)
    mejor = {k: t.iloc[0][k] for k in ("max_depth", "min_child_weight", "reg_lambda")}
    mejor = dict(max_depth=int(mejor["max_depth"]), min_child_weight=int(mejor["min_child_weight"]),
                 reg_lambda=float(mejor["reg_lambda"]))
    print(f"\nGanadora de la selección: {nombre(mejor)}")
    if mejor == ACTUAL:
        print("Es la actual: nada que confirmar.")
        return
    a = correr(bt, cols, conf, ACTUAL, A.SEMILLAS)
    b = correr(bt, cols, conf, mejor, A.SEMILLAS)
    y = a[A.OBJETIVO].values
    d = (a.p.values - y) ** 2 - (b.p.values - y) ** 2
    pos = sum(((a[a.mes == m].p - a[a.mes == m][A.OBJETIVO]) ** 2).mean() >
              ((b[b.mes == m].p - b[b.mes == m][A.OBJETIVO]) ** 2).mean() for m in conf)
    ini = (a.mes >= "2026-08").values
    print(f"CONFIRMACIÓN ({len(a)} partidos no vistos): ganadora vs actual "
          f"{d.mean()/(d.std(ddof=1)/np.sqrt(len(d))):+.2f}s (Brier {((b.p.values-y)**2).mean():.4f} vs "
          f"{((a.p.values-y)**2).mean():.4f}; mejora en {pos}/{len(conf)} meses; arranque 2026/27 "
          f"{d[ini].mean()*100:+.2f} pts)")
    a.merge(b[["match_id", "p"]].rename(columns={"p": "p_mejor"}), on="match_id").to_csv(
        "data/afinar_ambos_confirmacion.csv", index=False)


if __name__ == "__main__":
    main()
