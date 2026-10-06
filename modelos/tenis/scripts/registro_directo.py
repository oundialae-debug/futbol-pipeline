"""
Pronósticos EN DIRECTO y registro para medirlos (30/09/2026). Cada pasada (GitHub Actions
cada 5 minutos, workflow en main que trabaja sobre la rama de tenis): 2 peticiones a
API-Tennis (marcadores y cuotas en directo) + get_draw para torneos nuevos (superficie).

Para cada partido individual en juego con los dos jugadores conocidos:
- calculadora desde el marcador exacto (sets, juegos, puntos, quién saca;
  markov_tenis.partido_desde) con la fuerza de cada jugador (modelo de puntos, foto en
  data/tenis/estado_puntos_*.json) en la superficie real del torneo;
- cuotas en directo NO suspendidas de: ganador ("To Win"), total de juegos del partido
  ("Total Games in Match", cada línea) y resultado en sets ("Set Betting").

Escribe:
- modelos/tenis/pronosticos/directo_api.md: la tabla de AHORA (se sobrescribe);
- data/tenis/api_tennis/registro/<fecha>.csv: una fila por partido, mercado y línea, con
  prob. del modelo y cuota; el resultado final se cruza después para medir si acierta;
- una vez por hora, los previos de los partidos por empezar (previa_juegos.py) y
  data/tenis/api_tennis/resultados/<fecha>.csv (get_fixtures de hoy y ayer,
  2 peticiones más) y la evaluación en papel de la señal de juegos (evaluar_juegos.py).
"""
import csv
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "modelos/tenis/scripts")
import api_tennis as A  # noqa: E402
import markov_tenis as K  # noqa: E402
import pronosticos_api as Q  # noqa: E402

REG = "data/tenis/api_tennis/registro"
RES = "data/tenis/api_tennis/resultados"
CAMPOS = ["hora", "event_key", "tipo", "torneo", "superficie", "jugador1", "jugador2", "sets", "juegos", "puntos",
          "saca", "mercado", "linea", "seleccion", "cuota", "cuota_rival", "prob_mercado", "prob_modelo",
          "prob_modelo_directo", "p_saque1", "p_saque2", "p_saque1_directo", "p_saque2_directo", "jugados",
          "prob_modelo_ajustado"]
# lo que cada jugador lleva HOY (statistics de la API), para aprender de ello (calibrar_juegos.py)
EST = ["aces", "df", "primer_pct", "saque_gan", "saque_tot", "resto_gan", "resto_tot", "bp_salvados_gan",
       "bp_salvados_tot", "bp_convertidos_gan", "bp_convertidos_tot", "ultimos10"]
CAMPOS += [f"{c}{lado}" for lado in ("1", "2") for c in EST]


