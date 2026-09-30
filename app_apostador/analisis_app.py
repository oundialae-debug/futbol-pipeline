"""
Datos reales para 2yellow (LaLiga, ejemplo Real Madrid). Solo LEE data/.
Escribe app_apostador/datos_app.json. Sin API.

Cada bloque imprime una comprobación antes de dar el dato por bueno
(regla del proyecto: nada sin medir).

 1 bajas            peso de los lesionados en goles+asistencias, minutos y valor
 2 con/sin          puntos sobre lo esperado por Elo, con y sin cada titular
 3 amarillas        ciclo de sanción (5 amarillas = 1 partido en LaLiga)
 4 termómetro       tarjetas esperadas: equipos + árbitro (validado)
 5 tabla Elo        puntos esperados por Elo frente a reales (validado)
 6 segundas partes  puntos ganados/perdidos tras el descanso (estabilidad)
 7 rotación         cambios en el once y días desde el último partido de liga
 8 portero          goles evitados (xG a puerta - goles encajados)
 9 rachas           goles frente a xG (validado: ¿aguanta?)
10 moneyball        rendimiento frente a valor de mercado
11 estilos          perfil de juego frente a la media de la liga
12 cuotas           apertura -> cierre del mercado, nuestro % y acierto de la casa
 +  informe         post-partido: historia por mitades, Elo antes/después, merecido por xG
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import poisson, spearmanr, pearsonr

AQUI = Path(__file__).resolve().parent
DATA = AQUI.parent / "data"
sys.path.insert(0, str(AQUI))
from generar_datos import ajustar_ordenada, probs  # noqa: E402

LIGA = "La Liga"
HOY = pd.Timestamp("2026-09-30")
PREVIA = ("Real Madrid", "Villarreal", pd.Timestamp("2026-10-10"))
FD = {"Ath Madrid": "Atlético Madrid", "Ath Bilbao": "Athletic Club", "Betis": "Real Betis",
      "Sociedad": "Real Sociedad", "Celta": "Celta de Vigo", "Vallecano": "Rayo Vallecano",
      "La Coruna": "Deportivo La Coruña", "Sevilla": "Sevilla FC", "Santander": "Racing Santander",
      "Espanol": "Espanyol", "Alaves": "Alavés", "Malaga": "Malaga", "Leganes": "Leganés",
      "Almeria": "Almería", "Cadiz": "Cádiz", "Las Palmas": "Las Palmas", "Mallorca": "Mallorca",
      "Granada": "Granada", "Girona": "Girona", "Valladolid": "Valladolid", "Oviedo": "Oviedo"}
SALIDA = {}


def r(x, n=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


# ------------------------------------------------------------------ base
h = pd.read_csv(DATA / "historico_partidos.csv")
ll = h[h.liga == LIGA].dropna(subset=["goles_l", "goles_v"]).copy()
ll["fecha"] = pd.to_datetime(ll.fecha, utc=True).dt.tz_localize(None)
ll = ll.sort_values("fecha").reset_index(drop=True)
ids = {**dict(zip(ll.local, ll.local_id)), **dict(zip(ll.visitante, ll.visitante_id))}
nombre_eq = {v: k for k, v in ids.items()}

# Elo antes y después de cada partido (misma fórmula que scripts/rasgos.py)
rat, pre_l, pre_v, post_l, post_v = {}, [], [], [], []
for _, f in ll.iterrows():
    a, b = rat.get(f.local_id, 1500.0), rat.get(f.visitante_id, 1500.0)
    pre_l.append(a); pre_v.append(b)
    d = abs(f.goles_l - f.goles_v)
    g = 1.0 if d <= 1 else (1.5 if d == 2 else (11 + d) / 8.0)
    esp = 1 / (1 + 10 ** (-(a + 60 - b) / 400))
    real = 1.0 if f.goles_l > f.goles_v else (0.5 if f.goles_l == f.goles_v else 0.0)
    c = 20 * g * (real - esp)
    rat[f.local_id], rat[f.visitante_id] = a + c, b - c
    post_l.append(a + c); post_v.append(b - c)
ll["elo_l"], ll["elo_v"], ll["elo_l2"], ll["elo_v2"] = pre_l, pre_v, post_l, post_v
ll["y"] = np.where(ll.goles_l > ll.goles_v, 2, np.where(ll.goles_l == ll.goles_v, 1, 0))
aj = ll[ll.fecha >= ll.fecha.min() + pd.Timedelta(days=300)]
PAR = ajustar_ordenada((aj.elo_l - aj.elo_v).values, aj.y.values)
p1, px, p2 = probs(PAR, (ll.elo_l - ll.elo_v).values)
ll["p1"], ll["px"], ll["p2"] = p1, px, p2
ll["xpts_l"] = 3 * ll.p1 + ll.px
ll["xpts_v"] = 3 * ll.p2 + ll.px
ll["pts_l"] = np.select([ll.y == 2, ll.y == 1], [3, 1], 0)
ll["pts_v"] = np.select([ll.y == 0, ll.y == 1], [3, 1], 0)


def largo(df):
    """Una fila por equipo y partido."""
    a = df.assign(eqn=df.local, eq_id=df.local_id, riv=df.visitante, casa=True, gf=df.goles_l, gc=df.goles_v,
                  pts=df.pts_l, xpts=df.xpts_l, xg=df.l_expected_goals, xga=df.v_expected_goals,
                  elo=df.elo_l, elo2=df.elo_l2)
    b = df.assign(eqn=df.visitante, eq_id=df.visitante_id, riv=df.local, casa=False, gf=df.goles_v, gc=df.goles_l,
                  pts=df.pts_v, xpts=df.xpts_v, xg=df.v_expected_goals, xga=df.l_expected_goals,
                  elo=df.elo_v, elo2=df.elo_v2)
    return pd.concat([a, b]).sort_values("fecha")


L = largo(ll)

# nombres de jugadores
nom = {}
for f, c in (("eventos_tarjetas_jugadores_2025_26.csv", "jugador"), ("selecciones/jugadores_partido.csv", "jugador"),
             ("selecciones/alineaciones.csv", "jugador"), ("selecciones/notas_jugadores.csv", "jugador")):
    d = pd.read_csv(DATA / f)
    nom.update(dict(zip(d.jugador_id, d[c])))

X = pd.read_csv(DATA / "historico_xg_jugador.csv")
X = X[X.match_id.isin(ll.match_id)].merge(ll[["match_id", "fecha", "temporada"]], on="match_id")
val = pd.read_csv(DATA / "jugador_valor_mercado.csv")
val["fecha"] = pd.to_datetime(val.fecha, errors="coerce")
val = val[val.fecha <= HOY].sort_values("fecha").groupby("jugador_id").last()
perfil = pd.read_csv(DATA / "jugador_perfil.csv").set_index("jugador_id")


def valor(j):
    return float(val.valor.get(j, np.nan)) if j in val.index else np.nan


# ------------------------------------------------------------------ 5 tabla por Elo (primero: la usan otros)
def tabla_temporada(t, hasta=None):
    d = L[L.temporada == t]
    if hasta is not None:
        d = d.groupby("eqn").head(hasta)
    g = d.groupby("eqn").agg(pj=("pts", "size"), pts=("pts", "sum"), xpts=("xpts", "sum"),
                            gf=("gf", "sum"), gc=("gc", "sum"))
    g["dg"] = g.gf - g.gc
    return g.sort_values(["pts", "dg", "gf"], ascending=False)


# Comprobación: a la jornada 7, ¿qué predice mejor la tabla final, la tabla o el Elo?
val5 = []
for t in (2023, 2024, 2025):
    d = L[L.temporada == t]
    j7 = tabla_temporada(t, 7)
    fin = tabla_temporada(t)
    elo7 = d.groupby("eqn").nth(6).set_index("eqn").elo2
    rest = d.groupby("eqn").apply(lambda s: (s.pts.iloc[7:] - s.xpts.iloc[7:]).mean(), include_groups=False)
    suerte7 = (j7.pts - j7.xpts)
    eqs = fin.index
    rk_fin = pd.Series(range(1, len(fin) + 1), index=fin.index)
    rk_tab = pd.Series(range(1, len(j7) + 1), index=j7.index)
    rk_elo = elo7.rank(ascending=False)
    val5.append({"temporada": t,
                 "spearman_tabla_j7": r(spearmanr(rk_tab[eqs], rk_fin[eqs])[0]),
                 "spearman_elo_j7": r(spearmanr(rk_elo[eqs], rk_fin[eqs])[0]),
                 "suerte_j7_vs_resto": r(pearsonr(suerte7[eqs], rest[eqs])[0])})
print("5 comprobación:", val5)
t26 = tabla_temporada(2026)
elo_ahora = {nombre_eq[k]: v for k, v in rat.items() if k in nombre_eq}
t26["elo"] = [elo_ahora[e] for e in t26.index]
t26["elo_rank"] = t26.elo.rank(ascending=False).astype(int)
t26["elo_ini"] = [L[(L.temporada == 2026) & (L.eqn == e)].elo.iloc[0] for e in t26.index]
hist = {e: [r(v, 0) for v in L[(L.temporada == 2026) & (L.eqn == e)].elo2] for e in t26.index}
SALIDA["tabla_elo"] = {
    "comprobacion": val5,
    "filas": [{"pos": i + 1, "equipo": e, "pj": int(f.pj), "pts": int(f.pts), "xpts": r(f.xpts, 1),
               "suerte": r(f.pts - f.xpts, 1), "elo": r(f.elo, 0), "elo_rank": int(f.elo_rank),
               "elo_cambio": r(f.elo - f.elo_ini, 0), "elo_hist": hist[e]}
              for i, (e, f) in enumerate(t26.iterrows())]}

# ------------------------------------------------------------------ informe post-partido (RMA en Atlético, 20/09)
fdc = []
for f in sorted((DATA / "football_data").glob("*_SP1.csv")):
    d = pd.read_csv(f, encoding="utf-8-sig")
    d["temp"] = f.name[:4]
    fdc.append(d)
FDF = pd.concat(fdc, ignore_index=True)
FDF["fecha"] = pd.to_datetime(FDF.Date, dayfirst=True)
FDF["local"] = FDF.HomeTeam.map(lambda x: FD.get(x, x))
FDF["visitante"] = FDF.AwayTeam.map(lambda x: FD.get(x, x))

post = ll[(ll.local == "Atlético Madrid") & (ll.visitante == "Real Madrid") & (ll.temporada == 2026)].iloc[0]
fd_post = FDF[(FDF.local == "Atlético Madrid") & (FDF.visitante == "Real Madrid") & (FDF.temp == "2627")].iloc[0]
ev = pd.read_csv(DATA / "eventos_tarjetas_jugadores_2025_26.csv")
ev["minuto_txt"] = ev.minuto.astype(str)
ev["minuto"] = pd.to_numeric(ev.minuto_txt.str.split("+").str[0], errors="coerce")
ev.loc[ev.minuto < 0, "minuto"] = np.nan  # 8 filas con minuto negativo: dato roto, fuera
# Tarjetas duplicadas en la API (30/09/2026): el mismo jugador repetido, o el
# mismo jugador con dos nombres e IDs en el mismo partido y minuto
# («S. Mourino» / «Santiago Mouriño», «Vinícius» / «Vinícius Júnior»).
# Dos jugadores distintos amonestados en el mismo minuto sí son legítimos.
import unicodedata
def _tok(n):
    n = unicodedata.normalize("NFKD", str(n)).encode("ascii", "ignore").decode().lower().replace(".", " ")
    return n.split()
def _mismo(a, b):
    ta, tb = _tok(a), _tok(b)
    if not ta or not tb:
        return False
    if set(ta) <= set(tb) or set(tb) <= set(ta):
        return True
    return ta[-1] == tb[-1] and ta[0][0] == tb[0][0]
ev = ev.drop_duplicates(["match_id", "jugador_id", "minuto_txt", "tipo"])
alias, quitar = {}, []
for _, g in ev.groupby(["match_id", "equipo", "minuto_txt", "tipo"]):
    if len(g) < 2:
        continue
    filas_g = list(g.itertuples())
    for i_ in range(len(filas_g)):
        for k_ in range(i_ + 1, len(filas_g)):
            a_, b_ = filas_g[i_], filas_g[k_]
            if _mismo(a_.jugador, b_.jugador):
                largo_, corto_ = (a_, b_) if len(str(a_.jugador)) >= len(str(b_.jugador)) else (b_, a_)
                alias[corto_.jugador_id] = (largo_.jugador_id, largo_.jugador)
                quitar.append(corto_.Index)
ev = ev.drop(index=quitar)
for viejo, (nuevo, nombre) in alias.items():
    m_ = ev.jugador_id == viejo
    ev.loc[m_, "jugador_id"], ev.loc[m_, "jugador"] = nuevo, nombre
print("3 tarjetas: duplicados quitados", len(quitar), "alias", len(alias))
# El mismo jugador con dos IDs en partidos DISTINTOS: se unifica dentro de
# cada equipo por nombre (si no, sus amarillas se reparten y nunca llega al límite).
canon = {}
for eq_, g in ev.groupby("equipo"):
    pers = g.drop_duplicates("jugador_id")[["jugador_id", "jugador"]].values.tolist()
    pers.sort(key=lambda t: -len(str(t[1])))
    for i_, (ja, na) in enumerate(pers):
        if ja in canon:
            continue
        canon[ja] = (ja, na)
        for jb, nb in pers[i_ + 1:]:
            if jb not in canon and _mismo(na, nb):
                canon[jb] = (ja, na)
n_unif = sum(1 for k, v in canon.items() if k != v[0])
ev["jugador"] = ev.jugador_id.map(lambda j: canon.get(j, (j, None))[1]).fillna(ev.jugador)
ev["jugador_id"] = ev.jugador_id.map(lambda j: canon.get(j, (j, None))[0])
print("3 tarjetas: IDs unificados por nombre", n_unif)
tarjetas = ev[(ev.match_id == post.match_id) & ev.minuto.notna()].sort_values("minuto")
xp = X[X.match_id == post.match_id]


def sim_xg(xa, xb, n=200000, seed=1):
    """Probabilidad de ganar según las ocasiones: Poisson con el xG de cada uno."""
    rng = np.random.default_rng(seed)
    a, b = rng.poisson(xa, n), rng.poisson(xb, n)
    return r((a > b).mean() * 100, 0), r((a == b).mean() * 100, 0), r((a < b).mean() * 100, 0)


stat = lambda k: (r(post["l_" + k], 2), r(post["v_" + k], 2))
jug_post = []
for _, j in xp.sort_values("nota", ascending=False).iterrows():
    jug_post.append({"jugador": nom.get(j.jugador_id, str(j.jugador_id)), "equipo": nombre_eq.get(j.equipo_id),
                     "nota": r(j.nota), "min": int(j.minutos), "goles": int(j.goalsScored), "asist": int(j.assists),
                     "xg": r(j.expectedGoals), "pos": j.posicion})
gk = xp[xp.posicion == "Goalkeeper"]
SALIDA["informe"] = {
    "partido": f"{post.local} {int(post.goles_l)}-{int(post.goles_v)} {post.visitante}",
    "fecha": str(post.fecha.date()),
    "descanso": [int(fd_post.HTHG), int(fd_post.HTAG)], "final": [int(post.goles_l), int(post.goles_v)],
    "xg": [r(post.l_expected_goals), r(post.v_expected_goals)],
    "merecido_xg": sim_xg(post.l_expected_goals, post.v_expected_goals),
    "prob_previa": [r(post.p1 * 100, 0), r(post.px * 100, 0), r(post.p2 * 100, 0)],
    "elo_antes": [r(post.elo_l, 0), r(post.elo_v, 0)], "elo_despues": [r(post.elo_l2, 0), r(post.elo_v2, 0)],
    "stats": {k: stat(k) for k in ("possession", "shots_on_target", "shots_off_target", "big_chances_created",
                                   "corners", "fouls", "yellow_cards", "key_passes", "total_passes")},
    "tarjetas": [{"min": t.minuto_txt, "jugador": t.jugador, "equipo": t.equipo, "tipo": t.tipo} for _, t in tarjetas.iterrows()],
    "jugadores": jug_post[:6],
    "porteros": [{"jugador": nom.get(g.jugador_id, str(g.jugador_id)), "equipo": nombre_eq.get(g.equipo_id),
                  "paradas": int(g.goalsSaved), "evitados": r(g.expectedGoalsPrevented)} for _, g in gk.iterrows()],
    "cuotas": {"apertura": [r(fd_post.AvgH), r(fd_post.AvgD), r(fd_post.AvgA)],
               "cierre": [r(fd_post.AvgCH), r(fd_post.AvgCD), r(fd_post.AvgCA)]},
    "momentum_nota": "Por mitades (goles) y tarjetas por minuto. Sin minutos de goles ni cambios: la API los da en /matches/{id}, no guardados.",
}
print("informe:", SALIDA["informe"]["partido"], "HT", SALIDA["informe"]["descanso"], "xG", SALIDA["informe"]["xg"],
      "merecido", SALIDA["informe"]["merecido_xg"], "previa", SALIDA["informe"]["prob_previa"])

# ------------------------------------------------------------------ 1 bajas
les = pd.read_csv(DATA / "jugador_lesiones.csv")
les["d"] = pd.to_datetime(les.desde, format="%d.%m.%Y", errors="coerce")
les["h"] = pd.to_datetime(les.hasta, format="%d.%m.%Y", errors="coerce")
activos = les[(les.d <= HOY) & (les.h >= PREVIA[2])]


def plantilla(eq, desde="2025-08-01"):
    d = X[(X.equipo_id == ids[eq]) & (X.fecha >= desde)]
    g = d.groupby("jugador_id").agg(min=("minutos", "sum"), goles=("goalsScored", "sum"),
                                    asist=("assists", "sum"), xg=("expectedGoals", "sum"),
                                    xa=("expectedAssists", "sum"), nota=("nota", "mean"), pj=("match_id", "nunique"))
    return g


def bajas(eq):
    p = plantilla(eq)
    tot_ga, tot_min = (p.goles + p.asist).sum(), p["min"].sum()
    out = []
    for _, a in activos[activos.jugador_id.isin(p.index) & activos.jugador_id.isin(list(nom))].iterrows():
        f = p.loc[a.jugador_id]
        out.append({"jugador": nom.get(a.jugador_id, str(a.jugador_id)), "motivo": a.motivo,
                    "vuelve": str(a.h.date()), "pct_ga": r((f.goles + f.asist) / tot_ga * 100, 0),
                    "pct_min": r(f["min"] / tot_min * 100, 0), "valor_m": r(valor(a.jugador_id) / 1e6, 0)})
    out.sort(key=lambda x: -(x["pct_min"] or 0))
    return {"lista": out, "pct_ga": r(sum(o["pct_ga"] or 0 for o in out), 0),
            "pct_min": r(sum(o["pct_min"] or 0 for o in out), 0)}


SALIDA["bajas"] = {e: bajas(e) for e in PREVIA[:2]}
print("1 bajas:", {e: (v["pct_ga"], v["pct_min"], [o["jugador"] for o in v["lista"]]) for e, v in SALIDA["bajas"].items()})

# ------------------------------------------------------------------ 2 con / sin (Elo)
lu = pd.read_csv(DATA / "historico_lineups.csv")


def con_sin(eq, min_con=10, min_sin=5):
    i = ids[eq]
    d = L[(L.eqn == eq) & (L.fecha >= "2024-08-01")].merge(lu, on="match_id")
    d["once"] = np.where(d.casa, d.local_ids, d.visitante_ids)
    d = d.dropna(subset=["once"])
    d["once"] = d.once.map(lambda s: set(int(x) for x in str(s).split("|")))
    d["res"] = d.pts - d.xpts
    todos = set().union(*d.once)
    out = []
    for j in todos:
        c = d[d.once.map(lambda s: j in s)]
        s = d[~d.once.map(lambda s: j in s)]
        if len(c) >= min_con and len(s) >= min_sin and j in nom:
            out.append({"jugador": nom[j], "con_n": len(c), "sin_n": len(s),
                        "con_pts": r(c.pts.mean()), "sin_pts": r(s.pts.mean()),
                        "con_res": r(c.res.mean()), "sin_res": r(s.res.mean()),
                        "efecto": r(c.res.mean() - s.res.mean())})
    out.sort(key=lambda x: -x["efecto"])
    return {"partidos": int(len(d)), "lista": out}


SALIDA["con_sin"] = {e: con_sin(e) for e in PREVIA[:2]}
print("2 con/sin RMA top:", [(o["jugador"], o["efecto"], o["con_n"], o["sin_n"]) for o in SALIDA["con_sin"]["Real Madrid"]["lista"][:5]])

# ------------------------------------------------------------------ 3 ciclo de amarillas
ev["fecha"] = pd.to_datetime(ev.fecha, utc=True).dt.tz_localize(None)
am = ev[(ev.tipo == "Yellow Card") & (ev.fecha >= "2026-08-01")]
cuenta = am.groupby(["jugador_id", "jugador", "equipo"]).size().reset_index(name="amarillas")
cuenta["para_sancion"] = 5 - cuenta.amarillas % 5
minuto = ev[ev.tipo == "Yellow Card"].groupby("jugador_id").minuto.median()
cuenta["minuto_tipico"] = cuenta.jugador_id.map(minuto)
riesgo = cuenta[cuenta.para_sancion == 1].sort_values("amarillas", ascending=False)
SALIDA["amarillas"] = {
    "regla": "LaLiga: 5 amarillas = 1 partido de sanción (y cada 5 más)",
    "al_limite": [{"jugador": f.jugador, "equipo": f.equipo, "amarillas": int(f.amarillas),
                   "minuto": r(f.minuto_tipico, 0)} for _, f in riesgo.iterrows()],
    "equipos": {e: [{"jugador": f.jugador, "amarillas": int(f.amarillas), "faltan": int(f.para_sancion),
                     "minuto": r(f.minuto_tipico, 0)}
                    for _, f in cuenta[cuenta.equipo == e].sort_values("amarillas", ascending=False).iterrows()]
                for e in PREVIA[:2]}}
print("3 al límite:", [(a["jugador"], a["equipo"], a["amarillas"]) for a in SALIDA["amarillas"]["al_limite"]][:8])

# ------------------------------------------------------------------ 4 termómetro de tarjetas (validado)
arb = pd.read_csv(DATA / "historico_arbitro_clima.csv")[["match_id", "arbitro"]]
T = ll.merge(arb, on="match_id", how="left")
T["tj"] = T[["l_yellow_cards", "l_red_cards", "v_yellow_cards", "v_red_cards"]].sum(axis=1, min_count=2)
T = T.dropna(subset=["tj"]).reset_index(drop=True)
media_liga = T.tj.mean()


def estimar(fila, pasado):
    liga = pasado.tj.mean()
    def eqf(e):
        m = pasado[(pasado.local == e) | (pasado.visitante == e)].tail(20)
        return (m.tj.sum() + 10 * liga) / (len(m) + 10)
    ta, tb = eqf(fila.local), eqf(fila.visitante)
    base = (ta + tb) / 2
    ref = 1.0
    if isinstance(fila.arbitro, str):
        m = pasado[pasado.arbitro == fila.arbitro]
        ref = ((m.tj.sum() + 10 * liga) / (len(m) + 10)) / liga
    return liga, base, base * ref


filas = []
for i in range(len(T)):
    f = T.iloc[i]
    if f.fecha < pd.Timestamp("2024-08-01"):
        continue
    pas = T.iloc[:i]
    pas = pas[pas.fecha < f.fecha.normalize()]
    liga, eqs_, ambos = estimar(f, pas)
    filas.append((f.tj, liga, eqs_, ambos))
V = pd.DataFrame(filas, columns=["real", "liga", "equipos", "equipos_arbitro"])
brier = {c: r((((1 - poisson.cdf(4, V[c])) - (V.real > 4.5)) ** 2).mean(), 4) for c in ("liga", "equipos", "equipos_arbitro")}
corr = {c: r(pearsonr(V[c], V.real)[0], 3) for c in ("equipos", "equipos_arbitro")}
print("4 comprobación (Brier más de 4,5; menor es mejor):", brier, "correlación:", corr, "n", len(V))
fila_prev = pd.Series({"local": PREVIA[0], "visitante": PREVIA[1], "arbitro": np.nan})
liga, eq_, _ = estimar(fila_prev, T)
arbs = T[T.temporada >= 2025].groupby("arbitro").tj.agg(["mean", "size"])
arbs = arbs[arbs["size"] >= 15]
SALIDA["termometro"] = {
    "comprobacion": {"partidos": int(len(V)), "brier_mas45": brier, "correlacion": corr},
    "media_liga": r(media_liga), "esperadas": r(eq_, 1), "p_mas45": r((1 - poisson.cdf(4, eq_)) * 100, 0),
    "con_arbitro_estricto": r(eq_ * arbs["mean"].max() / media_liga, 1),
    "con_arbitro_suave": r(eq_ * arbs["mean"].min() / media_liga, 1)}
print("4 RMA-VIL esperadas:", SALIDA["termometro"])

# ------------------------------------------------------------------ 6 segundas partes
FDF["ht_l"] = np.select([FDF.HTHG > FDF.HTAG, FDF.HTHG == FDF.HTAG], [3, 1], 0)
FDF["ht_v"] = np.select([FDF.HTHG < FDF.HTAG, FDF.HTHG == FDF.HTAG], [3, 1], 0)
FDF["ft_l"] = np.select([FDF.FTHG > FDF.FTAG, FDF.FTHG == FDF.FTAG], [3, 1], 0)
FDF["ft_v"] = np.select([FDF.FTHG < FDF.FTAG, FDF.FTHG == FDF.FTAG], [3, 1], 0)
S = pd.concat([FDF.assign(eqn=FDF.local, d=FDF.ft_l - FDF.ht_l, remonta=(FDF.ht_l == 0) & (FDF.ft_l > 0),
                          cae=(FDF.ht_l == 3) & (FDF.ft_l < 3)),
               FDF.assign(eqn=FDF.visitante, d=FDF.ft_v - FDF.ht_v, remonta=(FDF.ht_v == 0) & (FDF.ft_v > 0),
                          cae=(FDF.ht_v == 3) & (FDF.ft_v < 3))])
por = S.groupby(["temp", "eqn"]).agg(delta=("d", "mean"), n=("d", "size"), remontas=("remonta", "sum"), caidas=("cae", "sum"))
estab = []
for a, b in (("2324", "2425"), ("2425", "2526")):
    x_, y_ = por.loc[a].delta, por.loc[b].delta
    comun = x_.index.intersection(y_.index)
    estab.append({"de": a, "a": b, "corr": r(pearsonr(x_[comun], y_[comun])[0]), "n": len(comun)})
print("6 estabilidad año a año:", estab)
t25 = por.loc["2526"].sort_values("delta", ascending=False)
SALIDA["segundas_partes"] = {
    "comprobacion": estab,
    "2025_26": [{"equipo": e, "pts_tras_descanso": r(f.delta * f.n, 0), "por_partido": r(f.delta),
                 "remontadas": int(f.remontas), "caidas": int(f.caidas)} for e, f in t25.iterrows()],
    "2026_27": {e: {"pts_tras_descanso": r(por.loc["2627"].delta.get(e, np.nan) * por.loc["2627"].n.get(e, np.nan), 0)}
                for e in PREVIA[:2]}}

# ------------------------------------------------------------------ 7 rotación y descanso
def rotacion(eq):
    d = L[(L.eqn == eq) & (L.fecha >= "2025-08-01")].merge(lu, on="match_id")
    d["once"] = np.where(d.casa, d.local_ids, d.visitante_ids)
    d = d.dropna(subset=["once"]).sort_values("fecha")
    d["once"] = d.once.map(lambda s: set(str(s).split("|")))
    cambios, dias = [], []
    prev = None
    for _, f in d.iterrows():
        if prev is not None:
            cambios.append(11 - len(f.once & prev.once))
            dias.append((f.fecha - prev.fecha).days)
        prev = f
    c, dd = np.array(cambios), np.array(dias)
    return {"media_cambios": r(c.mean(), 1), "corto": r(c[dd <= 4].mean(), 1) if (dd <= 4).any() else None,
            "n_corto": int((dd <= 4).sum()), "largo": r(c[dd >= 6].mean(), 1), "ultimo": int(c[-1]),
            "dias_hasta_previa": int((PREVIA[2] - d.fecha.iloc[-1]).days)}


SALIDA["rotacion"] = {e: rotacion(e) for e in PREVIA[:2]}
SALIDA["rotacion"]["nota"] = "Solo partidos de liga: Champions y Copa no están en los datos."
print("7 rotación:", SALIDA["rotacion"])

# ------------------------------------------------------------------ 8 portero
gkx = X[X.posicion == "Goalkeeper"]
g26 = gkx[gkx.temporada >= 2025].groupby(["jugador_id", "equipo_id"]).agg(
    evitados=("expectedGoalsPrevented", "sum"), min=("minutos", "sum")).reset_index()
g26 = g26[(g26["min"] >= 900) & g26.jugador_id.isin(list(nom))]
g26["por90"] = g26.evitados / g26["min"] * 90
# estabilidad: primera mitad vs segunda mitad de 2025/26
g5 = gkx[gkx.temporada == 2025].sort_values("fecha")
g5["mitad"] = g5.groupby("jugador_id").cumcount() < g5.groupby("jugador_id").jugador_id.transform("size") / 2
m = g5.groupby(["jugador_id", "mitad"]).expectedGoalsPrevented.mean().unstack().dropna()
m = m[g5.groupby("jugador_id").size().reindex(m.index) >= 16]
est8 = r(pearsonr(m[True], m[False])[0])
print("8 portero estabilidad mitad-mitad:", est8, "n", len(m))
SALIDA["porteros"] = {"comprobacion": {"corr_mitades_2025_26": est8, "n": int(len(m))},
                      "ranking": [{"jugador": nom.get(f.jugador_id, str(f.jugador_id)), "equipo": nombre_eq.get(f.equipo_id),
                                   "evitados": r(f.evitados, 1), "por90": r(f.por90)}
                                  for _, f in g26.sort_values("evitados", ascending=False).iterrows()]}

# ------------------------------------------------------------------ 9 rachas: goles frente a xG (validado)
q = L[(L.temporada == 2025)].dropna(subset=["xg"])
q["n"] = q.groupby("eqn").cumcount()
a_ = q[q.n < 19].groupby("eqn").agg(g=("gf", "sum"), xg=("xg", "sum"))
b_ = q[q.n >= 19].groupby("eqn").agg(g=("gf", "sum"), xg=("xg", "sum"))
val9 = {"racha_se_mantiene": r(pearsonr(a_.g - a_.xg, b_.g - b_.xg)[0]),
        "xg_predice_goles": r(pearsonr(a_.xg, b_.g)[0]), "goles_predicen_goles": r(pearsonr(a_.g, b_.g)[0])}
print("9 comprobación 2025/26 (1ª vuelta -> 2ª):", val9)
eq26 = L[L.temporada == 2026].groupby("eqn").agg(g=("gf", "sum"), xg=("xg", "sum"), gc=("gc", "sum"), xga=("xga", "sum"))
eq26["dif"] = eq26.g - eq26.xg
j = X[X.temporada >= 2025].groupby("jugador_id").agg(g=("goalsScored", "sum"), xg=("expectedGoals", "sum"),
                                                     min=("minutos", "sum"), eqid=("equipo_id", "last"))
j = j[(j["min"] >= 900) & j.index.isin(list(nom))]
j["dif"] = j.g - j.xg
SALIDA["rachas"] = {"comprobacion": val9,
                    "equipos_2026_27": [{"equipo": e, "goles": int(f.g), "xg": r(f.xg, 1), "dif": r(f.dif, 1),
                                         "encajados": int(f.gc), "xg_contra": r(f.xga, 1)}
                                        for e, f in eq26.sort_values("dif", ascending=False).iterrows()],
                    "jugadores_arriba": [{"jugador": nom[i], "equipo": nombre_eq.get(f.eqid), "goles": int(f.g), "xg": r(f.xg, 1)}
                                         for i, f in j.sort_values("dif", ascending=False).head(6).iterrows()],
                    "jugadores_abajo": [{"jugador": nom[i], "equipo": nombre_eq.get(f.eqid), "goles": int(f.g), "xg": r(f.xg, 1)}
                                        for i, f in j.sort_values("dif").head(6).iterrows()]}

# ------------------------------------------------------------------ 10 moneyball
mb = X[X.temporada >= 2025].groupby("jugador_id").agg(min=("minutos", "sum"), nota=("nota", "mean"),
                                                      xg=("expectedGoals", "sum"), xa=("expectedAssists", "sum"),
                                                      eqid=("equipo_id", "last"), pos=("posicion", "last"))
mb = mb[(mb["min"] >= 1500) & mb.index.isin(list(nom)) & mb.index.isin(val.index)]
mb["valor"] = [valor(i) / 1e6 for i in mb.index]
mb["xgi90"] = (mb.xg + mb.xa) / mb["min"] * 90
mb = mb[mb.valor >= 0.5]  # valor 0 = sin dato de valor
mb["pct_nota"] = mb.groupby("pos").nota.rank(pct=True)
mb["pct_valor"] = mb.groupby("pos").valor.rank(pct=True)
mb["ganga"] = mb.pct_nota - mb.pct_valor
print("10 moneyball jugadores:", len(mb))
SALIDA["moneyball"] = {"n": int(len(mb)), "gangas": [
    {"jugador": nom[i], "equipo": nombre_eq.get(f.eqid), "pos": f.pos, "nota": r(f.nota), "valor_m": r(f.valor, 0),
     "xgi90": r(f.xgi90), "pct_nota": r(f.pct_nota * 100, 0)}
    for i, f in mb.sort_values("ganga", ascending=False).head(8).iterrows()],
    "caros": [{"jugador": nom[i], "equipo": nombre_eq.get(f.eqid), "nota": r(f.nota), "valor_m": r(f.valor, 0),
               "pct_nota": r(f.pct_nota * 100, 0)}
              for i, f in mb.sort_values("ganga").head(5).iterrows()]}

# ------------------------------------------------------------------ 11 estilos
cols = {"possession": "Posesión", "total_passes": "Pases", "crosses": "Centros",
        "aerial_duels": "Duelos aéreos", "tackles": "Entradas", "interceptions": "Intercepciones",
        "shots_outside_penalty_area": "Tiros lejanos"}
E = ll[ll.temporada >= 2025]
per = pd.concat([E.assign(eqn=E.local, **{k: E["l_" + k] for k in cols}),
                 E.assign(eqn=E.visitante, **{k: E["v_" + k] for k in cols})]).groupby("eqn")[list(cols)].mean()
z = (per - per.mean()) / per.std()
SALIDA["estilos"] = {e: {cols[k]: r(z.loc[e, k], 1) for k in cols} for e in PREVIA[:2]}
# ¿cómo le va al Madrid contra equipos de mucha posesión?
alta = set(z[z.possession > 0.5].index)
d = L[(L.eqn == "Real Madrid") & (L.temporada >= 2025)]
d = d.assign(res=d.pts - d.xpts, contra_posesion=d.riv.isin(alta))
SALIDA["estilos"]["rma_vs_posesion"] = {k: {"n": int(len(g)), "res": r(g.res.mean())} for k, g in d.groupby("contra_posesion")}
print("11 estilos:", SALIDA["estilos"])

# ------------------------------------------------------------------ 12 cuotas
dj = json.loads((AQUI / "datos.json").read_text())
SALIDA["cuotas"] = {"pronosticos": dj["pronosticos"],
                    "apertura_cierre_post": SALIDA["informe"]["cuotas"]}

# ------------------------------------------------------------------ equipo y jugador de ejemplo
rm = L[(L.eqn == "Real Madrid") & (L.temporada == 2026)]
SALIDA["equipo"] = {"elo": r(elo_ahora["Real Madrid"], 0), "elo_hist": hist["Real Madrid"],
                    "forma": [{"riv": f.riv, "gf": int(f.gf), "gc": int(f.gc), "casa": bool(f.casa),
                               "elo_cambio": r(f.elo2 - f.elo, 0)} for _, f in rm.iterrows()]}
p = plantilla("Real Madrid")
p = p[p.index.isin(list(nom))]
top = p.sort_values("nota", ascending=False).head(1).index[0] if len(p) else None
SALIDA["jugador_top_rma"] = nom.get(top)

(AQUI / "datos_app.json").write_text(json.dumps(SALIDA, ensure_ascii=False, indent=1, default=str))
print("OK datos_app.json")


# ------------------------------------------------------------------ comprobaciones extra
# 4: ¿la mejora del termómetro sobre la media de la liga es más que ruido? (Brier emparejado)
d4 = (((1 - poisson.cdf(4, V.liga)) - (V.real > 4.5)) ** 2) - (((1 - poisson.cdf(4, V.equipos_arbitro)) - (V.real > 4.5)) ** 2)
sig4 = d4.mean() / (d4.std() / np.sqrt(len(d4)))
# 6: ¿las segundas partes son un rasgo propio o solo «los buenos ganan más»?
pp = S.groupby(["temp", "eqn"]).ft_l.size()  # placeholder de índice
ppg = pd.concat([FDF.assign(eqn=FDF.local, p=FDF.ft_l), FDF.assign(eqn=FDF.visitante, p=FDF.ft_v)]).groupby(["temp", "eqn"]).p.mean()
res6 = []
for a, b in (("2324", "2425"), ("2425", "2526")):
    ya, yb = por.loc[a].delta, por.loc[b].delta
    xa_, xb_ = ppg.loc[a], ppg.loc[b]
    comun = ya.index.intersection(yb.index)
    ra = ya[comun] - np.polyval(np.polyfit(xa_[comun], ya[comun], 1), xa_[comun])
    rb = yb[comun] - np.polyval(np.polyfit(xb_[comun], yb[comun], 1), xb_[comun])
    res6.append({"de": a, "a": b, "corr_sin_nivel": r(pearsonr(ra, rb)[0]),
                 "corr_con_nivel": r(pearsonr(ya[comun], xa_[comun])[0])})
print("4 sigmas de la mejora:", r(sig4), "| 6 controlando por nivel:", res6)
SALIDA["termometro"]["comprobacion"]["sigmas_vs_liga"] = r(sig4)
SALIDA["segundas_partes"]["comprobacion_sin_nivel"] = res6
(AQUI / "datos_app.json").write_text(json.dumps(SALIDA, ensure_ascii=False, indent=1, default=str))


# ------------------------------------------------------------------ alineaciones del informe y jugador de ejemplo
fl = lu[lu.match_id == post.match_id].iloc[0]
notas = dict(zip(xp.jugador_id, xp.nota))
def once(ids_txt, form):
    ids_ = [int(x) for x in str(ids_txt).split("|")]
    filas_ = [1] + [int(n) for n in str(form).split("-")]
    out, k = [], 0
    for n in filas_:
        out.append([{"jugador": nom.get(i, "?"), "nota": r(notas.get(i))} for i in ids_[k:k + n]])
        k += n
    return out
SALIDA["alineaciones_informe"] = {"local": {"formacion": fl.local_formacion, "lineas": once(fl.local_ids, fl.local_formacion)},
                                  "visitante": {"formacion": fl.visitante_formacion, "lineas": once(fl.visitante_ids, fl.visitante_formacion)}}
p = plantilla("Real Madrid", desde="2026-08-01")
p = p[p.index.isin(list(nom))].sort_values("min", ascending=False)
print("RMA 26/27:", [(nom[i], int(f["min"]), int(f.goles), r(f.xg, 1), r(f.nota)) for i, f in p.head(8).iterrows()])
(AQUI / "datos_app.json").write_text(json.dumps(SALIDA, ensure_ascii=False, indent=1, default=str))


# ------------------------------------------------------------------ jugador de ejemplo: Mbappé
jid = [i for i, n in nom.items() if n == "Kylian Mbappé"][0]
xj = X[X.jugador_id == jid].sort_values("fecha")
x26 = xj[xj.temporada == 2026]
x25 = xj[xj.temporada == 2025]
cs = [c for c in SALIDA["con_sin"]["Real Madrid"]["lista"] if c["jugador"] == "Kylian Mbappé"]
vh = pd.read_csv(DATA / "jugador_valor_mercado.csv")
vh["fecha"] = pd.to_datetime(vh.fecha, errors="coerce")
vh = vh[(vh.jugador_id == jid) & (vh.fecha <= HOY)].sort_values("fecha")
tj = cuenta[cuenta.jugador_id == jid]
per_mb = mb.loc[jid] if jid in mb.index else None
def temp(x):
    m = x.minutos.sum()
    return {"pj": int(len(x)), "min": int(m), "goles": int(x.goalsScored.sum()), "asist": int(x.assists.sum()),
            "xg": r(x.expectedGoals.sum(), 1), "xa": r(x.expectedAssists.sum(), 1), "nota": r(x.nota.mean()),
            "tiros": int(x.shotsTotal.sum()), "pases_clave": int(x.passesKey.sum())}
# percentiles por 90 frente a delanteros con 900+ min desde 2025/26
fw = X[(X.temporada >= 2025) & (X.posicion == "Forward")].groupby("jugador_id").agg(
    min=("minutos", "sum"), g=("goalsScored", "sum"), xg=("expectedGoals", "sum"), xa=("expectedAssists", "sum"),
    tiros=("shotsTotal", "sum"), regates=("dribblesSuccessful", "sum"), pc=("passesKey", "sum"), nota=("nota", "mean"))
fw = fw[fw["min"] >= 900]
for c in ("g", "xg", "xa", "tiros", "regates", "pc"):
    fw[c + "90"] = fw[c] / fw["min"] * 90
pct = {k: r(fw[c].rank(pct=True).get(jid, np.nan) * 100, 0) for k, c in
       (("Goles", "g90"), ("xG", "xg90"), ("xA", "xa90"), ("Tiros", "tiros90"), ("Regates", "regates90"), ("Pases clave", "pc90"), ("Nota", "nota"))}
SALIDA["jugador"] = {"nombre": "Kylian Mbappé", "equipo": "Real Madrid",
                     "perfil": {"edad": int((HOY - pd.Timestamp(perfil.nacimiento.get(jid))).days // 365.25) if jid in perfil.index else None,
                                "altura": r(perfil.altura_cm.get(jid), 0) if jid in perfil.index else None,
                                "pie": perfil.pie.get(jid) if jid in perfil.index else None,
                                "posicion": perfil.posicion.get(jid) if jid in perfil.index else None},
                     "valor_m": r(valor(jid) / 1e6, 0),
                     "valor_hist": [{"fecha": str(f.fecha.date()), "m": r(f.valor / 1e6, 0)} for _, f in vh.tail(8).iterrows()],
                     "t2026": temp(x26), "t2025": temp(x25),
                     "notas_ult": [r(v) for v in xj.nota.tail(10)],
                     "rivales_ult": [nombre_eq.get(m) for m in []],
                     "con_sin": cs[0] if cs else None,
                     "amarillas_2026": int(tj.amarillas.iloc[0]) if len(tj) else 0,
                     "percentiles_delanteros": pct, "n_delanteros": int(len(fw))}
print("jugador:", json.dumps(SALIDA["jugador"], ensure_ascii=False)[:700])
(AQUI / "datos_app.json").write_text(json.dumps(SALIDA, ensure_ascii=False, indent=1, default=str))


# ------------------------------------------------------------------ últimos resultados (portada): marcador, xG, merecido, Elo
ult = ll[(ll.temporada == 2026)].sort_values("fecha").tail(10)
SALIDA["resultados"] = [{"local": f.local, "visitante": f.visitante, "gl": int(f.goles_l), "gv": int(f.goles_v),
                         "xg": [r(f.l_expected_goals), r(f.v_expected_goals)],
                         "merecido": sim_xg(f.l_expected_goals, f.v_expected_goals, n=50000),
                         "prev": [r(f.p1 * 100, 0), r(f.px * 100, 0), r(f.p2 * 100, 0)],
                         "elo_cambio": r(f.elo_l2 - f.elo_l, 0), "fecha": str(f.fecha.date())}
                        for _, f in ult.iloc[::-1].iterrows()]
(AQUI / "datos_app.json").write_text(json.dumps(SALIDA, ensure_ascii=False, indent=1, default=str))
for x_ in SALIDA["resultados"]:
    print(x_)
