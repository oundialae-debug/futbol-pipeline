"""Jugadores de FotMob (data/fotmob_jugadores.csv, sin cuota de Highlightly) con el formato de historico_xg_jugador.csv,
para que 2yellow XI / Index sigan saliendo cuando la API no trae el box-score (13/10/2026: 100 llamadas/día).
Solo se usan los partidos que NO están ya en nuestros datos de Highlightly. Los jugadores se emparejan con su
jugador_id de Highlightly por nombre normalizado + club (así conservan su posición de jugador_perfil.csv); si no
empareja, id = -fotmob_jugador_id (solo podrá ocupar el hueco central de su línea)."""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fd_a_historico import limpio, parecido  # noqa: E402

MAPA = {"nota": "rating_title", "minutos": "minutes_played", "goalsScored": "goals", "assists": "assists",
        "expectedGoals": "expected_goals", "expectedAssists": "expected_assists", "shotsOnTarget": "ShotsOnTarget",
        "passesKey": "chances_created", "dribblesSuccessful": "dribbles_succeeded", "passesSuccessful": "accurate_passes",
        "tacklesTotal": "matchstats.headers.tackles", "interceptionsTotal": "interceptions", "duelsWon": "duel_won",
        "goalsSaved": "saves", "goalsConceded": "goals_conceded", "expectedGoalsPrevented": "goals_prevented"}


def extra(desde, hasta, h, x, nombres):
    """h = partidos (historico) del periodo con liga en las 5 grandes; x = jugadores de Highlightly ya cargados;
    nombres = jugador_id -> nombre. Devuelve filas tipo x (con columnas equipo_fm y jugador) de partidos sin cubrir."""
    ruta = ROOT / "data/fotmob_jugadores.csv"
    if not ruta.exists():
        return pd.DataFrame()
    f = pd.read_csv(ruta, low_memory=False)
    f = f[(f.fecha >= desde) & (f.fecha <= hasta) & (f.liga != "Champions League")]
    if f.empty:
        return pd.DataFrame()
    cubiertos = h[h.match_id > 0]
    cubiertos = cubiertos[cubiertos.match_id.isin(x.match_id)]
    cubiertos = [(pd.Timestamp(str(r.fecha)[:10]), r.local, r.visitante) for r in cubiertos.itertuples()]

    def cubierto(fecha, equipo):
        d0 = pd.Timestamp(fecha)
        return any(abs((d - d0).days) <= 1 and (parecido(equipo, a) >= .78 or parecido(equipo, b) >= .78) for d, a, b in cubiertos)

    ok = {(fm, e): not cubierto(fe, e) for fm, fe, e in f[["fotmob_match_id", "fecha", "equipo"]].drop_duplicates().itertuples(index=False)}
    f = f[[ok[(a, b)] for a, b in zip(f.fotmob_match_id, f.equipo)]].copy()
    if f.empty:
        return pd.DataFrame()
    # emparejar con ids de Highlightly: nombre normalizado -> ids (solo si es único) + posición conocida
    pos = x.dropna(subset=["jugador_id"]).drop_duplicates("jugador_id", keep="last").set_index("jugador_id").posicion.to_dict()
    por_nombre = {}
    for i, n in nombres.items():
        por_nombre.setdefault(limpio(n), set()).add(int(i))
    ids, posic = [], []
    for r in f.itertuples():
        c = por_nombre.get(limpio(r.jugador), set())
        c = {i for i in c if i in pos}
        if len(c) == 1:
            i = next(iter(c)); ids.append(i); posic.append(pos[i])
        else:
            ids.append(-int(r.fotmob_jugador_id))
            pf = getattr(r, "pos_fm", None)
            posic.append("Goalkeeper" if r.portero == 1 else {1: "Defender", 2: "Midfielder", 3: "Forward"}.get(int(pf) if pf == pf and pf is not None else -1))
    # nombre de club como en nuestro histórico (Highlightly): "Internazionale" -> "Inter"
    hist = pd.concat([h[["liga", "local"]].set_axis(["liga", "n"], axis=1), h[["liga", "visitante"]].set_axis(["liga", "n"], axis=1)])
    cat = {l: sorted(set(g.n.dropna())) for l, g in hist.groupby("liga")}
    cache = {}

    def club(l, e):
        if (l, e) not in cache:
            mej = max(((parecido(e, n), n) for n in cat.get(l, [])), default=(0, e))
            cache[(l, e)] = mej[1] if mej[0] >= .78 else e
        return cache[(l, e)]
    equipo_fm = [club(l, e) for l, e in zip(f.liga, f.equipo)]
    out = pd.DataFrame({"match_id": -f.fotmob_match_id.astype(int), "jugador_id": ids, "posicion": posic,
                        "jugador": f.jugador.values, "equipo_fm": equipo_fm})
    for dest, orig in MAPA.items():
        out[dest] = pd.to_numeric(f[orig], errors="coerce").values if orig in f else float("nan")
    out["duelsTotal"] = (pd.to_numeric(f.get("duel_won"), errors="coerce") + pd.to_numeric(f.get("duel_lost"), errors="coerce")).values
    out["equipo_id"] = float("nan")
    return out.dropna(subset=["posicion"])
