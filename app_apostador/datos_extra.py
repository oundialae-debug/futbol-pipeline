"""
Datos nuevos para 2yellow pedidos en los comentarios del lienzo (30/09/2026).
Solo LEE data/ (reutiliza lo que ya calcula analisis_app.py). Sin API.
Escribe app_apostador/datos_extra.json.

 bajas2        seguras (lesión que pasa del partido + sancionados) y dudas
 segundas2     puntos si los partidos acabaran al descanso contra los reales
 rangos        goles vs xG y goles evitados del portero: últimos 5, 10, temporada
 mbappe        últimos 10 partidos (rival, minutos, suplente) y percentiles por tramo
 informe2      "¿merecido?" ampliado y nuestro pronóstico previo contra la casa
 duelos        zona contra zona y jugador contra jugador por puesto en la alineación
 tablas        ranking 2yellow (por Elo) y clasificación real con G/E/P
 estilos2      estilo en unidades normales, media de la liga y etiquetas
"""
import contextlib
import io
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
with contextlib.redirect_stdout(io.StringIO()):
    import analisis_app as A
from generar_datos import lambdas, mercados_goles

AQUI = Path(__file__).resolve().parent
r = A.r
OUT = {}
PARTIDO = A.PREVIA[2]

# ------------------------------------------------------------------ bajas: seguras y dudas
# Duda: vuelve entre 2 días antes y 3 días después del partido. Después: baja segura.
# Sancionado: roja en su último partido de liga, o quinta amarilla en ese partido.
ev = A.ev


def bajas2(eq):
    p = A.plantilla(eq)
    tot_ga = (p.goles + p.asist).sum()

    def peso(j):
        if j not in p.index:
            return 0
        f = p.loc[j]
        return r((f.goles + f.asist) / tot_ga * 100, 0)

    les = A.les[A.les.jugador_id.isin(p.index) & (A.les.d <= A.HOY) & (A.les.h >= PARTIDO - pd.Timedelta(days=2))]
    fuera, duda = [], []
    for _, a in les.iterrows():
        if a.jugador_id not in A.nom:
            continue  # sin nombre: no se enseña (1 caso en el Madrid, rotura de tendón hasta 2027)
        x = {"jugador": A.nom[a.jugador_id], "motivo": a.motivo.replace(" injury", ""), "vuelve": str(a.h.date()),
             "pct_ga": peso(a.jugador_id)}
        (fuera if a.h > PARTIDO + pd.Timedelta(days=3) else duda).append(x)
    ult = A.L[(A.L.eqn == eq) & (A.L.fecha < PARTIDO)].iloc[-1]
    e = ev[(ev.match_id == ult.match_id) & (ev.equipo == eq)]
    for _, t in e[e.tipo == "Red Card"].iterrows():
        fuera.append({"jugador": t.jugador, "motivo": "Red card", "vuelve": None, "pct_ga": peso(t.jugador_id)})
    temp = ev[(ev.equipo == eq) & ev.match_id.isin(A.L[(A.L.temporada == 2026)].match_id)]
    am = temp[temp.tipo == "Yellow Card"].groupby("jugador_id").size()
    for _, t in e[e.tipo == "Yellow Card"].iterrows():
        if am.get(t.jugador_id, 0) % 5 == 0:
            fuera.append({"jugador": t.jugador, "motivo": "5 yellows", "vuelve": None, "pct_ga": peso(t.jugador_id)})
    fuera.sort(key=lambda x: -(x["pct_ga"] or 0))
    duda.sort(key=lambda x: -(x["pct_ga"] or 0))
    return {"fuera": fuera, "duda": duda, "pct_fuera": r(sum(x["pct_ga"] or 0 for x in fuera), 0),
            "pct_duda": r(sum(x["pct_ga"] or 0 for x in duda), 0)}


OUT["bajas2"] = {e: bajas2(e) for e in A.PREVIA[:2]}

