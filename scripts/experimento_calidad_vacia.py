"""
Depuración (29/09/2026): calcular_calidad_plantilla (rasgos.py) devuelve 0 en
vez de hueco cuando falta el once. Un partido sin alineación le llega al modelo
como "equipo con calidad 0" (toda 2022/23 y 184 partidos de abr-jun 2024).
Prueba fijada antes, un intento: oficial tal cual contra oficial con calidad
vacía (NaN) donde no hay ningún titular conocido. Mes a mes sep-2024 a sep-2026.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A
from experimento_titulares_2324 import comparar

CAL = ["calidad_minutos", "calidad_ga", "calidad_conocidos"]


def main():
    a, cols = A.preparar()
    b = a.copy()
    for lado in ("loc", "vis"):
        sin = b[f"{lado}_calidad_conocidos"] == 0
        print(f"{lado}: {sin.mean():.1%} de los partidos sin ningún titular conocido")
        for c in CAL:
            b.loc[sin, f"{lado}_{c}"] = np.nan
    for c in ("calidad_minutos", "calidad_ga"):
        if f"dif_{c}" in b.columns:
            b[f"dif_{c}"] = b[f"loc_{c}"] - b[f"vis_{c}"]
    meses = [m for m, k in a.mes.value_counts().sort_index().items() if m >= "2024-09" and k >= 20]
    pa = pd.concat([A.predecir_mes(a, cols, m) for m in meses])
    pb = pd.concat([A.predecir_mes(b, cols, m) for m in meses])
    comparar(pa, pb, meses, "calidad vacía (NaN) vs 0")


if __name__ == "__main__":
    main()
