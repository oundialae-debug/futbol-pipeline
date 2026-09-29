import sys, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0, "scripts")
import pandas as pd, modelo_ambos_marcan as A, modelo_xgboost as M, rasgos, portero
import auditoria_semillas as S
A.SEMILLAS = S.SEMILLAS
bt, cols = A.preparar()
M.TEMPORADA_MINIMA = 2023
old = rasgos.construir(M.cargar()).sort_values("fecha").reset_index(drop=True)
cols_old = rasgos.columnas_rasgo_default(old) + portero.COLS + A.MKT
fd = pd.read_csv("data/cuotas_historicas_fd.csv")
old = old.merge(A.rasgos_mercado(fd, "_previa"), on="match_id", how="left").merge(portero.historico(), on="match_id", how="left")
old = old[old.goles_l.notna()].reset_index(drop=True)
old["mes"] = pd.to_datetime(old.fecha, utc=True).dt.strftime("%Y-%m")
meses = [m for m, n in old.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
print(len(cols_old), "vs", len(cols), flush=True)
po = pd.concat([A.predecir_mes(old, cols_old, m) for m in meses])[["match_id", "mes", A.OBJETIVO, "p_ambos"]]
pn = pd.concat([A.predecir_mes(bt, cols, m) for m in meses])[["match_id", "p_ambos"]]
j = po.merge(pn, on="match_id", suffixes=("", "_n"))
S.comparar(j, j.assign(p_ambos=j.p_ambos_n), meses, "B 2022/23 sin xG (antes +2.55s con 0-4)")
