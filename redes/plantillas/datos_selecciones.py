"""Rellena las plantillas de 2yellow con datos REALES de selecciones (ya en disco, sin API).

Cruza data/selecciones/partidos.csv (resultados), registro_pronosticos.csv (nuestro
último pronóstico ANTES del saque, modelo y mercado), estadisticas_partido.csv (xG, tiros)
y el Elo de modelos/selecciones/experimento_variables.py.
    python3 redes/plantillas/datos_selecciones.py post Germany 2026-10-04
    python3 redes/plantillas/datos_selecciones.py pre France 2026-10-05
    python3 redes/plantillas/datos_selecciones.py hoy 2026-10-05        # todos los pronósticos del día
    python3 redes/plantillas/datos_selecciones.py perfil 2026-10-05     # los dos que tapa la 6ª
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
CORTO = {"Kosovo National Team": "Kosovo", "Republic of Ireland": "Ireland", "Bosnia and Herzegovina": "Bosnia", "Bosnia & Herzegovina": "Bosnia",
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


def dia(fecha_partido):
    t = pd.Timestamp(fecha_partido).tz_convert("Europe/Madrid")
    hoy = pd.Timestamp.now(tz="Europe/Madrid").normalize()
    return "tonight’s" if t.normalize() == hoy else "tomorrow’s" if t.normalize() == hoy + pd.Timedelta(days=1) \
        else f"{t:%A}’s"


def tapada(d):
    """La 6ª enseña los partidos pero tapa pronóstico y %: la lista completa está en el perfil."""
    n = len(d["picks"])
    return {**d, "locked": True, "kicker": "Locked", "title": f"{n} calls tonight",
            "question": "Swipe to unlock them all."}


def teaser_lista(fecha, excluir=()):
    """6ª: el pronóstico MÁS SEGURO de la lista del día (solo modelo) que no sea el del propio partido.
    Lo que se tapa es justo lo que enseña la imagen del perfil."""
    _, datos = lista_hoy(fecha)
    cand = [m for m in datos["perfil_picks_hoy"]["picks"]
            if m["home"]["name"] not in excluir and m["away"]["name"] not in excluir]
    if not cand:
        return None
    t = cand[0]                                   # la lista ya va ordenada de mayor a menor %
    hora = pd.Timestamp(f"{fecha} {t['time']}")
    return {"template": "follow", "competition": COMP, "home": t["home"], "away": t["away"],
            "kicker": "Next up · Tonight", "side": None, "hidden_pct": t["pct"],
            "text": f"Our call + {len(datos['perfil_picks_hoy']['picks']) - 1} more on our profile."}


def teaser(top):
    """Datos de la 6ª: el próximo partido grande y el % de nuestro favorito, que irá tapado."""
    pr = {"home": top.mod_1, "draw": top.mod_X, "away": top.mod_2}
    fav = max(pr, key=pr.get)
    return {"template": "follow", "competition": COMP, "home": eq(top.local), "away": eq(top.visitante),
            "kicker": f"Next up · {dia(top.fecha_partido).replace('’s', '')}", "side": fav,
            "hidden_pct": round(pr[fav] * 100), "text": "Our call is on our profile."}


def siguiente_en(r):
    f = pd.read_csv(f"{C}/ranking_fifa.csv").sort_values("fecha").groupby("equipo").puntos.last()
    import experimento_variables as X
    pts = lambda n: f.get(X.ALIAS.get(n, n), f.get(n.replace(" & ", " and "), 1000))
    r = r.drop_duplicates("match_id")
    return len(r), max(r.itertuples(), key=lambda x: pts(x.local) + pts(x.visitante))


def siguiente(desde, excluir=None):
    """Partidos ya pronosticados desde 'desde' y el más llamativo (más puntos FIFA sumados)."""
    r = pd.read_csv(f"{C}/registro_pronosticos.csv")
    r = r[pd.to_datetime(r.fecha_partido, utc=True) >= pd.Timestamp(desde, tz="UTC")].drop_duplicates("match_id")
    if excluir is not None:
        r = r[r.match_id != excluir]
    return siguiente_en(r) if len(r) else (0, None)


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
        buenos = sorted((pct[v], v) for f, v in elec.items() if f in G.PRINCIPALES and G.acierto(v, gh, ga))
        buenos = buenos or sorted(((pct[v], v) for v in elec.values() if G.acierto(v, gh, ga)), reverse=True)
        if buenos:
            pc, mk = buenos[0]
            out["post2_prediction_vs_result"] = {**base, "template": "prediction_vs_result", "market": mk, "pct": round(pc * 100)}
        fav = max(("home", "draw", "away"), key=lambda k: {"home": x.mod_1, "draw": x.mod_X, "away": x.mod_2}[k])
        ganador = "home" if gh > ga else "away" if ga > gh else None
        prob = {"home": x.mod_1, "away": x.mod_2}
        prob["draw"] = x.mod_X
        real = ganador or "draw"
        if real != fav and prob[real] < .3:
            out["post3_upset_happened"] = {**base, "template": "upset_happened", "underdog": real, "favourite": fav,
                                           "pre_pct": round(prob[real] * 100),
                                           "question": "Shock or fair?" if real == "draw" else "Who called it?"}
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
                          {k: [v, picks(y)[1][v]] for k, v in picks(y)[0].items()}])
    if len(filas) >= 3:
        out["post5_weekend_record"] = {"template": "weekend_record", "competition": f"{COMP} · {fecha[8:]}/{fecha[5:7]}",
                                       "matches": filas, "question": "Beat us next time?"}
    # 6ª: la lista de pronósticos de la jornada siguiente (solo modelo), con @2yellowdata
    sig = str((pd.Timestamp(fecha) + pd.Timedelta(days=1)).date())
    try:
        out["post6_lista"] = tapada(lista_hoy(sig)[1]["perfil_picks_hoy"])
    except Exception:
        pass
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
    out["pre6_lista"] = tapada(lista_hoy(fecha)[1]["perfil_picks_hoy"])     # 6ª: partidos a la vista, pronósticos tapados
    return m, out


def perfil(fecha):
    """La imagen del perfil: el partido grande de 'fecha' y el del día siguiente, destapados
    (son los que tapa la 6ª del post y del previo)."""
    r = pd.read_csv(f"{C}/registro_pronosticos.csv")
    tops = []
    for f in (fecha, str((pd.Timestamp(fecha) + pd.Timedelta(days=1)).date())):
        del_dia = r[r.fecha_partido.str.startswith(f)]
        if not del_dia.empty:
            tops.append(siguiente_en(del_dia)[1])
    partidos = []
    for t in tops:
        x = pronostico(t.match_id)
        elec, pct = picks(x)
        extra = max((elec[k] for k in ("Over/Under 2.5", "Both teams score")), key=lambda v: pct[v])
        ms = max(((i, j) for i in range(7) for j in range(7)),
                 key=lambda q: poisson.pmf(q[0], x.lam_l) * poisson.pmf(q[1], x.lam_v))
        hora = pd.Timestamp(x.fecha_partido).tz_convert("Europe/Madrid")
        partidos.append({"home": eq(x.local), "away": eq(x.visitante), "when": f"{dia(x.fecha_partido).replace('’s', '')} · {hora:%H:%M %Z}",
                         "probs": [round(x.mod_1 * 100), round(x.mod_X * 100), round(x.mod_2 * 100)],
                         "score": list(ms), "extra": [extra, float(pct[extra])]})
    d = {"template": "our_calls", "competition": COMP, "home": partidos[0]["home"], "away": partidos[-1]["away"],
         "kicker": "Unlocked", "title": "The calls you swiped for", "matches": partidos}
    return {"local": "perfil", "visitante": fecha}, {"perfil_our_calls": d}


def leer(nombre):
    """Lee data/selecciones/<nombre> de origin/main (lo actualiza el workflow de selecciones); si no, el local."""
    import io, subprocess
    try:
        txt = subprocess.run(["git", "show", f"origin/main:{C}/{nombre}"], capture_output=True, text=True, check=True).stdout
        return pd.read_csv(io.StringIO(txt))
    except Exception:
        return pd.read_csv(f"{C}/{nombre}")


# (columna del registro, mercado en cuotas_hoy, lado sí, lado no, texto sí, texto no). Solo mercados
# con historial medido (modelos/selecciones/CLAUDE.md, "Listas para el usuario").
MERCADOS_LISTA = [("1", "Full Time Result", "Home", None, "{h} win", None),
                  ("X", "Full Time Result", "Draw", None, "Draw", None),
                  ("2", "Full Time Result", "Away", None, "{a} win", None),
                  ("btts", "Both Teams To Score", "Yes", "No", "Both teams score", "Not both teams score")]
MERCADOS_LISTA += [(f"mas_{x}", f"Total Goals {x}", "Over", "Under", f"Over {x} goals", f"Under {x} goals")
                   for x in ("1.5", "2.5", "3.5")]
# Córners fuera de las listas del modelo: en evaluacion.md su Brier (0.27 y 0.25) es igual o peor que decir
# 50 % siempre (0.25). Volver a meterlos si el modelo de córners mejora.


def lista_hoy(fecha, cuota_min=1.44, mejor_min=1.50):
    """Lo más probable de cada partido según NUESTRO MODELO (sin mezclar con el mercado). Las cuotas
    solo filtran lo trivial: cuota mediana >= cuota_min y mejor cuota >= mejor_min."""
    r = leer("registro_pronosticos.csv")
    r = r[r.fecha_partido.str.startswith(fecha)].sort_values("generado").drop_duplicates("match_id", keep="last")
    cu = leer("cuotas_hoy.csv")
    picks_ = []
    for _, x in r.iterrows():
        q = cu[cu.match_id == x.match_id]
        cand = []
        for k, mk, si, no, tsi, tno in MERCADOS_LISTA:
            mo = x.get(f"mod_{k}")
            if pd.isna(mo):
                continue
            p = mo                       # SOLO nuestro modelo (decisión del usuario, 05/10): nada del mercado
            for lado, txt, pp in ((si, tsi, p), (no, tno, 1 - p)):
                o = q[(q.mercado == mk) & (q.lado == lado)].cuota if lado else pd.Series(dtype=float)
                if len(o) and o.median() >= cuota_min and o.max() >= mejor_min:
                    cand.append((pp, txt.format(h=CORTO.get(x.local, x.local), a=CORTO.get(x.visitante, x.visitante))))
        if cand:
            pp, txt = max(cand)
            hora = pd.Timestamp(x.fecha_partido).tz_convert("Europe/Madrid")
            picks_.append({"time": f"{hora:%H:%M}", "home": eq(x.local.replace(" & ", " and ")),
                           "away": eq(x.visitante.replace(" & ", " and ")), "pick": txt, "pct": round(pp * 100)})
    picks_.sort(key=lambda m: -m["pct"])
    d = {"template": "picks_list", "competition": f"{COMP} · {fecha[8:]}/{fecha[5:7]}", "home": picks_[0]["home"],
         "away": picks_[0]["away"], "kicker": "Unlocked", "title": f"Tonight’s {len(picks_)} calls", "picks": picks_}
    return {"local": "perfil", "visitante": fecha}, {"perfil_picks_hoy": d}


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo in ("perfil", "hoy"):
        fecha = sys.argv[2]
        m, datos = perfil(fecha) if modo == "perfil" else lista_hoy(fecha, *map(float, sys.argv[3:5]))
        m = pd.Series(m)
    else:
        equipo, fecha = sys.argv[2:4]
        m, datos = (post if modo == "post" else pre)(equipo, fecha)
    carpeta = AQUI / "salida" / f"{fecha}_{m.local}_{m.visitante}".replace(" ", "_")
    carpeta.mkdir(parents=True, exist_ok=True)
    trabajos = []
    for nombre, d in datos.items():
        (carpeta / f"{nombre}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, default=float))
        trabajos.append((d, carpeta / f"{nombre}.png"))
    G.renderizar(trabajos)
