"""Rellena las plantillas de 2yellow con datos REALES de clubes de las 5 grandes ligas (ya en disco, sin API).

Equivalente de datos_selecciones.py para Premier League, La Liga, Serie A, Bundesliga y Ligue 1 (NUNCA Segunda).
    python3 redes/plantillas/datos_clubes.py elegir 2026-10-11                                  # los 2 partidos grandes del día
    python3 redes/plantillas/datos_clubes.py pre "Liverpool" "Manchester City" 2026-10-11
    python3 redes/plantillas/datos_clubes.py post "Manchester United" "Tottenham" 2026-10-10
Deja los JSON y los PNG en redes/plantillas/salida/<fecha>_<local>_<visitante>/ (LIENZO=reel para la zona segura).
SIEMPRE 5 tarjetas + la 6ª (lista tapada) en previo y post (usuario 10/10); si falta una, entra una de relleno con
nuestros datos (forma, casa/fuera, tiros, marcadores; post: el partido en cifras, Elo). ZONA_ESTRICTA=1: sale con
error si algo se sale de x 80-880, y 318-1540 (generar.FUERA).

De dónde sale cada cosa (todo en disco; se lee de origin/main si está, como datos_selecciones.leer):
- Partidos del día: data/calendario.csv (solo las 5 ligas). Resultados, xG y tiros: data/historico_partidos.csv
  (lo actualiza ambos_marcan_diario.yml cada mañana con los de AYER: el post de hoy solo sale al día siguiente).
- % de 1X2, más de 2.5 y ambos marcan: SOLO nuestro modelo, nunca cuotas.
    1) "oficial": último pronóstico ANTES del pitido en data/ambos_marcan/registro_papel.csv (modelo XGBoost oficial,
       lo apunta ambos_marcan_diario.yml el mismo día del partido, ~10:07 Madrid).
    2) si aún no está (p. ej. el previo de mañana), "poisson": ataque/defensa por equipo ajustados con los goles de
       su liga en los 2 años anteriores (Poisson con peso que se reduce a la mitad cada 180 días y encogido hacia la
       media; recién ascendidos, hacia un ascendido típico). Medido en la temporada 2025/26: ver BITACORA 10/10.
  Goles esperados: los del Poisson que reproduce esos % (btts_implicito.ajustar), así el marcador más probable y los
  goles esperados no contradicen el 1X2.
- Elo: mismas reglas que rasgos.calcular_elo (K=20, local +60, multiplicador por goles).
- Tamaño de un partido (elegir): puntos por partido de cada club en las 5 grandes en las 4 temporadas anteriores,
  encogidos hacia 1.0 (lo que hace de media un recién ascendido en su 1ª temporada: 0.98 en 45 casos) con 38 partidos
  de peso. Partido = el más débil de los dos + la mitad del más fuerte: premia que los DOS sean fuertes (con la suma
  salía PSG - Le Mans). No se usa nada del mercado.
Sin "upset alert" (pre2) ni nada que enseñe el % del mercado (usuario: solo % de nuestro modelo).
"""
import io, json, os, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ / "scripts"))
import generar as G  # noqa: E402

LIGAS = ("Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1")   # nunca Segunda División
CORTO = {"Manchester United": "Man United", "Manchester City": "Man City", "Nottingham Forest": "Forest",
         "Wolverhampton Wanderers": "Wolves", "Crystal Palace": "Palace", "Brighton & Hove Albion": "Brighton",
         "Paris Saint Germain": "PSG", "Stade Brestois 29": "Brest", "LE Havre AC": "Le Havre", "Estac Troyes": "Troyes",
         "Rennes FC": "Rennes", "Olympique Lyonnais": "Lyon", "Olympique Marseille": "Marseille",
         "Borussia Mönchengladbach": "Gladbach", "Borussia Dortmund": "Dortmund", "Bayer Leverkusen": "Leverkusen",
         "Eintracht Frankfurt": "Frankfurt", "1899 Hoffenheim": "Hoffenheim", "SC Paderborn 07": "Paderborn",
         "FSV Mainz 05": "Mainz", "FC Schalke 04": "Schalke", "SC Freiburg": "Freiburg", "VfB Stuttgart": "Stuttgart",
         "FC Augsburg": "Augsburg", "SV Elversberg": "Elversberg", "Hamburger SV": "Hamburg", "Werder Bremen": "Bremen",
         "VfL Wolfsburg": "Wolfsburg", "FC Heidenheim": "Heidenheim", "FC St. Pauli": "St. Pauli",
         "Atlético Madrid": "Atlético", "Deportivo La Coruña": "Deportivo", "Celta de Vigo": "Celta",
         "Racing Santander": "Racing", "Rayo Vallecano": "Rayo", "Athletic Club": "Athletic", "Real Sociedad": "Real Sociedad",
         "Hellas Verona": "Verona", "AS Roma": "Roma"}
