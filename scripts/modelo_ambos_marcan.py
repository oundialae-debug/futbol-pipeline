"""
EL modelo de ambos marcan: la configuración que mejor ha funcionado
(fijada el 26/09/2026 a petición del usuario, ver CLAUDE.md "Ambos marcan
mes a mes").

  - variables: las de producción (columnas_rasgo_default, 99) + los 7
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
import rasgos, modelo_xgboost as M
from apuesta_ambos_marcan import rasgos_mercado
from cuota_como_variable import MKT

OBJETIVO = "ambos_marcan"
SEMILLAS = (0, 1, 2, 3, 4)


def preparar():
    """Histórico con rasgos + precio previo. Devuelve (tabla, columnas del modelo)."""
    hist = M.cargar()
    bt = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    cols = rasgos.columnas_rasgo_default(bt) + MKT
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    bt = bt.merge(rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    bt = bt[bt.goles_l.notna()].reset_index(drop=True)
    bt["mes"] = pd.to_datetime(bt.fecha, utc=True).dt.strftime("%Y-%m")
    return bt, cols


def predecir_mes(bt, cols, mes, extra=()):
    """P(ambos marcan) para los partidos de `mes`, entrenando con todo lo anterior."""
    c = list(cols) + list(extra)
    pasado, test = bt[bt.mes < mes], bt[bt.mes == mes]
    y = pasado[OBJETIVO].values.astype(int)
    p = np.mean([M.probabilidades(M.entrenar(pasado[c].values, y, 2, semilla=s),
                                  test[c].values, 2)[:, 1] for s in SEMILLAS], axis=0)
    return test.assign(p_ambos=p)


if __name__ == "__main__":
    bt, cols = preparar()
    ultimo = bt.mes.max()
    t = predecir_mes(bt, cols, ultimo)
    print(f"{len(cols)} variables. Mes {ultimo}: {len(t)} partidos, "
          f"P media {t.p_ambos.mean():.3f}, real {t[OBJETIVO].mean():.3f}")