# ------------------------------------------------------------------ segundas partes, en puntos que se entienden
S = A.S[A.S.temp == "2526"]
g = S.groupby("eqn").agg(ht=("ht_l", "size"), d=("d", "sum"), remontas=("remonta", "sum"), caidas=("cae", "sum"))
S_ = pd.concat([A.FDF[A.FDF.temp == "2526"].assign(eqn=A.FDF.local, pht=A.FDF.ht_l, pft=A.FDF.ft_l),
                A.FDF[A.FDF.temp == "2526"].assign(eqn=A.FDF.visitante, pht=A.FDF.ht_v, pft=A.FDF.ft_v)])
pts = S_.groupby("eqn").agg(pts_ht=("pht", "sum"), pts_ft=("pft", "sum"), pj=("pft", "size"))
pts["dif"] = pts.pts_ft - pts.pts_ht
pts["rank"] = pts.dif.rank(ascending=False, method="min").astype(int)
OUT["segundas2"] = {e: {"pts_ht": int(f.pts_ht), "pts_ft": int(f.pts_ft), "dif": int(f.dif), "rank": int(f["rank"]),
                        "remontadas": int(g.loc[e, "remontas"]), "caidas": int(g.loc[e, "caidas"]), "pj": int(f.pj)}
                    for e, f in pts.iterrows()}
print("segundas RMA:", OUT["segundas2"]["Real Madrid"])

# ------------------------------------------------------------------ tramos: últimos 5, 10, temporada
X = A.X
RANGOS = (("l5", 5), ("l10", 10), ("season", None))


def tramo(eq, n):
    d = A.L[(A.L.eqn == eq) & (A.L.temporada == 2026)] if n is None else A.L[A.L.eqn == eq].tail(n)
    return d


def goles_xg(eq):
    out = {}
    for k, n in RANGOS:
        d = tramo(eq, n)
        con = d.dropna(subset=["xg"])
        out[k] = {"pj": int(len(d)), "con_xg": int(len(con)), "goles": int(con.gf.sum()), "xg": r(con.xg.sum(), 1),
                  "dif": r(con.gf.sum() - con.xg.sum(), 1)}
    return out


def portero(eq):
    out = {}
    gks = X[(X.posicion == "Goalkeeper") & (X.equipo_id == A.ids[eq]) & (X.minutos > 0)]
    for k, n in RANGOS:
        d = tramo(eq, n)
        x = gks[gks.match_id.isin(d.match_id)]
        top = x.groupby("jugador_id").minutos.sum().idxmax() if len(x) else None
        y = x[x.jugador_id == top]
        out[k] = {"jugador": A.nom.get(top), "pj": int(len(y)), "de": int(len(d)),
                  "evitados": r(y.expectedGoalsPrevented.sum(), 1)}
    return out


eqs26 = sorted(A.L[A.L.temporada == 2026].eqn.unique())
OUT["rangos"] = {"goles_xg": {e: goles_xg(e) for e in eqs26}, "portero": {e: portero(e) for e in eqs26}}
# portero por tramo, toda la liga (ranking)
rk = {}
for k, n in RANGOS:
    filas = []
    for e in eqs26:
        p_ = OUT["rangos"]["portero"][e][k]
        if p_["jugador"]:
            filas.append({"jugador": p_["jugador"], "equipo": e, "evitados": p_["evitados"], "pj": p_["pj"]})
    filas.sort(key=lambda x: -x["evitados"])
    rk[k] = filas
OUT["rangos"]["porteros_liga"] = rk
print("RMA tramos:", OUT["rangos"]["goles_xg"]["Real Madrid"], OUT["rangos"]["portero"]["Real Madrid"])