PPG_PRIOR, PESO_PPG = 1.0, 38           # tamaño de club (1.0 = un recién ascendido típico)
SEMIVIDA, ENCOGER, ASCENDIDO = 180, 3.0, -0.15   # Poisson de reserva


def leer(ruta):
    """Lee la ruta de origin/main (la actualizan los workflows); si no se puede, la copia local."""
    try:
        txt = subprocess.run(["git", "-C", str(RAIZ), "show", f"origin/main:{ruta}"], capture_output=True, text=True,
                             check=True).stdout
        return pd.read_csv(io.StringIO(txt))
    except Exception:
        return pd.read_csv(RAIZ / ruta)


def eq(n):
    return {"name": n, "short": CORTO.get(n, n)}


def historico():
    h = leer("data/historico_partidos.csv")
    h["t"] = pd.to_datetime(h.fecha, utc=True, format="ISO8601")
    h["d"] = h.fecha.str[:10]
    return h.sort_values(["t", "match_id"]).reset_index(drop=True)


def calendario():
    c = leer("data/calendario.csv")
    c = c[c.liga.isin(LIGAS)].copy()
    c["t"] = pd.to_datetime(c.fecha + " " + c.saque_utc, utc=True)
    return c


def registro():
    try:
        r = leer("data/ambos_marcan/registro_papel.csv")
    except Exception:
        return pd.DataFrame(columns=["match_id"])
    return r[pd.to_datetime(r.generado, utc=True) < pd.to_datetime(r.saque, utc=True)].sort_values("generado")


# ---------- modelo ----------

def matriz(ll, lv, n=11):
    return np.outer(poisson.pmf(np.arange(n), ll), poisson.pmf(np.arange(n), lv))


def probs_de(ll, lv):
    m = matriz(ll, lv)
    tot = np.add.outer(np.arange(11), np.arange(11))
    return dict(p1=np.tril(m, -1).sum(), px=np.trace(m), p2=np.triu(m, 1).sum(), mas25=m[tot > 2.5].sum(),
                btts=(1 - np.exp(-ll)) * (1 - np.exp(-lv)), lam_l=ll, lam_v=lv)


def ajustar_poisson(h, liga, antes):
    """Ataque/defensa por equipo con los partidos de 'liga' de los 2 años antes de 'antes' (sin fuga)."""
    d = h[(h.liga == liga) & (h.t < antes) & (h.t >= antes - pd.Timedelta(days=730)) & h.goles_l.notna()]
    eqs = sorted(set(d.local_id) | set(d.visitante_id))
    ix = {e: k for k, e in enumerate(eqs)}
    n = len(eqs)
    li, vi = d.local_id.map(ix).values, d.visitante_id.map(ix).values
    gl, gv = d.goles_l.values.astype(float), d.goles_v.values.astype(float)
    w = 0.5 ** ((antes - d.t).dt.days.values / SEMIVIDA)
    # recién ascendidos (sin partidos en la liga la temporada anterior): se encogen hacia un ascendido típico
    temp = int(antes.year if antes.month >= 7 else antes.year - 1)
    previos = set(h[(h.liga == liga) & (h.temporada == temp - 1)].local_id)
    centro = np.array([0.0 if e in previos else ASCENDIDO for e in eqs])

    def f(x):
        mu, ho, at, de = x[0], x[1], x[2:2 + n], x[2 + n:]
        el = mu + ho + at[li] - de[vi]
        ev = mu + at[vi] - de[li]
        ll, lv = np.exp(el), np.exp(ev)
        nll = (w * (ll - gl * el)).sum() + (w * (lv - gv * ev)).sum()
        pen = ENCOGER * (((at - centro) ** 2).sum() + ((de - centro) ** 2).sum())
        rl, rv = w * (ll - gl), w * (lv - gv)
        g = np.zeros_like(x)
        g[0] = rl.sum() + rv.sum()
        g[1] = rl.sum()
        ga, gd = np.zeros(n), np.zeros(n)
        np.add.at(ga, li, rl); np.add.at(ga, vi, rv)
        np.add.at(gd, vi, -rl); np.add.at(gd, li, -rv)
        g[2:2 + n] = ga + 2 * ENCOGER * (at - centro)
        g[2 + n:] = gd + 2 * ENCOGER * (de - centro)
        return nll + pen, g
    x = minimize(f, np.zeros(2 + 2 * n), jac=True, method="L-BFGS-B").x
    return {"mu": x[0], "home": x[1], "at": dict(zip(eqs, x[2:2 + n])), "de": dict(zip(eqs, x[2 + n:]))}


