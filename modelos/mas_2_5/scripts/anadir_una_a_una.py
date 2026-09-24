"""
Añadir variables UNA A UNA sobre el modelo de 28 rasgos (petición del
usuario, 24/09/2026): se prueba cada una en el orden pedido; si baja el
Brier medio del tramo de selección se queda, si no se quita y se sigue.
Al final, UNA mirada a la prueba final: modelo resultante contra el de 28 y
contra el mercado. Mismos tramos y 5 semillas que seleccion_combinaciones.py.
"""
import sys, io, contextlib, time, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
from collections import defaultdict, deque
import numpy as np, pandas as pd
import rasgos, rasgos_mas25 as R, modelo_xgboost as M, evaluar_mercados as EM

t0 = time.time()
OBJ = "mas_2_5"
with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
# box-score: solo para esta prueba, leído del repo padre (no se copia a la carpeta)
box = pd.read_csv("../../data/historico_boxscore.csv")
hist = hist.merge(box, on="match_id", how="left")
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"),
                 pd.read_csv("data/historico_h2h_profundo.csv"))
G = R.grupos(bc)
GR = rasgos.grupos_rasgo(bc)


def arbitro_goles_v20(hist, ventana=20):
    orden = hist.assign(_f=pd.to_datetime(hist.fecha, format="mixed", utc=True)).sort_values("_f")
    dq, n_glob, s_glob, filas = {}, 0, 0.0, []
    for f in orden.itertuples(index=False):
        arb = getattr(f, "arbitro", np.nan)
        media = s_glob / n_glob if n_glob else 2.7
        if pd.notna(arb) and dq.get(arb):
            filas.append((f.match_id, float(np.mean(dq[arb])), len(dq[arb])))
        else:
            filas.append((f.match_id, media, 0))
        if pd.notna(f.goles_l) and pd.notna(f.goles_v):
            g = f.goles_l + f.goles_v
            n_glob += 1; s_glob += g
            if pd.notna(arb):
                dq.setdefault(arb, deque(maxlen=ventana)).append(g)
    return pd.DataFrame(filas, columns=["match_id", "arbv20_goles_media", "arbv20_previos"])


def impacto_jugador(hist):
    orden = hist.assign(_f=pd.to_datetime(hist.fecha, format="mixed", utc=True)).sort_values("_f")
    h, filas = defaultdict(list), []

    def medias(ids):
        if pd.isna(ids):
            return np.nan, np.nan, 0
        gf = [np.mean([x[0] for x in h[int(j)]]) for j in ids.split("|") if h.get(int(j))]
        gc = [np.mean([x[1] for x in h[int(j)]]) for j in ids.split("|") if h.get(int(j))]
        return (float(np.mean(gf)), float(np.mean(gc)), len(gf)) if gf else (np.nan, np.nan, 0)

    for f in orden.itertuples(index=False):
        l, v = medias(getattr(f, "local_ids", np.nan)), medias(getattr(f, "visitante_ids", np.nan))
        filas.append({"match_id": f.match_id,
                      "loc_imp_gf": l[0], "vis_imp_gf": v[0], "dif_imp_gf": l[0] - v[0],
                      "loc_imp_gc": l[1], "vis_imp_gc": v[1], "dif_imp_gc": l[1] - v[1],
                      "loc_imp_n": l[2], "vis_imp_n": v[2]})
        if pd.notna(f.goles_l) and pd.notna(f.goles_v):
            for ids, gf, gc in ((getattr(f, "local_ids", np.nan), f.goles_l, f.goles_v),
                                (getattr(f, "visitante_ids", np.nan), f.goles_v, f.goles_l)):
                if pd.notna(ids):
                    for j in ids.split("|"):
                        h[int(j)].append((gf, gc))
    return pd.DataFrame(filas)


