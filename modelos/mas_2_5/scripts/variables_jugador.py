"""
Variables de jugador sobre el mejor modelo (XGBoost 28), 25/09/2026.

1. impacto_xg: para cada titular, xG a favor y en contra de SU equipo en sus
   titularidades ANTERIORES (contraído hacia la media global con K=5); media
   del once. loc/vis/dif. Solo cuenta partidos con xG.
2. impacto_goles: lo mismo con goles.
3. lesiones: fracción del peso del equipo que está lesionado el día del
   partido. Peso de cada jugador = sus titularidades ANTERIORES con ese
   equipo (no los minutos de toda la temporada, que usaba el índice del repo
   1x2 y mete información futura). Solo La Liga y Segunda (lesiones copiadas
   de 1x2 en data/de_1x2/). OJO: esa lista cubre ~20 jugadores por equipo
   elegidos por minutos de la temporada entera -- sesgo de selección pequeño.
Todo en orden cronológico: se lee el estado y DESPUÉS se actualiza.

Evaluación: mes a mes (ago 2025 - sep 2026), cada config contra el 28 solo y
contra la media de casas (football-data). Lesiones, además, solo en España.
"""
import sys, io, glob, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
from collections import defaultdict
import numpy as np, pandas as pd
import modelo_xgboost as M, rasgos_mas25 as R, evaluar_mercados as EM

K = 5.0
LES = pd.concat([pd.read_csv(f) for f in glob.glob("data/de_1x2/*_lesiones.csv")]).drop_duplicates()
LES["desde"] = pd.to_datetime(LES.fromDate, format="%d.%m.%Y", errors="coerce")
LES["hasta"] = pd.to_datetime(LES.toDate, format="%d.%m.%Y", errors="coerce").fillna(pd.Timestamp("2100-01-01"))
LES = LES.dropna(subset=["desde"])
por_jug = {j: g[["desde", "hasta"]].values for j, g in LES.groupby("player_id")}
LIGAS_LES = {"La Liga", "Segunda"}


def variables(hist):
    o = hist.assign(fdt=pd.to_datetime(hist.fecha, format="mixed", utc=True)).sort_values("fdt")
    acc = {k: defaultdict(lambda: [0.0, 0.0]) for k in ("xgf", "xgc", "gf", "gc")}   # jugador -> [suma, n]
    glob_ = {k: [0.0, 0.0] for k in acc}
    titular = defaultdict(lambda: defaultdict(int))      # equipo -> jugador -> titularidades previas
    filas = []
    for f in o.itertuples(index=False):
        r = {"match_id": f.match_id}
        dia = f.fdt.tz_localize(None)
        lados = (("loc", getattr(f, "local_ids", np.nan), f.local_id),
                 ("vis", getattr(f, "visitante_ids", np.nan), f.visitante_id))
        for lado, ids, eq in lados:
            js = [int(x) for x in ids.split("|")] if isinstance(ids, str) else []
            for k in acc:
                g = glob_[k][0] / glob_[k][1] if glob_[k][1] else np.nan
                v = [(acc[k][j][0] + K * g) / (acc[k][j][1] + K) for j in js] if js and not np.isnan(g) else []
                r[f"{lado}_imp_{k}"] = float(np.mean(v)) if v else np.nan
            if f.liga in LIGAS_LES and titular[eq]:
                peso = titular[eq]
                tot = sum(peso.values())
                les = sum(w for j, w in peso.items()
                          if j in por_jug and any((a <= dia) & (dia <= b) for a, b in por_jug[j]))
                r[f"{lado}_les"] = les / tot if tot else np.nan
            else:
                r[f"{lado}_les"] = np.nan
        for k in list(acc) + ["les"]:
            r[f"dif_imp_{k}" if k != "les" else "dif_les"] = (r[f"loc_imp_{k}"] - r[f"vis_imp_{k}"]) if k != "les" \
                else r["loc_les"] - r["vis_les"]
        filas.append(r)
        # actualizar DESPUÉS de leer
        if pd.isna(f.goles_l) or pd.isna(f.goles_v):
            continue
        xl, xv = getattr(f, "l_expected_goals", np.nan), getattr(f, "v_expected_goals", np.nan)
        for (lado, ids, eq), mis, sus, mxg, sxg in ((lados[0], f.goles_l, f.goles_v, xl, xv),
                                                    (lados[1], f.goles_v, f.goles_l, xv, xl)):
            if not isinstance(ids, str):
                continue
            vals = {"gf": mis, "gc": sus}
            if pd.notna(mxg) and pd.notna(sxg):
                vals.update(xgf=float(mxg), xgc=float(sxg))
            for j in (int(x) for x in ids.split("|")):
                titular[eq][j] += 1
                for k, v in vals.items():
                    acc[k][j][0] += v; acc[k][j][1] += 1
            for k, v in vals.items():
                glob_[k][0] += v; glob_[k][1] += 1
    return pd.DataFrame(filas)


