"""Datos para las plantillas head_to_head y ranking (clubes de las 5 grandes, temporada en curso). Sin API: solo disco.
    python3 redes/plantillas/datos_rankings.py ranking <metrica> [liga|all]   # métricas: ver METRICAS
    python3 redes/plantillas/datos_rankings.py duelo <equipo A> <equipo B>
    python3 redes/plantillas/datos_rankings.py jugadores "<jugador A>" "<jugador B>" [foto_A.jpg foto_B.jpg]
        # jugador vs jugador (formato preferido, usuario 06/10). Fotos: workflow bajar-fotos del repo Live (fotos/<slug>.jpg)
    python3 redes/plantillas/datos_rankings.py top_jugadores <definicion|xg90|goles|asistencias|creacion> [liga|all]
Jugadores: data/redes/jugadores_temporada.csv (workflow jugadores_redes.yml, diario).
Escribe el JSON y el PNG en redes/plantillas/salida/<fecha>_<tipo>/. Nunca Segunda División."""
import json, subprocess, sys
from datetime import date
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GRANDES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
# métrica -> (título, explicación, función sobre la tabla por equipo, decimales, unidad, menos_mejor)
METRICAS = {
    "suerte": ("Scoring more than they <b>should</b>", "Goals minus expected goals (xG), this season",
               lambda t: t.gf - t.xgf, 1, "", False),
    "xg": ("Creating the <b>most</b> chances", "Expected goals (xG) per game", lambda t: t.xgf / t.pj, 2, "", False),
    "muro": ("The <b>meanest</b> defences", "xG conceded per game", lambda t: t.xgc / t.pj, 2, "", True),
    "tiros": ("Shooting on <b>sight</b>", "Shots per game", lambda t: t.tiros / t.pj, 1, "", False),
    "posesion": ("Who <b>keeps</b> the ball", "Average possession", lambda t: t.pos, 0, "%", False),
}


def tabla():
    p = pd.read_csv(ROOT / "data/historico_partidos.csv", low_memory=False)
    p = p[(p.temporada == p.temporada.max()) & p.liga.isin(GRANDES) & p.goles_l.notna()]
    filas = []
    for lado, otro in (("l", "v"), ("v", "l")):
        eq = "local" if lado == "l" else "visitante"
        filas.append(pd.DataFrame({
            "equipo": p[eq], "liga": p.liga, "gf": p[f"goles_{lado}"], "gc": p[f"goles_{otro}"],
            "xgf": p[f"{lado}_expected_goals"], "xgc": p[f"{otro}_expected_goals"], "pos": p[f"{lado}_possession"] * (100 if p[f"{lado}_possession"].max() <= 1 else 1),
            "tiros": p[f"{lado}_shots_on_target"] + p[f"{lado}_shots_off_target"] + p[f"{lado}_blocked_shots"].fillna(0),
            "pts": (p[f"goles_{lado}"] > p[f"goles_{otro}"]) * 3 + (p[f"goles_{lado}"] == p[f"goles_{otro}"])}))
    d = pd.concat(filas)
    t = d.groupby(["equipo", "liga"]).agg(pj=("gf", "size"), gf=("gf", "sum"), gc=("gc", "sum"), xgf=("xgf", "sum"),
                                           xgc=("xgc", "sum"), pos=("pos", "mean"), tiros=("tiros", "sum"), pts=("pts", "sum"))
    return t.reset_index()


def render(nombre, datos):
    out = ROOT / "redes/plantillas/salida" / f"{date.today()}_{nombre}"
    out.mkdir(parents=True, exist_ok=True)
    j = out / f"{nombre}.json"
    j.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    subprocess.run([sys.executable, str(ROOT / "redes/plantillas/generar.py"), str(j), "-o", str(out)], check=True)


def ranking(metrica, liga="all"):
    titulo, expl, f, dec, unidad, menos = METRICAS[metrica]
    t = tabla()
    t = t[t.pj >= 3]
    if liga != "all":
        t = t[t.liga == liga]
    t = t.assign(v=f(t)).sort_values("v", ascending=menos).head(5)
    rows = [{"name": r.equipo, "team": r.equipo, "value": round(float(r.v), dec), "sub": f"{r.liga} · {r.pj} games"}
            for r in t.itertuples()]
    render(f"ranking_{metrica}", {"template": "ranking", "competition": liga if liga != "all" else "Top 5 leagues",
                                  "title": titulo, "metric": expl, "rows": rows, "dec": dec, "unit": unidad,
                                  "question": "Who's missing from this list?"})