def poisson_partido(h, liga, lid, vid, antes, _cache={}):
    clave = (liga, str(antes.date()))
    if clave not in _cache:
        _cache[clave] = ajustar_poisson(h, liga, antes.normalize())
    p = _cache[clave]
    ll = np.exp(p["mu"] + p["home"] + p["at"].get(lid, ASCENDIDO) - p["de"].get(vid, ASCENDIDO))
    lv = np.exp(p["mu"] + p["at"].get(vid, ASCENDIDO) - p["de"].get(lid, ASCENDIDO))
    return probs_de(ll, lv)


def modelo(h, reg, mid, liga, lid, vid, saque):
    """% de nuestro modelo para un partido: el oficial si ya se apuntó antes del pitido; si no, el Poisson."""
    r = reg[reg.match_id == mid]
    if len(r):
        x = r.iloc[-1]
        from btts_implicito import ajustar
        ll, lv = ajustar(x.mod_1, x.mod_x, x.mod_2, x.mod_mas25)
        s = x.mod_1 + x.mod_x + x.mod_2
        return dict(p1=x.mod_1 / s, px=x.mod_x / s, p2=x.mod_2 / s, mas25=x.mod_mas25, btts=x.mod_ambos,
                    lam_l=ll, lam_v=lv, fuente="oficial")
    return {**poisson_partido(h, liga, lid, vid, saque), "fuente": "poisson"}


def pct3(p):
    """Tres % enteros que suman 100 (resto mayor)."""
    v = np.array(p) * 100 / sum(p)
    r = np.floor(v).astype(int)
    for k in np.argsort(-(v - r))[:100 - r.sum()]:
        r[k] += 1
    return [int(x) for x in r]


def marcador(x):
    m = matriz(x["lam_l"], x["lam_v"], 7)
    return list(map(int, np.unravel_index(m.argmax(), m.shape)))


def picks(x):
    pr = {"home": x["p1"], "draw": x["px"], "away": x["p2"]}
    out = {"1X2": max(pr, key=pr.get)}
    pct = {out["1X2"]: pr[out["1X2"]]}
    for fam, k, si, no in (("Over/Under 2.5", "mas25", "over25", "under25"), ("Both teams score", "btts", "btts_yes", "btts_no")):
        out[fam] = si if x[k] >= .5 else no
        pct[out[fam]] = x[k] if x[k] >= .5 else 1 - x[k]
    return out, pct


# ---------- Elo y tamaño ----------

def elo_series(h, ids, hasta):
    """Elo de cada id tras cada partido jugado antes de 'hasta' (reglas de rasgos.calcular_elo)."""
    r, serie = {}, {i: [] for i in ids}
    for x in h[(h.t < hasta) & h.goles_l.notna()].itertuples():
        rl, rv = r.get(x.local_id, 1500.0), r.get(x.visitante_id, 1500.0)
        dif = abs(x.goles_l - x.goles_v)
        g = 1.0 if dif <= 1 else (1.5 if dif == 2 else (11 + dif) / 8.0)
        esp = 1 / (1 + 10 ** (-(rl + 60 - rv) / 400))
        real = 1.0 if x.goles_l > x.goles_v else .5 if x.goles_l == x.goles_v else 0.0
        c = 20 * g * (real - esp)
        r[x.local_id], r[x.visitante_id] = rl + c, rv - c
        for i in (x.local_id, x.visitante_id):
            if i in serie:
                serie[i].append(round(r[i]))
    return serie


def tamano(h, antes):
    """Puntos por partido de cada club en las 5 grandes en las 4 temporadas anteriores, encogidos hacia 1.0."""
    d = h[h.liga.isin(LIGAS) & (h.t < antes) & (h.t >= antes - pd.Timedelta(days=4 * 365)) & h.goles_l.notna()]
    pl = np.select([d.goles_l > d.goles_v, d.goles_l == d.goles_v], [3, 1], 0)
    pv = np.select([d.goles_v > d.goles_l, d.goles_l == d.goles_v], [3, 1], 0)
    t = pd.concat([pd.DataFrame({"e": d.local, "p": pl}), pd.DataFrame({"e": d.visitante, "p": pv})])
    g = t.groupby("e").p.agg(["sum", "count"])
    return ((g["sum"] + PPG_PRIOR * PESO_PPG) / (g["count"] + PESO_PPG)).to_dict()


