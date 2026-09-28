"""
¿Ayuda la temporada 2022/23 al modelo oficial de ambos marcan? (28/09/2026)

2022/23 trae partidos y estadísticas, pero NO árbitro ni alineaciones (así que
tampoco calidad de plantilla ni portero): entra con huecos. Prueba FIJADA
ANTES de mirar resultados, la misma mes a mes del modelo oficial:
  A  histórico sin 2022/23 (el modelo oficial de hoy)
  B  histórico con 2022/23 (rasgos recalculados con esa historia detrás)
Meses de prueba: sep-2024 a hoy, mismos partidos en los dos brazos, Brier
emparejado. Entra si mejora; si sale en el ruido, se queda fuera del
entrenamiento (más filas sin su señal ya no compraron nada con 2023/24).
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


def preparar(sin_2022):
    M.TEMPORADA_MINIMA = 2023 if sin_2022 else 2022
    hist = M.cargar()
    bt = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    cols = rasgos.columnas_rasgo_default(bt) + portero.COLS + A.MKT
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    bt = bt.merge(A.rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    bt = bt.merge(portero.historico(), on="match_id", how="left")
    bt = bt[bt.goles_l.notna()].reset_index(drop=True)
    bt["mes"] = pd.to_datetime(bt.fecha, utc=True).dt.strftime("%Y-%m")
    return bt, cols


def main():
    a, cols_a = preparar(True)
    b, cols_b = preparar(False)
    print(f"Filas: sin 2022/23 {len(a)}, con {len(b)}")
    meses = [m for m, n in a.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    filas = []
    for m in meses:
        pa = A.predecir_mes(a, cols_a, m)[["match_id", "mes", A.OBJETIVO, "p_ambos"]]
        pb = A.predecir_mes(b, cols_b, m)[["match_id", "p_ambos"]].rename(columns={"p_ambos": "p_con"})
        t = pa.merge(pb, on="match_id")
        y = t[A.OBJETIVO]
        d = (t.p_ambos - y) ** 2 - (t.p_con - y) ** 2
        print(f"  {m}: n={len(t)}  con 2022/23 {d.mean()*100:+.2f} pts de Brier", flush=True)
        filas.append(t)
    t = pd.concat(filas)
    y = t[A.OBJETIVO]
    d = (t.p_ambos - y) ** 2 - (t.p_con - y) ** 2
    pos = sum(((f.p_ambos - f[A.OBJETIVO]) ** 2).mean() > ((f.p_con - f[A.OBJETIVO]) ** 2).mean() for f in filas)
    print(f"\nTOTAL {len(t)} partidos: con 2022/23 vs sin {d.mean()/(d.std(ddof=1)/np.sqrt(len(d))):+.2f}s "
          f"(Brier sin {((t.p_ambos-y)**2).mean():.4f}, con {((t.p_con-y)**2).mean():.4f}; "
          f"mejora en {pos}/{len(filas)} meses)")
    t.to_csv("data/experimento_temporada_2022.csv", index=False)


if __name__ == "__main__":
    main()
