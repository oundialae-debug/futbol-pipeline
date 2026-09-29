"""
Auditoría externa, punto 6 (29/09/2026): ¿aguantan los cambios aceptados por
debajo del listón si se repiten con OTRAS semillas?

El 29/09 se vio que el mismo modelo con semillas 0-4 y 10-14 difiere +2.12s
consigo mismo. Dos cambios entraron en el oficial con pruebas en el filo:
  A  portero titular (+1.25s, 10 de 14 meses, semillas 0-4)
  B  2022/23 dentro y xG del equipo fuera (+2.55s, 13 de 21 meses, tras 3 intentos)
Se repiten con semillas 10-14 (no usadas en ninguna decisión), mismos meses,
contra el modelo SIN ese cambio. Fijado antes: si el signo se da la vuelta o
el efecto cae a la mitad, se documenta como no confirmado.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A
import modelo_xgboost as M
import rasgos
import portero

SEMILLAS = (10, 11, 12, 13, 14)
EPS = 1e-4


def comparar(base, nuevo, meses, nombre):
    y = base[A.OBJETIVO].values
    d = (base.p_ambos.values - y) ** 2 - (nuevo.p_ambos.values - y) ** 2
    lo = lambda p: -(y * np.log(np.clip(p, EPS, 1)) + (1 - y) * np.log(np.clip(1 - p, EPS, 1)))
    dl = lo(base.p_ambos.values) - lo(nuevo.p_ambos.values)
    pos = sum(((base[base.mes == m].p_ambos - base[base.mes == m][A.OBJETIVO]) ** 2).mean() >
              ((nuevo[nuevo.mes == m].p_ambos - nuevo[nuevo.mes == m][A.OBJETIVO]) ** 2).mean() for m in meses)
    s = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
    print(f"{nombre:44s} Brier {s(d):+.2f}s  log loss {s(dl):+.2f}s  mejor en {pos}/{len(meses)} meses", flush=True)


def main():
    A.SEMILLAS = SEMILLAS
    bt, cols = A.preparar()
    # A: portero, en los meses donde existe (como se probó)
    cob = bt.groupby("mes").loc_gk_gp90.apply(lambda s: s.notna().mean())
    meses_a = [m for m, n in bt.mes.value_counts().sort_index().items() if n >= 20 and cob.get(m, 0) >= 0.5]
    sin_gk = [c for c in cols if c not in portero.COLS]
    pa = pd.concat([A.predecir_mes(bt, sin_gk, m) for m in meses_a])
    pb = pd.concat([A.predecir_mes(bt, cols, m) for m in meses_a])
    comparar(pa, pb, meses_a, "A portero (antes +1.25s con semillas 0-4)")
    # B: 2022/23 + sin xG del equipo contra 2023+ con xG (oficial anterior)
    M.TEMPORADA_MINIMA = 2023
    hist = M.cargar()
    old = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    cols_old = rasgos.columnas_rasgo_default(old) + portero.COLS + A.MKT
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    old = old.merge(A.rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    old = old.merge(portero.historico(), on="match_id", how="left")
    old = old[old.goles_l.notna()].reset_index(drop=True)
    old["mes"] = pd.to_datetime(old.fecha, utc=True).dt.strftime("%Y-%m")
    meses_b = [m for m, n in old.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    po = pd.concat([A.predecir_mes(old, cols_old, m) for m in meses_b])[["match_id", "mes", A.OBJETIVO, "p_ambos"]]
    pn = pd.concat([A.predecir_mes(bt, cols, m) for m in meses_b])[["match_id", "p_ambos"]]
    j = po.merge(pn, on="match_id", suffixes=("", "_n"))
    comparar(j, j.assign(p_ambos=j.p_ambos_n), meses_b, "B 2022/23 sin xG (antes +2.55s con 0-4)")


if __name__ == "__main__":
    main()