def con_tamano(c, h, fecha):
    tm = tamano(h, pd.Timestamp(fecha, tz="UTC"))
    a, b = c.local.map(tm).fillna(PPG_PRIOR), c.visitante.map(tm).fillna(PPG_PRIOR)
    c = c.assign(tam=np.minimum(a, b) + np.maximum(a, b) / 2)      # grande = los DOS fuertes (no PSG contra un ascendido)
    return c.sort_values(["tam", "t"], ascending=[False, True])


def del_dia(fecha, h=None):
    c = calendario()
    c = c[c.fecha == fecha].drop_duplicates("match_id")
    return con_tamano(c, historico() if h is None else h, fecha)


def elegir(fecha, n=2):
    c = del_dia(fecha)
    if c.empty:
        sys.exit(f"Sin partidos de las 5 grandes el {fecha} en data/calendario.csv")
    for x in c.head(n).itertuples():
        hora = x.t.tz_convert("Europe/Madrid")
        print(f"{x.local}|{x.visitante}|{x.liga}|{hora:%H:%M} Madrid|tamaño {x.tam:.2f}")
    return c.head(n)


# ---------- partido ----------

def ids_de(h):
    return dict(zip(pd.concat([h.local, h.visitante]), pd.concat([h.local_id, h.visitante_id])))


def buscar(local, visitante, fecha, h, jugado):
    if jugado:
        m = h[(h.d == fecha) & (h.local == local) & (h.visitante == visitante) & h.liga.isin(LIGAS)]
        if m.empty or m.goles_l.isna().all():
            ult = h[h.liga.isin(LIGAS)].d.max()
            sys.exit(f"{local} - {visitante} ({fecha}) aún no está en data/historico_partidos.csv (último partido de "
                     f"las 5 ligas: {ult}). Lo baja ambos_marcan_diario.yml la mañana siguiente.")
        return m.iloc[0]
    c = calendario()
    m = c[(c.fecha == fecha) & (c.local == local) & (c.visitante == visitante)]
    if m.empty:
        sys.exit(f"No hay {local} - {visitante} el {fecha} en data/calendario.csv (5 grandes ligas)")
    x = m.iloc[0]
    ids = ids_de(h)
    return pd.Series({"match_id": x.match_id, "liga": x.liga, "t": x.t, "local": local, "visitante": visitante,
                      "local_id": ids.get(local), "visitante_id": ids.get(visitante)})


def dia(t):
    t = pd.Timestamp(t).tz_convert("Europe/Madrid").normalize()
    hoy = pd.Timestamp.now(tz="Europe/Madrid").normalize()
    return "Today" if t == hoy else "Tomorrow" if t == hoy + pd.Timedelta(days=1) else f"{t:%A}"


def lista_hoy(fecha, h=None, reg=None, maximo=7):
    """Lo más probable de cada partido grande del día según NUESTRO modelo (1X2, más/menos 2.5, ambos marcan).
    Solo los 'maximo' partidos más grandes: más filas se salen de la zona segura."""
    h = historico() if h is None else h
    reg = registro() if reg is None else reg
    ids = ids_de(h)
    filas = []
    for x in del_dia(fecha, h).head(maximo).itertuples():
        p = modelo(h, reg, x.match_id, x.liga, ids.get(x.local), ids.get(x.visitante), x.t)
        a, b = CORTO.get(x.local, x.local), CORTO.get(x.visitante, x.visitante)
        cand = [(p["p1"], f"{a} win"), (p["px"], "Draw"), (p["p2"], f"{b} win"),
                (p["mas25"], "Over 2.5 goals"), (1 - p["mas25"], "Under 2.5 goals"),
                (p["btts"], "Both teams score"), (1 - p["btts"], "Not both teams score")]
        pp, txt = max(cand)
        filas.append({"time": f"{x.t.tz_convert('Europe/Madrid'):%H:%M}", "home": eq(x.local), "away": eq(x.visitante),
                      "pick": txt, "pct": round(pp * 100)})
    if not filas:
        raise ValueError(f"sin partidos el {fecha}")
    filas.sort(key=lambda m: -m["pct"])
    return {"template": "picks_list", "competition": f"Top 5 leagues · {fecha[8:]}/{fecha[5:7]}", "home": filas[0]["home"],
            "away": filas[0]["away"], "kicker": "Unlocked", "title": f"{len(filas)} big games, our calls", "picks": filas}


def tapada(d, cuando):
    return {**d, "locked": True, "kicker": "Locked", "title": f"{len(d['picks'])} calls {cuando}",
            "question": "All unlocked on our profile."}



# ---------- tarjetas de relleno (siempre 5 + la lista tapada; usuario 10/10) ----------

N_CARTAS = 5        # previo y post-partido: SIEMPRE 5 tarjetas de contenido + la 6ª (lista tapada)


