"""
Recalibrar el modelo oficial de ambos marcan (29/09/2026).

Hallazgo que lo motiva: en 4.601 partidos (sep-2024 a sep-2026, mes a mes),
el modelo es honesto hasta el 65%, pero cuando da 65-70% pasa el 60%, y
cuando da 70% o más pasa el 56%. Exagera justo los porcentajes altos.

Corrección, FIJADA ANTES de mirar resultados: para cada mes, un calibrador
ajustado SOLO con las predicciones de los meses anteriores (que a su vez
eran fuera de muestra), con al menos 6 meses detrás. Dos formas:
  A  Platt      logística sobre logit(p): encoge los extremos de forma suave.
  B  isotónica  curva escalonada que solo puede subir.
Mismos partidos, Brier emparejado contra el modelo sin recalibrar. Con 2
intentos, listón ~+2.2s. Se da también la tabla de calibración y la
comparación con el mercado real en los partidos con cuota.
"""
import os
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
import modelo_ambos_marcan as A

RUTA_WF = "data/wf_ambos_oficial.csv"
MESES_MIN = 6
EPS = 1e-4


def predicciones():
    """Predicción mes a mes del modelo oficial (cada mes entrenado con lo anterior)."""
    if os.path.exists(RUTA_WF):
        return pd.read_csv(RUTA_WF)
    bt, cols = A.preparar()
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    t = pd.concat([A.predecir_mes(bt, cols, m) for m in meses])[["match_id", "mes", A.OBJETIVO, "p_ambos"]]
    t.to_csv(RUTA_WF, index=False)
    return t


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sigmas(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def tabla(p, y, etiqueta):
    lado = np.where(p >= 0.5, p, 1 - p)
    gana = np.where(p >= 0.5, y == 1, y == 0)
    print(f"  {etiqueta}")
    for a, b in ((.5, .55), (.55, .6), (.6, .65), (.65, .7), (.7, 1.01)):
        m = (lado >= a) & (lado < b)
        if m.sum():
            print(f"    dice {a:.0%}-{min(b, 1):.0%}: n={m.sum():4d}  dice {lado[m].mean():.1%}  pasa {gana[m].mean():.1%}")


def main():
    t = predicciones()
    meses = sorted(t.mes.unique())
    out = []
    for i, m in enumerate(meses):
        if i < MESES_MIN:
            continue
        pasado, hoy = t[t.mes < m], t[t.mes == m].copy()
        y0 = pasado[A.OBJETIVO].values.astype(int)
        platt = LogisticRegression(C=1e6).fit(logit(pasado.p_ambos.values).reshape(-1, 1), y0)
        hoy["p_platt"] = platt.predict_proba(logit(hoy.p_ambos.values).reshape(-1, 1))[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip", y_min=EPS, y_max=1 - EPS).fit(pasado.p_ambos.values, y0)
        hoy["p_iso"] = iso.predict(hoy.p_ambos.values)
        out.append(hoy)
    r = pd.concat(out)
    y = r[A.OBJETIVO].values
    b0 = (r.p_ambos - y) ** 2
    print(f"Prueba: {r.mes.min()}..{r.mes.max()}, {len(r)} partidos (calibrador con >= {MESES_MIN} meses detrás)\n")
    for c, nombre in (("p_platt", "A Platt"), ("p_iso", "B isotónica")):
        d = b0 - (r[c] - y) ** 2
        pos = sum(((g.p_ambos - g[A.OBJETIVO]) ** 2).mean() > ((g[c] - g[A.OBJETIVO]) ** 2).mean()
                  for _, g in r.groupby("mes"))
        ini = (r.mes >= "2026-08").values
        print(f"{nombre:12s} vs sin recalibrar {sigmas(d):+.2f}s  (Brier {((r[c]-y)**2).mean():.4f} vs {b0.mean():.4f}; "
              f"mejora en {pos}/{r.mes.nunique()} meses; arranque 2026/27 {d[ini].mean()*100:+.2f} pts)")
    print("\nCalibración:")
    tabla(r.p_ambos.values, y, "sin recalibrar")
    tabla(r.p_platt.values, y, "A Platt")
    tabla(r.p_iso.values, y, "B isotónica")
    r.to_csv("data/recalibrar_ambos.csv", index=False)
    # contra el mercado real, en los partidos con cuota de ambos marcan
    try:
        import evaluar_mercados as EM
        c = EM.cargar_cuotas_crudas()
        b = c[c.familia == "Both Teams To Score"]
        piv = b.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
        piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
        piv["p"] = (1 / piv.yes) / (1 / piv.yes + 1 / piv.no)
        v = r.merge(piv.groupby("match_id").p.median().rename("p_mkt"), left_on="match_id", right_index=True)
        yv = v[A.OBJETIVO]
        print(f"\nContra el mercado real ({len(v)} partidos con cuota):")
        for c_, n in (("p_ambos", "sin recalibrar"), ("p_platt", "A Platt"), ("p_iso", "B isotónica")):
            print(f"  {n:15s} {sigmas((v.p_mkt - yv) ** 2 - (v[c_] - yv) ** 2):+.2f}s")
    except Exception as e:
        print(f"(sin comparación con el mercado: {e})")


if __name__ == "__main__":
    main()
