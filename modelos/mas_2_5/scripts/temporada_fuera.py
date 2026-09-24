"""
Acierto en 2025/26 dejando FUERA esa temporada entera (24/09/2026).

Pregunta del usuario: ¿qué % acertaría el modelo en 2025/26 sin haberla
visto? Dos formas honestas:
  - mes a mes: cada mes se predice con un modelo entrenado solo con lo
    anterior (ya medido: 56.0%)
  - temporada fuera: un único modelo entrenado con 2024/25 + arranque de
    2026/27 (antes y después), sin ningún partido de 2025/26.
Los rasgos de cada partido siguen usando solo partidos anteriores
(shift antes de rolling), así que entrenar con 2026/27 no mete el resultado
de ningún partido de 2025/26 en sus propios rasgos.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
import modelo_xgboost as M, rasgos_mas25 as R, evaluar_mercados as EM

with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"),
                 pd.read_csv("data/historico_h2h_profundo.csv"))
cols = R.columnas_produccion(bc)
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].copy()
f = pd.to_datetime(bc.fecha, utc=True)
temp = (f >= "2025-07-01") & (f < "2026-07-01")
ent, val = bc[~temp], bc[temp]
y = ent.mas_2_5.values.astype(int)
p = np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s), val[cols].values, 2)[:, 1]
             for s in EM.SEMILLAS], axis=0)
yv = val.mas_2_5.values
acierto = (p > .5) == yv
print(f"Entrenado con {len(ent)} partidos (2024/25: {(f[~temp] < '2025-07-01').sum()}, "
      f"2026/27: {(f[~temp] >= '2026-07-01').sum()}), sin ninguno de 2025/26")
print(f"TEMPORADA FUERA: {acierto.mean()*100:.1f}% de {len(val)} partidos de 2025/26")
print(f"Siempre lo más frecuente del entrenamiento: {(yv == int(y.mean() > .5)).mean()*100:.1f}%")
mes = pd.to_datetime(val.fecha, utc=True).dt.strftime("%Y-%m").values
print(pd.Series(acierto, index=mes).groupby(level=0).agg(["mean", "count"])
      .assign(mean=lambda d: (d["mean"] * 100).round(1)).to_string())
conf = np.abs(p - .5)
for q in (0.1, 0.2):
    m = conf > q
    print(f"cuando da más del {50+q*100:.0f}% a un lado ({m.sum()} partidos): acierta {acierto[m].mean()*100:.1f}%")