# ------------------------------------------------------------------ Mbappé: últimos 10 y percentiles por tramo
jid = [i for i, nn in A.nom.items() if nn == "Kylian Mbappé"][0]
xj = X[(X.jugador_id == jid) & (X.minutos > 0)].sort_values("fecha").tail(10)
ult10 = []
for _, f in xj.iterrows():
    m = A.ll[A.ll.match_id == f.match_id].iloc[0]
    casa = m.local_id == f.equipo_id
    riv = m.visitante if casa else m.local
    gf, gc = (m.goles_l, m.goles_v) if casa else (m.goles_v, m.goles_l)
    ult10.append({"rival": riv, "casa": bool(casa), "min": int(f.minutos), "suplente": bool(f.suplente),
                  "nota": r(f.nota), "goles": int(f.goalsScored), "res": f"{int(gf)}-{int(gc)}", "fecha": str(m.fecha.date())})

MET = (("Goals", "goalsScored"), ("xG", "expectedGoals"), ("xA", "expectedAssists"), ("Shots", "shotsTotal"),
       ("Dribbles", "dribblesSuccessful"), ("Key passes", "passesKey"))


def percentiles(ventana):
    """Percentil por 90 frente a delanteros con al menos la mitad de los minutos posibles del tramo."""
    fw = X[X.posicion == "Forward"]
    if ventana in ("l5", "l10"):
        n = 5 if ventana == "l5" else 10
        partes, posibles = [], {}
        for e in A.ids:
            ms = A.L[A.L.eqn == e].tail(n).match_id
            partes.append(fw[(fw.equipo_id == A.ids[e]) & fw.match_id.isin(ms)])
        d = pd.concat(partes)
        minimo = n * 90 / 2
    else:
        t = 2026 if ventana == "season" else 2025
        d = fw[fw.temporada == t]
        pj = A.L[A.L.temporada == t].groupby("eqn").size().max()
        minimo = pj * 90 / 2
    ag = d.groupby("jugador_id").agg(min=("minutos", "sum"), nota=("nota", "mean"),
                                     **{k: (c, "sum") for k, c in MET})
    ag = ag[ag["min"] >= minimo]
    for k, _ in MET:
        ag[k] = ag[k] / ag["min"] * 90
    ag = ag.rename(columns={"nota": "Rating"})
    if jid not in ag.index:
        return {"n": int(len(ag)), "pct": None, "minimo": int(minimo)}
    pct = {k: r(ag[k].rank(pct=True)[jid] * 100, 0) for k in [m[0] for m in MET] + ["Rating"]}
    vals = {k: r(ag.loc[jid, k], 2) for k in [m[0] for m in MET] + ["Rating"]}
    return {"n": int(len(ag)), "pct": pct, "por90": vals, "minimo": int(minimo), "min": int(ag.loc[jid, "min"])}


OUT["mbappe"] = {"ult10": ult10, "percentiles": {k: percentiles(k) for k in ("l5", "l10", "season", "last")}}
print("Mbappé:", [(u["rival"], u["min"], u["nota"]) for u in ult10])
print("percentiles:", {k: (v["n"], v["pct"]) for k, v in OUT["mbappe"]["percentiles"].items()})

# ------------------------------------------------------------------ informe: merecido ampliado y nuestro pronóstico contra la casa
M = A.post
st = lambda k: [r(M["l_" + k], 2), r(M["v_" + k], 2)]
gk = A.xp[(A.xp.posicion == "Goalkeeper") & (A.xp.minutos > 0)]
ev_gk = {A.nombre_eq[f.equipo_id]: {"jugador": A.nom.get(f.jugador_id), "paradas": int(f.goalsSaved),
                                    "evitados": r(f.expectedGoalsPrevented)} for _, f in gk.iterrows()}
merecido = {"tiros_puerta": st("shots_on_target"), "tiros_fuera": st("shots_off_target"),
            "bloqueados": st("blocked_shots"), "dentro_area": st("shots_within_penalty_area"),
            "ocasiones": st("big_chances_created"), "ultimo_tercio": st("passes_into_final_third"),
            "pases_clave": st("key_passes"), "paradas": st("goalkeeper_saves"), "porteros": ev_gk}

