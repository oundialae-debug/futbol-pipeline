"""
Variables de clubes llevadas a selecciones (28/09/2026). Tema aparte del
proyecto de ambos marcan.

Pregunta del usuario: ¿por qué el modelo de selecciones no tiene las variables
del de clubes, si una selección es como un club? Se prueban las que tienen
equivalente, cada una sin mirar al futuro:

  fifa  puntos del ranking FIFA publicado ANTES del partido (11 publicaciones,
        dic-2024 a jul-2026, data/selecciones/ranking_fifa.csv; sustituye a la
        "clasificación de liga", idea del usuario).
  elo   Elo desde ene-2025, arrancando de los puntos FIFA de dic-2024 (el
        usuario pidió no ir muy atrás: las selecciones de hace años son otras).
  xi    xG y xA por 90 de club de los titulares (sus 10 apariciones de club
        anteriores, encogido a la media de su posición con 270'). Solo cubre
        jugadores de nuestras 6 ligas desde abr-2025: un titular sin dato
        cuenta 0 (= jugador medio de su posición), para no repetir el fallo de
        la "forma inventada" de las selecciones pequeñas.
  (h2h: se mide la cobertura y se descarta si casi no hay pares repetidos.)

Cada variable entra en el Poisson de goles como covariable del atacante y del
defensor, igual que la calidad de plantilla. Prueba hacia delante desde
oct-2025, cada fecha solo con los partidos anteriores, contra el modelo actual
en 1X2, más de 2.5, ambos marcan y sin empate. Salida:
modelos/selecciones/experimento_variables.md
"""
import sys
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor

sys.path.insert(0, "modelos/selecciones")
import modelo_selecciones as S

warnings.filterwarnings("ignore")
DESDE = "2025-10-01"
SALIDA = "modelos/selecciones/experimento_variables.md"
ALIAS = {"Bosnia & Herzegovina": "Bosnia and Herzegovina", "Cape Verde": "Cabo Verde",
         "Czech Republic": "Czechia", "Iran": "IR Iran", "Ivory Coast": "Côte d'Ivoire",
         "Kosovo National Team": "Kosovo", "North Korea": "Korea DPR", "South Korea": "Korea Republic",
         "St. Lucia": "St Lucia", "Turkey": "Türkiye", "Sao Tome and Principe": "São Tomé and Príncipe"}
K_ELO, VENTAJA_CASA = 40.0, 60.0


def fifa_antes(fechas, equipos):
    """Puntos FIFA del último ranking publicado ANTES de cada fecha (NaN si no hay)."""
    r = pd.read_csv("data/selecciones/ranking_fifa.csv")
    r["fecha"] = pd.to_datetime(r.fecha)
    q = pd.DataFrame({"fecha": pd.to_datetime(fechas) - pd.Timedelta(days=1),
                      "equipo": [ALIAS.get(e, e) for e in equipos], "i": range(len(fechas))})
    out = pd.merge_asof(q.sort_values("fecha"), r.sort_values("fecha"), on="fecha", by="equipo",
                        direction="backward").sort_values("i")
    return out.puntos.values


def elo_previo(p):
    """Elo ANTES de cada partido. Arranca de los puntos FIFA de dic-2024."""
    r = pd.read_csv("data/selecciones/ranking_fifa.csv")
    ini = r[r.fecha == r.fecha.min()].set_index("equipo").puntos
    base = ini.quantile(0.1)                          # sin ranking: selección flojita
    elo, pre_l, pre_v = {}, [], []
    for _, x in p.sort_values(["fecha", "match_id"]).iterrows():
        for t, n in ((x.local_id, x.local), (x.visitante_id, x.visitante)):
            elo.setdefault(t, float(ini.get(ALIAS.get(n, n), base)))
        a, b = elo[x.local_id], elo[x.visitante_id]
        pre_l.append((x.match_id, a)); pre_v.append((x.match_id, b))
        esperado = 1 / (1 + 10 ** (-(a + VENTAJA_CASA * x.casa - b) / 400))
        real = 1.0 if x.goles_l > x.goles_v else 0.5 if x.goles_l == x.goles_v else 0.0
        k = K_ELO * (0.5 if x.amistoso else 1.0) * np.log1p(abs(x.goles_l - x.goles_v) or 1)
        elo[x.local_id] += k * (real - esperado)
        elo[x.visitante_id] -= k * (real - esperado)
    return dict(pre_l), dict(pre_v)


