"""
Valor de mercado del once y temporada 2022/23 (29/09/2026), sobre el mejor
modelo: C = mezcla 50/50 de XGBoost 28 y logística (suma xG+xA, tiros, g/a).

Nuevos datos (main, otro chat): jugador_valor_mercado.csv (historial de valor
con fechas) y 2022/23 en el histórico (sin alineaciones).

valor_suma: log(1 + suma del valor de los 22 titulares), usando para cada
jugador su ÚLTIMO valor con fecha ANTERIOR al partido (sin información futura).
Una sola columna: para Más 2.5 importa la suma de los dos equipos.

Fijado antes de mirar, mismo periodo que xg_jugador.py (oct 2025 - sep 2026):
  C             referencia (entrenamiento sin 2022/23)
  C +2022/23    mismo modelo, entrenamiento con 2022/23
  C'            valor_suma dentro de la logística
  C' +2022/23
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

src = open("scripts/xg_jugador.py", encoding="utf-8").read().split("with contextlib.redirect_stdout")[0]
exec(src)                                   # variables() de xG/xA por jugador
import modelo_xgboost as M, rasgos_mas25 as R, evaluar_mercados as EM

with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
hist["fdt"] = pd.to_datetime(hist.fecha, format="mixed", utc=True).dt.tz_localize(None)

# ---- valor de mercado del once a la fecha del partido ----
vm = pd.read_csv("data/jugador_valor_mercado.csv").dropna(subset=["fecha", "valor"])
vm["fecha"] = pd.to_datetime(vm.fecha, errors="coerce")
vm = vm.dropna(subset=["fecha"]).astype({"jugador_id": int}).sort_values("fecha")
tit = []
for f in hist.itertuples(index=False):
    for ids in (getattr(f, "local_ids", np.nan), getattr(f, "visitante_ids", np.nan)):
        if isinstance(ids, str):
            tit += [(f.match_id, f.fdt - pd.Timedelta(days=1), int(j)) for j in ids.split("|")]
tit = pd.DataFrame(tit, columns=["match_id", "fecha", "jugador_id"]).sort_values("fecha")
tit = pd.merge_asof(tit, vm[["fecha", "jugador_id", "valor"]], on="fecha", by="jugador_id",
                    direction="backward", allow_exact_matches=True)
agg = tit.groupby("match_id").agg(valor_total=("valor", "sum"), conocidos=("valor", "count"), n=("jugador_id", "size"))
agg["valor_suma"] = np.log1p(agg.valor_total * agg.n / agg.conocidos.clip(lower=1))   # escalado a 22 si faltan
agg.loc[agg.conocidos < 11, "valor_suma"] = np.nan
print(f"valor del once: {agg.valor_suma.notna().sum()} partidos con dato; titulares con valor "
      f"{tit.valor.notna().mean()*100:.0f}%")
# fuga: el valor usado nunca tiene fecha posterior al partido (merge_asof backward, día anterior)

v1 = variables(hist)
fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
bc = R.construir(hist.drop(columns=["fdt"]), pd.read_csv("data/historico_jugador_stats.csv"),
                 pd.read_csv("data/historico_h2h_profundo.csv"))
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(v1, on="match_id", how="left") \
    .merge(agg[["valor_suma"]].reset_index(), on="match_id", how="left") \
    .merge(fd[["match_id", "p_mercado", "Avg>2.5", "Avg<2.5"]], on="match_id") \
    .merge(hist[["match_id", "temporada"]], on="match_id")
bc["f"] = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = bc.f.dt.strftime("%Y-%m")
bc["xga_suma"] = bc.loc_xg90 + bc.vis_xg90 + bc.loc_xa90 + bc.vis_xa90
bc["tiros_suma"] = (bc.loc_m_shots_on_target + bc.vis_m_shots_on_target
                    + bc.loc_m_contra_shots_on_target + bc.vis_m_contra_shots_on_target)
bc["ga_suma"] = bc.loc_cp_del_ga90 + bc.vis_cp_del_ga90
C28 = R.columnas_produccion(bc)
ev = bc[bc.f >= "2025-10-01"]
print(f"valor_suma en la evaluación: {ev.valor_suma.notna().mean()*100:.0f}%; "
      f"correlación con total de goles: {ev.valor_suma.corr(ev.goles_l + ev.goles_v):+.3f}")


def xgb(ent, val):
    y = ent.mas_2_5.values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[C28].values, y, 2, semilla=s), val[C28].values, 2)[:, 1]
                    for s in EM.SEMILLAS], axis=0)


def logistica(ent, val, cols):
    e = ent.dropna(subset=cols)
    sc = StandardScaler().fit(e[cols])
    lr = LogisticRegression().fit(sc.transform(e[cols]), e.mas_2_5.astype(int))
    return lr.predict_proba(sc.transform(val[cols].fillna(e[cols].mean())))[:, 1]


L0, L1 = ["xga_suma", "tiros_suma", "ga_suma"], ["xga_suma", "tiros_suma", "ga_suma", "valor_suma"]
res = []
for mes in sorted(ev.mes.unique()):
    val = ev[ev.mes == mes]
    ent_all = bc[bc.f < pd.Timestamp(mes + "-01", tz="UTC")]
    ent_sin = ent_all[ent_all.temporada != 2022]
    r = pd.DataFrame({"y": val.mas_2_5.values, "pm": val.p_mercado.values,
                      "o": val["Avg>2.5"].values, "u": val["Avg<2.5"].values})
    x_sin, x_con = xgb(ent_sin, val), xgb(ent_all, val)
    r["C"] = (x_sin + logistica(ent_sin, val, L0)) / 2
    r["C +2022/23"] = (x_con + logistica(ent_all, val, L0)) / 2
    r["C' (con valor)"] = (x_sin + logistica(ent_sin, val, L1)) / 2
    r["C' +2022/23"] = (x_con + logistica(ent_all, val, L1)) / 2
    r["28 solo"] = x_sin
    res.append(r)
d = pd.concat(res, ignore_index=True)
d.to_csv("data/valor_y_2022.csv", index=False)
sig = lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
bm, bC = 2 * (d.pm - d.y) ** 2, 2 * (d["C"] - d.y) ** 2
print(f"\n{len(d)} partidos, oct 2025 - sep 2026, mes a mes. Positivo = mejor.")
print(f"{'modelo':18s} {'vs C':>7s} {'vs casa':>8s} {'acierto':>8s} {'apostando (cuota media)':>26s}")
for n in ("28 solo", "C", "C +2022/23", "C' (con valor)", "C' +2022/23"):
    b = 2 * (d[n] - d.y) ** 2
    vo, vu = d[n] * d.o - 1, (1 - d[n]) * d.u - 1
    ov, un = (vo > 0) & (vo >= vu), (vu > 0) & (vu > vo)
    ret = np.r_[(d.y[ov] * d.o[ov] - 1).values, ((1 - d.y[un]) * d.u[un] - 1).values]
    print(f"{n:18s} {sig(bC - b) if n != 'C' else 0:+6.2f}s {sig(bm - b):+7.2f}s "
          f"{((d[n] > .5) == d.y).mean()*100:7.1f}% {ret.mean()*100:+9.2f}% (±{ret.std(ddof=1)/np.sqrt(len(ret))*100:.2f}, {len(ret)})")
print(f"{'casa':18s} {'':7s} {'':8s} {((d.pm > .5) == d.y).mean()*100:7.1f}%")