# nuestro % previo: 1X2 por Elo (antes del partido) y goles por Poisson con solo partidos anteriores
h = pd.read_csv(A.DATA / "historico_partidos.csv")
hl = h[h.liga == A.LIGA].dropna(subset=["goles_l", "goles_v"]).sort_values("fecha")
prev = hl[hl.fecha < str(M.fecha.date())]
gm = {k: r(v * 100, 0) for k, v in mercados_goles(*lambdas(prev, M.local, M.visitante)).items()}
nuestro = {"1x2": [r(M.p1 * 100, 0), r(M.px * 100, 0), r(M.p2 * 100, 0)], "mas15": gm["mas15"], "mas25": gm["mas25"],
           "ambos": gm["ambos"]}
# la casa: mediana de las casas cosechadas antes del partido, sin margen
c = pd.read_csv(A.DATA / "cuotas_cosechadas.csv")
c = c[c.match_id == M.match_id]


def sin_margen(mercado, lados):
    x = c[c.mercado == mercado].groupby("lado").cuota.median()
    if not all(l_ in x.index for l_ in lados):
        return None, 0
    inv = np.array([1 / x[l_] for l_ in lados])
    return [r(v * 100, 0) for v in inv / inv.sum()], int(c[c.mercado == mercado].casa.nunique())


print("lados 1X2:", c[c.mercado == "Full Time Result"].lado.unique(), "BTTS:", c[c.mercado == "Both Teams To Score"].lado.unique())
ft = c[c.mercado == "Full Time Result"].lado.unique().tolist()
orden = [l_ for l_ in ("Home", "Draw", "Away") if l_ in ft] or [l_ for l_ in ("1", "X", "2") if l_ in ft]
casa = {"1x2": sin_margen("Full Time Result", orden), "mas15": sin_margen("Total Goals 1.5", ["Over", "Under"]),
        "mas25": sin_margen("Total Goals 2.5", ["Over", "Under"]), "ambos": sin_margen("Both Teams To Score", ["Yes", "No"])}
gl, gv = int(M.goles_l), int(M.goles_v)
real = {"1x2": 0 if gl > gv else (1 if gl == gv else 2), "mas15": gl + gv > 1, "mas25": gl + gv > 2, "ambos": gl > 0 and gv > 0}
fd = A.fd_post
cierre = 1 / np.array([fd.AvgCH, fd.AvgCD, fd.AvgCA])
OUT["informe2"] = {"merecido": merecido, "nuestro": nuestro,
                   "casa": {k: v[0] for k, v in casa.items()}, "casas_n": {k: v[1] for k, v in casa.items()},
                   "cierre_1x2_fd": [r(v * 100, 0) for v in cierre / cierre.sum()], "real": real}
print("informe2:", OUT["informe2"]["nuestro"], OUT["informe2"]["casa"], OUT["informe2"]["casas_n"], OUT["informe2"]["cierre_1x2_fd"])

# ------------------------------------------------------------------ zona contra zona y duelos por puesto
fl = A.lu[A.lu.match_id == M.match_id].iloc[0]
xp = A.xp.set_index("jugador_id")


def jug(i):
    f = xp.loc[i]
    return {"jugador": A.nom.get(i, "?"), "min": int(f.minutos), "nota": r(f.nota), "duelos": int(f.duelsWon),
            "duelos_t": int(f.duelsTotal), "entradas": int(f.tacklesTotal), "intercep": int(f.interceptionsTotal),
            "regates": int(f.dribblesSuccessful), "tiros": int(f.shotsTotal), "xg": r(f.expectedGoals if pd.notna(f.expectedGoals) else 0),
            "pases_clave": int(f.passesKey)}


def lineas(ids_txt, form):
    ids_ = [int(x) for x in str(ids_txt).split("|")]
    out, k = [], 0
    for n in [1] + [int(n) for n in str(form).split("-")]:
        out.append(ids_[k:k + n])  # de izquierda a derecha (Hancko, Romero, Pubill, Llorente)
        k += n
    return out


la, lv = lineas(fl.local_ids, fl.local_formacion), lineas(fl.visitante_ids, fl.visitante_formacion)


