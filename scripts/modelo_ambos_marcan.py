"""
EL modelo de ambos marcan: la configuración que mejor ha funcionado
(fijada el 26/09/2026 a petición del usuario, ver CLAUDE.md "Ambos marcan
mes a mes"; desde el 28/09/2026 con el portero titular, scripts/portero.py,
+1.25s sobre la versión anterior en la prueba mes a mes).

  - variables: las de producción (columnas_rasgo_default, 99) + portero
    titular (loc_/vis_gk_gp90, goles evitados por 90) + los 7
    rasgos del precio PREVIO de Pinnacle/Betfair (football-data, días antes
    del partido; nunca el cierre, que no se conoce al apostar)
  - entrenamiento: con huecos (M.partir), con TODO lo anterior a la fecha
    que se quiere predecir, reentrenado cada mes
  - SIN selección automática de variables y SIN recalibración: el brazo
    "adaptativo" que las añadía perdió dinero (-12% vs +6.2% del reentreno)

Cualquier prueba nueva para ambos marcan (p. ej. xG/xA por jugador) se
compara CONTRA esto, con walk_forward_ambos.py o predecir_mes().
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M, portero
from apuesta_ambos_marcan import rasgos_mercado
from cuota_como_variable import MKT

OBJETIVO = "ambos_marcan"
SEMILLAS = (0, 1, 2, 3, 4)
# Desde el 28/09/2026 (experimento_temporada_2022.py, mes a mes sep-2024 a
# sep-2026): entra 2022/23 y sale el xG medio del EQUIPO (6 columnas
# *_expected_goals). Juntos, +2.55s y 13 de 21 meses. Por separado: 2022/23
# +1.89s, quitar el xG +1.39s. El xG del equipo solo existe desde 2025 y el
# precio ya lo lleva dentro. El portero (xG por jugador) sigue.
TEMPORADA_MINIMA = 2022


# Ajuste interno propio de ambos marcan (29/09/2026, afinar_ambos.py): árboles
# de UN nivel. Elegido en sep-2024..ago-2025 y confirmado en sep-2025..sep-2026
# (2.387 partidos que la selección no vio): +1.54s sobre profundidad 2, mejor
# en 9 de 11 meses. Contra el mercado, igual. El resto de modelos sigue con
# modelo_xgboost.entrenar (profundidad 2).
PARAMS = dict(n_estimators=400, max_depth=1, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
              min_child_weight=20, reg_lambda=5.0)


def entrenar(X, y, semilla=0):
    from xgboost import XGBClassifier
    return XGBClassifier(objective="binary:logistic", random_state=semilla, n_jobs=2,
                         eval_metric="logloss", tree_method="hist", **PARAMS).fit(X, y)


def columnas(bt):
    """Las variables del modelo oficial."""
    return ([c for c in rasgos.columnas_rasgo_default(bt) if "expected_goals" not in c]
            + portero.COLS + MKT)


def preparar():
    """Histórico con rasgos + precio previo. Devuelve (tabla, columnas del modelo)."""
    M.TEMPORADA_MINIMA = TEMPORADA_MINIMA
    hist = M.cargar()
    bt = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    cols = columnas(bt)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    bt = bt.merge(rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    bt = bt.merge(portero.historico(), on="match_id", how="left")
    bt = bt[bt.goles_l.notna()].reset_index(drop=True)
    bt["mes"] = pd.to_datetime(bt.fecha, utc=True).dt.strftime("%Y-%m")
    return bt, cols


def predecir_mes(bt, cols, mes, extra=()):
    """P(ambos marcan) para los partidos de `mes`, entrenando con todo lo anterior."""
    c = list(cols) + list(extra)
    pasado, test = bt[bt.mes < mes], bt[bt.mes == mes]
    y = pasado[OBJETIVO].values.astype(int)
    p = np.mean([M.probabilidades(entrenar(pasado[c].values, y, semilla=s),
                                  test[c].values, 2)[:, 1] for s in SEMILLAS], axis=0)
    return test.assign(p_ambos=p)


if __name__ == "__main__":
    bt, cols = preparar()
    ultimo = bt.mes.max()
    t = predecir_mes(bt, cols, ultimo)
    print(f"{len(cols)} variables. Mes {ultimo}: {len(t)} partidos, "
          f"P media {t.p_ambos.mean():.3f}, real {t[OBJETIVO].mean():.3f}")
