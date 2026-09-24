"""
Prueba de humo SIN red: ejercita rasgos.py + modelo_xgboost.py de verdad.

El prueba_humo.py del repo padre (futbol-pipeline) prueba descanso_en_vivo.py,
que no tiene nada que ver con este pipeline -- no serviría de nada copiado
aquí. Esta versión hace lo que su nombre promete para ESTE modelo: construye
los rasgos, comprueba que no hay fuga, y entrena un modelo real sobre datos
reales, todo sin tocar la API (los CSV ya están en disco).
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import rasgos
import modelo_xgboost as M

hist = M.cargar()
if hist is None:
    print("Falta data/historico_partidos.csv")
    sys.exit(1)

ok, detalle = rasgos.comprobar_sin_fuga(hist)
print(f"COMPROBACIÓN DE FUGA: {'pasa' if ok else 'FALLA'} -- {detalle}")
if not ok:
    sys.exit(1)

base = rasgos.construir(hist).sort_values("fecha")
cols = rasgos.columnas_rasgo_default(base)
base = base[base[cols].notna().all(axis=1)].reset_index(drop=True)
corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
ent, val = base.iloc[:corte], base.iloc[corte:]
print(f"{len(base)} partidos utilizables, {len(cols)} rasgos, "
      f"entreno {len(ent)} / valido {len(val)}")

y_ent = ent["ambos_marcan"].values.astype(int)
y_val = val["ambos_marcan"].values.astype(int)
m = M.entrenar(ent[cols].values, y_ent, 2, semilla=0)
p = M.probabilidades(m, val[cols].values, 2)
b = M.brier(p, y_val, 2)
print(f"Brier ambos_marcan (1 semilla, solo para comprobar que corre): {b:.4f}")
print("\nprueba_humo: OK")
