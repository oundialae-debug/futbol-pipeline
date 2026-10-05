"""Escenas para el directo de TikTok (web/live): datos de selecciones -> escenas.json.

Sin red: lee data/selecciones/ (calendario y resultados de la Nations League,
pronósticos registrados, estadísticas de partido, notas de jugadores, ranking
FIFA). Cada escena lleva las frases en inglés que el narrador (repo
narrador-live) convierte en guion desbocado, y los datos que pinta la web.
Lenguaje de estadística, nunca de apuestas (normas de TikTok).

    python3 scripts/live_tiktok_escenas.py [--ahora 2026-10-05T14:30]
"""
import argparse
import collections
import csv
import datetime as dt
import json
import math
import os

D = "data/selecciones"
SALIDA = "web/live/escenas.json"
NOMBRE = {"Kosovo National Team": "Kosovo", "Bosnia & Herzegovina": "Bosnia and Herzegovina"}
RANKING_ALIAS = {"Turkey": "Türkiye", "Czech Republic": "Czechia",
                 "Bosnia & Herzegovina": "Bosnia and Herzegovina", "Kosovo National Team": "Kosovo"}
CODIGO_EXTRA = {"Turkey": "TUR", "Czech Republic": "CZE", "Bosnia & Herzegovina": "BIH",
                "Kosovo National Team": "KVX"}
