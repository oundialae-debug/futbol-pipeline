"""
Modelo oficial mes a mes desde ago 2024 (29/09/2026), con los titulares de
2023/24 ya reconstruidos desde /box-score (cobertura 14% -> 92%).

2024/25 era la temporada peor evaluada de todas (-4.89s el XGBoost 28 en
adaptativo.py) porque su entrenamiento, 2023/24, casi no tenía alineaciones
ni g/a. Mismo protocolo que siempre: cada mes entrenado solo con lo anterior.
Se compara el XGBoost 28 solo y el modelo oficial (28 + logística), contra la
media de casas de football-data, por temporada.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import modelo_xgboost as M, rasgos_mas25 as R
from modelo_oficial import rasgos, SUMAS, cargar_hist

hist = cargar_hist()
bc = rasgos(hist)
fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(
    fd[["match_id", "p_mercado", "Avg>2.5", "Avg<2.5"]], on="match_id", how="left")
bc["f"] = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = bc.f.dt.strftime("%Y-%m")
C28 = R.columnas_produccion(bc)
print("g/a de delanteros disponible por temporada:",
      bc.groupby(bc.f.dt.year - (bc.f.dt.month < 7)).loc_cp_del_ga90.apply(lambda s: f"{s.notna().mean()*100:.0f}%").to_dict())

res = []
for mes in sorted(bc.loc[(bc.f >= "2024-08-01") & bc.p_mercado.notna(), "mes"].unique()):
    val = bc[(bc.mes == mes) & bc.p_mercado.notna()]
    ent = bc[bc.f < pd.Timestamp(mes + "-01", tz="UTC")]
    y = ent.mas_2_5.values.astype(int)
    px = np.mean([M.probabilidades(M.entrenar(ent[C28].values, y, 2, semilla=s), val[C28].values, 2)[:, 1]
                  for s in range(5)], axis=0)
    e = ent.dropna(subset=SUMAS)
    if len(e) >= 200:
        sc = StandardScaler().fit(e[SUMAS])
        lr = LogisticRegression().fit(sc.transform(e[SUMAS]), e.mas_2_5.astype(int))
        pl = lr.predict_proba(sc.transform(val[SUMAS].fillna(e[SUMAS].mean())))[:, 1]
        po = (px + pl) / 2
    else:                                   # antes de tener xG por jugador: solo XGBoost
        po = px
    res.append(pd.DataFrame({"mes": mes, "y": val.mas_2_5.values, "pm": val.p_mercado.values,
                             "o": val["Avg>2.5"].values, "u": val["Avg<2.5"].values,
                             "p_28": px, "p_oficial": po}))
d = pd.concat(res, ignore_index=True)
d.to_csv("data/wf_oficial.csv", index=False)
d["temp"] = np.where(d.mes < "2025-07", "2024/25", np.where(d.mes < "2026-07", "2025/26", "2026/27"))
sig = lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
bm = 2 * (d.pm - d.y) ** 2
print(f"\n{len(d)} partidos, {d.mes.min()} a {d.mes.max()}, mes a mes. Positivo = mejor que la casa.")
for c in ("p_28", "p_oficial"):
    b = 2 * (d[c] - d.y) ** 2
    vo, vu = d[c] * d.o - 1, (1 - d[c]) * d.u - 1
    ov, un = (vo > 0) & (vo >= vu), (vu > 0) & (vu > vo)
    ret = np.r_[(d.y[ov] * d.o[ov] - 1).values, ((1 - d.y[un]) * d.u[un] - 1).values]
    por = "  ".join(f"{t} {sig(bm[g.index] - b[g.index]):+.2f}s" for t, g in d.groupby("temp"))
    print(f"  {c:10s} vs casa {sig(bm - b):+.2f}s | {por} | acierto {((d[c]>.5)==d.y).mean()*100:.1f}% "
          f"| apostando {ret.mean()*100:+.2f}% (±{ret.std(ddof=1)/np.sqrt(len(ret))*100:.2f}, {len(ret)})")
print(f"  casa: acierto {((d.pm>.5)==d.y).mean()*100:.1f}%")