def duelo(a, b):
    t = tabla().set_index("equipo")
    x, y = t.loc[a], t.loc[b]
    st = lambda lab, f, dec=1, menos=False: {"label": lab, "h": round(float(f(x)), dec), "a": round(float(f(y)), dec),
                                              "dec": dec, "menos_mejor": menos}
    stats = [st("Points per game", lambda r: r.pts / r.pj, 2), st("Goals per game", lambda r: r.gf / r.pj),
             st("xG per game", lambda r: r.xgf / r.pj), st("xG conceded per game", lambda r: r.xgc / r.pj, 1, True),
             st("Shots per game", lambda r: r.tiros / r.pj), st("Possession %", lambda r: r.pos, 0)]
    render(f"duelo_{a}_{b}".replace(" ", ""), {"template": "head_to_head", "competition": x.liga if x.liga == y.liga else "Club football",
                                               "home": {"name": a}, "away": {"name": b},
                                               "title": f"{a} vs {b}: this season in numbers", "stats": stats,
                                               "note": f"{int(x.pj)} and {int(y.pj)} league games", "question": "Who wins it?"})


def _norm(t):
    import unicodedata
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower().strip()


def nombres_propios():
    """jugador_id -> nombre, de nuestras descargas de Highlightly (selecciones y box-score diario de redes)."""
    n = {}
    s = ROOT / "data/selecciones/jugadores_partido.csv"
    if s.exists():
        d = pd.read_csv(s, usecols=["jugador_id", "jugador"]).dropna().drop_duplicates("jugador_id")
        n.update(dict(zip(d.jugador_id.astype(int), d.jugador)))
    r = ROOT / "data/redes/jugadores_nombres.csv"
    if r.exists():
        d = pd.read_csv(r).dropna(subset=["jugador_id", "nombre"])
        d = d[d.nombre.astype(str).str.len() > 0]
        n.update(dict(zip(d.jugador_id.astype(int), d.nombre)))
    return n


def jugadores_propios():
    """Temporada en curso de las 5 grandes con NUESTROS datos (box-score de Highlightly). Usuario 06/10: siempre
    nuestros datos salvo que no estén al día. Devuelve (tabla, al_dia): al_dia = todos los partidos jugados tienen box-score."""
    h = pd.read_csv(ROOT / "data/historico_partidos.csv", low_memory=False)
    h = h[(h.temporada == h.temporada.max()) & h.liga.isin(GRANDES) & h.goles_l.notna()]
    x = pd.read_csv(ROOT / "data/historico_xg_jugador.csv", low_memory=False)
    x = x[x.match_id.isin(h.match_id) & x.jugador_id.notna()]
    al_dia = x.match_id.nunique() >= len(h)
    eq = pd.concat([h[["local_id", "local", "liga"]].set_axis(["id", "equipo", "liga"], axis=1),
                    h[["visitante_id", "visitante", "liga"]].set_axis(["id", "equipo", "liga"], axis=1)]).drop_duplicates("id")
    num = lambda c: pd.to_numeric(x[c], errors="coerce").fillna(0)
    x = x.assign(goles=num("goalsScored"), xg=num("expectedGoals"), asistencias=num("assists"), xa=num("expectedAssists"),
                 tiros=num("shotsTotal"), pases_clave=num("passesKey"), minutos=num("minutos"), jugador_id=x.jugador_id.astype(int))
    t = x.groupby("jugador_id").agg(partidos=("match_id", "nunique"), minutos=("minutos", "sum"), goles=("goles", "sum"),
                                    xg=("xg", "sum"), asistencias=("asistencias", "sum"), xa=("xa", "sum"), tiros=("tiros", "sum"),
                                    pases_clave=("pases_clave", "sum"), equipo_id=("equipo_id", "last")).reset_index()
    t = t.merge(eq.rename(columns={"id": "equipo_id"}), on="equipo_id", how="left")
    t["jugador"] = t.jugador_id.map(nombres_propios())
    t["fuente"] = "2yellow"
    total = len(t)
    t = t.dropna(subset=["jugador", "equipo"])
    t.attrs["cobertura"] = len(t) / total if total else 0
    return t, al_dia


def jugadores_tabla():
    """Respaldo: understat (workflow jugadores_redes.yml)."""
    j = pd.read_csv(ROOT / "data/redes/jugadores_temporada.csv")
    for c in ["partidos", "minutos", "goles", "xg", "asistencias", "xa", "tiros", "pases_clave", "npg", "npxg"]:
        j[c] = pd.to_numeric(j[c], errors="coerce").fillna(0)
    return j[j.liga.isin(GRANDES)]


def buscar(j, nombre):
    n = _norm(nombre)
    m = j[j.jugador.map(_norm) == n]
    if m.empty:
        m = j[j.jugador.map(_norm).str.contains(n, regex=False)]
    if m.empty:
        sys.exit(f"No encuentro a {nombre}")
    return m.sort_values("minutos", ascending=False).iloc[0]


# understat usa nombres de registro: aquí los que la gente conoce de otra forma (añadir cuando salga uno raro)
ALIAS = {"Kylian Mbappe-Lottin": "Kylian Mbappé", "Vinicius Júnior": "Vinícius Jr", "Vinicius Junior": "Vinícius Jr"}


def visible_nombre(n):
    return ALIAS.get(n, n)