NUM = ["nil", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def leer(f):
    return list(csv.DictReader(open(os.path.join(D, f), encoding="utf-8")))


def nom(e):
    return NOMBRE.get(e, e)


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pct(p):
    return round(100 * p)


def marcador(a, b):
    return f"{NUM[a] if a < len(NUM) else a}-{NUM[b] if b < len(NUM) else b}"


def hora_uk(fecha):
    t = dt.datetime.fromisoformat(fecha.replace("Z", "+00:00")) + dt.timedelta(hours=1)  # BST hasta el 25/10
    return t.strftime("%H:%M")


def dia(fecha):
    return dt.datetime.fromisoformat(fecha.replace("Z", "+00:00")).strftime("%A")


def marcador_probable(l1, l2):
    pois = lambda l, k: math.exp(-l) * l ** k / math.factorial(k)
    return max(((i, j) for i in range(7) for j in range(7)), key=lambda s: pois(l1, s[0]) * pois(l2, s[1]))


def cargar(ahora):
    cal = leer("nl_calendario.csv")
    jugados = [m for m in cal if m["terminado"] == "True" and m["goles_l"]]
    proximos = [m for m in cal if m["terminado"] != "True" and m["fecha"] >= ahora]
    for m in jugados:
        m["gl"], m["gv"] = int(float(m["goles_l"])), int(float(m["goles_v"]))
    # Último pronóstico registrado antes del partido
    reg = {}
    for r in leer("registro_pronosticos.csv"):
        if r["generado"] < r["fecha_partido"].replace("Z", "+00:00"):
            reg[r["match_id"]] = r
    rk_fecha = max(r["fecha"] for r in leer("ranking_fifa.csv"))
    rk = {r["equipo"]: r for r in leer("ranking_fifa.csv") if r["fecha"] == rk_fecha}
    return cal, jugados, proximos, reg, rk


def prob(r, lado):
    """Probabilidad final: el peso aprendido del modelo es 0 (pesos_mezcla.json), así que manda el mercado sin margen."""
    v = fnum(r.get(f"mkt_{lado}"))
    return v if v is not None else fnum(r.get(f"mod_{lado}"))


def ranking(rk, e):
    r = rk.get(RANKING_ALIAS.get(e, e)) or rk.get(e)
    return (int(float(r["puesto"])), r["codigo"]) if r else (None, CODIGO_EXTRA.get(e, e[:3].upper()))


def grupos(cal):
    """Grupos deducidos: en cada liga, los equipos que se han enfrentado entre sí."""
    padre = {}

    def raiz(x):
        while padre.setdefault(x, x) != x:
            x = padre[x]
        return x
    liga = {}
    for m in cal:
        liga[m["local"]] = liga[m["visitante"]] = m["ronda"].split(" - ")[0]
        padre[raiz(m["local"])] = raiz(m["visitante"])
    g = collections.defaultdict(list)
    for e in liga:
        g[(liga[e], raiz(e))].append(e)
    return sorted(((k[0], v) for k, v in g.items()), key=lambda x: (x[0], sorted(x[1])))


def tabla(equipos, jugados):
    t = {e: {"equipo": e, "pj": 0, "pts": 0, "gf": 0, "gc": 0, "forma": ""} for e in equipos}
    for m in sorted(jugados, key=lambda m: m["fecha"]):
        if m["local"] not in t:
            continue
        for e, gf, gc in ((m["local"], m["gl"], m["gv"]), (m["visitante"], m["gv"], m["gl"])):
            x = t[e]
            x["pj"] += 1; x["gf"] += gf; x["gc"] += gc
            x["pts"] += 3 if gf > gc else 1 if gf == gc else 0
            x["forma"] += "W" if gf > gc else "D" if gf == gc else "L"
    return sorted(t.values(), key=lambda x: (-x["pts"], -(x["gf"] - x["gc"]), -x["gf"]))


def jugadores(cal_ids, jugados):
    eq = {m["match_id"]: m for m in jugados}
    goles, asist, notas, equipo = collections.Counter(), collections.Counter(), collections.defaultdict(list), {}
    for x in leer("jugadores_partido.csv"):
        m = eq.get(x["match_id"])
        if not m:
            continue
        k = x["jugador"]
        equipo[k] = m["local"] if x["equipo_id"] == m["local_id"] else m["visitante"]
        goles[k] += int(fnum(x["goalsScored"]) or 0)
        asist[k] += int(fnum(x["assists"]) or 0)
        if fnum(x["nota"]) and (fnum(x["minutos"]) or 0) >= 45:
            notas[k].append(float(x["nota"]))
    mejores = sorted(((sum(v) / len(v), k) for k, v in notas.items() if len(v) >= 3), reverse=True)
    return goles, asist, mejores, equipo


def xg(jugados):
    ids = {m["match_id"]: m for m in jugados}
    acum = collections.defaultdict(lambda: [0.0, 0])
    for s in leer("estadisticas_partido.csv"):
        m = ids.get(s["match_id"])
        if not m or s["estadistica"] != "Expected Goals":
            continue
        local = s["equipo_id"] == m["local_id"]
        e = m["local"] if local else m["visitante"]
        acum[e][0] += float(s["valor"])
        acum[e][1] += m["gl"] if local else m["gv"]
    return {e: {"xg": round(v[0], 1), "goles": v[1], "dif": round(v[1] - v[0], 1)} for e, v in acum.items()}


def estrellas():
    mejor = {}
    for x in leer("notas_jugadores.csv"):
        n = fnum(x["nota"])
        if x["once_probable"] == "True" and n and (x["seleccion"] not in mejor or n > mejor[x["seleccion"]][1]):
            mejor[x["seleccion"]] = (x["jugador"], n, x["posicion"])
    return mejor


def escena_partido(m, r, rk, tab_eq, estrella, abre=False):
    L, V = m["local"], m["visitante"]
    p1, px, p2 = prob(r, "1"), prob(r, "X"), prob(r, "2")
    l1, l2 = float(r["lam_l"]), float(r["lam_v"])
    s = marcador_probable(l1, l2)
    fav, pf, dog, pd_ = (L, p1, V, p2) if p1 >= p2 else (V, p2, L, p1)
    frases = [f"{nom(L)} against {nom(V)}! {dia(m['fecha'])}, {hora_uk(m['fecha'])} UK time.",
              f"{nom(fav)} win this *{pct(pf)} percent* of the time.",
              f"The draw: {pct(px)} percent. {nom(dog)}: {pct(pd_)} percent."]
    if pf >= 0.8:
        frases.append(f"That is not a match, that's a *mismatch*.")
    elif abs(p1 - p2) < 0.1:
        frases.append("This one is a proper *coin flip*.")
    frases.append(f"Expected goals: {l1:.1f} for {nom(L)}, {l2:.1f} for {nom(V)}.")
    frases.append(f"Single most likely score: *{marcador(*s)}*.")
    o25, btts = prob(r, "mas_2.5"), prob(r, "btts")
    if o25:
        frases.append(f"Three goals or more? {pct(o25)} percent.")
    if btts:
        frases.append(f"Both teams scoring: {pct(btts)} percent.")
    if fnum(r.get("corners")):
        frases.append(f"About {round(float(r['corners']))} corners and {round(float(r['tarjetas']))} yellow cards expected.")
    for e in (L, V):
        f = tab_eq.get(e)
        if f and f["forma"]:
            g = f["forma"].count("W")
            frases.append(f"{nom(e)} so far: {g} {'win' if g == 1 else 'wins'} from {len(f['forma'])}, "
                          f"{f['gf']} scored, {f['gc']} conceded.")
    for e in (L, V):
        if e in estrella:
            j, n, _ = estrella[e]
            frases.append(f"Watch {j}: player rating *{n:.1f}*.")
    rl, rv = ranking(rk, L), ranking(rk, V)
    if rl[0] and rv[0]:
        frases.append(f"FIFA ranking: {nom(L)} number {rl[0]}, {nom(V)} number {rv[0]}.")
    return {"id": "", "tipo": "partido", "objetivo_s": 72, "abre": abre, "frases": frases,
            "datos": {"local": nom(L), "visitante": nom(V), "cod_l": rl[1], "cod_v": rv[1],
                      "rk_l": rl[0], "rk_v": rv[0], "dia": dia(m["fecha"]), "hora_uk": hora_uk(m["fecha"]),
                      "liga": m["ronda"].split(" - ")[0], "p1": pct(p1), "px": pct(px), "p2": pct(p2),
                      "xg_l": round(l1, 2), "xg_v": round(l2, 2), "marcador": f"{s[0]}-{s[1]}",
                      "mas25": pct(o25) if o25 else None, "btts": pct(btts) if btts else None,
                      "corners": round(float(r["corners"]), 1) if fnum(r.get("corners")) else None,
                      "tarjetas": round(float(r["tarjetas"]), 1) if fnum(r.get("tarjetas")) else None,
                      "forma_l": tab_eq.get(L, {}).get("forma", ""), "forma_v": tab_eq.get(V, {}).get("forma", ""),
                      "estrella_l": estrella.get(L, [None, None])[:2], "estrella_v": estrella.get(V, [None, None])[:2]}}


def construir(ahora):
    cal, jugados, proximos, reg, rk = cargar(ahora)
    grs = grupos(cal)
    tablas, tab_eq = [], {}
    for liga, eqs in grs:
        t = tabla(eqs, jugados)
        tablas.append({"liga": liga, "filas": t})
        tab_eq.update({x["equipo"]: x for x in t})
    goles, asist, mejores, equipo = jugadores(None, jugados)
    xgs = xg(jugados)
    estrella = estrellas()
    proximos = [m for m in sorted(proximos, key=lambda m: (m["fecha"], m["local"])) if m["match_id"] in reg]
    dias = collections.OrderedDict()
    for m in proximos:
        dias.setdefault(dia(m["fecha"]), []).append(m)
    escenas = []

    def agenda(nombre, ms):
        frases = [f"{nombre}: *{len(ms)} matches*."]
        for m in ms:
            frases.append(f"{nom(m['local'])} against {nom(m['visitante'])}, {hora_uk(m['fecha'])}.")
        return {"tipo": "agenda", "objetivo_s": 45, "frases": frases,
                "datos": {"dia": nombre, "partidos": [{"local": nom(m["local"]), "visitante": nom(m["visitante"]),
                                                       "cod_l": ranking(rk, m["local"])[1],
                                                       "cod_v": ranking(rk, m["visitante"])[1],
                                                       "hora_uk": hora_uk(m["fecha"]),
                                                       "p1": pct(prob(reg[m["match_id"]], "1")),
                                                       "px": pct(prob(reg[m["match_id"]], "X")),
                                                       "p2": pct(prob(reg[m["match_id"]], "2"))} for m in ms]}}

    n_jug = len(jugados)
    escenas.append({"tipo": "intro", "objetivo_s": 35, "abre": True, "frases": [
        "Hey hey hey! Welcome in! I'm *Blitz*, and tonight every number comes from our AI model.",
        f"Nations League week. *{sum(len(v) for v in dias.values())} matches* coming up, and I've got numbers on every single one.",
        f"{n_jug} games already played. *{sum(m['gl'] + m['gv'] for m in jugados)} goals*. Let's go!"],
        "datos": {"jugados": n_jug, "goles": sum(m["gl"] + m["gv"] for m in jugados),
                  "proximos": sum(len(v) for v in dias.values())}})

    bloques_extra = []
    # Resultados recientes
    recientes = sorted(jugados, key=lambda m: m["fecha"])[-8:]
    frases = ["The weekend, in thirty seconds. Go!"]
    for m in recientes:
        frases.append(f"{nom(m['local'])} {marcador(m['gl'], m['gv'])} {nom(m['visitante'])}.")
    bloques_extra.append({"tipo": "resultados", "objetivo_s": 45, "frases": frases,
                          "datos": {"partidos": [{"local": nom(m["local"]), "visitante": nom(m["visitante"]),
                                                  "cod_l": ranking(rk, m["local"])[1], "cod_v": ranking(rk, m["visitante"])[1],
                                                  "gl": m["gl"], "gv": m["gv"]} for m in recientes]}})
    # Goleada
    g = max(jugados, key=lambda m: (abs(m["gl"] - m["gv"]), m["gl"] + m["gv"]))
    ganador, perdedor = (g["local"], g["visitante"]) if g["gl"] > g["gv"] else (g["visitante"], g["local"])
    frases = [f"Biggest win of the whole tournament so far: *{nom(g['local'])} {marcador(g['gl'], g['gv'])} {nom(g['visitante'])}*.",
              f"{nom(ganador)} by {abs(g['gl'] - g['gv'])}! Away from home! Ridiculous."
              if g["gv"] > g["gl"] else f"{nom(ganador)} by {abs(g['gl'] - g['gv'])}. Ridiculous."]
    if g["match_id"] in reg:
        r = reg[g["match_id"]]
        pg = prob(r, "1" if ganador == g["local"] else "2")
        frases.append(f"Before kick-off, {nom(ganador)} had a {pct(pg)} percent win chance. A win, sure. But *by {abs(g['gl'] - g['gv'])}*?")
    bloques_extra.append({"tipo": "goleada", "objetivo_s": 40, "frases": frases,
                          "datos": {"local": nom(g["local"]), "visitante": nom(g["visitante"]), "gl": g["gl"], "gv": g["gv"],
                                    "cod_l": ranking(rk, g["local"])[1], "cod_v": ranking(rk, g["visitante"])[1]}})
    # Goleadores
    top = [(k, v) for k, v in goles.most_common(8) if v > 0]
    frases = ["Top scorers! Who's on fire?"]
    for k, v in top[:5]:
        frases.append(f"{k}, {nom(equipo[k])}: *{v} goals*." if v > 1 else f"{k}, {nom(equipo[k])}: {v} goal.")
    ta = [(k, v) for k, v in asist.most_common(3) if v > 1]
    if ta:
        frases.append("Assists king: " + " and ".join(f"{k} with *{v}*" for k, v in ta[:2]) + ".")
    bloques_extra.append({"tipo": "goleadores", "objetivo_s": 45, "frases": frases,
                          "datos": {"goles": [{"jugador": k, "equipo": nom(equipo[k]), "cod": ranking(rk, equipo[k])[1],
                                               "n": v} for k, v in top[:6]],
                                    "asistencias": [{"jugador": k, "equipo": nom(equipo[k]), "n": v} for k, v in ta]}})
    # Mejores notas
    frases = ["Player ratings. The best performers, three games or more."]
    for n, k in mejores[:5]:
        frases.append(f"{k}, {nom(equipo[k])}: *{n:.1f}*.")
    bloques_extra.append({"tipo": "notas", "objetivo_s": 40, "frases": frases,
                          "datos": {"jugadores": [{"jugador": k, "equipo": nom(equipo[k]), "cod": ranking(rk, equipo[k])[1],
                                                   "nota": round(n, 2)} for n, k in mejores[:6]]}})
    # Suerte con el xG
    orden = sorted(xgs.items(), key=lambda x: x[1]["dif"])
    frio, caliente = orden[:3], orden[::-1][:3]
    frases = ["Luck check! Goals scored versus expected goals."]
    for e, v in caliente[:2]:
        frases.append(f"{nom(e)}: {v['goles']} goals from {v['xg']} expected. *Plus {v['dif']}*. Clinical!")
    for e, v in frio[:2]:
        frases.append(f"{nom(e)}: just {v['goles']} goals from {v['xg']} expected. *Minus {abs(v['dif'])}*. Ouch.")
    bloques_extra.append({"tipo": "xg", "objetivo_s": 45, "frases": frases,
                          "datos": {"arriba": [{"equipo": nom(e), "cod": ranking(rk, e)[1], **v} for e, v in caliente],
                                    "abajo": [{"equipo": nom(e), "cod": ranking(rk, e)[1], **v} for e, v in frio]}})
    # Acierto del favorito
    ac = [(m, reg[m["match_id"]]) for m in jugados if m["match_id"] in reg]
    if ac:
        aciertos = 0
        for m, r in ac:
            p1, px, p2 = prob(r, "1"), prob(r, "X"), prob(r, "2")
            res = "1" if m["gl"] > m["gv"] else "X" if m["gl"] == m["gv"] else "2"
            aciertos += max((p1, "1"), (px, "X"), (p2, "2"))[1] == res
        tasa = aciertos / len(ac)
        bloques_extra.append({"tipo": "acierto", "objetivo_s": 35, "frases": [
            "Honesty time. How good are the numbers?",
            f"We tracked {len(ac)} games. The favourite got it right *{pct(tasa)} percent* of the time.",
            "Not a crystal ball. Football is chaos. That's why we love it."],
            "datos": {"partidos": len(ac), "aciertos": aciertos, "pct": pct(tasa)}})
    # Líderes de grupo
    lid = [(t["liga"], t["filas"][0]) for t in tablas if t["filas"][0]["pj"]]
    frases = ["Group leaders, every league, quick fire!"]
    for liga, x in lid:
        frases.append(f"{liga}: {nom(x['equipo'])}, {x['pts']} points.")
    bloques_extra.append({"tipo": "tablas", "objetivo_s": 50, "frases": frases,
                          "datos": {"tablas": [{"liga": t["liga"], "filas": [{**x, "equipo": nom(x["equipo"]),
                                                                             "cod": ranking(rk, x["equipo"])[1]}
                                                                            for x in t["filas"]]} for t in tablas]}})
    # Ranking FIFA
    en = sorted({e for m in cal for e in (m["local"], m["visitante"]) if ranking(rk, e)[0]}, key=lambda e: ranking(rk, e)[0])
    frases = ["FIFA ranking, Europe's top five in this Nations League."]
    for e in en[:5]:
        frases.append(f"Number {ranking(rk, e)[0]} in the world: *{nom(e)}*.")
    bloques_extra.append({"tipo": "ranking", "objetivo_s": 35, "frases": frases,
                          "datos": {"equipos": [{"equipo": nom(e), "cod": ranking(rk, e)[1], "puesto": ranking(rk, e)[0]}
                                                for e in en[:10]]}})

    # Orden: agenda y partidos de cada día, con bloques de datos intercalados
    extra = iter(bloques_extra)
    for d, ms in dias.items():
        escenas.append(agenda(d, ms))
        for i, m in enumerate(ms):
            escenas.append(escena_partido(m, reg[m["match_id"]], rk, tab_eq, estrella))
            if i % 2 == 1:
                b = next(extra, None)
                if b:
                    escenas.append(b)
    escenas.extend(extra)
    escenas.append({"tipo": "cierre", "objetivo_s": 25, "frases": [
        "That's the full board! Every match, every number.",
        "All of it worked out by our AI model. I'll be right back, from the top. Stay, stay, stay!"], "datos": {}})
    for i, e in enumerate(escenas):
        e["id"] = f"s{i:02d}"
        e.setdefault("abre", False)
    return {"titulo": "Nations League live data", "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
            "datos_hasta": max(r["generado"] for r in reg.values())[:16], "escenas": escenas}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ahora", default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M"))
    ap.add_argument("--salida", default=SALIDA)
    a = ap.parse_args()
    e = construir(a.ahora)
    os.makedirs(os.path.dirname(a.salida), exist_ok=True)
    json.dump(e, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    obj = sum(x["objetivo_s"] for x in e["escenas"])
    print(f"{len(e['escenas'])} escenas, objetivo {obj / 60:.1f} min -> {a.salida}")


if __name__ == "__main__":
    main()
