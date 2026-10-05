"""Rellena las plantillas de 2yellow con datos REALES de selecciones (ya en disco, sin API).

Cruza data/selecciones/partidos.csv (resultados), registro_pronosticos.csv (nuestro
último pronóstico ANTES del saque, modelo y mercado), estadisticas_partido.csv (xG, tiros)
y el Elo de modelos/selecciones/experimento_variables.py.
    python3 redes/plantillas/datos_selecciones.py post Germany 2026-10-04
    python3 redes/plantillas/datos_selecciones.py pre France 2026-10-05
Deja los JSON y los PNG en redes/plantillas/salida/<fecha>_<local>_<visitante>/.
Ejecutar desde la raíz del repo.
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import poisson

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, "modelos/selecciones")
import generar as G  # noqa: E402

C = "data/selecciones"
CORTO = {"Kosovo National Team": "Kosovo", "Republic of Ireland": "Ireland", "Bosnia and Herzegovina": "Bosnia",
         "Czech Republic": "Czechia", "North Macedonia": "N. Macedonia", "Northern Ireland": "N. Ireland"}
COMP = "Nations League"


def eq(n):
    return {"name": n, "short": CORTO.get(n, n)}


def pronostico(mid):
    """Último pronóstico generado antes del saque."""
    r = pd.read_csv(f"{C}/registro_pronosticos.csv")
    g = r[r.match_id == mid].copy()
    g = g[pd.to_datetime(g.generado, utc=True) < pd.to_datetime(g.fecha_partido, utc=True)]
    return None if g.empty else g.sort_values("generado").iloc[-1]


def picks(x):
    """Nuestra elección en cada mercado (la opción con >= 50 %) y su probabilidad."""
    pr = {"home": x.mod_1, "draw": x.mod_X, "away": x.mod_2}
    out = {"1X2": max(pr, key=pr.get)}
    pct = {out["1X2"]: pr[out["1X2"]]}
    for fam, col, si, no in (("Over/Under 2.5", "mod_mas_2.5", "over25", "under25"),
                             ("Both teams score", "mod_btts", "btts_yes", "btts_no"),
                             ("Over/Under 1.5", "mod_mas_1.5", "over15", "under15"),
                             ("Over/Under 3.5", "mod_mas_3.5", "over35", "under35")):
        v = x[col]
        out[fam] = si if v >= .5 else no
        pct[out[fam]] = v if v >= .5 else 1 - v
    return out, pct


def stats(mid, tid):
    e = pd.read_csv(f"{C}/estadisticas_partido.csv")
    e = e[(e.match_id == mid) & (e.equipo_id == tid)]
    return dict(zip(e.estadistica, pd.to_numeric(e.valor, errors="coerce")))


def elo_series(nombres):
    """Elo tras cada partido (último valor = Elo actual), con el código del modelo de selecciones."""
    import modelo_selecciones as S, experimento_variables as X
    p, _, _, _ = S.cargar()
    ids = dict(zip(pd.concat([p.local, p.visitante]), pd.concat([p.local_id, p.visitante_id])))
    # una fila de cierre por equipo para leer su Elo actual como "Elo previo"
    cierre = pd.DataFrame([dict(match_id=9e15 + k, fecha="2100-01-01", local=n, local_id=ids[n], visitante=n,
                                visitante_id=-1 - k, goles_l=0.0, goles_v=0.0, casa=0.0, amistoso=0.0)
                           for k, n in enumerate(nombres)])
    q = pd.concat([p, cierre], ignore_index=True)
    pl, pv = X.elo_previo(q)
    q = q.sort_values(["fecha", "match_id"])
    return {n: [round(pl[x.match_id] if x.local == n else pv[x.match_id])
                for _, x in q.iterrows() if n in (x.local, x.visitante)]
            for n in nombres}


def partido(equipo, fecha):
    p = pd.read_csv(f"{C}/partidos.csv")
    m = p[(p.fecha == fecha) & ((p.local == equipo) | (p.visitante == equipo))]
    if m.empty:
        sys.exit(f"No hay partido de {equipo} el {fecha} en {C}/partidos.csv")
    return m.iloc[0], p


def post(equipo, fecha):
    m, p = partido(equipo, fecha)
    h, a = eq(m.local), eq(m.visitante)
    gh, ga = int(m.goles_l), int(m.goles_v)
    x = pronostico(m.match_id)
    sl, sv = stats(m.match_id, m.local_id), stats(m.match_id, m.visitante_id)
    out = {}
    base = {"competition": COMP, "home": h, "away": a, "score": [gh, ga]}
    if "Expected Goals" in sl:
        out["post1_deserved"] = {**base, "template": "deserved", "xg": [sl["Expected Goals"], sv["Expected Goals"]]}
    if x is not None:
        elec, pct = picks(x)
        # el mercado acertado con más confianza
        buenos = [(pct[v], v) for v in elec.values() if G.acierto(v, gh, ga)]
        if buenos:
            pc, mk = max(buenos)
            out["post2_prediction_vs_result"] = {**base, "template": "prediction_vs_result", "market": mk, "pct": round(pc * 100)}
        fav = max(("home", "draw", "away"), key=lambda k: {"home": x.mod_1, "draw": x.mod_X, "away": x.mod_2}[k])
        ganador = "home" if gh > ga else "away" if ga > gh else None
        prob = {"home": x.mod_1, "away": x.mod_2}
        if ganador and ganador != fav and prob[ganador] < .3:
            out["post3_upset_happened"] = {**base, "template": "upset_happened", "underdog": ganador,
                                           "pre_pct": round(prob[ganador] * 100)}
    # dato del partido: el equipo que más tiró sin marcar, o el que más tiró
    tiros = {"home": sum(sl.get(k, 0) for k in ("Shots on target", "Shots off target", "Blocked shots")),
             "away": sum(sv.get(k, 0) for k in ("Shots on target", "Shots off target", "Blocked shots"))}
    lado = max(tiros, key=tiros.get)
    goles = gh if lado == "home" else ga
    if tiros[lado]:
        t = h if lado == "home" else a
        texto = (f'shots from <b>{t["short"]}</b>. Zero goals.' if goles == 0
                 else f'shots from <b>{t["short"]}</b> for {goles} goal{"s" * (goles > 1)}.')
        out["post4_stat_of_match"] = {**base, "template": "stat_of_match", "number": str(int(tiros[lado])),
                                      "text": texto, "team": lado, "question": "Wasteful or unlucky?"}
    # la jornada entera (todos los partidos de ese día con pronóstico)
    filas = []
    for _, r in p[(p.fecha == fecha) & p.terminado].iterrows():
        y = pronostico(r.match_id)
        if y is not None:
            filas.append([CORTO.get(r.local, r.local), int(r.goles_l), int(r.goles_v), CORTO.get(r.visitante, r.visitante),
                          picks(y)[0]])
    if len(filas) >= 3:
        out["post5_weekend_record"] = {"template": "weekend_record", "competition": f"{COMP} · {fecha[8:]}/{fecha[5:7]}",
                                       "matches": filas, "question": "Beat us next time?"}
    return m, out


def pre(equipo, fecha):
    m, p = partido(equipo, fecha)
    h, a = eq(m.local), eq(m.visitante)
    x = pronostico(m.match_id)
    if x is None:
        sys.exit("Sin pronóstico previo para ese partido")
    base = {"competition": COMP, "home": h, "away": a}
    probs = [round(x.mod_1 * 100), round(x.mod_X * 100), round(x.mod_2 * 100)]
    ms = max(((i, j) for i in range(7) for j in range(7)),
             key=lambda t: poisson.pmf(t[0], x.lam_l) * poisson.pmf(t[1], x.lam_v))
    out = {"pre1_prediction": {**base, "template": "prediction", "probs": probs, "predicted_score": list(ms)}}
    # sorpresa: el no favorito al que damos más que las casas
    dog = "home" if x.mod_1 < x.mod_2 else "away"
    mod, mkt = (x.mod_1, x.mkt_1) if dog == "home" else (x.mod_2, x.mkt_2)
    if mod > mkt and pd.notna(mkt):
        out["pre2_upset_alert"] = {**base, "template": "upset_alert", "underdog": dog,
                                   "model_pct": round(mod * 100), "bookies_pct": round(mkt * 100)}
    out["pre3_goals"] = {**base, "template": "goals", "btts": round(x.mod_btts * 100),
                         "exp_goals": [round(x.lam_l, 1), round(x.lam_v, 1)]}
    el = elo_series([m.local, m.visitante])
    cambio = {k: v[-1] - v[-6] for k, v in el.items()}
    foco = max(cambio, key=lambda k: abs(cambio[k]))
    otro = m.visitante if foco == m.local else m.local
    extra = f'{CORTO.get(otro, otro)}: {"+" if cambio[otro] >= 0 else "−"}{abs(cambio[otro])} in the same span.'
    out["pre4_elo_form"] = {**base, "template": "elo_form", "focus": "home" if foco == m.local else "away",
                            "elo_home": el[m.local][-10:], "elo_away": el[m.visitante][-10:], "extra": extra,
                            "question": "Real form or a lucky run?" if cambio[foco] >= 0 else "Crisis or just a blip?"}
    # dato clave: el último cara a cara
    cc = p[p.terminado & (((p.local == m.local) & (p.visitante == m.visitante)) |
                          ((p.local == m.visitante) & (p.visitante == m.local))) & (p.fecha < fecha)]
    if not cc.empty:
        u = cc.sort_values("fecha").iloc[-1]
        dias = (pd.Timestamp(fecha) - pd.Timestamp(u.fecha)).days
        gl, gv = int(u.goles_l), int(u.goles_v)
        if gl == gv:
            txt = f"in their last meeting, {dias} days ago."
        else:
            gan = u.local if gl > gv else u.visitante
            txt = f'<b>{CORTO.get(gan, gan)}</b> won the last meeting, {dias} days ago.'
        lado = None if gl == gv else ("home" if (u.local if gl > gv else u.visitante) == m.local else "away")
        out["pre5_key_number"] = {**base, "template": "key_number", "team": lado, "number": f"{max(gl, gv)}–{min(gl, gv)}", "text": txt,
                                  "when": "Tonight · " + pd.Timestamp(x.fecha_partido).tz_convert("Europe/Madrid").strftime("%H:%M %Z"), "question": "Revenge or repeat?"}
    return m, out


if __name__ == "__main__":
    modo, equipo, fecha = sys.argv[1:4]
    m, datos = (post if modo == "post" else pre)(equipo, fecha)
    carpeta = AQUI / "salida" / f"{fecha}_{m.local}_{m.visitante}".replace(" ", "_")
    carpeta.mkdir(parents=True, exist_ok=True)
    trabajos = []
    for nombre, d in datos.items():
        (carpeta / f"{nombre}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, default=float))
        trabajos.append((d, carpeta / f"{nombre}.png"))
    G.renderizar(trabajos)