def tabla_goles(hist):
    orden = hist.assign(_f=pd.to_datetime(hist.fecha, format="mixed", utc=True)).sort_values("_f")
    tablas, filas = {}, []
    for f in orden.itertuples(index=False):
        t = tablas.setdefault((f.liga_id, f.temporada), {})
        gfl, gcl, pl = t.get(f.local_id, (0, 0, 0))
        gfv, gcv, pv = t.get(f.visitante_id, (0, 0, 0))
        r = {"match_id": f.match_id,
             "loc_tg_gfpg": gfl / pl if pl else np.nan, "vis_tg_gfpg": gfv / pv if pv else np.nan,
             "loc_tg_gcpg": gcl / pl if pl else np.nan, "vis_tg_gcpg": gcv / pv if pv else np.nan}
        r["dif_tg_gfpg"] = r["loc_tg_gfpg"] - r["vis_tg_gfpg"]
        r["dif_tg_gcpg"] = r["loc_tg_gcpg"] - r["vis_tg_gcpg"]
        filas.append(r)
        if pd.notna(f.goles_l) and pd.notna(f.goles_v):
            t[f.local_id] = (gfl + f.goles_l, gcl + f.goles_v, pl + 1)
            t[f.visitante_id] = (gfv + f.goles_v, gcv + f.goles_l, pv + 1)
    return pd.DataFrame(filas)


def formacion(hist):
    filas = []
    for f in hist.itertuples(index=False):
        r = {"match_id": f.match_id}
        for lado, col in (("loc", "local_formacion"), ("vis", "visitante_formacion")):
            try:
                ln = [int(x) for x in str(getattr(f, col, "")).split("-")]
                assert sum(ln) == 10 and len(ln) >= 2
                r[f"{lado}_fm_def"], r[f"{lado}_fm_del"] = ln[0], ln[-1]
                r[f"{lado}_fm_med"] = 10 - ln[0] - ln[-1]
            except (ValueError, AssertionError):
                r[f"{lado}_fm_def"] = r[f"{lado}_fm_del"] = r[f"{lado}_fm_med"] = np.nan
        for k in ("def", "med", "del"):
            r[f"dif_fm_{k}"] = r[f"loc_fm_{k}"] - r[f"vis_fm_{k}"]
        filas.append(r)
    return pd.DataFrame(filas)


for extra in (arbitro_goles_v20(hist), impacto_jugador(hist), tabla_goles(hist), formacion(hist)):
    bc = bc.merge(extra, on="match_id", how="left")
for p in ("loc", "vis"):
    bc[f"{p}_mom_puntos"] = bc[f"{p}_r_puntos"] - bc[f"{p}_m_puntos"]
    bc[f"{p}_mom_goles"] = bc[f"{p}_r_goles"] - bc[f"{p}_m_goles"]
for k in ("puntos", "goles"):
    bc[f"dif_mom_{k}"] = bc[f"loc_mom_{k}"] - bc[f"vis_mom_{k}"]
bc = bc.sort_values("fecha").reset_index(drop=True)

tri = lambda *cs: [f"{p}_{c}" for c in cs for p in ("loc", "vis", "dif")]
CANDIDATAS = [
    ("formacion", tri("fm_def", "fm_med", "fm_del")),
    ("arbitro_goles_v20", ["arbv20_goles_media", "arbv20_previos"]),
    ("impacto_jugador", tri("imp_gf", "imp_gc") + ["loc_imp_n", "vis_imp_n"]),
    ("goles", tri("m_goles", "m_goles_contra")),
    ("xg", tri("m_expected_goals", "m_contra_expected_goals")),
    ("posesion", tri("m_possession", "m_contra_possession")),
    ("centros", tri("m_crosses", "m_contra_crosses")),
    ("previos_descanso", tri("partidos_previos", "descanso")),
    ("forma3_momentum", tri("r_puntos", "r_goles", "mom_puntos", "mom_goles")),
    ("elo", G["elo"]),
    ("goles_temporada", tri("tg_gfpg", "tg_gcpg")),
    ("calidad_vieja", G["calidad_plantilla_vieja"]),
    ("porterias_cero", G["cp_defensa"]),
    ("minutos_conocidos", G["cp_minutos"]),
    ("rotacion", GR["rotacion"]),
    ("h2h_2anios", G["h2h_reciente"]),
    ("clima", GR["clima"]),
    ("boxscore", GR["boxscore"] + GR["duelos"]),
]
for n, c in CANDIDATAS:
    falta = [x for x in c if x not in bc.columns]
    assert c and not falta, f"{n}: faltan {falta[:5]}"

