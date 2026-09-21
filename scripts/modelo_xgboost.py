"""
EL MODELO: gradient boosting sobre el histórico

LAS DOS DECISIONES QUE IMPORTAN MÁS QUE EL ALGORITMO
----------------------------------------------------

1. **El corte de validación es TEMPORAL, no aleatorio.**
   Una validación cruzada normal reparte los partidos al azar: entrena con la
   jornada 30 y valida con la 12. Eso es ver el futuro. En fútbol además la
   fuga es indirecta: la forma de un equipo en marzo informa de febrero. Aquí
   se entrena con lo viejo y se valida con lo nuevo, que es la única prueba
   que se parece a apostar.

2. **El rival no es el azar: es el MERCADO.**
   Un modelo que acierta el 53% del 1X2 parece bueno y es inútil si la casa
   acierta el 54%. Lo único que decide es si nuestra probabilidad es MEJOR que
   la suya, medida en Brier fuera de muestra. Por eso el informe pone las dos
   siempre juntas, y si no tenemos cuotas para un partido, se dice.

EL BASELINE HONESTO
-------------------
Además del mercado, se compara contra dos referencias tontas:
  - la frecuencia base de la liga (local/empate/visitante sin mirar nada)
  - el modelo con los rasgos barajados (destruye la señal, conserva el formato)
Si el modelo no bate claramente a las dos, no hay modelo.

POR QUÉ NO SE PROMETE NADA DE DINERO AQUÍ
-----------------------------------------
Este script produce probabilidades y su error. Convertir eso en apuestas es
trabajo de `gestion_banca.py`, que se niega a apostar cuando la ventaja no
supera al error. La separación es a propósito: mezclar "qué creo" con "cuánto
juego" es como se acaba apostando sobre ruido.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rasgos

RUTA_HIST = "data/historico_partidos.csv"
RUTA_SALIDA = "modelo.md"
PROPORCION_VALIDACION = 0.25     # el 25% más reciente
MINIMO_ENTRENAMIENTO = 300

OBJETIVOS = {
    "resultado": ("1X2 (local / empate / visitante)", 3),
    "mas_2_5": ("Más de 2.5 goles", 2),
    "ambos_marcan": ("Ambos marcan", 2),
    "mas_9_5_corners": ("Más de 9.5 córners", 2),
    "mas_4_5_tarjetas": ("Más de 4.5 tarjetas", 2),
}


def cargar():
    if not os.path.exists(RUTA_HIST):
        print(f"No existe {RUTA_HIST}. Lanza antes el backfill del histórico.")
        return None
    return pd.read_csv(RUTA_HIST)


def brier(probs, reales, n_clases):
    """Brier multiclase. Más bajo es mejor. Es el error medio al cuadrado."""
    uno = np.zeros((len(reales), n_clases))
    uno[np.arange(len(reales)), reales] = 1
    return float(((probs - uno) ** 2).sum(axis=1).mean())


def entrenar(X, y, n_clases, semilla=0):
    try:
        from xgboost import XGBClassifier
        m = XGBClassifier(
            n_estimators=400, max_depth=3, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8,
            min_child_weight=8, reg_lambda=2.0,
            objective="multi:softprob" if n_clases > 2 else "binary:logistic",
            num_class=n_clases if n_clases > 2 else None,
            random_state=semilla, n_jobs=2, eval_metric="mlogloss",
            tree_method="hist",
        )
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        print("    [xgboost no instalado, uso HistGradientBoosting]")
        m = HistGradientBoostingClassifier(
            max_depth=3, learning_rate=0.03, max_iter=400,
            min_samples_leaf=20, l2_regularization=2.0, random_state=semilla)
    m.fit(X, y)
    return m


def probabilidades(m, X, n_clases):
    p = m.predict_proba(X)
    if p.ndim == 1 or p.shape[1] == 1:
        p = np.column_stack([1 - p.ravel(), p.ravel()])
    return p


def main():
    hist = cargar()
    if hist is None or len(hist) < MINIMO_ENTRENAMIENTO:
        n = 0 if hist is None else len(hist)
        print(f"Solo hay {n} partidos. Hacen falta {MINIMO_ENTRENAMIENTO} "
              f"para que el corte temporal deje algo con que validar.")
        return

    print(f"{len(hist)} partidos en el histórico.\n")

    ok, detalle = rasgos.comprobar_sin_fuga(hist)
    print(f"COMPROBACIÓN DE FUGA: {'pasa' if ok else 'FALLA'} -- {detalle}")
    if not ok:
        print("\nParado. Un modelo con fuga da números buenos y falsos, que es")
        print("peor que no tener modelo.")
        raise SystemExit(1)

    base = rasgos.construir(hist).sort_values("fecha")
    cols = rasgos.columnas_rasgo(base)
    base = base[base[cols].notna().all(axis=1)].reset_index(drop=True)
    corte = int(len(base) * (1 - PROPORCION_VALIDACION))
    ent, val = base.iloc[:corte], base.iloc[corte:]
    print(f"\nCorte TEMPORAL: entreno {len(ent)} (hasta "
          f"{pd.to_datetime(ent.fecha.max()).date()}), "
          f"valido {len(val)} (desde "
          f"{pd.to_datetime(val.fecha.min()).date()})\n")

    lineas = ["# El modelo\n",
              f"{len(base)} partidos utilizables de {len(hist)} en el "
              f"histórico. Corte temporal: se entrena con los "
              f"{len(ent)} más viejos y se valida con los {len(val)} más "
              f"nuevos.\n",
              "> El rival de este modelo no es el azar, es el mercado. Un "
              "Brier bueno no sirve de nada si el de la casa es mejor.\n",
              "| Objetivo | Brier modelo | Brier base liga | Brier barajado | "
              "mejora sobre base |", "|---|---|---|---|---|"]

    rng = np.random.default_rng(0)
    for objetivo, (nombre, n_clases) in OBJETIVOS.items():
        Xe, ye = ent[cols].values, ent[objetivo].values.astype(int)
        Xv, yv = val[cols].values, val[objetivo].values.astype(int)
        if len(np.unique(ye)) < n_clases:
            continue

        m = entrenar(Xe, ye, n_clases)
        pv = probabilidades(m, Xv, n_clases)
        b_modelo = brier(pv, yv, n_clases)

        # base tonta: la frecuencia del conjunto de entrenamiento
        frec = np.bincount(ye, minlength=n_clases) / len(ye)
        b_base = brier(np.tile(frec, (len(yv), 1)), yv, n_clases)

        # control: los mismos rasgos barajados. Si el modelo no bate a esto,
        # lo que "aprendió" era el formato de los datos, no señal.
        Xe_b = Xe.copy()
        rng.shuffle(Xe_b)
        m_b = entrenar(Xe_b, ye, n_clases, semilla=1)
        b_baraja = brier(probabilidades(m_b, Xv, n_clases), yv, n_clases)

        mejora = (b_base - b_modelo) / b_base * 100
        print(f"  {nombre:36s} modelo {b_modelo:.4f}  base {b_base:.4f}  "
              f"barajado {b_baraja:.4f}  -> {mejora:+.2f}%")
        lineas.append(f"| {nombre} | {b_modelo:.4f} | {b_base:.4f} | "
                      f"{b_baraja:.4f} | {mejora:+.2f}% |")

    lineas += [
        "\n## Cómo leer esto\n",
        "**Brier** es el error medio al cuadrado de la probabilidad. Más bajo, "
        "mejor. Un modelo que dijera siempre la frecuencia de la liga saca la "
        "columna *base liga*.\n",
        "**Barajado** entrena el mismo modelo con los rasgos revueltos. "
        "Conserva el formato y destruye la señal. Si el modelo no le saca "
        "ventaja clara, no ha aprendido fútbol: ha aprendido la forma del "
        "fichero.\n",
        "## Lo que este fichero NO dice\n",
        "No dice si hay dinero. Para eso hace falta comparar contra la "
        "probabilidad del MERCADO sobre los mismos partidos, y que la ventaja "
        "supere al margen. Eso es `evaluar_contra_mercado.py`.\n",
    ]
    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"\nEscrito {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
