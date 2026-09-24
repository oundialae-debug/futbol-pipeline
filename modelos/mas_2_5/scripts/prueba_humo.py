"""
Prueba de humo SIN red para mas_2_5: construye los rasgos (los de rasgos.py y
los nuevos de rasgos_mas25.py), comprueba que no hay fuga en ninguno de los
dos, y entrena un modelo real con el conjunto de producción de esta carpeta.
"""
import sys, io, contextlib, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import pandas as pd
import rasgos, rasgos_mas25 as R, modelo_xgboost as M

hist = M.cargar()
if hist is None:
    print("Falta data/historico_partidos.csv")
    sys.exit(1)
js = pd.read_csv("data/historico_jugador_stats.csv")
h2 = pd.read_csv("data/historico_h2h_profundo.csv")

ok, detalle = rasgos.comprobar_sin_fuga(hist)
print(f"FUGA (rasgos.py):       {'pasa' if ok else 'FALLA'} -- {detalle}")
if not ok:
    sys.exit(1)
ok, detalle = R.comprobar_sin_fuga(hist, js, h2)
print(f"FUGA (rasgos_mas25.py): {'pasa' if ok else 'FALLA'} -- {detalle}")
if not ok:
    sys.exit(1)

base = R.construir(hist, js, h2)
cols = R.columnas_produccion(base)
fechas = pd.to_datetime(base.fecha, utc=True)
ent = base[fechas <= pd.Timestamp("2026-04-24", tz="UTC")]
val = base[(fechas > pd.Timestamp("2026-04-24", tz="UTC")) & base[cols].notna().all(axis=1)]
m = M.entrenar(ent[cols].values, ent["mas_2_5"].values.astype(int), 2, semilla=0)
p = M.probabilidades(m, val[cols].values, 2)
b = M.brier(p, val["mas_2_5"].values.astype(int), 2)
print(f"{len(cols)} rasgos, entreno {len(ent)} / valido {len(val)}")
print(f"Brier mas_2_5 (1 semilla, solo para comprobar que corre): {b:.4f}")
print("\nprueba_humo: OK")