def partidos_de(h, eid, antes, n, sede=None):
    """Últimos n partidos jugados de un club antes de 'antes' (sede: "local"/"visitante" para solo casa/fuera),
    vistos desde el club: pts, gf, gc, xgf, xgc, tiros, a puerta."""
    d = h[h.goles_l.notna() & (h.t < antes)]
    if sede == "local":
        d = d[d.local_id == eid]
    elif sede == "visitante":
        d = d[d.visitante_id == eid]
    else:
        d = d[(d.local_id == eid) | (d.visitante_id == eid)]
    filas = []
    for x in d.tail(n).itertuples():
        yo, el = ("l", "v") if x.local_id == eid else ("v", "l")
        gf, gc = (x.goles_l, x.goles_v) if yo == "l" else (x.goles_v, x.goles_l)
        tiros = sum(getattr(x, f"{yo}_{s}") for s in ("shots_on_target", "shots_off_target", "blocked_shots")
                    if pd.notna(getattr(x, f"{yo}_{s}")))
        filas.append({"pts": 3 if gf > gc else 1 if gf == gc else 0, "gf": gf, "gc": gc,
                      "xgf": getattr(x, f"{yo}_expected_goals"), "xgc": getattr(x, f"{el}_expected_goals"),
                      "tiros": tiros, "puerta": getattr(x, f"{yo}_shots_on_target")})
    return pd.DataFrame(filas)


def filas_duelo(ph, pa, por_partido):
    """Filas de head_to_head con lo que haya (xG solo si está en los dos)."""
    def media(df, k):
        v = df[k].dropna()
        return float(v.mean()) if len(v) else None
    out = []
    if por_partido:
        out.append({"label": "Points per game", "h": round(ph.pts.mean(), 1), "a": round(pa.pts.mean(), 1), "dec": 1})
        out.append({"label": "Goals per game", "h": round(ph.gf.mean(), 1), "a": round(pa.gf.mean(), 1), "dec": 1})
        out.append({"label": "Conceded per game", "h": round(ph.gc.mean(), 1), "a": round(pa.gc.mean(), 1), "dec": 1,
                    "menos_mejor": True})
    else:
        out.append({"label": f"Points, last {len(ph)}", "h": int(ph.pts.sum()), "a": int(pa.pts.sum())})
        out.append({"label": "Goals scored", "h": int(ph.gf.sum()), "a": int(pa.gf.sum())})
        out.append({"label": "Goals conceded", "h": int(ph.gc.sum()), "a": int(pa.gc.sum()), "menos_mejor": True})
    for k, lab, menos in (("xgf", "xG created per game", False), ("xgc", "xG conceded per game", True)):
        vh, va = media(ph, k), media(pa, k)
        if vh is not None and va is not None:
            out.append({"label": lab, "h": round(vh, 1), "a": round(va, 1), "dec": 1, "menos_mejor": menos})
    return out[:5]


def carta_forma(base, h, m, n=5):
    ph, pa = partidos_de(h, m.local_id, m.t, n), partidos_de(h, m.visitante_id, m.t, n)
    if min(len(ph), len(pa)) < 3:
        return None
    return {**base, "template": "head_to_head", "kicker": "Form check", "title": f"Last {min(len(ph), len(pa))} games",
            "stats": filas_duelo(ph.tail(min(len(ph), len(pa))), pa.tail(min(len(ph), len(pa))), False),
            "question": "Who arrives in better shape?"}


def carta_casa_fuera(base, h, m, n=5):
    ph, pa = partidos_de(h, m.local_id, m.t, n, "local"), partidos_de(h, m.visitante_id, m.t, n, "visitante")
    if min(len(ph), len(pa)) < 3:
        return None
    return {**base, "template": "head_to_head", "kicker": "Home vs away",
            "title": f"<b>{base['home']['short']}</b> at home, <b>{base['away']['short']}</b> away",
            "stats": filas_duelo(ph, pa, True)[:4], "note": f"Last {len(ph)} home and {len(pa)} away games",
            "question": "Does home advantage decide it?"}


def carta_tiros(base, h, m, n=10):
    ph, pa = partidos_de(h, m.local_id, m.t, n), partidos_de(h, m.visitante_id, m.t, n)
    if min(len(ph), len(pa)) < 3:
        return None
    st = [{"label": "Shots per game", "h": round(ph.tiros.mean(), 1), "a": round(pa.tiros.mean(), 1), "dec": 1},
          {"label": "On target per game", "h": round(ph.puerta.mean(), 1), "a": round(pa.puerta.mean(), 1), "dec": 1},
          {"label": "Goals per game", "h": round(ph.gf.mean(), 1), "a": round(pa.gf.mean(), 1), "dec": 1}]
    return {**base, "template": "head_to_head", "kicker": "Attack check", "title": f"Last {min(len(ph), len(pa))} games",
            "stats": st, "question": "Who scores first?"}


