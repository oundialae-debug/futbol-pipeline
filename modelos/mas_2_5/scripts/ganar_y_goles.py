"""
¿Quién gana dice cuántos goles habrá? (idea del usuario, 24/09/2026)

Dato: gana el local -> 63% Más 2.5; gana el visitante -> 60%; empate -> 27%.

Base: las 28 de producción MENOS puntos y pases (19 rasgos).
V1  goles cuando gana: de las últimas 10 victorias del local EN CASA, qué
    parte acabó en Más 2.5 (y del visitante FUERA). Contraída hacia la tasa
    de la liga con K=5 victorias ficticias.
V2  minimodelo 1X2: regresión logística con el Elo, el % de victorias del
    local en sus últimos 10 en casa y el del visitante en sus últimos 10 fuera
    (contraídos igual). Se ajusta SOLO con partidos de entrenamiento.
C   combinada: P(gana local)*V1_local + P(gana visitante)*V1_visitante
    + P(empate)*tasa de Más 2.5 en empates de la liga.
Todo con información anterior al partido (se lee y DESPUÉS se actualiza).
"""
import sys, io, contextlib, time, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
from collections import defaultdict, deque
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression

t0 = time.time()
src = open("scripts/anadir_una_a_una.py", encoding="utf-8").read().split("BASE28 = ")[0]
with contextlib.redirect_stdout(io.StringIO()):
    exec(src)

K, VENT = 5.0, 10


def ganar_y_goles(hist):
    orden = hist.assign(_f=pd.to_datetime(hist.fecha, format="mixed", utc=True)).sort_values("_f")
    over_win = {}                 # (equipo, en_casa) -> deque de over en sus victorias
    res = {}                      # (equipo, en_casa) -> deque de 1 si ganó
    liga = defaultdict(lambda: [0, 0, 0, 0, 0, 0])   # over_win_n, over_win_k, pgcasa_n, k, pgfuera_n, k
    empate = defaultdict(lambda: [0, 0])             # liga -> [empates, over en empates]
    filas = []
    for f in orden.itertuples(index=False):
        L = liga[f.liga_id]
        p_ow = L[1] / L[0] if L[0] else 0.62
        p_hc = L[3] / L[2] if L[2] else 0.44
        p_af = L[5] / L[4] if L[4] else 0.30
        e = empate[f.liga_id]
        dl, dv = over_win.get((f.local_id, 1), ()), over_win.get((f.visitante_id, 0), ())
        rl, rv = res.get((f.local_id, 1), ()), res.get((f.visitante_id, 0), ())
        filas.append({
            "match_id": f.match_id,
            "loc_over_si_gana": (sum(dl) + K * p_ow) / (len(dl) + K),
            "vis_over_si_gana": (sum(dv) + K * p_ow) / (len(dv) + K),
            "loc_pg_casa": (sum(rl) + K * p_hc) / (len(rl) + K),
            "vis_pg_fuera": (sum(rv) + K * p_af) / (len(rv) + K),
            "over_en_empate_liga": (e[1] + K * 0.27) / (e[0] + K),
        })
        gl, gv = f.goles_l, f.goles_v
        if pd.isna(gl) or pd.isna(gv):
            continue
        over = float(gl + gv > 2.5)
        res.setdefault((f.local_id, 1), deque(maxlen=VENT)).append(float(gl > gv))
        res.setdefault((f.visitante_id, 0), deque(maxlen=VENT)).append(float(gv > gl))
        L[2] += 1; L[3] += gl > gv; L[4] += 1; L[5] += gv > gl
        if gl > gv:
            over_win.setdefault((f.local_id, 1), deque(maxlen=VENT)).append(over)
            L[0] += 1; L[1] += over
        elif gv > gl:
            over_win.setdefault((f.visitante_id, 0), deque(maxlen=VENT)).append(over)
            L[0] += 1; L[1] += over
        else:
            e[0] += 1; e[1] += over
    return pd.DataFrame(filas)