def ataque(ls):
    """(izquierda, derecha, centro) de quienes atacan: los extremos de la línea de detrás de los delanteros, y los delanteros."""
    delanteros = ls[-1]
    detras = ls[-2]
    izq, der = detras[0], detras[-1]
    return izq, der, delanteros if len(delanteros) > 1 else [detras[len(detras) // 2], delanteros[0]]


def defensa(ls):
    d = ls[1]
    return d[0], d[-1], d[1:-1]  # lateral izquierdo, lateral derecho, centrales (de izquierda a derecha)


def duelos(ls_at, ls_def):
    izq, der, cen = ataque(ls_at)
    li, ld, cs = defensa(ls_def)
    pares = [(izq, ld), (der, li)]  # su extremo izquierdo contra el lateral derecho rival, y al revés
    # centro: el de la izquierda del ataque contra el central derecho rival
    for a_, d_ in zip(cen, reversed(cs)):
        pares.append((a_, d_))
    return [{"at": jug(a_), "df": jug(d_)} for a_, d_ in pares]


def zona(ls_at, ls_def):
    izq, der, cen = ataque(ls_at)
    at = [izq, der] + list(cen)
    df = [ls_def[0][0]] + list(ls_def[1])
    A_ = [jug(i) for i in at]
    D_ = [jug(i) for i in df]
    return {"ataque": {"xg": r(sum(j["xg"] for j in A_), 2), "tiros": sum(j["tiros"] for j in A_),
                       "regates": sum(j["regates"] for j in A_), "duelos": sum(j["duelos"] for j in A_),
                       "duelos_t": sum(j["duelos_t"] for j in A_), "nota": r(np.nanmean([j["nota"] for j in A_]), 2)},
            "defensa": {"entradas": sum(j["entradas"] for j in D_), "intercep": sum(j["intercep"] for j in D_),
                        "duelos": sum(j["duelos"] for j in D_), "duelos_t": sum(j["duelos_t"] for j in D_),
                        "nota": r(np.nanmean([j["nota"] for j in D_]), 2)}}


OUT["duelos"] = {"atm_ataque": zona(la, lv), "rma_ataque": zona(lv, la),
                 "pares_atm": duelos(la, lv), "pares_rma": duelos(lv, la),
                 "lineas": {"local": [[A.nom.get(i, "?") for i in l_] for l_ in la],
                            "visitante": [[A.nom.get(i, "?") for i in l_] for l_ in lv]}}
print("líneas:", OUT["duelos"]["lineas"])
print("pares ATM:", [(p["at"]["jugador"], p["df"]["jugador"]) for p in OUT["duelos"]["pares_atm"]])
print("pares RMA:", [(p["at"]["jugador"], p["df"]["jugador"]) for p in OUT["duelos"]["pares_rma"]])
print("zonas:", OUT["duelos"]["atm_ataque"], OUT["duelos"]["rma_ataque"])

# ------------------------------------------------------------------ tablas: ranking 2yellow (Elo) y clasificación real
t = A.L[A.L.temporada == 2026]
wdl = t.groupby("eqn").agg(g=("pts", lambda s: int((s == 3).sum())), e=("pts", lambda s: int((s == 1).sum())),
                           p=("pts", lambda s: int((s == 0).sum())))
filas = A.SALIDA["tabla_elo"]["filas"]
liga = [{**f, "g": int(wdl.loc[f["equipo"], "g"]), "e": int(wdl.loc[f["equipo"], "e"]), "p": int(wdl.loc[f["equipo"], "p"]),
         "dg": int(A.t26.loc[f["equipo"], "dg"])} for f in filas]
ranking = sorted(liga, key=lambda f: -f["elo"])
for i, f in enumerate(ranking):
    f["rank"] = i + 1
OUT["tablas"] = {"liga": liga, "ranking": ranking}

# ------------------------------------------------------------------ estilos en unidades normales
cols = {"possession": "Possession", "total_passes": "Passes", "shots_outside_penalty_area": "Long shots",
        "interceptions": "Interceptions", "crosses": "Crosses", "aerial_duels": "Aerial duels", "tackles": "Tackles"}
E = A.ll[A.ll.temporada >= 2025]
per = pd.concat([E.assign(eqn=E.local, **{k: E["l_" + k] for k in cols}),
                 E.assign(eqn=E.visitante, **{k: E["v_" + k] for k in cols})]).groupby("eqn")[list(cols)].mean()
z = (per - per.mean()) / per.std()
media = per.mean()
ETIQ = [("possession", 0.8, "Keeps the ball"), ("possession", -0.8, "Plays without the ball"),
        ("shots_outside_penalty_area", 0.8, "Shoots from distance"), ("crosses", 0.8, "Crosses a lot"),
        ("interceptions", 0.6, "Reads the game"), ("tackles", 0.8, "Tackles hard"),
        ("aerial_duels", 0.8, "Aerial battles"), ("aerial_duels", -0.8, "Keeps it on the ground")]


def etiquetas(e):
    out = []
    for c_, u, txt in ETIQ:
        v = z.loc[e, c_]
        if (u > 0 and v >= u) or (u < 0 and v <= u):
            out.append((abs(v), txt))
    return [t_ for _, t_ in sorted(out, reverse=True)[:3]]


OUT["estilos2"] = {"media": {cols[k]: r(media[k] * (100 if k == "possession" else 1), 1) for k in cols},
                   "equipos": {e: {"tags": etiquetas(e), **{cols[k]: r(per.loc[e, k] * (100 if k == "possession" else 1), 1) for k in cols}}
                               for e in A.PREVIA[:2]}}
print("estilos:", OUT["estilos2"])
print("bajas:", OUT["bajas2"])

(AQUI / "datos_extra.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1, default=str))
print("OK datos_extra.json")

# ------------------------------------------------------------------ alineaciones: nota media del once contra sus 10 partidos anteriores
def once_ids(match_id, eq):
    f = A.lu[A.lu.match_id == match_id]
    if not len(f):
        return None
    f = f.iloc[0]
    m = A.ll[A.ll.match_id == match_id].iloc[0]
    txt = f.local_ids if m.local == eq else f.visitante_ids
    return [int(x) for x in str(txt).split("|")] if pd.notna(txt) else None


def media_once(match_id, eq):
    ids_ = once_ids(match_id, eq)
    if not ids_:
        return np.nan
    x = X[(X.match_id == match_id) & X.jugador_id.isin(ids_)].nota.dropna()
    return x.mean() if len(x) >= 9 else np.nan


notas_eq = {}
for e in (M.local, M.visitante):
    hoy = media_once(M.match_id, e)
    prev = A.L[(A.L.eqn == e) & (A.L.fecha < M.fecha)].tail(10)
    medias = [media_once(mid, e) for mid in prev.match_id]
    medias = [v for v in medias if pd.notna(v)]
    notas_eq[e] = {"hoy": r(hoy), "media10": r(np.mean(medias)), "n": len(medias), "dif": r(hoy - np.mean(medias))}
jug_prev = {}
for e in (M.local, M.visitante):
    for i in once_ids(M.match_id, e):
        x = X[(X.jugador_id == i) & (X.fecha < M.fecha) & (X.minutos > 0)].sort_values("fecha").nota.dropna().tail(10)
        hoy = X[(X.match_id == M.match_id) & (X.jugador_id == i)].nota
        if len(x) >= 5 and len(hoy) and pd.notna(hoy.iloc[0]):
            jug_prev[A.nom.get(i, str(i))] = {"media10": r(x.mean()), "dif": r(hoy.iloc[0] - x.mean()), "n": int(len(x))}
OUT["notas_once"] = {"equipos": notas_eq, "jugadores": jug_prev}
print("notas once:", notas_eq)
print("jugadores:", {k: v["dif"] for k, v in jug_prev.items()})
(AQUI / "datos_extra.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1, default=str))
