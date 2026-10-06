"""
Pronósticos PREVIOS registrados cada hora (30/09/2026), para que el modelo aprenda también del previo
y no solo del directo. Para cada partido individual de hoy que aún no ha empezado: ganador y total de
juegos según el modelo (fuerza antes del partido, superficie real) y según la casa (get_odds: mediana
de las casas que da la API, sin margen), en la línea principal (la más cercana al 50%) y en las demás.
Cada hora se sobrescribe la foto de los que siguen sin empezar: la que queda es la última antes del
pitido. 1 petición más por hora (get_odds del día). Escribe data/tenis/api_tennis/previa/<fecha>.csv.
"""
import csv
import os
import statistics as S

import api_tennis as A
import markov_tenis as K
import pronosticos_api as Q

PRE = "data/tenis/api_tennis/previa"
CAMPOS = ["hora", "event_key", "tipo", "torneo", "superficie", "jugador1", "jugador2", "mejor_de", "p_saque1",
          "p_saque2", "gana1_modelo", "gana1_casa", "linea", "mas_modelo", "mas_casa", "cuota_mas", "cuota_menos",
          "principal", "esperado_modelo", "mas_ajustado"]


def _mediana(d):
    v = [float(x) for x in (d or {}).values() if x not in (None, "")]
    return S.median(v) if v else None


def registrar(ahora, partidos):
    fecha = f"{ahora:%Y-%m-%d}"
    ruta = f"{PRE}/{fecha}.csv"
    previas = {}
    if os.path.exists(ruta):
        for r in csv.DictReader(open(ruta)):
            previas.setdefault(r["event_key"], []).append(r)
    pendientes = [p for p in partidos if not p.get("event_status") and A.circuito(p) and "/" not in
                  str(p.get("event_first_player"))]
    if not pendientes:
        return
    try:
        odds = A.cuotas_dia(fecha)
    except RuntimeError as e:
        print(e)
        return
    for p in pendientes:
        k = str(p.get("event_key"))
        o = odds.get(k) if isinstance(odds, dict) else None
        circ = A.circuito(p)
        a, b = Q.jugador(circ, p.get("event_first_player")), Q.jugador(circ, p.get("event_second_player"))
        if not o or a is None or b is None:
            continue
        sup = Q.superficie(circ, p.get("tournament_name"), p.get("tournament_key"))
        pa, pb = K.redondear(Q.prob_saque(circ, a, b, sup)), K.redondear(Q.prob_saque(circ, b, a, sup))
        bo = A.mejor_de(p)
        r1 = K.partido_desde(pa, pb, bo, 0, 0, 0, 0, True, 0, 0, (0, 0))
        r2 = K.partido_desde(pa, pb, bo, 0, 0, 0, 0, False, 0, 0, (0, 0))    # no se sabe quién saca: media
        gana = (r1["gana_A"] + r2["gana_A"]) / 2
        tot = {g: (r1["total"].get(g, 0) + r2["total"].get(g, 0)) / 2 for g in set(r1["total"]) | set(r2["total"])}
        qa, qb = (K.redondear(x) for x in Q.ajuste_juegos(p.get("event_type_type"), pa, pb))
        s1, s2 = K.partido_desde(qa, qb, bo, 0, 0, 0, 0, True, 0, 0, (0, 0)), K.partido_desde(qa, qb, bo, 0, 0, 0, 0, False, 0, 0, (0, 0))
        tot_aj = {g: (s1["total"].get(g, 0) + s2["total"].get(g, 0)) / 2 for g in set(s1["total"]) | set(s2["total"])}
        ha = o.get("Home/Away", {})
        h, w = _mediana(ha.get("Home")), _mediana(ha.get("Away"))
        gcasa = Q.sin_margen(h, w) if h and w else None
        ou = o.get("Over/Under by Games in Match", {})
        O, U = ou.get("Over/Under by Games in Match Over", {}), ou.get("Over/Under by Games in Match Under", {})
        lineas = []
        for ln in O:
            if ln in U and ln.endswith(".5"):
                co, cu = _mediana(O[ln]), _mediana(U[ln])
                if co and cu:
                    lineas.append((float(ln), Q.sin_margen(co, cu), co, cu))
        if not lineas:
            continue
        princ = min(lineas, key=lambda z: abs(z[1] - 0.5))[0]
        base = {"hora": f"{ahora:%Y-%m-%d %H:%M}", "event_key": k, "tipo": p.get("event_type_type"),
                "torneo": p.get("tournament_name"), "superficie": sup, "jugador1": p.get("event_first_player"),
                "jugador2": p.get("event_second_player"), "mejor_de": bo, "p_saque1": pa, "p_saque2": pb,
                "gana1_modelo": round(gana, 4), "gana1_casa": None if gcasa is None else round(gcasa, 4),
                "esperado_modelo": round(sum(g * x for g, x in tot.items()), 2)}
        previas[k] = [{**base, "linea": ln, "mas_modelo": round(sum(x for g, x in tot.items() if g > ln), 4),
                       "mas_casa": round(pk, 4), "mas_ajustado": round(sum(x for g, x in tot_aj.items() if g > ln), 4), "cuota_mas": co, "cuota_menos": cu, "principal": int(ln == princ)}
                      for ln, pk, co, cu in sorted(lineas)]
    os.makedirs(PRE, exist_ok=True)
    with open(ruta, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        for filas in previas.values():
            w.writerows(filas)
    print(f"previa: {len(previas)} partidos")
