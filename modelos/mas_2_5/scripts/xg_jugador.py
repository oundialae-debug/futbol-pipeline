"""
xG y xA POR JUGADOR (de /box-score, descargados por el otro chat, main:
data/historico_xg_jugador.csv) sobre el mejor modelo, 28/09/2026.

Solo existen desde abril de 2025. Variable, en orden cronológico y sin
mirar el partido que se predice:
  para cada titular, xG/90 y xA/90 con sus minutos ANTERIORES (desde abr 2025),
  contraídos hacia la media de su posición con 270 minutos ficticios;
  por equipo: suma del once de xG/90 y de xA/90 (loc/vis/dif, 6 columnas).
Vacíos: xG vacío sin tiros = 0; xG vacío CON tiros = desconocido (no cuenta).
Igual con xA y pases clave.

Fijado antes de mirar: evaluación mes a mes de oct 2025 a sep 2026 (antes los
jugadores apenas tienen historial), contra el 28 fijo y la media de casas.
Configs: 28 | 28 + xG/xA jugador | 28 con xG/xA EN LUGAR de g/a.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
from collections import defaultdict
import numpy as np, pandas as pd
import modelo_xgboost as M, rasgos_mas25 as R, evaluar_mercados as EM

K_MIN = 270.0
x = pd.read_csv("data/historico_xg_jugador.csv")
x = x[(x.minutos > 0) & x.jugador_id.notna()].copy()
x["xg"] = np.where(x.expectedGoals.notna(), x.expectedGoals,
                   np.where(x.shotsTotal.fillna(0) == 0, 0.0, np.nan))
x["xa"] = np.where(x.expectedAssists.notna(), x.expectedAssists,
                   np.where(x.passesKey.fillna(0) == 0, 0.0, np.nan))
x["jugador_id"] = x.jugador_id.astype(int)
por_partido = {m: g for m, g in x.groupby("match_id")}
pos_jug = x.groupby("jugador_id").posicion.agg(lambda s: s.mode().iloc[0])


def variables(hist):
    o = hist.assign(fdt=pd.to_datetime(hist.fecha, format="mixed", utc=True)).sort_values("fdt")
    acc = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])        # jugador -> xg, min_xg, xa, min_xa
    pos_acc = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])    # posición -> igual
    filas = []
    for f in o.itertuples(index=False):
        r = {"match_id": f.match_id}
        for lado, ids in (("loc", getattr(f, "local_ids", np.nan)), ("vis", getattr(f, "visitante_ids", np.nan))):
            if not isinstance(ids, str) or not acc:
                r[f"{lado}_xg90"] = r[f"{lado}_xa90"] = np.nan
                continue
            sx = sa = 0.0
            for j in (int(v) for v in ids.split("|")):
                p = pos_acc[pos_jug.get(j, "Midfielder")]
                mx = p[0] / p[1] * 90 if p[1] else 0.1
                ma = p[2] / p[3] * 90 if p[3] else 0.05
                a = acc.get(j, [0, 0, 0, 0])
                sx += (a[0] + K_MIN / 90 * mx) / ((a[1] + K_MIN) / 90)
                sa += (a[2] + K_MIN / 90 * ma) / ((a[3] + K_MIN) / 90)
            r[f"{lado}_xg90"], r[f"{lado}_xa90"] = sx, sa
        r["dif_xg90"] = r["loc_xg90"] - r["vis_xg90"]
        r["dif_xa90"] = r["loc_xa90"] - r["vis_xa90"]
        filas.append(r)
        g = por_partido.get(f.match_id)            # actualizar DESPUÉS de leer
        if g is not None:
            for t in g.itertuples(index=False):
                a, p = acc[t.jugador_id], pos_acc[t.posicion]
                if not np.isnan(t.xg):
                    a[0] += t.xg; a[1] += t.minutos; p[0] += t.xg; p[1] += t.minutos
                if not np.isnan(t.xa):
                    a[2] += t.xa; a[3] += t.minutos; p[2] += t.xa; p[3] += t.minutos
    return pd.DataFrame(filas)


with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
v1 = variables(hist).set_index("match_id")
# fuga: quitar del fichero el box-score de UN partido no debe mover SUS variables
obj = v1.index[v1.loc_xg90.notna()][len(v1.index[v1.loc_xg90.notna()]) * 3 // 4]
guard = por_partido.pop(obj)
v2 = variables(hist).set_index("match_id")
por_partido[obj] = guard
propio = np.allclose(v1.loc[obj].values, v2.loc[obj].values, equal_nan=True)
cambian = (v1.fillna(-9) != v2.fillna(-9)).any(axis=1).sum()
print(f"FUGA: {'pasa' if propio and cambian > 0 else 'FALLA'} (propio igual: {propio}; posteriores que cambian: {cambian})")
assert propio and cambian > 0

fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"), pd.read_csv("data/historico_h2h_profundo.csv"))
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(v1.reset_index(), on="match_id", how="left") \
    .merge(fd[["match_id", "p_mercado", "Avg>2.5", "Avg<2.5"]], on="match_id")
bc["f"] = pd.to_datetime(bc.fecha, utc=True)
bc["mes"] = bc.f.dt.strftime("%Y-%m")
C28 = R.columnas_produccion(bc)
XGJ = [f"{p}_{k}" for k in ("xg90", "xa90") for p in ("loc", "vis", "dif")]
CFG = {"28": C28, "28 + xG/xA jugador": C28 + XGJ,
       "28 con xG/xA en lugar de g/a": [c for c in C28 if "_cp_" not in c] + XGJ}
ev = bc[bc.f >= "2025-10-01"]
print(f"Cobertura de la variable en la evaluación: {ev.loc_xg90.notna().mean()*100:.0f}%")


def pred(cols, ent, val):
    y = ent.mas_2_5.values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s), val[cols].values, 2)[:, 1]
                    for s in EM.SEMILLAS], axis=0)


res = []
for mes in sorted(ev.mes.unique()):
    val, ent = ev[ev.mes == mes], bc[bc.f < pd.Timestamp(mes + "-01", tz="UTC")]
    r = pd.DataFrame({"y": val.mas_2_5.values, "pm": val.p_mercado.values,
                      "o": val["Avg>2.5"].values, "u": val["Avg<2.5"].values})
    for n, c in CFG.items():
        r[n] = pred(c, ent, val)
    res.append(r)
d = pd.concat(res, ignore_index=True)
d.to_csv("data/xg_jugador.csv", index=False)
sig = lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
bm, b28 = 2 * (d.pm - d.y) ** 2, 2 * (d["28"] - d.y) ** 2
print(f"\n{len(d)} partidos, oct 2025 - sep 2026, mes a mes. Positivo = mejor.")
print(f"{'modelo':30s} {'vs 28':>7s} {'vs casa':>8s} {'acierto':>8s} {'apostando (cuota media)':>26s}")
for n in CFG:
    b = 2 * (d[n] - d.y) ** 2
    vo, vu = d[n] * d.o - 1, (1 - d[n]) * d.u - 1
    ov, un = (vo > 0) & (vo >= vu), (vu > 0) & (vu > vo)
    ret = np.r_[(d.y[ov] * d.o[ov] - 1).values, ((1 - d.y[un]) * d.u[un] - 1).values]
    print(f"{n:30s} {sig(b28 - b) if n != '28' else 0:+6.2f}s {sig(bm - b):+7.2f}s "
          f"{((d[n] > .5) == d.y).mean()*100:7.1f}% {ret.mean()*100:+9.2f}% (±{ret.std(ddof=1)/np.sqrt(len(ret))*100:.2f}, {len(ret)})")
print(f"{'casa':30s} {'':7s} {'':8s} {((d.pm > .5) == d.y).mean()*100:7.1f}%")
