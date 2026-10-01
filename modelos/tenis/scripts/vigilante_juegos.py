"""
Vigilante de más/menos juegos en directo con aviso al móvil (30/09/2026). Lo corre GitHub Actions
(vigilante_tenis.yml en main): cada 2 minutos, durante casi 6 horas, 2 peticiones a API-Tennis
(marcadores y cuotas en directo). No gasta créditos de Claude. Desde el 30/09 cada minuto
(CADA=60), a petición del usuario.

Regla (pedida por el usuario): en la línea principal de cada partido (la más cercana al 50% según
la casa), el modelo Y la casa (sin margen) dan más del 54% al MENOS (el más se quitó el 30/09), durante
2 pasadas seguidas (~1-2 min) para no avisar por un vaivén puntual, y la casa no
pasa del 75%, salvo que la cuota real de la API para ese lado pague 1,33 o más. Un aviso por partido y lado.
Aviso por ntfy (topic en NTFY_TOPIC):
  Jugador VS Jugador | más/menos de X juegos | modelo 57% / cuota 55% | mínima 1,82 | torneo
"mínima" = 1 / prob. de la casa: apostar solo si la casa (Stake) paga eso o más.
"""
import os
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, "modelos/tenis/scripts")
import api_tennis as A  # noqa: E402
import calibrar_juegos as C  # noqa: E402
import juegos_directo as J  # noqa: E402
import markov_tenis as K  # noqa: E402
import pronosticos_api as Q  # noqa: E402
import stake  # noqa: E402

UMBRAL, PASADAS = 0.54, 2
TECHO, CUOTA_BUENA = 0.75, 1.33   # por encima del 75% solo se avisa si la cuota REAL de la API paga 1,33 o más
CADA = float(os.environ.get("CADA", 60))   # segundos entre pasadas
MINUTOS = float(os.environ.get("MINUTOS", 345))
TOPIC = os.environ.get("NTFY_TOPIC", "tenis-f059172b4dc7")
# 01/10, usuario: SOLO PAPEL. Con 112 avisos el "menos" acertaba lo mismo que ya decía la casa (−3%).
# No se manda nada al móvil (salvo fallos); se registran tres reglas fijadas hoy para medirlas:
#   actual     - la de hasta ahora: casa Y aprendido > 54% al menos (con el tope del 75%)
#   casa65     - la casa da al menos >= 65% (sale de mirar los 112 avisos: hay que probarla en partidos NUEVOS)
#   aprendida  - lo aprendido (calibrar_juegos) se separa de la casa >= 5 puntos, a cualquier lado
AVISAR = os.environ.get("AVISAR", "0") == "1"


def avisar(txt, jugadores=(), url=stake.BASE, forzar=False):
    """Ni Luckia ni Stake tienen dirección por partido que se pueda montar (llevan un número interno):
    el título son los apellidos, hay un botón para COPIAR cada uno (acción "copy" de ntfy, en la
    app de Android) y otro que abre la página del TORNEO en Stake (stake.py; el usuario cambió
    de Luckia a Stake el 30/09). Se publica en JSON para que los acentos
    y letras raras de los nombres no se rompan en las cabeceras."""
    print(txt, flush=True)
    if not (AVISAR or forzar):
        return
    ap = [apellido(j) for j in jugadores]
    acciones = [{"action": "copy", "label": f"Copiar {a}", "value": a} for a in ap]
    acciones.append({"action": "view", "label": "Abrir en Stake", "url": url})
    try:
        requests.post("https://ntfy.sh/", timeout=15, json={
            "topic": TOPIC, "title": " - ".join(ap) or "Tenis: juegos", "message": txt, "priority": 4,
            "click": url, "actions": acciones[:3]})
    except requests.RequestException as e:
        print(f"ntfy falló: {type(e).__name__}", flush=True)


CAL = C.cargar()   # recalibración aprendida de lo recogido (se relee al arrancar cada ejecución)
TOTALES, CASA = {}, {}   # por partido, de la última pasada: reparto de juegos del modelo y líneas de la casa


def escalera(k, linea, lado):
    """Otras líneas cercanas: la casa mueve la línea en cuanto se juega un juego, y cuando el usuario
    llega a Luckia puede estar ya en otra. Para cada una, prob. del modelo / de la casa (si la API
    la da) y cuota mínima; sin precio de la casa, la mínima sale del modelo (menos fiable en el más)."""
    (tot, tot2), casa, out = TOTALES.get(k, ({}, {})), CASA.get(k, {}), []
    for d in (-2, -1, 1, 2):
        ln = linea + d
        pc = casa.get(ln)
        mo = sum(x for g, x in tot.items() if g > ln)
        mo = mo if lado == "más" else 1 - mo
        pc = None if pc is None else (pc if lado == "más" else 1 - pc)
        ref = pc if pc else mo
        if not 0.01 < ref < 0.99:
            continue
        txt = f"{ln:g}: {mo:.0%}" + (f"/{pc:.0%}" if pc else "") + f" mín {1 / ref:.2f}"
        out.append(txt.replace(".", ","))
    return " · ".join(out)


AVISOS = "data/tenis/api_tennis/avisos"


