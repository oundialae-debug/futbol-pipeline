"""
Vigilante de más/menos juegos en directo con aviso al móvil (30/09/2026). Lo corre GitHub Actions
(vigilante_tenis.yml en main): cada 2 minutos, durante casi 6 horas, 2 peticiones a API-Tennis
(marcadores y cuotas en directo). No gasta créditos de Claude. Desde el 30/09 cada minuto
(CADA=60), a petición del usuario.

Regla (pedida por el usuario): en la línea principal de cada partido (la más cercana al 50% según
la casa), el modelo Y la casa (sin margen) dan más del 54% al mismo lado (más o menos), durante
2 pasadas seguidas (~1-2 min) para no avisar por un vaivén puntual, y la casa no
pasa del 75%, salvo que la cuota real de la API para ese lado pague 1,33 o más. Un aviso por partido y lado.
Aviso por ntfy (topic en NTFY_TOPIC):
  Jugador VS Jugador | más/menos de X juegos | modelo 57% / cuota 55% | mínima 1,82 | torneo
"mínima" = 1 / prob. de la casa: apostar solo si Luckia paga eso o más.
"""
import os
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, "modelos/tenis/scripts")
import api_tennis as A  # noqa: E402
import juegos_directo as J  # noqa: E402
import markov_tenis as K  # noqa: E402
import pronosticos_api as Q  # noqa: E402

UMBRAL, PASADAS = 0.54, 2
TECHO, CUOTA_BUENA = 0.75, 1.33   # por encima del 75% solo se avisa si la cuota REAL de la API paga 1,33 o más
CADA = float(os.environ.get("CADA", 60))   # segundos entre pasadas
MINUTOS = float(os.environ.get("MINUTOS", 345))
TOPIC = os.environ.get("NTFY_TOPIC", "tenis-f059172b4dc7")


def avisar(txt, jugadores=()):
    """Luckia no tiene dirección por partido que se pueda montar (lleva un número interno suyo):
    el título son los apellidos y hay un botón para COPIAR cada uno (acción "copy" de ntfy, en la
    app de Android) y pegarlo en el buscador de Luckia. Se publica en JSON para que los acentos
    y letras raras de los nombres no se rompan en las cabeceras."""
    print(txt, flush=True)
    ap = [apellido(j) for j in jugadores]
    acciones = [{"action": "copy", "label": f"Copiar {a}", "value": a} for a in ap]
    acciones.append({"action": "view", "label": "Abrir Luckia", "url": J.LUCKIA})
    try:
        requests.post("https://ntfy.sh/", timeout=15, json={
            "topic": TOPIC, "title": " - ".join(ap) or "Tenis: juegos", "message": txt, "priority": 4,
            "click": J.LUCKIA, "actions": acciones[:3]})
    except requests.RequestException as e:
        print(f"ntfy falló: {type(e).__name__}", flush=True)


TOTALES, CASA = {}, {}   # por partido, de la última pasada: reparto de juegos del modelo y líneas de la casa


def escalera(k, linea, lado):
    """Otras líneas cercanas: la casa mueve la línea en cuanto se juega un juego, y cuando el usuario
    llega a Luckia puede estar ya en otra. Para cada una, prob. del modelo / de la casa (si la API
    la da) y cuota mínima; sin precio de la casa, la mínima sale del modelo (menos fiable en el más)."""
    tot, casa, out = TOTALES.get(k, {}), CASA.get(k, {}), []
    for d in (-2, -1, 1, 2):
        ln = linea + d
        mo = sum(x for g, x in tot.items() if g > ln)
        mo = mo if lado == "más" else 1 - mo
        pc = casa.get(ln)
        pc = None if pc is None else (pc if lado == "más" else 1 - pc)
        ref = pc if pc else mo
        if not 0.01 < ref < 0.99:
            continue
        txt = f"{ln:g}: {mo:.0%}" + (f"/{pc:.0%}" if pc else "") + f" mín {1 / ref:.2f}"
        out.append(txt.replace(".", ","))
    return " · ".join(out)


def apellido(n):
    return str(n).split(". ", 1)[-1]