def carta_marcadores(base, x, m):
    """Previo, relleno que siempre existe: los 3 marcadores más probables de nuestro modelo."""
    mt = matriz(x["lam_l"], x["lam_v"], 7)
    top = sorted(((mt[i, j], i, j) for i in range(7) for j in range(7)), reverse=True)[:3]
    p0, i0, j0 = top[0]
    resto = ", ".join(f"{i}–{j} ({p * 100:.0f}%)" for p, i, j in top[1:])
    hora = m.t.tz_convert("Europe/Madrid")
    return {**base, "template": "key_number", "team": None, "number": f"{i0}–{j0}",
            "text": f"Our most likely score, <b>{p0 * 100:.0f}%</b>. Next: {resto}.",
            "when": f"{dia(m.t)} · {hora:%H:%M %Z}", "question": "What's your score?"}


def carta_estadisticas(base, m):
    """Post: el partido en cifras (nuestro box-score), con el marcador en el centro."""
    def v(lado, s):
        x = m[f"{lado}_{s}"]
        return None if pd.isna(x) else float(x)
    tiros = {l: sum(v(l, s) or 0 for s in ("shots_on_target", "shots_off_target", "blocked_shots")) for l in "lv"}
    st = []
    for lab, fh, fa, dec in (("Expected goals (xG)", v("l", "expected_goals"), v("v", "expected_goals"), 1),
                             ("Shots", tiros["l"], tiros["v"], 0),
                             ("Shots on target", v("l", "shots_on_target"), v("v", "shots_on_target"), 0),
                             ("Big chances", v("l", "big_chances_created"), v("v", "big_chances_created"), 0),
                             ("Possession %", v("l", "possession"), v("v", "possession"), 0),
                             ("Corners", v("l", "corners"), v("v", "corners"), 0)):
        if fh is None or fa is None:
            continue
        if lab == "Possession %":
            fh, fa = (fh * 100, fa * 100) if fh <= 1 else (fh, fa)
        st.append({"label": lab, "h": round(fh, dec) if dec else int(round(fh)), "a": round(fa, dec) if dec else int(round(fa)),
                   "dec": dec})
    if len(st) < 3:
        return None
    return {**base, "template": "head_to_head", "kicker": "Match stats", "title": "", "stats": st[:5],
            "centro": "score", "question": "Who really ran the game?"}


def carta_elo_post(base, h, m, local, visitante):
    el = elo_series(h, [m.local_id, m.visitante_id], m.t + pd.Timedelta(seconds=1))   # incluye este partido
    el = {local: el[m.local_id], visitante: el[m.visitante_id]}
    if min(map(len, el.values())) < 6:
        return None
    cambio = {k: v[-1] - v[-6] for k, v in el.items()}
    foco = max(cambio, key=lambda k: abs(cambio[k]))
    otro = visitante if foco == local else local
    extra = f'{CORTO.get(otro, otro)}: {"+" if cambio[otro] >= 0 else "−"}{abs(cambio[otro])} in the same span.'
    return {**base, "template": "elo_form", "focus": "home" if foco == local else "away",
            "elo_home": el[local][-10:], "elo_away": el[visitante][-10:], "extra": extra,
            "question": "Real form or a lucky run?" if cambio[foco] >= 0 else "Crisis or just a blip?"}


def cinco_mas_final(pref, cartas, final):
    """Las 5 primeras tarjetas disponibles (en orden) renumeradas pre1..pre5 / post1..post5 + la 6ª (lista tapada)."""
    elegidas = [(k, d) for k, d in cartas if d][:N_CARTAS]
    if len(elegidas) < N_CARTAS:
        print(f"AVISO: solo {len(elegidas)} tarjetas de contenido (se piden {N_CARTAS})", file=sys.stderr)
    out = {f"{pref}{i}_{k}": d for i, (k, d) in enumerate(elegidas, 1)}
    if final:
        out[f"{pref}6_lista"] = final
    return out