def guardar(x, lado, pmod, pcas, real, regla):
    """Cada aviso queda en data/tenis/api_tennis/avisos/<fecha>.csv (y se sube a la rama) para
    evaluarlo en papel con el resultado final (evaluar_juegos.py)."""
    import csv
    import subprocess
    from datetime import datetime, timezone
    ahora = datetime.now(timezone.utc)
    os.makedirs(AVISOS, exist_ok=True)
    ruta = f"{AVISOS}/{ahora:%Y-%m-%d}_papel.csv"     # desde el 01/10: con la columna "regla"
    nuevo = not os.path.exists(ruta)
    with open(ruta, "a", newline="") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(["hora", "event_key", "tipo", "torneo", "jugador1", "jugador2", "lado", "linea",
                        "prob_modelo", "prob_casa", "cuota_api", "calibrado", "regla"])
        w.writerow([f"{ahora:%Y-%m-%d %H:%M}", x.event_key, x.tipo, x.torneo, x.jugador1, x.jugador2, lado,
                    x.linea, round(pmod, 4), round(pcas, 4), real, bool(CAL.get("coef")), regla])
    if os.environ.get("GITHUB_ACTIONS"):
        orden = (f'git add {AVISOS} && git commit -q -m "Tenis aviso ({ahora:%Y-%m-%dT%H:%M})" && '
                 'for i in 1 2 3 4 5; do git pull -q --rebase origin ccr-3c3cfe57-etcioo && '
                 'git push -q origin HEAD:ccr-3c3cfe57-etcioo && exit 0; sleep 5; done; exit 1')
        subprocess.run(orden, shell=True, timeout=120)


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
        st = A.estadisticas(p)
        pa2 = K.redondear(Q.saque_directo(pa, st["1"].get("saque_gan", 0), st["1"].get("saque_tot", 0)))
        pb2 = K.redondear(Q.saque_directo(pb, st["2"].get("saque_gan", 0), st["2"].get("saque_tot", 0)))
        r2 = r if (pa2, pb2) == (pa, pb) else K.partido_desde(pa2, pb2, e["mejor_de"], e["sa"], e["sb"], e["ga"], e["gb"],
                                                             e["a_saca"], e["xa"], e["xb"], e["previos"])
        TOTALES[p.get("event_key")] = (r["total"], r2["total"])
        CASA[p.get("event_key")] = {float(h): Q.sin_margen(t["Over"], t["Under"]) for (_, h), t in mk.items()}
        for (_, h), t in mk.items():
            ln = float(h)
            filas.append({"hora": "", "event_key": p.get("event_key"), "tipo": p.get("event_type_type"),
                          "torneo": p.get("tournament_name"), "jugador1": p.get("event_first_player"),
                          "jugador2": p.get("event_second_player"), "mercado": "total_juegos", "linea": ln,
                          "cuota": t["Over"], "cuota_rival": t["Under"],
                          "prob_mercado": Q.sin_margen(t["Over"], t["Under"]),
                          "prob_modelo": sum(x for k, x in r["total"].items() if k > ln),
                          "prob_modelo_directo": sum(x for k, x in r2["total"].items() if k > ln),
                          "jugados": sum(e["previos"]) + e["ga"] + e["gb"]})
    if not filas:
        return pd.DataFrame()
    pr = J.principales(pd.DataFrame(filas))
    pr["p_aprendida"] = [C.aplicar(CAL, f) for f in pr.to_dict("records")]
    return pr


def reglas(x):
    """{regla: (lado, p_regla, p_casa, cuota_real)} de las reglas que se cumplen en esta línea."""
    pm, pa = float(x.prob_mercado), float(x.p_aprendida)
    out = {}
    if 1 - pm > UMBRAL and 1 - pa > UMBRAL:
        real = float(x.cuota_rival)
        if 1 - pm <= TECHO or real >= CUOTA_BUENA:
            out["actual"] = ("menos", 1 - pa, 1 - pm, real)
    if 1 - pm >= 0.65:
        out["casa65"] = ("menos", 1 - pm, 1 - pm, float(x.cuota_rival))
    if abs(pa - pm) >= C.UMBRAL:
        mas = pa > pm
        out["aprendida"] = ("más" if mas else "menos", pa if mas else 1 - pa, pm if mas else 1 - pm,
                            float(x.cuota if mas else x.cuota_rival))
    return out


def main():
    fin = time.time() + MINUTOS * 60
    racha, hechos, fallos = {}, set(), 0
    while time.time() < fin:
        t0 = time.time()
        try:
            pr = lineas()
            vistos = set()
            for _, x in pr.iterrows():
                k = x.event_key
                rg = reglas(x)
                for nombre in ("actual", "casa65", "aprendida"):
                    clave = (k, nombre)
                    vistos.add(clave)
                    lado = rg[nombre][0] if nombre in rg else None
                    n = racha[clave][1] + 1 if lado and racha.get(clave, (None, 0))[0] == lado else (1 if lado else 0)
                    racha[clave] = (lado, n)
                    if lado and n >= PASADAS and (k, nombre, lado) not in hechos:
                        hechos.add((k, nombre, lado))
                        _, preg, pcas, real = rg[nombre]
                        guardar(x, lado, preg, pcas, real, nombre)
                        ln, mn = f"{x.linea:g}".replace(".", ","), f"{1 / pcas:.2f}".replace(".", ",")
                        avisar(f"[{nombre}] {x.jugador1} VS {x.jugador2} | {lado} de {ln} juegos | modelo {preg:.0%} / "
                               f"cuota {pcas:.0%} | mínima {mn} | {J.torneo(x.tipo, x.torneo)}",
                               (x.jugador1, x.jugador2), stake.enlace(x.tipo, x.torneo))
            for c in set(racha) - vistos:
                racha.pop(c)
            fallos = 0
        except Exception as ex:  # una pasada fallida no para el vigilante
            fallos += 1
            print(f"pasada fallida: {type(ex).__name__}: {str(ex)[:150]}", flush=True)
            if fallos == 5:
                avisar("Vigilante de tenis: 5 fallos seguidos leyendo la API (¿clave caducada?)", forzar=True)
        time.sleep(max(5, CADA - (time.time() - t0)))


if __name__ == "__main__":
    main()