def corto(nombre):
    partes = str(nombre).split()
    return partes[-1] if len(partes) > 1 and len(nombre) > 11 else nombre


def elegir_fuente(a, b):
    """Nuestros datos si están al día y tienen a los dos jugadores; si no, understat."""
    try:
        t, al_dia = jugadores_propios()
        if al_dia:
            return t, buscar(t, a).copy(), buscar(t, b).copy()
        print("[!] nuestros datos no están al día: uso understat")
    except SystemExit as ex:
        print(f"[!] {ex} en nuestros datos: uso understat")
    j = jugadores_tabla()
    return j, buscar(j, a).copy(), buscar(j, b).copy()


def foto_de(ruta):
    """Foto (jpg) + crédito (<mismo nombre>.json del workflow bajar-fotos de Live). Sin foto: plantilla sin caras."""
    if not ruta or not Path(ruta).exists():
        return {}
    meta = Path(ruta).with_suffix(".json")
    cred = json.loads(meta.read_text()).get("credito", "") if meta.exists() else ""
    return {"foto": str(Path(ruta).resolve()), "credito": cred}


def jugadores(a, b, foto_a=None, foto_b=None):
    j, x, y = elegir_fuente(a, b)
    print("fuente:", x.fuente, "/", y.fuente)
    x["jugador"], y["jugador"] = visible_nombre(x.jugador), visible_nombre(y.jugador)
    p90 = lambda r, c: r[c] / r.minutos * 90 if r.minutos else 0
    st = lambda lab, f, dec=1: {"label": lab, "h": round(float(f(x)), dec), "a": round(float(f(y)), dec), "dec": dec}
    stats = [st("Goals", lambda r: r.goles, 0), st("Expected goals (xG)", lambda r: r.xg),
             st("Assists", lambda r: r.asistencias, 0), st("Expected assists (xA)", lambda r: r.xa),
             st("Shots per 90", lambda r: p90(r, "tiros")), st("Key passes per 90", lambda r: p90(r, "pases_clave"))]
    if foto_de(foto_a) and foto_de(foto_b):
        stats = [x_ for x_ in stats if x_["label"] != "Shots per 90"]  # con caras caben 5 filas
    misma = x.liga == y.liga
    render(f"jugadores_{_norm(x.jugador)}_{_norm(y.jugador)}".replace(" ", ""),
           {"template": "head_to_head", "competition": x.liga if misma else "Top 5 leagues",
            "home": {"name": x.equipo, "short": corto(x.jugador), **foto_de(foto_a)},
            "away": {"name": y.equipo, "short": corto(y.jugador), **foto_de(foto_b)},
            "title": f"{x.jugador} vs {y.jugador}", "stats": stats,
            "note": f"{x.equipo} · {int(x.minutos)}' | {y.equipo} · {int(y.minutos)}' — this season",
            "question": "Who are you picking?"})


MET_JUG = {
    "definicion": ("Finishing <b>above</b> the odds", "Goals minus xG, this season", lambda t: t.goles - t.xg, 1),
    "xg90": ("The most <b>dangerous</b> in the box", "xG per 90 (min. 270')", lambda t: t.xg / t.minutos * 90, 2),
    "goles": ("Top <b>scorers</b>", "League goals, this season", lambda t: t.goles, 0),
    "asistencias": ("Top <b>creators</b>", "League assists, this season", lambda t: t.asistencias, 0),
    "creacion": ("Chance <b>machines</b>", "Expected assists (xA) per 90 (min. 270')", lambda t: t.xa / t.minutos * 90, 2),
}


def top_jugadores(metrica, liga="all"):
    titulo, expl, f, dec = MET_JUG[metrica]
    # ranking: solo con nuestros datos si tenemos nombre de casi todos (si no, el top saldría sesgado)
    t, al_dia = jugadores_propios()
    j = t if al_dia and t.attrs["cobertura"] >= 0.9 else jugadores_tabla()
    print("fuente:", j.fuente.iloc[0])
    j = j[j.minutos >= 270]
    if liga != "all":
        j = j[j.liga == liga]
    j = j.assign(v=f(j)).sort_values(["v", "minutos"], ascending=[False, True]).head(5)
    rows = [{"name": visible_nombre(r.jugador), "team": r.equipo, "value": round(float(r.v), dec), "sub": f"{r.equipo} · {r.liga}"}
            for r in j.itertuples()]
    render(f"topjug_{metrica}", {"template": "ranking", "competition": liga if liga != "all" else "Top 5 leagues",
                                 "title": titulo, "metric": expl, "rows": rows, "dec": dec,
                                 "question": "Who's missing from this list?"})


if __name__ == "__main__":
    if sys.argv[1] in ("jugadores", "top_jugadores"):
        {"jugadores": jugadores, "top_jugadores": top_jugadores}[sys.argv[1]](*sys.argv[2:])
        sys.exit()
    if sys.argv[1] == "ranking":
        ranking(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "all")
    else:
        duelo(sys.argv[2], sys.argv[3])