def comprobar_sin_fuga(hist):
    base = ganar_y_goles(hist).set_index("match_id")
    obj = hist.match_id.iloc[len(hist) * 3 // 4]
    tr = hist.copy()
    tr.loc[tr.match_id == obj, ["goles_l", "goles_v"]] = [7, 0]
    b2 = ganar_y_goles(tr).set_index("match_id")
    igual = np.allclose(base.loc[obj].values, b2.loc[obj].values)
    movido = (base.fillna(-9) != b2.fillna(-9)).any(axis=1).sum()
    return igual and movido > 0, f"propio partido igual: {igual}; filas posteriores que cambian: {movido}"


ok, det = comprobar_sin_fuga(hist)
print(f"FUGA: {'pasa' if ok else 'FALLA'} -- {det}")
if not ok:
    sys.exit(1)
bc = bc.merge(ganar_y_goles(hist), on="match_id", how="left")
bc["dif_over_si_gana"] = bc.loc_over_si_gana - bc.vis_over_si_gana
fechas = pd.to_datetime(bc.fecha, utc=True)
con_obj = bc.goles_l.notna() & bc.goles_v.notna()
sel = bc.set_index("match_id").loc[sel.match_id].reset_index()
prueba = bc.set_index("match_id").loc[prueba.match_id].reset_index()
ent_sel = bc[con_obj & (fechas < pd.to_datetime(sel.fecha.min(), utc=True))]
ent_fin = bc[con_obj & (fechas <= CORTE)]

MINI = ["dif_elo", "loc_pg_casa", "vis_pg_fuera"]


def con_minimodelo(ent, *dfs):
    """Ajusta el 1X2 SOLO con `ent` y añade P(local/empate/visitante) + combinada."""
    e = ent.dropna(subset=MINI)
    lr = LogisticRegression(max_iter=1000).fit(e[MINI].values, e["resultado"].values.astype(int))
    out = []
    for d in dfs:
        d = d.copy()
        p = lr.predict_proba(d[MINI].fillna(e[MINI].mean()).values)
        d["mm_p_local"], d["mm_p_empate"], d["mm_p_visit"] = p[:, 0], p[:, 1], p[:, 2]
        d["mm_over_combinada"] = (d.mm_p_local * d.loc_over_si_gana + d.mm_p_visit * d.vis_over_si_gana
                                  + d.mm_p_empate * d.over_en_empate_liga)
        out.append(d)
    return out


BASE28 = R.columnas_produccion(bc)
BASE19 = [c for c in BASE28 if "total_passes" not in c and "m_puntos" not in c]
assert len(BASE19) == 19, len(BASE19)
V1 = ["loc_over_si_gana", "vis_over_si_gana", "dif_over_si_gana"]
V2 = ["mm_p_local", "mm_p_empate", "mm_p_visit"]
CFG = {"28 (actual)": BASE28, "19 (sin puntos ni pases)": BASE19,
       "19 + V1 goles si gana": BASE19 + V1, "19 + V2 minimodelo": BASE19 + V2,
       "19 + combinada": BASE19 + ["mm_over_combinada"],
       "19 + V1 + V2 + combinada": BASE19 + V1 + V2 + ["mm_over_combinada"],
       "28 + V1 goles si gana": BASE28 + V1, "28 + V2 minimodelo": BASE28 + V2,
       "28 + combinada": BASE28 + ["mm_over_combinada"]}

# ¿cuánto acierta el minimodelo 1X2 por sí solo? (en la prueba)
ent_m, prueba_m = con_minimodelo(ent_fin, ent_fin, prueba)
acierto_1x2 = (prueba_m[["mm_p_local", "mm_p_empate", "mm_p_visit"]].values.argmax(1)
               == prueba_m.resultado.values).mean()
from sklearn.metrics import roc_auc_score
print(f"minimodelo 1X2 en la prueba: acierta el ganador el {acierto_1x2*100:.1f}%")
print(f"combinada SOLA como probabilidad de Más 2.5: AUC {roc_auc_score(prueba_m.mas_2_5, prueba_m.mm_over_combinada):.3f} "
      f"(0.5 = azar)\n")

ent_s, sel_m = con_minimodelo(ent_sel, ent_sel, sel)
ent_f, pru_m = con_minimodelo(ent_fin, ent_fin, prueba)
y_s, y = sel_m[OBJ].values.astype(int), pru_m[OBJ].values.astype(int)
pmer = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS[OBJ])
pm = pmer.reindex(pru_m.match_id).values
cc = ~np.isnan(pm)
bm = 2 * (pm - y) ** 2
ref_s = ref_p = None
print(f"{'modelo':28s} {'rasgos':>6s} | {'selección vs 28':>15s} | {'prueba vs 28':>12s} {'vs mercado':>11s} {'acierto':>8s}")
for n, c in CFG.items():
    bs = 2 * (predecir(c, ent_s, sel_m) - y_s) ** 2
    pp = predecir(c, ent_f, pru_m)
    bp = 2 * (pp - y) ** 2
    if ref_s is None:
        ref_s, ref_p = bs, bp
    print(f"{n:28s} {len(c):6d} | {sig(ref_s - bs) if bs is not ref_s else 0:+14.2f}s | "
          f"{sig(ref_p - bp) if bp is not ref_p else 0:+11.2f}s {sig(bm[cc] - bp[cc]):+10.2f}s "
          f"{((pp[cc] > .5) == y[cc]).mean()*100:7.1f}%")
print(f"{'mercado':28s} {'':6s} | {'':15s} | {'':12s} {'':11s} {((pm[cc] > .5) == y[cc]).mean()*100:7.1f}%")
print(f"\n({time.time()-t0:.0f}s)")
