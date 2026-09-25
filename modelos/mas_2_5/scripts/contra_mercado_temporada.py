"""
El modelo de 28 contra el mercado en TODA la temporada 2025/26 y el inicio
de 2026/27, con cuotas de football-data.co.uk (24-25/09/2026).

1. Comprobación de la fuente: donde hay cuotas de la API y de football-data
   a la vez, las dos probabilidades deben parecerse (resolutor nuevo contra
   viejo, partido a partido).
2. Predicción mes a mes: cada mes, modelo entrenado solo con lo anterior.
3. Contra el mercado: media de casas antes del partido (Avg) y Pinnacle al
   cierre (la referencia más dura). Brier emparejado + acierto.
4. Simulación de apuestas a 1 unidad: apostar el lado con valor contra la
   cuota MEDIA (lo que da una casa normal) y contra la MÁXIMA (optimista:
   mejor casa de ~40, no siempre simultáneas).
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
import modelo_xgboost as M, rasgos_mas25 as R, evaluar_mercados as EM

fd = pd.read_csv("data/cuotas_football_data.csv").set_index("match_id")
prob = lambda o, u: (1 / o) / (1 / o + 1 / u)

# 1. comprobación contra la API
api = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS["mas_2_5"])
comun = api.index.intersection(fd.index)
p_fd = prob(fd.loc[comun, "Avg>2.5"], fd.loc[comun, "Avg<2.5"])
print(f"1. {len(comun)} partidos con las dos fuentes: correlación {np.corrcoef(api.loc[comun], p_fd)[0,1]:.3f}, "
      f"diferencia media {np.abs(api.loc[comun].values - p_fd.values).mean()*100:.1f} puntos\n")

with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"),
                 pd.read_csv("data/historico_h2h_profundo.csv"))
cols = R.columnas_produccion(bc)
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].copy()
f = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = f.dt.strftime("%Y-%m")
evalua = bc[(f >= "2025-07-01") & bc.match_id.isin(fd.index)]

# 2. mes a mes
preds = []
for mes in sorted(evalua.mes.unique()):
    val = evalua[evalua.mes == mes]
    ent = bc[f < pd.Timestamp(mes + "-01", tz="UTC")]
    y = ent.mas_2_5.values.astype(int)
    p = np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s), val[cols].values, 2)[:, 1]
                 for s in EM.SEMILLAS], axis=0)
    preds.append(pd.DataFrame({"match_id": val.match_id.values, "mes": mes, "p": p,
                               "y": val.mas_2_5.values.astype(int)}))
d = pd.concat(preds).merge(fd, left_on="match_id", right_index=True)
d["p_avg"] = prob(d["Avg>2.5"], d["Avg<2.5"])
d["p_pc"] = prob(d["PC>2.5"], d["PC<2.5"])
d["temporada"] = np.where(d.mes < "2026-07", "2025/26", "2026/27")
d.to_csv("data/contra_mercado_temporada.csv", index=False)


def sig(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


# 3. contra el mercado
print("3. Modelo contra el mercado (positivo = el modelo es mejor)")
for t, g in list(d.groupby("temporada")) + [("todo", d)]:
    bmod = 2 * (g.p - g.y) ** 2
    s = f"  {t:8s} n={len(g):4d}  vs media casas {sig(2*(g.p_avg-g.y)**2 - bmod):+.2f}s"
    gp = g.dropna(subset=["p_pc"])
    if len(gp) > 30:
        s += f" | vs Pinnacle cierre {sig(2*(gp.p_pc-gp.y)**2 - 2*(gp.p-gp.y)**2):+.2f}s (n={len(gp)})"
    s += f" | acierto modelo {((g.p>.5)==g.y).mean()*100:.1f}% casas {((g.p_avg>.5)==g.y).mean()*100:.1f}%"
    print(s)

# 4. simulación de apuestas
print("\n4. Apostando 1 unidad al lado con valor (valor = prob. modelo x cuota - 1)")
for nombre, co, cu in (("cuota media", "Avg>2.5", "Avg<2.5"), ("cuota máxima", "Max>2.5", "Max<2.5")):
    for umbral in (0.0, 0.05, 0.10):
        vo = d.p * d[co] - 1
        vu = (1 - d.p) * d[cu] - 1
        over = (vo > umbral) & (vo >= vu)
        under = (vu > umbral) & (vu > vo)
        ret = np.concatenate([(d.y[over] * d[co][over] - 1).values,
                              ((1 - d.y[under]) * d[cu][under] - 1).values])
        if len(ret) < 20:
            continue
        print(f"  {nombre:13s} umbral {umbral:>4.0%}: {len(ret):5d} apuestas  rentabilidad "
              f"{ret.mean()*100:+6.2f}%  (±{ret.std(ddof=1)/np.sqrt(len(ret))*100:.2f}, {sig(ret):+.2f}s)")