def xi_club(p):
    """xG y xA por 90 de club de los titulares, por encima de la media de su posición."""
    club = pd.read_csv("data/historico_xg_jugador.csv",
                       usecols=["match_id", "jugador_id", "posicion", "minutos", "expectedGoals", "expectedAssists"])
    h = pd.read_csv("data/historico_partidos.csv", usecols=["match_id", "fecha"]).set_index("match_id")
    club["fecha"] = pd.to_datetime(club.match_id.map(h.fecha).astype(str).str[:10], errors="coerce")
    club = club[club.fecha.notna() & (pd.to_numeric(club.minutos, errors="coerce") > 0)].copy()
    club["minutos"] = pd.to_numeric(club.minutos, errors="coerce")
    for c in ("expectedGoals", "expectedAssists"):
        club[c] = pd.to_numeric(club[c], errors="coerce").fillna(0)   # vacío = no tiró (88,5%)
    media = club.groupby("posicion").apply(lambda g: pd.Series({
        "xg": g.expectedGoals.sum() / g.minutos.sum() * 90, "xa": g.expectedAssists.sum() / g.minutos.sum() * 90}))
    club = club.sort_values("fecha")
    por_jug = {j: g for j, g in club.groupby("jugador_id")}
    al = pd.read_csv(f"{S.CARPETA}/alineaciones.csv")
    fechas = p.set_index("match_id").fecha
    out = {}
    for (mid, tid), g in al.groupby(["match_id", "equipo_id"]):
        if mid not in fechas.index:
            continue
        f = pd.Timestamp(fechas[mid])
        sx = sa = 0.0
        for jid in g.jugador_id.dropna().astype(int):
            c = por_jug.get(jid)
            if c is None:
                continue
            c = c[c.fecha < f].tail(10)
            if c.empty:
                continue
            pos = c.posicion.mode().iloc[0]
            mu = media.loc[pos] if pos in media.index else media.mean()
            m = c.minutos.sum()
            sx += (c.expectedGoals.sum() * 90 / 90 + mu.xg * 270 / 90) / ((m + 270) / 90) - mu.xg
            sa += (c.expectedAssists.sum() * 90 / 90 + mu.xa * 270 / 90) / ((m + 270) / 90) - mu.xa
        out[(mid, tid)] = (sx, sa)
    return out


def preparar():
    p, q, _, _ = S.cargar()
    p["fifa_l"] = fifa_antes(p.fecha, p.local)
    p["fifa_v"] = fifa_antes(p.fecha, p.visitante)
    base = np.nanpercentile(np.r_[p.fifa_l, p.fifa_v], 10)
    p[["fifa_l", "fifa_v"]] = p[["fifa_l", "fifa_v"]].fillna(base)
    el, ev = elo_previo(p)
    p["elo_l"], p["elo_v"] = p.match_id.map(el), p.match_id.map(ev)
    xi = xi_club(p)
    for k, n in ((0, "xig"), (1, "xia")):
        p[f"{n}_l"] = [xi.get((m, t), (0.0, 0.0))[k] for m, t in zip(p.match_id, p.local_id)]
        p[f"{n}_v"] = [xi.get((m, t), (0.0, 0.0))[k] for m, t in zip(p.match_id, p.visitante_id)]
    p["xi_ok"] = [(m, t) in xi for m, t in zip(p.match_id, p.local_id)]
    # h2h: ¿cuántos partidos tienen un enfrentamiento previo entre las dos en la ventana?
    visto, h2h = set(), 0
    for _, x in p.sort_values("fecha").iterrows():
        par = frozenset((x.local_id, x.visitante_id))
        h2h += par in visto
        visto.add(par)
    return p, q, h2h


def ajustar(p, q, objetivo, extras, escala):
    """S.ajustar con covariables del atacante y del defensor (estandarizadas con el entreno)."""
    a = pd.DataFrame({"at": p.local_id, "de": p.visitante_id, "casa": p.casa, "am": p.amistoso,
                      "y": p[f"{objetivo}_l"], "w": p.w,
                      **{f"{e}_at": p[f"{e}_l"] for e in extras}, **{f"{e}_de": p[f"{e}_v"] for e in extras}})
    b = pd.DataFrame({"at": p.visitante_id, "de": p.local_id, "casa": 0.0, "am": p.amistoso,
                      "y": p[f"{objetivo}_v"], "w": p.w,
                      **{f"{e}_at": p[f"{e}_v"] for e in extras}, **{f"{e}_de": p[f"{e}_l"] for e in extras}})
    d = pd.concat([a, b]).dropna(subset=["y"])
    idx = {t: i for i, t in enumerate(sorted(set(d["at"]) | set(d["de"])))}
    n = len(idx)

    def matriz(df):
        X = np.zeros((len(df), 2 * n + 4 + 2 * len(extras)))
        for k, (x, y) in enumerate(zip(df["at"], df["de"])):
            if x in idx:
                X[k, idx[x]] = 1
            if y in idx:
                X[k, n + idx[y]] = -1
        X[:, 2 * n], X[:, 2 * n + 1] = df.casa, df.am
        X[:, 2 * n + 2] = [10 * q[x] for x in df["at"]]
        X[:, 2 * n + 3] = [-10 * q[y] for y in df["de"]]
        for j, e in enumerate(extras):
            mu, sd = escala[e]
            X[:, 2 * n + 4 + 2 * j] = (df[f"{e}_at"] - mu) / sd
            X[:, 2 * n + 5 + 2 * j] = -(df[f"{e}_de"] - mu) / sd
        return X

    m = PoissonRegressor(alpha=S.ALPHA, max_iter=3000)
    m.fit(matriz(d), d.y, sample_weight=d.w)
    return lambda fila: float(m.predict(matriz(fila))[0])