def lineas():
    vivos = A.marcadores()
    try:
        vodds = A.cuotas_directo()
    except RuntimeError:
        vodds = {}
    filas = []
    for p in vivos:
        circ, e = A.circuito(p), A.estado(p)
        if circ is None or e is None:
            continue
        a, b = Q.jugador(circ, p.get("event_first_player")), Q.jugador(circ, p.get("event_second_player"))
        if a is None or b is None:
            continue
        ev = vodds.get(str(p.get("event_key")), {}) if isinstance(vodds, dict) else {}
        mk = {k: t for k, t in Q.mercados_directo(ev.get("live_odds")).items()
              if k[0] == "Total Games in Match" and "Over" in t and "Under" in t}
        if not mk:
            continue
        sup = Q.superficie(circ, p.get("tournament_name"), p.get("tournament_key"))
        pa, pb = K.redondear(Q.prob_saque(circ, a, b, sup)), K.redondear(Q.prob_saque(circ, b, a, sup))
        r = K.partido_desde(pa, pb, e["mejor_de"], e["sa"], e["sb"], e["ga"], e["gb"], e["a_saca"], e["xa"], e["xb"],
                            e["previos"])
        TOTALES[p.get("event_key")] = r["total"]
        CASA[p.get("event_key")] = {float(h): Q.sin_margen(t["Over"], t["Under"]) for (_, h), t in mk.items()}
        for (_, h), t in mk.items():
            ln = float(h)
            filas.append({"hora": "", "event_key": p.get("event_key"), "tipo": p.get("event_type_type"),
                          "torneo": p.get("tournament_name"), "jugador1": p.get("event_first_player"),
                          "jugador2": p.get("event_second_player"), "mercado": "total_juegos", "linea": ln,
                          "cuota": t["Over"], "cuota_rival": t["Under"],
                          "prob_mercado": Q.sin_margen(t["Over"], t["Under"]),
                          "prob_modelo": sum(x for k, x in r["total"].items() if k > ln)})
    return J.principales(pd.DataFrame(filas)) if filas else pd.DataFrame()


def main():
    fin = time.time() + MINUTOS * 60
    racha, avisados, fallos = {}, set(), 0
    while time.time() < fin:
        t0 = time.time()
        try:
            pr = lineas()
            vistos = set()
            for _, x in pr.iterrows():
                pm, mo = float(x.prob_mercado), float(x.prob_modelo)
                lado = ("más" if pm > UMBRAL and mo > UMBRAL else
                        "menos" if 1 - pm > UMBRAL and 1 - mo > UMBRAL else None)
                k = x.event_key
                vistos.add(k)
                n = racha[k][1] + 1 if lado and racha.get(k, (None, 0))[0] == lado else (1 if lado else 0)
                racha[k] = (lado, n)
                pmod, pcas = (mo, pm) if lado == "más" else (1 - mo, 1 - pm)
                real = float(x.cuota if lado == "más" else x.cuota_rival)
                if lado and n >= PASADAS and (pcas <= TECHO or real >= CUOTA_BUENA) and (k, lado) not in avisados:
                    avisados.add((k, lado))
                    ln, mn = f"{x.linea:g}".replace(".", ","), f"{1 / pcas:.2f}".replace(".", ",")
                    avisar(f"{x.jugador1} VS {x.jugador2} | {lado} de {ln} juegos | modelo {pmod:.0%} / cuota {pcas:.0%} | "
                           f"mínima {mn} | {J.torneo(x.tipo, x.torneo)}\n"
                           f"Si la línea ya cambió ({lado}, modelo/casa): {escalera(k, float(x.linea), lado)}",
                           (x.jugador1, x.jugador2))
            for k in set(racha) - vistos:
                racha.pop(k)
            fallos = 0
        except Exception as ex:  # una pasada fallida no para el vigilante
            fallos += 1
            print(f"pasada fallida: {type(ex).__name__}: {str(ex)[:150]}", flush=True)
            if fallos == 5:
                avisar("Vigilante de tenis: 5 fallos seguidos leyendo la API (¿clave caducada?)")
        time.sleep(max(5, CADA - (time.time() - t0)))


if __name__ == "__main__":
    main()