with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
hist["l_expected_goals"] = pd.to_numeric(hist.get("l_expected_goals"), errors="coerce")
hist["v_expected_goals"] = pd.to_numeric(hist.get("v_expected_goals"), errors="coerce")

# ---- fuga: trucar UN partido no mueve sus variables; sí las posteriores ----
v1 = variables(hist).set_index("match_id")
con = v1.loc_imp_xgf.notna() & v1.loc_les.notna()
obj = v1.index[con][len(v1.index[con]) // 2]
tr = hist.copy()
tr.loc[tr.match_id == obj, ["goles_l", "goles_v", "l_expected_goals", "v_expected_goals"]] = [8, 0, 6.0, 0.1]
v2 = variables(tr).set_index("match_id")
propio = np.allclose(v1.loc[obj].fillna(-9).values, v2.loc[obj].fillna(-9).values)
cambian = (v1.fillna(-9) != v2.fillna(-9)).any(axis=1).sum()
print(f"FUGA: {'pasa' if propio and cambian > 1 else 'FALLA'} (propio igual: {propio}; filas que cambian: {cambian})")
assert propio and cambian > 1

fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"), pd.read_csv("data/historico_h2h_profundo.csv"))
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(v1.reset_index(), on="match_id", how="left") \
    .merge(fd[["match_id", "p_mercado"]], on="match_id").merge(hist[["match_id", "liga"]], on="match_id")
f = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = f.dt.strftime("%Y-%m")
tri = lambda *ks: [f"{p}_{k}" for k in ks for p in ("loc", "vis", "dif")]
C28 = R.columnas_produccion(bc)
CFG = {"28": C28, "28 + impacto xG": C28 + tri("imp_xgf", "imp_xgc"),
       "28 + impacto goles": C28 + tri("imp_gf", "imp_gc"),
       "28 + impacto xG y goles": C28 + tri("imp_xgf", "imp_xgc", "imp_gf", "imp_gc"),
       "28 + lesiones": C28 + tri("les")}
print("Cobertura en la evaluación: impacto xG "
      f"{bc.loc[f >= '2025-08-01', 'loc_imp_xgf'].notna().mean()*100:.0f}%, lesiones (España) "
      f"{bc.loc[(f >= '2025-08-01') & bc.liga.isin(LIGAS_LES), 'loc_les'].notna().mean()*100:.0f}%")


def pred(cols, ent, val):
    y = ent.mas_2_5.values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s), val[cols].values, 2)[:, 1]
                    for s in EM.SEMILLAS], axis=0)


ev = bc[f >= "2025-08-01"]
res = []
for mes in sorted(ev.mes.unique()):
    val, ent = ev[ev.mes == mes], bc[f < pd.Timestamp(mes + "-01", tz="UTC")]
    r = pd.DataFrame({"y": val.mas_2_5.values, "pm": val.p_mercado.values, "liga": val.liga.values})
    for n, c in CFG.items():
        r[n] = pred(c, ent, val)
    res.append(r)
d = pd.concat(res, ignore_index=True)
d.to_csv("data/variables_jugador.csv", index=False)
sig = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
for nombre, g in (("TODAS LAS LIGAS", d), ("SOLO LA LIGA Y SEGUNDA", d[d.liga.isin(LIGAS_LES)])):
    bm, b28 = 2 * (g.pm - g.y) ** 2, 2 * (g["28"] - g.y) ** 2
    print(f"\n{nombre} (n={len(g)}). Positivo = mejor.")
    print(f"{'modelo':28s} {'vs 28':>7s} {'vs media casas':>15s} {'acierto':>8s}")
    for n in CFG:
        b = 2 * (g[n] - g.y) ** 2
        print(f"{n:28s} {sig(b28 - b) if n != '28' else 0:+6.2f}s {sig(bm - b):+14.2f}s "
              f"{((g[n] > .5) == g.y).mean()*100:7.1f}%")