def pre(local, visitante, fecha):
    h, reg = historico(), registro()
    m = buscar(local, visitante, fecha, h, jugado=False)
    x = modelo(h, reg, m.match_id, m.liga, m.local_id, m.visitante_id, m.t)
    print(f"Modelo: {x['fuente']}  1 {x['p1']:.3f}  X {x['px']:.3f}  2 {x['p2']:.3f}  +2.5 {x['mas25']:.3f}  "
          f"ambos {x['btts']:.3f}  goles {x['lam_l']:.2f}-{x['lam_v']:.2f}")
    hh, a = eq(local), eq(visitante)
    base = {"competition": m.liga, "home": hh, "away": a}
    out = {"pre1_prediction": {**base, "template": "prediction", "probs": pct3([x["p1"], x["px"], x["p2"]]),
                               "predicted_score": marcador(x), "fuente": x["fuente"]},
           "pre2_form": carta_forma(base, h, m),        # sustituye al "upset alert" (enseñaba el % del mercado)
           "pre3_goals": {**base, "template": "goals", "btts": round(x["btts"] * 100),
                          "exp_goals": [round(x["lam_l"], 1), round(x["lam_v"], 1)], "fuente": x["fuente"]}}
    el = elo_series(h, [m.local_id, m.visitante_id], m.t)
    el = {local: el[m.local_id], visitante: el[m.visitante_id]}
    if min(map(len, el.values())) >= 6:
        cambio = {k: v[-1] - v[-6] for k, v in el.items()}
        foco = max(cambio, key=lambda k: abs(cambio[k]))
        otro = visitante if foco == local else local
        extra = f'{CORTO.get(otro, otro)}: {"+" if cambio[otro] >= 0 else "−"}{abs(cambio[otro])} in the same span.'
        out["pre4_elo_form"] = {**base, "template": "elo_form", "focus": "home" if foco == local else "away",
                                "elo_home": el[local][-10:], "elo_away": el[visitante][-10:], "extra": extra,
                                "question": "Real form or a lucky run?" if cambio[foco] >= 0 else "Crisis or just a blip?"}
    cc = h[h.goles_l.notna() & (h.t < m.t) & (((h.local == local) & (h.visitante == visitante)) |
                                               ((h.local == visitante) & (h.visitante == local)))]
    if not cc.empty:
        u = cc.iloc[-1]
        gl, gv = int(u.goles_l), int(u.goles_v)
        cuando = pd.Timestamp(u.t).strftime("%B %Y")
        if gl == gv:
            txt, lado = f"in their last meeting, {cuando}.", None
        else:
            gan = u.local if gl > gv else u.visitante
            txt, lado = f"<b>{CORTO.get(gan, gan)}</b> won the last meeting, {cuando}.", "home" if gan == local else "away"
        hora = m.t.tz_convert("Europe/Madrid")
        out["pre5_key_number"] = {**base, "template": "key_number", "team": lado, "number": f"{max(gl, gv)}–{min(gl, gv)}",
                                  "text": txt, "when": f"{dia(m.t)} · {hora:%H:%M %Z}", "question": "Revenge or repeat?"}
    try:
        final = tapada(lista_hoy(fecha, h, reg), dia(m.t).lower())
    except ValueError:
        final = None
    cartas = [(k.split("_", 1)[1], d) for k, d in out.items()]
    cartas += [("home_away", carta_casa_fuera(base, h, m)), ("attack", carta_tiros(base, h, m)),   # de relleno
               ("scores", carta_marcadores(base, x, m))]
    return m, cinco_mas_final("pre", cartas, final)


