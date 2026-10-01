"""
Datos para 2yellow · Nations League, con Inglaterra de ejemplo. Sin API.

Lee copias de data/selecciones y modelos/selecciones tomadas de `main` el 30/09/2026
(carpeta datos_main/; de main solo se copia). Reutiliza el modelo de selecciones
(modelos/selecciones/modelo_selecciones.py) sin tocarlo, apuntándolo a la copia.
Escribe diseno_nl/datos_nl.json.

 resultados   Liga A jugados: marcador, xG, nuestro pronóstico previo (acierto o fallo)
 proximos     Liga A, jornada 3: probabilidades del registro; Croacia-Inglaterra con el modelo
 previa       Croacia - Inglaterra (03/10): modelo en local (aún no hay cuotas: 36 h antes)
 informe      Chequia 0-2 Inglaterra (29/09): estadísticas, notas, onces, nuestro % contra la casa
 equipo       Inglaterra: forma, ranking FIFA, goles vs xG, sus jugadores
 grupos       clasificación de los 4 grupos de la Liga A; ranking FIFA
 acierto      todos los partidos evaluados: nuestro favorito contra el de las casas
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DM = AQUI / "datos_main"
sys.path.insert(0, str(RAIZ / "modelos" / "selecciones"))
import modelo_selecciones as S  # noqa: E402
S.CARPETA = str(DM)             # la copia de main, no data/selecciones de esta rama
import pronostico_selecciones as P  # noqa: E402

OUT = {}
HOY = pd.Timestamp("2026-09-30")
r = lambda x, n=2: None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)

cal = pd.read_csv(DM / "nl_calendario.csv")
cal["dia"] = cal.fecha.str[:10]
reg = pd.read_csv(DM / "registro_pronosticos.csv")
est = pd.read_csv(DM / "estadisticas_partido.csv")
est["valor"] = pd.to_numeric(est.valor, errors="coerce")
jp = pd.read_csv(DM / "jugadores_partido.csv")
al = pd.read_csv(DM / "alineaciones.csv")
part = pd.read_csv(DM / "partidos.csv")
fifa = pd.read_csv(DM / "ranking_fifa.csv")
ids = {**dict(zip(part.local, part.local_id)), **dict(zip(part.visitante, part.visitante_id))}
W = {k: P.PESOS_INICIALES.get(k, 0.0) for k in P.MERCADOS}   # los pesos en uso (aún sin aprender: <30 partidos)


def final(fila):
    """Nuestro % final, como en pronostico_selecciones.py: mezcla modelo/mercado con el peso en uso."""
    out = {}
    for k in ("1", "X", "2", "mas_2.5", "btts", "mas_1.5", "mas_3.5"):
        mo, mk = fila.get(f"mod_{k}"), fila.get(f"mkt_{k}")
        out[k] = W[k] * mo + (1 - W[k]) * mk if pd.notna(mk) else mo
    t = out["1"] + out["X"] + out["2"]
    for k in ("1", "X", "2"):
        out[k] /= t
    return out


def previo(mid, inicio, con_mercado=True):
    """Último pronóstico hecho ANTES del pitido (la misma regla que evaluar_selecciones.py).
    Con mercado: el último que aún lleva cuotas. Desde 3 h antes del pitido las pasadas del
    29/09 ya no traen cuotas (mkt_ vacío): si no, la casa no saldría en ningún partido de ese día."""
    x = reg[(reg.match_id == mid) & (pd.to_datetime(reg.generado, format="ISO8601", utc=True) < pd.to_datetime(inicio, utc=True))]
    if con_mercado:
        x = x[x.mkt_1.notna()]
    return x.sort_values("generado").iloc[-1] if len(x) else None


def stat(mid, eqid, nombre):
    x = est[(est.match_id == mid) & (est.equipo_id == eqid) & (est.estadistica == nombre)].valor
    return float(x.iloc[0]) if len(x) else np.nan


def xg_ok(mid, l, v):
    a, b = stat(mid, l, "Expected Goals"), stat(mid, v, "Expected Goals")
    return (np.nan, np.nan) if a == b else (a, b)   # xG idéntico en los dos lados: roto (CLAUDE.md de selecciones)


def sim_xg(a, b, n=100000):
    rng = np.random.default_rng(1)
    x, y = rng.poisson(a, n), rng.poisson(b, n)
    return [r((x > y).mean() * 100, 0), r((x == y).mean() * 100, 0), r((x < y).mean() * 100, 0)]


# ------------------------------------------------------------------ Liga A: resultados con nuestro pronóstico previo
A = cal[cal.ronda.str.startswith("League A")].copy()
res = []
for _, f in A[A.terminado].sort_values("fecha", ascending=False).iterrows():
    l, v = ids[f.local], ids[f.visitante]
    xl, xv = xg_ok(f.match_id, l, v)
    pr = previo(f.match_id, f.fecha)
    gl, gv = int(f.goles_l), int(f.goles_v)
    real = 0 if gl > gv else (1 if gl == gv else 2)
    fila = {"local": f.local, "visitante": f.visitante, "gl": gl, "gv": gv, "fecha": f.dia, "ronda": f.ronda,
            "xg": [r(xl), r(xv)], "merecido": sim_xg(xl, xv) if pd.notna(xl) else None, "match_id": int(f.match_id)}
    if pr is not None:
        fi = final(pr)
        p3 = [fi["1"], fi["X"], fi["2"]]
        fila["nuestro"] = [r(x * 100, 0) for x in p3]
        fila["acierto"] = int(np.argmax(p3)) == real
    res.append(fila)
OUT["resultados"] = res
print("resultados Liga A:", [(x["local"], x["gl"], x["gv"], x["visitante"], x.get("acierto")) for x in res[:6]])

# ------------------------------------------------------------------ modelo en local para Croacia - Inglaterra
p, q, roto, sinq = S.cargar()
f_gol = [S.ajustar(p[p[f"{o}_l"].notna()], q, o, extras=("fifa",)) for o in ("goles", "xg")]
f_cor = S.ajustar(p[p.corners_l.notna()], q, "corners")
f_tar = S.ajustar(p[p.amarillas_l.notna()], q, "amarillas")
notas = pd.read_csv(DM / "notas_2909.csv")   # notas del ciclo del 29/09 (onces reales de ese día)


def modelo(loc, vis):
    tl, tv = ids[loc], ids[vis]
    pf_l, pf_v = S.fifa_antes([HOY.date().isoformat()], [loc])[0], S.fifa_antes([HOY.date().isoformat()], [vis])[0]
    lam = (np.mean([f(tl, tv, 1.0, ext={"fifa": (pf_l, pf_v)}) for f in f_gol]),
           np.mean([f(tv, tl, 0.0, ext={"fifa": (pf_v, pf_l)}) for f in f_gol]))
    fl, ol = P.forma(notas, loc)
    fv, ov = P.forma(notas, vis)
    lam = (lam[0] * np.exp(P.B_FORMA * fl - 0.5 * P.B_FORMA * fv), lam[1] * np.exp(P.B_FORMA * fv - 0.5 * P.B_FORMA * fl))
    gm = S.goles(*lam)
    cor = f_cor(tl, tv, 1.0) + f_cor(tv, tl, 0.0)
    tar = f_tar(tl, tv, 1.0) + f_tar(tv, tl, 0.0)   # árbitro sin designar: factor 1
    return {"lam": [r(lam[0]), r(lam[1])], "p1x2": [r(gm[k] * 100, 0) for k in ("1", "X", "2")],
            "mas15": r(gm["mas_1.5"] * 100, 0), "mas25": r(gm["mas_2.5"] * 100, 0), "mas35": r(gm["mas_3.5"] * 100, 0),
            "btts": r(gm["btts"] * 100, 0), "marcador": [int(gm["marcador"][0]), int(gm["marcador"][1])],
            "primero": [r(gm["primero_local"] * 100, 0), r(gm["primero_visitante"] * 100, 0), r(gm["sin_goles"] * 100, 0)],
            "corners": r(cor, 1), "corners_85": r(S.prob_mas(cor, 8.5, P.DISPERSION["corners"]) * 100, 0),
            "corners_95": r(S.prob_mas(cor, 9.5, P.DISPERSION["corners"]) * 100, 0),
            "tarjetas": r(tar, 1), "tarjetas_35": r(S.prob_mas(tar, 3.5, P.DISPERSION["amarillas"]) * 100, 0),
            "forma": [r(fl), r(fv)], "fifa_pts": [r(pf_l, 0), r(pf_v, 0)],
            "once": {loc: ol[["jugador", "posicion", "nota"]].to_dict("records"),
                     vis: ov[["jugador", "posicion", "nota"]].to_dict("records")}}


# ------------------------------------------------------------------ próxima jornada de la Liga A
prox = []
for _, f in A[(~A.terminado) & (A.dia <= "2026-10-03")].sort_values("fecha").iterrows():
    x = reg[reg.match_id == f.match_id].sort_values("generado")
    fila = {"local": f.local, "visitante": f.visitante, "fecha": f.fecha, "ronda": f.ronda, "p": None, "fuente": None}
    if len(x):
        fi = final(x.iloc[-1])
        fila["p"], fila["fuente"] = [r(fi[k] * 100, 0) for k in ("1", "X", "2")], "registro"
    else:   # sin pasada del ciclo todavía: el mismo modelo en local
        fila["p"], fila["fuente"] = modelo(f.local, f.visitante)["p1x2"], "modelo"
    prox.append(fila)
OUT["proximos"] = prox
print("próximos:", [(x["local"], x["visitante"], x["p"], x["fuente"]) for x in prox])

# ------------------------------------------------------------------ previa Croacia - Inglaterra
PV = modelo("Croatia", "England")
ult = fifa[fifa.fecha == fifa.fecha.max()].set_index("equipo")
PV["fifa_puesto"] = [int(ult.loc["Croatia", "puesto"]), int(ult.loc["England", "puesto"])]


def forma_eq(eq, n=5, hasta="2026-10-01"):
    d = part[((part.local == eq) | (part.visitante == eq)) & part.terminado & (part.fecha < hasta)].sort_values("fecha").tail(n)
    out = []
    for _, f in d.iterrows():
        casa = f.local == eq
        gf, gc = (f.goles_l, f.goles_v) if casa else (f.goles_v, f.goles_l)
        out.append({"riv": f.visitante if casa else f.local, "casa": bool(casa), "gf": int(gf), "gc": int(gc),
                    "comp": f.competicion, "fecha": f.fecha[:10]})
    return out


PV["forma"] = {e: forma_eq(e) for e in ("Croatia", "England")}
h2h = part[(((part.local == "Croatia") & (part.visitante == "England")) | ((part.local == "England") & (part.visitante == "Croatia")))
           & part.terminado]
PV["h2h"] = [{"local": f.local, "visitante": f.visitante, "gl": int(f.goles_l), "gv": int(f.goles_v), "fecha": f.fecha[:10],
              "comp": f.competicion} for _, f in h2h.sort_values("fecha").iterrows()]
OUT["previa"] = PV
print("previa CRO-ENG:", {k: PV[k] for k in ("lam", "p1x2", "mas25", "btts", "marcador", "corners", "tarjetas", "forma", "fifa_pts", "fifa_puesto")})

# ------------------------------------------------------------------ informe Chequia 0-2 Inglaterra (29/09)
m = A[(A.local == "Czech Republic") & (A.visitante == "England")].iloc[0]
MID, LID, VID = int(m.match_id), ids["Czech Republic"], ids["England"]
ST = ["Expected Goals", "Possession", "Shots on target", "Shots off target", "Blocked shots", "Shots within penalty area",
      "Big Chances Created", "Total passes", "Passes Into Final Third", "Key Passes", "Crosses", "Tackles", "Interceptions",
      "Clearances", "Goalkeeper saves", "Fouls", "Yellow cards", "Red cards", "Offsides", "Corners"]
stats = {s: [r(stat(MID, LID, s)), r(stat(MID, VID, s))] for s in ST}
x = jp[(jp.match_id == MID)].copy()
x["nota"] = pd.to_numeric(x.nota, errors="coerce")
x["eqn"] = np.where(x.equipo_id == LID, "Czech Republic", "England")   # «eq» chocaba con DataFrame.eq
jug = [{"jugador": f.jugador, "equipo": f.eqn, "pos": f.posicion, "min": int(f.minutos), "nota": r(f.nota),
        "goles": int(f.goalsScored), "asist": int(f.assists), "suplente": bool(f.suplente)}
       for _, f in x[x.minutos > 0].sort_values("nota", ascending=False).iterrows()]
gks = [{"jugador": f.jugador, "equipo": f.eqn, "paradas": int(f.goalsSaved),
        "evitados": r(pd.to_numeric(f.get("expectedGoalsPrevented"), errors="coerce"))}
       for _, f in x[(x.posicion == "Goalkeeper") & (x.minutos > 0)].iterrows()]
lin = {}
for eqn, eid in (("Czech Republic", LID), ("England", VID)):
    a = al[(al.match_id == MID) & (al.equipo_id == eid)]
    form = a.formacion.iloc[0]
    ids_ = a.jugador_id.tolist()
    nom = dict(zip(a.jugador_id, a.jugador))
    notas_m = dict(zip(x.jugador_id, x.nota))   # por ID: los nombres no coinciden entre alineaciones y notas
    filas, k = [], 0
    for n in [1] + [int(t) for t in str(form).split("-")]:
        filas.append([{"jugador": nom[j], "nota": r(notas_m.get(j))} for j in ids_[k:k + n]])
        k += n
    lin[eqn] = {"formacion": form, "lineas": filas}
pr = previo(MID, m.fecha)
fi = final(pr)
gl, gv = int(m.goles_l), int(m.goles_v)
realm = {"1x2": 0 if gl > gv else (1 if gl == gv else 2), "mas15": gl + gv > 1, "mas25": gl + gv > 2, "btts": gl > 0 and gv > 0}
mk = lambda k: r(pr[f"mkt_{k}"] * 100, 0) if pd.notna(pr[f"mkt_{k}"]) else None
t3 = sum(pr[f"mkt_{k}"] for k in ("1", "X", "2"))
OUT["informe"] = {
    "local": "Czech Republic", "visitante": "England", "gl": gl, "gv": gv, "fecha": m.dia, "ronda": m.ronda,
    "stats": stats, "merecido": sim_xg(stats["Expected Goals"][0], stats["Expected Goals"][1]),
    "jugadores": jug, "porteros": gks, "lineas": lin,
    "nuestro": {"1x2": [r(fi[k] * 100, 0) for k in ("1", "X", "2")], "mas15": r(fi["mas_1.5"] * 100, 0),
                "mas25": r(fi["mas_2.5"] * 100, 0), "btts": r(fi["btts"] * 100, 0)},
    "casa": {"1x2": [r(pr[f"mkt_{k}"] / t3 * 100, 0) for k in ("1", "X", "2")], "mas15": mk("mas_1.5"),
             "mas25": mk("mas_2.5"), "btts": mk("btts")},
    "real": realm, "fuente_once": pr.fuente_once, "generado": pr.generado,
    "horas_antes": r((pd.to_datetime(m.fecha, utc=True) - pd.to_datetime(pr.generado, utc=True)).total_seconds() / 3600, 1),
    "esperados": [r(pr.lam_l), r(pr.lam_v)], "corners_esp": r(pr.corners, 1), "tarjetas_esp": r(pr.tarjetas, 1),
    "corners_real": [r(stat(MID, LID, "Corners"), 0), r(stat(MID, VID, "Corners"), 0)],
    "fifa_antes": [r(S.fifa_antes([m.dia], ["Czech Republic"])[0], 0), r(S.fifa_antes([m.dia], ["England"])[0], 0)]}
print("informe CZE-ENG:", OUT["informe"]["nuestro"], OUT["informe"]["casa"], OUT["informe"]["real"], "xG", stats["Expected Goals"])

# ------------------------------------------------------------------ equipo: Inglaterra
E = part[((part.local == "England") | (part.visitante == "England")) & part.terminado].sort_values("fecha")
filas = []
for _, f in E.iterrows():
    casa = f.local == "England"
    xl, xv = xg_ok(f.match_id, f.local_id, f.visitante_id)
    filas.append({"fecha": f.fecha[:10], "riv": f.visitante if casa else f.local, "casa": bool(casa), "comp": f.competicion,
                  "gf": int(f.goles_l if casa else f.goles_v), "gc": int(f.goles_v if casa else f.goles_l),
                  "xg": r(xl if casa else xv), "xga": r(xv if casa else xl)})
ing_fifa = fifa[fifa.equipo == "England"].sort_values("fecha")
jj = jp[jp.equipo_id == ids["England"]].copy()
jj["nota"] = pd.to_numeric(jj.nota, errors="coerce")
jj = jj.merge(part[["match_id", "fecha"]], on="match_id")
jj = jj[jj.fecha >= "2025-01-01"]
top = jj[jj.minutos > 0].groupby("jugador").agg(pj=("match_id", "nunique"), min=("minutos", "sum"), goles=("goalsScored", "sum"),
                                                 asist=("assists", "sum"), nota=("nota", "mean"), xg=("expectedGoals", "sum"))
top = top[top["min"] >= 270]
OUT["equipo"] = {"partidos": filas, "fifa": [{"fecha": f.fecha, "puesto": int(f.puesto), "puntos": r(f.puntos, 0)} for _, f in ing_fifa.iterrows()],
                 "goleadores": [{"jugador": i, **{k: (r(v) if k in ("nota", "xg") else int(v)) for k, v in f.items()}}
                                for i, f in top.sort_values(["goles", "nota"], ascending=False).head(5).iterrows()],
                 "mejores": [{"jugador": i, "nota": r(f.nota), "pj": int(f.pj)} for i, f in top.sort_values("nota", ascending=False).head(5).iterrows()]}
print("Inglaterra:", len(filas), "partidos; FIFA", OUT["equipo"]["fifa"][-1], "goleadores", [(g["jugador"], g["goles"]) for g in OUT["equipo"]["goleadores"]])

# ------------------------------------------------------------------ Inglaterra en el pasado: balance, Mundial, dominio, porterías
Pd = pd.DataFrame(filas)
Pd["r"] = np.where(Pd.gf > Pd.gc, "W", np.where(Pd.gf == Pd.gc, "D", "L"))
bal = [{"comp": c, "pj": int(len(g)), "g": int((g.r == "W").sum()), "e": int((g.r == "D").sum()), "p": int((g.r == "L").sum()),
        "gf": int(g.gf.sum()), "gc": int(g.gc.sum())} for c, g in Pd.groupby("comp")]
ms = part[((part.local == "England") | (part.visitante == "England")) & part.terminado & (part.fecha >= "2025-01-01")].match_id
ss = est[est.match_id.isin(ms)]
dom = {}
for st_ in ("Possession", "Shots on target", "Big Chances Created", "Corners", "Yellow cards"):
    a_ = ss[(ss.estadistica == st_) & (ss.equipo_id == ids["England"])].valor
    b_ = ss[(ss.estadistica == st_) & (ss.equipo_id != ids["England"])].valor
    dom[st_] = [r(a_.mean()), r(b_.mean()), int(len(a_))]
OUT["historial"] = {"desde": str(Pd.fecha.min()), "pj": int(len(Pd)), "g": int((Pd.r == "W").sum()), "e": int((Pd.r == "D").sum()),
                    "p": int((Pd.r == "L").sum()), "gf": int(Pd.gf.sum()), "gc": int(Pd.gc.sum()),
                    "porterias_cero": int((Pd.gc == 0).sum()), "balance": bal, "dominio": dom,
                    "mundial": Pd[Pd.comp == "World Cup"][["fecha", "riv", "gf", "gc", "xg", "xga"]].to_dict("records"),
                    "clasificacion": Pd[Pd.comp == "World Cup - Qualification Europe"][["fecha", "riv", "casa", "gf", "gc"]].to_dict("records"),
                    "derrotas": Pd[Pd.r == "L"][["fecha", "riv", "comp", "gf", "gc"]].to_dict("records"),
                    "mayores": Pd.assign(d=Pd.gf - Pd.gc).sort_values(["d", "gf"], ascending=False).head(3)[["fecha", "riv", "comp", "casa", "gf", "gc"]].to_dict("records")}
print("historial:", {k: OUT["historial"][k] for k in ("pj", "g", "e", "p", "gf", "gc", "porterias_cero")}, OUT["historial"]["dominio"])


# ------------------------------------------------------------------ minuto a minuto (sondeo del 01/10: /matches/{id} de partidos terminados)
# Trampas comprobadas (IDEAS_API.md): en un cambio `player` SALE y `substituted` ENTRA;
# un penalti marcado es `Penalty`, no `Goal`; los tiros no cuadran al 100% con las
# estadísticas del equipo (la lista vale para el minuto a minuto, no para totales).
import re
import unicodedata
RAW = AQUI.parent / "sondeos" / "raw"


def minuto(t):
    n = [int(x) for x in re.findall(r"\d+", str(t))]
    return (n[0], n[1] if len(n) > 1 else 0) if n else (None, 0)


def plano(n):
    return unicodedata.normalize("NFKD", str(n)).encode("ascii", "ignore").decode().lower()


def apellido_ok(a, b):
    """«Anthony Gordon» y «A. Gordon» son el mismo; compara por el último apellido sin tildes."""
    return plano(a).split()[-1] == plano(b).split()[-1]


def minuto_a_minuto(mid, local, visitante):
    d = json.loads((RAW / f"match_{mid}.json").read_text())
    d = d[0] if isinstance(d, list) else d
    lado = {d["homeTeam"]["id"]: "l", d["awayTeam"]["id"]: "v"}
    jj = jp[jp.match_id == mid]
    eqid = {"l": ids[local], "v": ids[visitante]}

    def nota(nombre, l_):
        # el que entra siempre es suplente: así no se confunden dos con el mismo apellido
        # (Croacia: Mario Pašalić entra, Marco Pašalić es titular)
        x = jj[(jj.equipo_id == eqid[l_]) & (jj.suplente == True) & jj.jugador.map(lambda j: apellido_ok(j, nombre))]  # noqa: E712
        if len(x) > 1:
            x = x[x.jugador.map(lambda j: plano(j).split()[0][0] == plano(nombre).split()[0][0])]
        v = pd.to_numeric(x.nota, errors="coerce").dropna()
        return r(v.iloc[0]) if len(v) else None
    ev = []
    for e in d["events"]:
        m, extra = minuto(e["time"])
        l_ = lado.get(e["team"]["id"])
        t = e["type"]
        tipo = {"Goal": "gol", "Penalty": "gol", "Own Goal": "gol_pp", "Yellow Card": "amarilla", "Red Card": "roja",
                "Substitution": "cambio", "Missed Penalty": "penalti_fallado"}.get(t, t)
        x = {"min": m, "extra": extra, "lado": l_, "tipo": tipo, "penalti": t == "Penalty"}
        if tipo == "cambio":
            x.update({"sale": e.get("player"), "entra": e.get("substituted"), "nota_entra": nota(e.get("substituted") or "?", l_)})
        else:
            x.update({"jugador": e.get("player"), "asist": e.get("assist")})
        ev.append(x)
    tiros = []
    for t_, l_ in (("homeTeam", "l"), ("awayTeam", "v")):
        for s_ in d[t_]["shots"]:
            m, extra = minuto(s_["time"])
            tiros.append({"min": m, "extra": extra, "lado": l_, "jugador": s_["playerName"], "res": s_["outcome"],
                          "zona": (s_["goalTarget"] or "").replace("CloseLeft", "Close Left")})
    claves = [plano(w) for w in (local, visitante)] + [plano(x.get("jugador") or x.get("entra") or "").split()[-1]
                                                       for x in ev if (x.get("jugador") or x.get("entra"))]
    claves += ["tuchel", "three lions", "croatia", "czech", "spain", "england"]
    news = []
    for n_ in d.get("news") or []:
        tit = plano(n_["title"])
        if any(k and k in tit for k in claves) and not any(x in tit for x in ("how to watch", "boots", "free stream")):
            news.append({"titulo": n_["title"], "fuente": n_["url"].split("/")[2].replace("www.", "").replace("undefined", ""),
                         "fecha": n_["datePublished"][:10]})
    return {"venue": d.get("venue"), "arbitro": d.get("referee"), "tiempo": d.get("forecast"), "eventos": ev, "tiros": tiros,
            "news": news[:4], "marcador": d["state"]["score"]["current"]}


OUT["minuto"] = {"Czech Republic-England": minuto_a_minuto(1301103194, "Czech Republic", "England"),
                 "Spain-Croatia": minuto_a_minuto(1301102343, "Spain", "Croatia")}
for k, v in OUT["minuto"].items():
    print("minuto", k, v["marcador"], len(v["eventos"]), "eventos,", len(v["tiros"]), "tiros,", len(v["news"]), "noticias",
          [(e["min"], e["tipo"], e.get("jugador") or (e.get("sale"), e.get("entra"), e.get("nota_entra"))) for e in v["eventos"] if e["tipo"] in ("gol", "roja", "cambio")][:8])


# ------------------------------------------------------------------ previa: qué se juegan, último cara a cara, choque de estilos
G4 = ["England", "Croatia", "Spain", "Czech Republic"]
pg = part[(part.competicion == "UEFA Nations League") & part.local.isin(G4) & part.visitante.isin(G4)]
jugados = pg[pg.terminado]
quedan = pg[~pg.terminado].sort_values("fecha")
lam_q = {int(f.match_id): modelo(f.local, f.visitante)["lam"] for _, f in quedan.iterrows()}
rng = np.random.default_rng(7)
NS = 20000
pos = {e: np.zeros(4) for e in G4}
cond = {k: {"n": 0, "pos": np.zeros(4)} for k in ("W", "D", "L")}   # según el Croacia - Inglaterra del sábado
mid_sab = int(quedan[(quedan.local == "Croatia") & (quedan.visitante == "England")].match_id.iloc[0])
base = [(f.local, f.visitante, int(f.goles_l), int(f.goles_v)) for _, f in jugados.iterrows()]
sims = {m: (rng.poisson(lam_q[m][0], NS), rng.poisson(lam_q[m][1], NS)) for m in lam_q}
filas_q = [(int(f.match_id), f.local, f.visitante) for _, f in quedan.iterrows()]


def tabla(res):
    t = {e: [0, 0, 0] for e in G4}   # puntos, dg, gf
    for l_, v_, a_, b_ in res:
        t[l_][1] += a_ - b_; t[v_][1] += b_ - a_; t[l_][2] += a_; t[v_][2] += b_
        t[l_][0] += 3 if a_ > b_ else (1 if a_ == b_ else 0)
        t[v_][0] += 3 if b_ > a_ else (1 if a_ == b_ else 0)
    # desempate: puntos; entre empatados, puntos y diferencia en sus partidos; luego diferencia y goles totales
    def clave(e):
        empatados = [x for x in G4 if t[x][0] == t[e][0]]
        h = [0, 0]
        for l_, v_, a_, b_ in res:
            if l_ in empatados and v_ in empatados and e in (l_, v_):
                gf, gc = (a_, b_) if e == l_ else (b_, a_)
                h[0] += 3 if gf > gc else (1 if gf == gc else 0)
                h[1] += gf - gc
        return (t[e][0], h[0], h[1], t[e][1], t[e][2])
    return sorted(G4, key=clave, reverse=True)


for i in range(NS):
    res = base + [(l_, v_, int(sims[m][0][i]), int(sims[m][1][i])) for m, l_, v_ in filas_q]
    orden = tabla(res)
    for k, e in enumerate(orden):
        pos[e][k] += 1
    a_, b_ = sims[mid_sab][0][i], sims[mid_sab][1][i]
    r_ = "W" if b_ > a_ else ("D" if a_ == b_ else "L")   # visto desde Inglaterra (visitante)
    cond[r_]["n"] += 1
    cond[r_]["pos"][orden.index("England")] += 1
OUT["en_juego"] = {"pos": {e: [r(x / NS * 100, 0) for x in pos[e]] for e in G4},
                   "si": {k: {"n": r(v["n"] / NS * 100, 0), "primero": r(v["pos"][0] / max(v["n"], 1) * 100, 0),
                              "top2": r((v["pos"][0] + v["pos"][1]) / max(v["n"], 1) * 100, 0)} for k, v in cond.items()},
                   "quedan": [{"fecha": f.fecha, "local": f.local, "visitante": f.visitante} for _, f in quedan.iterrows()],
                   "sims": NS}
print("en juego:", OUT["en_juego"]["pos"], OUT["en_juego"]["si"])

wc = part[(part.local == "England") & (part.visitante == "Croatia") & (part.competicion == "World Cup")].iloc[0]
jw = jp[jp.match_id == wc.match_id].copy()
jw["nota"] = pd.to_numeric(jw.nota, errors="coerce")
jw["eqn"] = np.where(jw.equipo_id == ids["England"], "England", "Croatia")
xl, xv = xg_ok(wc.match_id, wc.local_id, wc.visitante_id)
OUT["ultimo_cara"] = {"fecha": wc.fecha[:10], "comp": wc.competicion, "gl": int(wc.goles_l), "gv": int(wc.goles_v), "xg": [r(xl), r(xv)],
                      "goles": [{"jugador": f.jugador, "equipo": f.eqn, "n": int(f.goalsScored)} for _, f in jw[jw.goalsScored > 0].sort_values("goalsScored", ascending=False).iterrows()],
                      "asist": [{"jugador": f.jugador, "equipo": f.eqn} for _, f in jw[jw.assists > 0].iterrows()],
                      "mejores": [{"jugador": f.jugador, "equipo": f.eqn, "nota": r(f.nota)} for _, f in jw.dropna(subset=["nota"]).sort_values("nota", ascending=False).head(3).iterrows()],
                      "stats": {s_: [r(stat(wc.match_id, wc.local_id, s_)), r(stat(wc.match_id, wc.visitante_id, s_))] for s_ in ("Possession", "Shots on target", "Big Chances Created", "Corners")}}
print("último cara a cara:", OUT["ultimo_cara"]["goles"], OUT["ultimo_cara"]["xg"])


def estilo_sel(e):
    ms = part[((part.local == e) | (part.visitante == e)) & part.terminado & (part.fecha >= "2025-01-01")]
    x = est[est.match_id.isin(ms.match_id)]
    out = {}
    for s_ in ("Possession", "Shots on target", "Big Chances Created", "Corners", "Yellow cards"):
        out[s_] = r(x[(x.estadistica == s_) & (x.equipo_id == ids[e])].valor.mean())
    gc = np.where(ms.local == e, ms.goles_v, ms.goles_l)
    gf = np.where(ms.local == e, ms.goles_l, ms.goles_v)
    out["Goals scored"], out["Goals conceded"], out["pj"] = r(gf.mean()), r(gc.mean()), int(len(ms))
    out["porterias_cero"] = int((gc == 0).sum())
    return out


OUT["estilo_sel"] = {e: estilo_sel(e) for e in ("Croatia", "England")}
print("estilos:", OUT["estilo_sel"])

# ------------------------------------------------------------------ grupos de la Liga A y ranking FIFA
grupos, visto = [], set()
for eq in sorted(set(A.local) | set(A.visitante)):
    if eq in visto:
        continue
    g, pend = set(), [eq]
    while pend:
        e = pend.pop()
        if e in g:
            continue
        g.add(e)
        pend += list(A[A.local == e].visitante) + list(A[A.visitante == e].local)
    visto |= g
    J = A[A.terminado & (A.local.isin(g))]
    t = {e: {"equipo": e, "pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0, "pts": 0} for e in g}
    for _, f in J.iterrows():
        for e, a_, b_ in ((f.local, f.goles_l, f.goles_v), (f.visitante, f.goles_v, f.goles_l)):
            s = t[e]
            s["pj"] += 1; s["gf"] += int(a_); s["gc"] += int(b_)
            k = "g" if a_ > b_ else ("e" if a_ == b_ else "p")
            s[k] += 1
            s["pts"] += {"g": 3, "e": 1, "p": 0}[k]
    tabla = sorted(t.values(), key=lambda s: (-s["pts"], -(s["gf"] - s["gc"]), -s["gf"]))
    for s in tabla:
        s["fifa"] = int(ult.loc[S.ALIAS_FIFA.get(s["equipo"], s["equipo"]), "puesto"])
    grupos.append({"equipos": sorted(g), "tabla": tabla})
grupos.sort(key=lambda g: "England" not in g["equipos"])
for i, g in enumerate(grupos):
    g["nombre"] = f"Group {i + 1}"  # la API no da el nombre del grupo: no se inventa
OUT["grupos"] = grupos
prev_pub = sorted(fifa.fecha.unique())[-2]
pa = fifa[fifa.fecha == prev_pub].set_index("equipo")
OUT["fifa"] = [{"equipo": e, "codigo": f.codigo, "puesto": int(f.puesto), "puntos": r(f.puntos, 0),
                "cambio": int(pa.loc[e, "puesto"] - f.puesto) if e in pa.index else 0}
               for e, f in ult.sort_values("puesto").head(20).iterrows()]
OUT["fifa_fecha"] = str(fifa.fecha.max())
print("grupo de Inglaterra:", [(s["equipo"], s["pts"]) for s in grupos[0]["tabla"]])

# ------------------------------------------------------------------ acierto: nuestro favorito contra el de las casas
ev = []
for _, f in cal[cal.terminado].iterrows():
    pr = previo(f.match_id, f.fecha)
    if pr is None or pd.isna(pr.mkt_1):
        continue
    fi = final(pr)
    gl, gv = int(f.goles_l), int(f.goles_v)
    real = 0 if gl > gv else (1 if gl == gv else 2)
    fila = {"n1x2_n": int(np.argmax([fi["1"], fi["X"], fi["2"]])) == real,
            "n1x2_c": int(np.argmax([pr.mkt_1, pr.mkt_X, pr.mkt_2])) == real}
    for k, pasa in (("mas_2.5", gl + gv > 2), ("btts", gl > 0 and gv > 0), ("mas_1.5", gl + gv > 1)):
        if pd.notna(pr[f"mkt_{k}"]):
            fila[f"{k}_n"] = (fi[k] >= 0.5) == pasa
            fila[f"{k}_c"] = (pr[f"mkt_{k}"] >= 0.5) == pasa
    ev.append(fila)
ev = pd.DataFrame(ev)
OUT["acierto"] = {"n": int(len(ev)), "mercados": [
    {"mercado": nm, "n": int(ev[f"{k}_n"].notna().sum()), "nuestro": r(ev[f"{k}_n"].dropna().mean() * 100, 0),
     "casa": r(ev[f"{k}_c"].dropna().mean() * 100, 0)}
    for k, nm in (("n1x2", "Result"), ("mas_1.5", "Over 1.5"), ("mas_2.5", "Over 2.5"), ("btts", "Both score"))]}
print("acierto:", OUT["acierto"])

# ------------------------------------------------------------------ tips de la jornada (registro: partidos del 01/10, con cuotas)
tips = []
cuotas = pd.read_csv(DM / "cuotas_hoy.csv")
for mid, x in reg[reg.fecha_partido.str.startswith("2026-10-01")].groupby("match_id"):
    pr = x.sort_values("generado").iloc[-1]
    fi = final(pr)
    c = cuotas[cuotas.match_id == mid]
    for k, txt_si, txt_no, merc, si, no in (("mas_2.5", "Over 2.5 goals", "Under 2.5 goals", "Total Goals 2.5", "Over", "Under"),
                                            ("btts", "Both teams score", "Not both score", "Both Teams To Score", "Yes", "No")):
        s = fi[k] >= 0.5
        pf = fi[k] if s else 1 - fi[k]
        pk = pr[f"mkt_{k}"] if s else 1 - pr[f"mkt_{k}"]
        o = c[(c.mercado == merc) & (c.lado == (si if s else no))].cuota
        tips.append({"partido": f"{pr.local} – {pr.visitante}", "local": pr.local, "visitante": pr.visitante,
                     "pick": txt_si if s else txt_no, "p": r(pf * 100, 0), "casa": r(pk * 100, 0),
                     "mejor": r(o[o <= o.median() * 1.12].max()) if len(o) else None, "mediana": r(o.median()) if len(o) else None,
                     "casas": int(c[c.mercado == merc].casa.nunique())})
    k1 = int(np.argmax([fi["1"], fi["X"], fi["2"]]))
    lado = ["Home", "Draw", "Away"][k1]
    o = c[(c.mercado == "Full Time Result") & (c.lado == lado)].cuota
    tips.append({"partido": f"{pr.local} – {pr.visitante}", "local": pr.local, "visitante": pr.visitante,
                 "pick": [f"{pr.local} to win", "Draw", f"{pr.visitante} to win"][k1], "p": r([fi["1"], fi["X"], fi["2"]][k1] * 100, 0),
                 "casa": r([pr.mkt_1, pr.mkt_X, pr.mkt_2][k1] / (pr.mkt_1 + pr.mkt_X + pr.mkt_2) * 100, 0),
                 "mejor": r(o[o <= o.median() * 1.12].max()) if len(o) else None, "mediana": r(o.median()) if len(o) else None,
                 "casas": int(c[c.mercado == "Full Time Result"].casa.nunique())})
tips = sorted(tips, key=lambda t: -t["p"])
uno = {}
for t in tips:
    if 55 <= t["p"] <= 90 and t["partido"] not in uno:
        uno[t["partido"]] = t
OUT["tips"] = list(uno.values())[:6]
print("tips:", [(t["partido"], t["pick"], t["p"], t["casa"], t["mejor"]) for t in OUT["tips"]])

(AQUI / "datos_nl.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1, default=str))
print("OK datos_nl.json")