CONFIGS = {"actual": [], "+fifa": ["fifa"], "+elo": ["elo"], "+xi": ["xig", "xia"],
           "+fifa+elo": ["fifa", "elo"], "+todas": ["fifa", "elo", "xig", "xia"]}


def prueba(p, q):
    filas = []
    for f in sorted(p.fecha[p.fecha >= DESDE].unique()):
        ent = p[p.fecha < f].copy()
        ent["w"] = 0.5 ** ((pd.Timestamp(f) - pd.to_datetime(ent.fecha)).dt.days / S.VIDA_MEDIA)
        hoy = p[p.fecha == f]
        vals = {e: np.r_[ent[f"{e}_l"], ent[f"{e}_v"]] for e in ("fifa", "elo", "xig", "xia")}
        escala = {e: (v.mean(), v.std() or 1.0) for e, v in vals.items()}
        for nombre, ex in CONFIGS.items():
            fs = [ajustar(ent[ent[f"{o}_l"].notna()], q, o, ex, escala) for o in ("goles", "xg")]
            for _, r in hoy.iterrows():
                fa = pd.DataFrame([{"at": r.local_id, "de": r.visitante_id, "casa": r.casa, "am": r.amistoso,
                                    **{f"{e}_at": r[f"{e}_l"] for e in ex}, **{f"{e}_de": r[f"{e}_v"] for e in ex}}])
                fb = pd.DataFrame([{"at": r.visitante_id, "de": r.local_id, "casa": 0.0, "am": r.amistoso,
                                    **{f"{e}_at": r[f"{e}_v"] for e in ex}, **{f"{e}_de": r[f"{e}_l"] for e in ex}}])
                g = S.goles(np.mean([h(fa) for h in fs]), np.mean([h(fb) for h in fs]))
                filas.append({"config": nombre, "match_id": r.match_id, "fecha": f, "gl": r.goles_l, "gv": r.goles_v,
                              "p1": g["1"], "pX": g["X"], "p2": g["2"], "mas25": g["mas_2.5"], "btts": g["btts"],
                              "se": g["1"] / (g["1"] + g["2"])})
    return pd.DataFrame(filas)


def brier(t):
    # .values: con index=match_id, las Series con el índice viejo se alineaban mal y
    # salían NaN (primera corrida del 28/09); sin_empate usaba np.where y sí salía
    t = t.reset_index(drop=True)
    y1, yx, y2 = (t.gl > t.gv) * 1.0, (t.gl == t.gv) * 1.0, (t.gl < t.gv) * 1.0
    return pd.DataFrame({k: np.asarray(v, dtype=float) for k, v in {
        "1X2": (t.p1 - y1) ** 2 + (t.pX - yx) ** 2 + (t.p2 - y2) ** 2,
        "mas_2.5": (t.mas25 - ((t.gl + t.gv) > 2.5)) ** 2,
        "ambos": (t.btts - ((t.gl > 0) & (t.gv > 0))) ** 2,
        "sin_empate": np.where(t.gl != t.gv, (t.se - y1) ** 2, np.nan)}.items()}, index=t.match_id.values)


def main():
    p, q, h2h = preparar()
    cob_xi = p.xi_ok[p.fecha >= DESDE].mean()
    if "--desde-csv" in sys.argv:       # recalcular la tabla sin repetir la prueba (~25 min)
        t = pd.read_csv("data/selecciones/experimento_variables.csv")
    else:
        t = prueba(p, q)
        t.to_csv("data/selecciones/experimento_variables.csv", index=False)
    b = {c: brier(g) for c, g in t.groupby("config")}
    base = b["actual"]
    L = ["# Variables de clubes en el modelo de selecciones", "",
         f"Prueba hacia delante: {t.match_id.nunique()} partidos desde {DESDE}, cada fecha solo con los "
         f"anteriores. Entreno desde ene-2025 (peso por recencia de {S.VIDA_MEDIA:.0f} días). Sigmas "
         "emparejadas contra el modelo actual (+ = mejor; hace falta +2). Brier del 1X2 = suma de las tres.", "",
         f"Cobertura: once conocido en el {cob_xi:.0%} de los partidos de prueba; enfrentamiento previo "
         f"entre las dos selecciones dentro de la ventana en {h2h} de {len(p)} partidos.", "",
         "| config | 1X2 | más de 2.5 | ambos marcan | sin empate | suma sigmas |", "|---|---|---|---|---|---|"]
    for c in CONFIGS:
        celdas, suma = [], 0.0
        for k in base:
            d = (base[k] - b[c][k]).dropna()
            s = d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if c != "actual" and d.std() > 0 else 0.0
            suma += s
            celdas.append(f"{b[c][k].mean():.4f}" + ("" if c == "actual" else f" ({s:+.2f}s)"))
        L.append(f"| {c} | " + " | ".join(celdas) + f" | {'-' if c == 'actual' else f'{suma:+.2f}'} |")
    open(SALIDA, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