def resultados(ahora):
    """Una vez por hora: partidos de hoy y de ayer (UTC) con su estado y juegos totales (2 peticiones
    get_fixtures), para cruzar con el registro (evaluar_juegos.py)."""
    os.makedirs(RES, exist_ok=True)
    hoy = []
    for dia in (ahora - timedelta(days=1), ahora):
        f = f"{dia:%Y-%m-%d}"
        try:
            ps = A.partidos_dia(f)
        except RuntimeError as e:
            print(e)
            continue
        with open(f"{RES}/{f}.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["event_key", "tipo", "torneo", "jugador1", "jugador2", "estado", "sets", "juegos_totales"])
            for p in ps:
                sc = p.get("scores") or []
                try:
                    tot = sum(int(float(s.get("score_first") or 0)) + int(float(s.get("score_second") or 0)) for s in sc)
                except ValueError:
                    tot = ""
                w.writerow([p.get("event_key"), p.get("event_type_type"), p.get("tournament_name"),
                            p.get("event_first_player"), p.get("event_second_player"), p.get("event_status"),
                            p.get("event_final_result"), tot])
        hoy = ps
    import previa_juegos       # pronósticos previos de los que aún no han empezado (1 petición más)
    previa_juegos.registrar(ahora, hoy)


def main():
    ahora = datetime.now(timezone.utc)
    vivos = A.marcadores()
    try:
        vodds = A.cuotas_directo()
    except RuntimeError:
        vodds = {}
    filas, tabla = [], []
    for p in vivos:
        circ = A.circuito(p)
        e = A.estado(p)
        if circ is None or e is None:
            continue
        a, b = Q.jugador(circ, p.get("event_first_player")), Q.jugador(circ, p.get("event_second_player"))
        if a is None or b is None:
            continue
        sup = Q.superficie(circ, p.get("tournament_name"), p.get("tournament_key"))
        pa, pb = K.redondear(Q.prob_saque(circ, a, b, sup)), K.redondear(Q.prob_saque(circ, b, a, sup))
        r = K.partido_desde(pa, pb, e["mejor_de"], e["sa"], e["sb"], e["ga"], e["gb"], e["a_saca"], e["xa"], e["xb"],
                            e["previos"])
        # versión "directo": la prob. al saque se mezcla con lo que cada uno lleva hoy (se guardan las dos
        # y la evaluación dirá cuál acierta más)
        st = A.estadisticas(p)
        pa2 = K.redondear(Q.saque_directo(pa, st["1"].get("saque_gan", 0), st["1"].get("saque_tot", 0)))
        pb2 = K.redondear(Q.saque_directo(pb, st["2"].get("saque_gan", 0), st["2"].get("saque_tot", 0)))
        r2 = r if (pa2, pb2) == (pa, pb) else K.partido_desde(pa2, pb2, e["mejor_de"], e["sa"], e["sb"], e["ga"], e["gb"],
                                                             e["a_saca"], e["xa"], e["xb"], e["previos"])
        pa3, pb3 = (K.redondear(x) for x in Q.ajuste_juegos(p.get("event_type_type"), pa, pb))
        r3 = K.partido_desde(pa3, pb3, e["mejor_de"], e["sa"], e["sb"], e["ga"], e["gb"], e["a_saca"], e["xa"], e["xb"],
                             e["previos"])
        ev = vodds.get(str(p.get("event_key")), {}) if isinstance(vodds, dict) else {}
        mk = Q.mercados_directo(ev.get("live_odds"))
        base = {"hora": ahora.strftime("%Y-%m-%d %H:%M"), "event_key": p.get("event_key"),
                "tipo": p.get("event_type_type"), "torneo": p.get("tournament_name"), "superficie": sup,
                "jugador1": p.get("event_first_player"), "jugador2": p.get("event_second_player"),
                "sets": f"{e['sa']}-{e['sb']}", "juegos": f"{e['ga']}-{e['gb']}", "puntos": p.get("event_game_result"),
                "saca": {True: 1, False: 2}.get(e["a_saca"], ""),
                "p_saque1": pa, "p_saque2": pb, "p_saque1_directo": pa2, "p_saque2_directo": pb2,
                "jugados": sum(e["previos"]) + e["ga"] + e["gb"],
                **{f"{c}{lado}": st[lado].get(c, "") for lado in ("1", "2") for c in EST}}
        gan = tot = None
        mejor_tot = None
        for (n, h), tipos in mk.items():
            if n == "To Win" and len(tipos) == 2:
                v = [tipos.get("Home", tipos.get("1")), tipos.get("Away", tipos.get("2"))]
                if None in v:
                    v = list(tipos.values())
                gan = Q.sin_margen(v[0], v[1])
                filas.append({**base, "mercado": "ganador", "linea": "", "seleccion": "jugador1", "cuota": v[0],
                              "cuota_rival": v[1], "prob_mercado": gan, "prob_modelo": r["gana_A"],
                              "prob_modelo_directo": r2["gana_A"]})
            elif n == "Total Games in Match" and "Over" in tipos and "Under" in tipos:
                linea = float(h)
                pm = sum(x for k, x in r["total"].items() if k > linea)
                pk = Q.sin_margen(tipos["Over"], tipos["Under"])
                filas.append({**base, "mercado": "total_juegos", "linea": linea, "seleccion": "mas",
                              "cuota": tipos["Over"], "cuota_rival": tipos["Under"], "prob_mercado": pk,
                              "prob_modelo": pm,
                              "prob_modelo_directo": sum(x for k, x in r2["total"].items() if k > linea),
                              "prob_modelo_ajustado": sum(x for k, x in r3["total"].items() if k > linea)})
                if pk is not None and (mejor_tot is None or abs(pk - 0.5) < abs(mejor_tot[1] - 0.5)):
                    mejor_tot = (linea, pk, pm)
            elif n == "Set Betting" and tipos:
                inv = {k: 1 / float(x) for k, x in tipos.items() if x and float(x) > 1}
                s = sum(inv.values())
                for k, x in tipos.items():
                    kk = k.replace("-", ":")
                    if ":" not in kk or k not in inv:
                        continue
                    ab = tuple(int(y) for y in kk.split(":"))
                    filas.append({**base, "mercado": "sets", "linea": kk, "seleccion": kk, "cuota": x,
                                  "cuota_rival": "", "prob_mercado": inv[k] / s, "prob_modelo": r["sets"].get(ab, 0),
                                  "prob_modelo_directo": r2["sets"].get(ab, 0)})
        sets = sorted(r["sets"].items(), key=lambda kv: -kv[1])[:2]
        tabla.append((p, e, sup, r, gan, mejor_tot, sets))
    # registro
    os.makedirs(REG, exist_ok=True)
    ruta = f"{REG}/{ahora:%Y-%m-%d}.csv"
    if os.path.exists(ruta) and open(ruta).readline().strip().split(",") != CAMPOS:
        ruta = f"{REG}/{ahora:%Y-%m-%d}_v3.csv"         # columnas nuevas: fichero aparte ese día
    nuevo = not os.path.exists(ruta)
    with open(ruta, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerows(filas)
    # tabla de ahora
    lin = [f"# Tenis en directo, {ahora:%d/%m/%Y %H:%M} UTC ({(ahora.hour + 2) % 24:02d}:{ahora:%M} en España)\n",
           "Calculadora desde el marcador exacto (modelo de puntos, superficie real) frente a la cuota en directo",
           "(sin margen). Ganador y sets: la calculadora suele coincidir con la casa. Total de juegos: el modelo",
           "SOBREESTIMA los juegos (sesgo visto en Kalshi y en directo): no fiarse del 'más de' del modelo.",
           "Se actualiza cada ~5 min; el registro en data/tenis/api_tennis/registro/ servirá para medir si acierta.\n",
           "| partido | tipo | superficie | marcador (sets, juegos, puntos, saca) | gana 1º: modelo / cuota | "
           "sets más probables (modelo) | total juegos: línea, modelo / cuota |", "|---|---|---|---|---|---|---|"]
    for p, e, sup, r, gan, mt, sets in sorted(tabla, key=lambda z: str(z[0].get("event_type_type"))):
        saca = {True: p.get("event_first_player"), False: p.get("event_second_player")}.get(e["a_saca"], "?")
        g = f"{r['gana_A']:.0%} / {'' if gan is None else f'{gan:.0%}'}"
        t = "" if mt is None else f"{mt[0]}: {mt[2]:.0%} / {mt[1]:.0%}"
        lin.append(f"| {p.get('event_first_player')} vs {p.get('event_second_player')} | {p.get('event_type_type')} | "
                   f"{sup} | {e['sa']}-{e['sb']}, {e['ga']}-{e['gb']}, {p.get('event_game_result')}, saca {saca} | {g} | "
                   f"{', '.join(f'{x}-{y} {v:.0%}' for (x, y), v in sets)} | {t} |")
    os.makedirs("modelos/tenis/pronosticos", exist_ok=True)
    open("modelos/tenis/pronosticos/directo_api.md", "w").write("\n".join(lin) + "\n")
    import json
    json.dump(Q.SUP_API, open(Q.CACHE_SUP, "w"), indent=0, sort_keys=True)
    print(f"{len(tabla)} partidos, {len(filas)} filas de registro")
    if ahora.minute < 5 or not os.path.exists(f"{RES}/{ahora:%Y-%m-%d}.csv"):
        resultados(ahora)
        import evaluar_juegos
        evaluar_juegos.main()


if __name__ == "__main__":
    main()