# ---------- tramos (idénticos a seleccion_combinaciones.py) ----------
CORTE = pd.Timestamp("2026-04-24", tz="UTC")
INICIO_2526 = pd.Timestamp("2025-07-01", tz="UTC")
INICIO_2627 = pd.Timestamp("2026-07-01", tz="UTC")
fechas = pd.to_datetime(bc.fecha, utc=True)
con_obj = bc["goles_l"].notna() & bc["goles_v"].notna()
fijo = (con_obj & (fechas >= INICIO_2526) & (bc.loc_cp_conocidos > 0) & (bc.vis_cp_conocidos > 0)
        & bc[G["base_cf"]].notna().all(axis=1) & bc[G["base_clasica"]].notna().all(axis=1))
antes = bc[fijo & (fechas <= CORTE)]
prueba = bc[fijo & (fechas > CORTE)]
sel = antes.iloc[-int(len(antes) * 0.25):]
ent_sel = bc[con_obj & (fechas < pd.to_datetime(sel.fecha.min(), utc=True))]
ent_fin = bc[con_obj & (fechas <= CORTE)]


def predecir(cols, ent, val):
    y = ent[OBJ].values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s),
                                     val[cols].values, 2)[:, 1] for s in EM.SEMILLAS], axis=0)


def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


ys = sel[OBJ].values.astype(int)
b_sel = lambda cols: 2 * (predecir(cols, ent_sel, sel) - ys) ** 2
BASE28 = R.columnas_produccion(bc)
actual = list(BASE28)
b_act = b_sel(actual)
print(f"Selección {len(sel)} partidos ({str(sel.fecha.min())[:10]} a {str(sel.fecha.max())[:10]}), "
      f"prueba {len(prueba)}. Punto de partida: {len(actual)} rasgos, Brier {b_act.mean():.4f}\n")
print(f"{'variable':20s} {'+cols':>5s} {'Brier con ella':>15s} {'vs actual':>10s}  decisión")
filas = []
for nombre, c in CANDIDATAS:
    nuevas = [x for x in c if x not in actual]
    b = b_sel(actual + nuevas)
    mejora = b.mean() < b_act.mean()
    print(f"{nombre:20s} {len(nuevas):5d} {b.mean():15.4f} {sig(b_act - b):+9.2f}s  "
          f"{'SE QUEDA' if mejora else 'fuera'}")
    filas.append({"variable": nombre, "cols": len(nuevas), "brier": b.mean(),
                  "sigmas": sig(b_act - b), "se_queda": mejora})
    if mejora:
        actual += nuevas; b_act = b
pd.DataFrame(filas).to_csv("data/anadir_una_a_una.csv", index=False)
quedan = [f["variable"] for f in filas if f["se_queda"]]
print(f"\nResultado: 28 + {quedan} = {len(actual)} rasgos  ({time.time()-t0:.0f}s)\n")

# ---------- prueba final, UNA vez ----------
y = prueba[OBJ].values.astype(int)
pmer = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS[OBJ])
pm = pmer.reindex(prueba.match_id).values
cc = ~np.isnan(pm)
bm = 2 * (pm - y) ** 2
ini = (pd.to_datetime(prueba.fecha, utc=True) >= INICIO_2627).values
bmed = 2 * (ent_fin[OBJ].mean() - y) ** 2
P = {"28 rasgos": predecir(BASE28, ent_fin, prueba), f"final ({len(actual)} rasgos)": predecir(actual, ent_fin, prueba)}
B = {n: 2 * (p - y) ** 2 for n, p in P.items()}
r28 = B["28 rasgos"]
print(f"PRUEBA FINAL: final 25/26 n={(~ini).sum()}, inicio 26/27 n={ini.sum()} ({cc.sum()} con cuota)")
for n, b in B.items():
    print(f"  {n:18s} final25/26 vs media {(1-b[~ini].mean()/bmed[~ini].mean())*100:+.2f}% | "
          f"inicio26/27 vs media {(1-b[ini].mean()/bmed[ini].mean())*100:+.2f}% | "
          f"vs 28 {sig(r28 - b) if b is not r28 else 0:+.2f}s | vs mercado {sig(bm[cc]-b[cc]):+.2f}s | "
          f"acierto {((P[n][cc] > .5) == y[cc]).mean()*100:.1f}%")
print(f"  mercado acierto {((pm[cc] > .5) == y[cc]).mean()*100:.1f}%")
print(f"\n({time.time()-t0:.0f}s)")
