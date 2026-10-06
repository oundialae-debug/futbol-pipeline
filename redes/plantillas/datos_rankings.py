"""Datos para las plantillas head_to_head y ranking (clubes de las 5 grandes, temporada en curso). Sin API: solo disco.
    python3 redes/plantillas/datos_rankings.py ranking <metrica> [liga|all]   # métricas: ver METRICAS
    python3 redes/plantillas/datos_rankings.py duelo <equipo A> <equipo B>
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


if __name__ == "__main__":
    if sys.argv[1] == "ranking":
        ranking(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "all")
    else:
        duelo(sys.argv[2], sys.argv[3])