def post(local, visitante, fecha):
    h, reg = historico(), registro()
    m = buscar(local, visitante, fecha, h, jugado=True)
    hh, a = eq(local), eq(visitante)
    gh, ga = int(m.goles_l), int(m.goles_v)
    base = {"competition": m.liga, "home": hh, "away": a, "score": [gh, ga]}
    out = {}
    if pd.notna(m.l_expected_goals) and pd.notna(m.v_expected_goals):
        out["post1_deserved"] = {**base, "template": "deserved", "xg": [float(m.l_expected_goals), float(m.v_expected_goals)]}
    x = modelo(h, reg, m.match_id, m.liga, m.local_id, m.visitante_id, m.t)
    elec, pct = picks(x)
    buenos = sorted((pct[v], v) for v in elec.values() if G.acierto(v, gh, ga))
    if buenos:
        pc, mk = buenos[0]               # el acierto más difícil
        out["post2_prediction_vs_result"] = {**base, "template": "prediction_vs_result", "market": mk,
                                             "pct": round(pc * 100), "fuente": x["fuente"]}
    prob = {"home": x["p1"], "draw": x["px"], "away": x["p2"]}
    fav = max(prob, key=prob.get)
    real = "home" if gh > ga else "away" if ga > gh else "draw"
    # empate: solo es sorpresa si le dábamos < 20 % (casi todos los empates salen al 22-30 %)
    if real != fav and prob[real] < (.2 if real == "draw" else .3):
        out["post3_upset_happened"] = {**base, "template": "upset_happened", "underdog": real, "favourite": fav,
                                       "pre_pct": round(prob[real] * 100),
                                       "question": "Shock or fair?" if real == "draw" else "Who called it?"}
    tiros = {k: sum(float(m[f"{p}_{s}"]) for s in ("shots_on_target", "shots_off_target", "blocked_shots")
                    if pd.notna(m[f"{p}_{s}"])) for k, p in (("home", "l"), ("away", "v"))}
    lado = max(tiros, key=tiros.get)
    goles = gh if lado == "home" else ga
    if tiros[lado]:
        t = hh if lado == "home" else a
        texto = (f'shots from <b>{t["short"]}</b>. Zero goals.' if goles == 0
                 else f'shots from <b>{t["short"]}</b> for {goles} goal{"s" * (goles > 1)}.')
        out["post4_stat_of_match"] = {**base, "template": "stat_of_match", "number": str(int(tiros[lado])),
                                      "text": texto, "team": lado, "question": "Wasteful or unlucky?"}
    # la jornada: los partidos grandes de ese día ya jugados, con nuestro % previo
    # la jornada: este partido + los grandes ya jugados ese día; si hay pocos (el resto de la jornada aún no está en el
    # histórico), se completa con los de los 3 días anteriores. 6 filas como mucho.
    trozos = []
    for k in range(4):
        dd = str((pd.Timestamp(fecha) - pd.Timedelta(days=k)).date())
        trozos.append(con_tamano(h[(h.d == dd) & h.liga.isin(LIGAS) & h.goles_l.notna() & (h.match_id != m.match_id)], h, dd))
    otros = pd.concat(trozos)
    if len(trozos[0]) >= 3:
        otros = trozos[0]
    jugados = pd.concat([h[h.match_id == m.match_id], otros.head(5)])
    jugados = jugados.drop(columns="tam", errors="ignore").sort_values("t")
    dias = sorted(jugados.d.unique())
    rango = f"{dias[0][8:]}/{dias[0][5:7]}" + (f"–{dias[-1][8:]}/{dias[-1][5:7]}" if len(dias) > 1 else "")
    # 6 filas como mucho: con 8 la pregunta se salía de la zona segura (y > 1540)
    filas = []
    for _, r in jugados.iterrows():
        y = modelo(h, reg, r.match_id, r.liga, r.local_id, r.visitante_id, r.t)
        e_, p_ = picks(y)
        filas.append([CORTO.get(r.local, r.local), int(r.goles_l), int(r.goles_v), CORTO.get(r.visitante, r.visitante),
                      {k: [v, float(p_[v])] for k, v in e_.items()}])
    if filas:          # SIEMPRE (usuario 10/10), aunque la jornada aún tenga pocos partidos en el histórico
        out["post5_weekend_record"] = {"template": "weekend_record", "competition": f"Top 5 leagues · {rango}",
                                       "matches": filas, "question": "Beat us next time?"}
    final = None
    for k in range(1, 8):           # la 6ª: el próximo día con partidos de las 5 ligas (parones de selecciones)
        sig = str((pd.Timestamp(fecha) + pd.Timedelta(days=k)).date())
        try:
            final = tapada(lista_hoy(sig, h, reg), "next")
            break
        except ValueError:
            continue
    stats = carta_estadisticas(base, m)
    orden = ["post1_deserved", "post2_prediction_vs_result", "post3_upset_happened", "post4_stat_of_match", "post5_weekend_record"]
    cartas = []
    for k in orden:
        if k == "post3_upset_happened" and k not in out:
            cartas.append(("match_stats", stats))       # sin sorpresa: el partido en cifras ocupa su hueco
            stats = None
        else:
            cartas.append((k.split("_", 1)[1], out.get(k)))
    cartas += [("match_stats", stats), ("elo_form", carta_elo_post(base, h, m, local, visitante))]   # de relleno
    return m, cinco_mas_final("post", cartas, final)


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "elegir":
        elegir(sys.argv[2])
        sys.exit()
    local, visitante, fecha = sys.argv[2:5]
    m, datos = (post if modo == "post" else pre)(local, visitante, fecha)
    carpeta = AQUI / "salida" / f"{fecha}_{local}_{visitante}".replace(" ", "_")
    carpeta.mkdir(parents=True, exist_ok=True)
    trabajos = []
    for nombre, d in datos.items():
        (carpeta / f"{nombre}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, default=float))
        trabajos.append((d, carpeta / f"{nombre}.png"))
    G.renderizar(trabajos)
    if G.FUERA and os.environ.get("ZONA_ESTRICTA") == "1":      # Live (post automático): no se publica si algo se sale
        sys.exit(f"FUERA DE LA ZONA SEGURA: {G.FUERA}")
