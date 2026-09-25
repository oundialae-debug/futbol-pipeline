"""
La cuota de la casa como variable (25/09/2026). Posible ahora: football-data
da cuotas de 2024/25 y 2025/26 enteras, así que el entrenamiento las tiene.

Dos versiones, fijadas ANTES de mirar resultados (no se elige entre más):
  A  28 rasgos + p_mercado (probabilidad de la media de casas) como columna
  B  el modelo ARRANCA en la probabilidad del mercado (base_margin = logit
     p_mercado) y los árboles solo aprenden correcciones con los 28 rasgos.
     Sin señal, se queda en el mercado.
Evaluación igual que contra_mercado_temporada.py: mes a mes (cada mes
entrenado solo con lo anterior), contra la media de casas y Pinnacle cierre,
y apuestas a 1 unidad con la cuota media.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
from xgboost import XGBClassifier
import modelo_xgboost as M, rasgos_mas25 as R, evaluar_mercados as EM

fd = pd.read_csv("data/cuotas_football_data.csv")
prob = lambda o, u: (1 / o) / (1 / o + 1 / u)
fd["p_mercado"] = prob(fd["Avg>2.5"], fd["Avg<2.5"])
fd["p_pc"] = prob(fd["PC>2.5"], fd["PC<2.5"])

with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"),
                 pd.read_csv("data/historico_h2h_profundo.csv"))
cols = R.columnas_produccion(bc)
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(
    fd[["match_id", "p_mercado", "p_pc", "Avg>2.5", "Avg<2.5"]], on="match_id", how="inner")
f = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = f.dt.strftime("%Y-%m")
logit = lambda p: np.log(p / (1 - p))


def xgb(semilla):
    return XGBClassifier(n_estimators=400, max_depth=2, learning_rate=0.03, subsample=0.8,
                         colsample_bytree=0.8, min_child_weight=20, reg_lambda=5.0,
                         objective="binary:logistic", random_state=semilla, n_jobs=2,
                         eval_metric="logloss", tree_method="hist")


def predecir(version, ent, val):
    y = ent.mas_2_5.values.astype(int)
    ps = []
    for s in EM.SEMILLAS:
        if version == "28":
            m = xgb(s).fit(ent[cols].values, y); ps.append(m.predict_proba(val[cols].values)[:, 1])
        elif version == "A":
            c = cols + ["p_mercado"]
            m = xgb(s).fit(ent[c].values, y); ps.append(m.predict_proba(val[c].values)[:, 1])
        else:
            m = xgb(s).fit(ent[cols].values, y, base_margin=logit(ent.p_mercado.values))
            ps.append(m.predict_proba(val[cols].values, base_margin=logit(val.p_mercado.values))[:, 1])
    return np.mean(ps, axis=0)


evalua = bc[f >= "2025-07-01"]
res = []
for mes in sorted(evalua.mes.unique()):
    val = evalua[evalua.mes == mes]
    ent = bc[f < pd.Timestamp(mes + "-01", tz="UTC")]
    r = val[["match_id", "mes", "mas_2_5", "p_mercado", "p_pc", "Avg>2.5", "Avg<2.5"]].copy()
    for v in ("28", "A", "B"):
        r[f"p_{v}"] = predecir(v, ent, val)
    res.append(r)
d = pd.concat(res).rename(columns={"mas_2_5": "y"})
d.to_csv("data/cuota_como_variable.csv", index=False)


def sig(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


print(f"{len(d)} partidos evaluados mes a mes ({d.mes.min()} a {d.mes.max()})\n")
print(f"{'modelo':34s} {'vs media casas':>15s} {'vs Pinnacle cierre':>19s} {'acierto':>8s}")
bm = 2 * (d.p_mercado - d.y) ** 2
gp = d.dropna(subset=["p_pc"])
for v, n in (("28", "28 (sin cuota)"), ("A", "A: 28 + cuota como variable"), ("B", "B: parte de la cuota y corrige")):
    b = 2 * (d[f"p_{v}"] - d.y) ** 2
    bp = 2 * (gp[f"p_{v}"] - gp.y) ** 2
    print(f"{n:34s} {sig(bm - b):+14.2f}s {sig(2*(gp.p_pc-gp.y)**2 - bp):+18.2f}s "
          f"{((d[f'p_{v}'] > .5) == d.y).mean()*100:7.1f}%")
print(f"{'media de casas':34s} {'':15s} {sig(2*(gp.p_pc-gp.y)**2 - 2*(gp.p_mercado-gp.y)**2):+18.2f}s "
      f"{((d.p_mercado > .5) == d.y).mean()*100:7.1f}%")
print(f"(Pinnacle cierre: {len(gp)} partidos)")
print(f"\nCuánto se separa B del mercado: diferencia media {np.abs(d.p_B - d.p_mercado).mean()*100:.1f} puntos, "
      f"máxima {np.abs(d.p_B - d.p_mercado).max()*100:.1f}")

print("\nApostando 1 unidad con la cuota MEDIA al lado con valor:")
for v in ("A", "B"):
    for umbral in (0.0, 0.03, 0.05):
        vo = d[f"p_{v}"] * d["Avg>2.5"] - 1
        vu = (1 - d[f"p_{v}"]) * d["Avg<2.5"] - 1
        over, under = (vo > umbral) & (vo >= vu), (vu > umbral) & (vu > vo)
        ret = np.concatenate([(d.y[over] * d["Avg>2.5"][over] - 1).values,
                              ((1 - d.y[under]) * d["Avg<2.5"][under] - 1).values])
        if len(ret) >= 20:
            print(f"  {v} umbral {umbral:>3.0%}: {len(ret):5d} apuestas  rentabilidad {ret.mean()*100:+6.2f}% "
                  f"(±{ret.std(ddof=1)/np.sqrt(len(ret))*100:.2f}, {sig(ret):+.2f}s)")
        else:
            print(f"  {v} umbral {umbral:>3.0%}: {len(ret)} apuestas (no apuesta casi nunca)")
