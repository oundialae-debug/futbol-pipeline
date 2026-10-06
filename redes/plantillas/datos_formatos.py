"""Datos de los formatos propios de 2yellow (usuario 06/10): 2yellow XI (once de la jornada por nota) y 2yellow Index
(top 5 de la semana). Solo NUESTROS datos (box-score de Highlightly), sin API.
    python3 redes/plantillas/datos_formatos.py xi <desde> <hasta> [selecciones|clubes] "<título>"
    python3 redes/plantillas/datos_formatos.py indice <desde> <hasta> [selecciones|clubes] "<título>"
2yellow Index = nota media x10 + 3 por gol o asistencia por partido (mín. 120' en el periodo), tope 100.
Clubes: solo jugadores con nombre en nuestros datos (todos desde el 9/10 con jugadores_redes.yml)."""
import json, subprocess, sys
from datetime import date
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import datos_rankings as R  # noqa: E402

POS = {"Goalkeeper": "GK", "Defender": "DF", "Midfielder": "MF", "Forward": "FW", "Attacker": "FW"}
FORMACION = {"GK": 1, "DF": 4, "MF": 3, "FW": 3}


def filas(desde, hasta, fuente):
    if fuente == "selecciones":
        p = pd.read_csv(ROOT / "data/selecciones/partidos.csv")
        p = p[(p.fecha >= desde) & (p.fecha <= hasta) & p.goles_l.notna()]
        j = pd.read_csv(ROOT / "data/selecciones/jugadores_partido.csv", low_memory=False)
        j = j[j.match_id.isin(p.match_id)].copy()
        eq = pd.concat([p[["local_id", "local"]].set_axis(["id", "n"], axis=1), p[["visitante_id", "visitante"]].set_axis(["id", "n"], axis=1)])
        j["equipo"] = j.equipo_id.map(dict(zip(eq.id, eq.n)))
        comp = ", ".join(sorted(p.competicion.unique()))
    else:
        h = pd.read_csv(ROOT / "data/historico_partidos.csv", low_memory=False)
        h = h[(h.fecha.astype(str).str[:10] >= desde) & (h.fecha.astype(str).str[:10] <= hasta) & h.liga.isin(R.GRANDES) & h.goles_l.notna()]
        j = pd.read_csv(ROOT / "data/historico_xg_jugador.csv", low_memory=False)
        j = j[j.match_id.isin(h.match_id) & j.jugador_id.notna()].copy()
        j["jugador"] = j.jugador_id.astype(int).map(R.nombres_propios())
        eq = pd.concat([h[["local_id", "local"]].set_axis(["id", "n"], axis=1), h[["visitante_id", "visitante"]].set_axis(["id", "n"], axis=1)])
        j["equipo"] = j.equipo_id.map(dict(zip(eq.id, eq.n)))
        j = j.dropna(subset=["jugador"])
        comp = "Top 5 leagues"
    for c in ("nota", "minutos", "goalsScored", "assists"):
        j[c] = pd.to_numeric(j[c], errors="coerce")
    j = j[j.minutos > 0]
    t = j.groupby(["jugador_id"]).agg(jugador=("jugador", "last"), equipo=("equipo", "last"), posicion=("posicion", "last"),
                                      nota=("nota", "mean"), partidos=("match_id", "nunique"), minutos=("minutos", "sum"),
                                      ga=("goalsScored", "sum"), asis=("assists", "sum")).reset_index()
    t["ga"] = t.ga.fillna(0) + t.asis.fillna(0)
    t["indice"] = (10 * t.nota + 3 * t.ga / t.partidos).clip(upper=100).round(0)
    t["pos"] = t.posicion.map(POS)
    return t.dropna(subset=["nota", "pos"]), comp


def render(nombre, datos):
    out = ROOT / "redes/plantillas/salida" / f"{date.today()}_{nombre}"
    out.mkdir(parents=True, exist_ok=True)
    jf = out / f"{nombre}.json"
    jf.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    subprocess.run([sys.executable, str(ROOT / "redes/plantillas/generar.py"), str(jf), "-o", str(out)], check=True)


def corto(n):
    p = str(n).split()
    return n if len(n) <= 13 or len(p) < 2 else " ".join(p[1:])  # quita el nombre de pila: "Kevin De Bruyne" -> "De Bruyne"


def xi(desde, hasta, fuente="clubes", titulo=None):
    t, comp = filas(desde, hasta, fuente)
    largo = (pd.Timestamp(hasta) - pd.Timestamp(desde)).days > 10
    t = t[t.minutos >= (360 if largo else 60)]  # torneo: mín. 4 partidos completos; jornada: titular
    jug = []
    for pos, n in FORMACION.items():
        for r in t[t.pos == pos].sort_values(["nota", "minutos"], ascending=False).head(n).itertuples():
            jug.append({"name": corto(R.visible_nombre(r.jugador)), "team": r.equipo, "pos": pos, "value": round(float(r.nota), 1)})
    render(f"xi_{desde}_{hasta}", {"template": "xi", "competition": comp, "kicker": "2yellow XI",
                                   "title": titulo or "Team of the week", "metric": "Best average match rating · 4-3-3", "players": jug,
                                   "question": "Who did we leave out?"})


def indice(desde, hasta, fuente="clubes", titulo=None):
    t, comp = filas(desde, hasta, fuente)
    largo = (pd.Timestamp(hasta) - pd.Timestamp(desde)).days > 10
    t = t[t.minutos >= (360 if largo else 120)].sort_values(["indice", "nota"], ascending=False).head(5)
    rows = [{"name": R.visible_nombre(r.jugador), "team": r.equipo, "value": int(r.indice),
             "detail": f"{r.nota:.1f} rating · {int(r.ga)} G+A"} for r in t.itertuples()]
    render(f"indice_{desde}_{hasta}", {"template": "indice", "competition": comp, "kicker": "2yellow Index",
                                       "title": titulo or "The week's top 5", "metric": "Match rating ×10 + 3 per goal or assist per game",
                                       "rows": rows, "question": "Who's too low?"})


if __name__ == "__main__":
    {"xi": xi, "indice": indice}[sys.argv[1]](*sys.argv[2:])
