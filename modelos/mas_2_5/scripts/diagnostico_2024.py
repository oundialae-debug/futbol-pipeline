"""
¿Por qué 2024/25 sale tan mal (-5s contra la casa) y 2025/26 no (-0.5s)?
(29/09/2026). Tres miradas, sin tocar el modelo:

1. Por liga: XGBoost 28 mes a mes (3 semillas) en 2024/25 y 2025/26,
   contra la casa, liga a liga.
2. Las 28 variables: media por temporada, para ver si alguna cambia de escala
   (una fuente que cuenta distinto un año hace que el modelo aprenda mal).
3. Un modelo tonto (tasa de Más 2.5 de la liga en lo anterior): si también
   cae mucho más en 2024/25 que en 2025/26, el cambio es de la casa o del
   año, no del XGBoost.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
import modelo_xgboost as M, rasgos_mas25 as R
from modelo_oficial import rasgos, cargar_hist

hist = cargar_hist()
bc = rasgos(hist)
fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(fd[["match_id", "p_mercado"]], on="match_id", how="left") \
    .merge(hist[["match_id", "liga"]], on="match_id")
bc["f"] = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = bc.f.dt.strftime("%Y-%m")
bc["temp"] = bc.f.dt.year - (bc.f.dt.month < 7)
C28 = R.columnas_produccion(bc)

# 2. variables por temporada
print("2. Media de cada variable (solo loc_) por temporada:")
loc = [c for c in C28 if c.startswith("loc_")]
print(bc.groupby("temp")[loc].mean().round(2).T.to_string())

# 1 y 3. mes a mes 2024/25 y 2025/26
res = []
for mes in sorted(bc.loc[(bc.f >= "2024-08-01") & (bc.f < "2026-07-01") & bc.p_mercado.notna(), "mes"].unique()):
    val = bc[(bc.mes == mes) & bc.p_mercado.notna()]
    ent = bc[bc.f < pd.Timestamp(mes + "-01", tz="UTC")]
    y = ent.mas_2_5.values.astype(int)
    px = np.mean([M.probabilidades(M.entrenar(ent[C28].values, y, 2, semilla=s), val[C28].values, 2)[:, 1]
                  for s in range(3)], axis=0)
    tasa = ent[ent.f >= ent.f.max() - pd.Timedelta(days=730)].groupby("liga").mas_2_5.mean()
    res.append(pd.DataFrame({"temp": val.temp.values, "liga": val.liga.values, "y": val.mas_2_5.values,
                             "pm": val.p_mercado.values, "p28": px, "ptonto": val.liga.map(tasa).values}))
d = pd.concat(res, ignore_index=True)
d.to_csv("data/diagnostico_2024.csv", index=False)
sig = lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 else np.nan
d["bm"], d["b28"], d["bt"] = [2 * (d[c] - d.y) ** 2 for c in ("pm", "p28", "ptonto")]

print("\n1. XGBoost 28 contra la casa, por liga (sigmas; n):")
t = d.groupby(["liga", "temp"]).apply(lambda g: f"{sig(g.bm - g.b28):+.2f}s (n={len(g)})").unstack()
print(t.to_string())
print("\n3. Por temporada: Brier casa / XGBoost 28 / modelo tonto, y cada uno contra la casa:")
for tp, g in d.groupby("temp"):
    print(f"   {tp}/{(tp+1)%100:02d} n={len(g)}: casa {g.bm.mean():.4f}  XGB {g.b28.mean():.4f} ({sig(g.bm-g.b28):+.2f}s)  "
          f"tonto {g.bt.mean():.4f} ({sig(g.bm-g.bt):+.2f}s) | casa mejora al tonto en {(1-g.bm.mean()/g.bt.mean())*100:.1f}%, "
          f"XGB en {(1-g.b28.mean()/g.bt.mean())*100:.1f}%")
