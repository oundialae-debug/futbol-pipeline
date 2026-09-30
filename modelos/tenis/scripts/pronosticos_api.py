"""
Pronósticos con API-Tennis (30/09/2026). Corre en GitHub Actions (la clave está en el
secreto API_TENNIS_KEY). 4 peticiones: partidos del día, cuotas del día, marcadores en
directo y cuotas en directo.

- Fuerza de cada jugador: foto del modelo de puntos (data/tenis/estado_puntos_*.json,
  estado_jugadores.py), con la incertidumbre que crece desde su último partido.
- Antes del partido: la mejor predicción del ganador es la CUOTA (mediana de casas, sin
  margen); el modelo de puntos da además sets y total de juegos.
- En juego: calculadora desde el marcador (markov_tenis.partido_desde) comparada con las
  cuotas en directo de los mercados reconocidos.
- Superficie: campo tournament_surface de get_draw (una petición por torneo nuevo, guardada
  en data/tenis/api_tennis/superficies.json); si no viene, la última edición del torneo en el
  historial; si tampoco, pista dura. Dobles: fuera.
Escribe modelos/tenis/pronosticos/api_<fecha-hora>.md.
"""
import json
import math
import statistics
import sys
from datetime import datetime, timezone

sys.path.insert(0, "modelos/tenis/scripts")
import api_tennis as A  # noqa: E402
import elo_tenis as E  # noqa: E402
import markov_tenis as K  # noqa: E402

ESTADO = {c: json.load(open(f"data/tenis/estado_puntos_{c}.json")) for c in ("atp", "wta")}
HOY = datetime.now(timezone.utc)
DIA = (HOY - datetime(1970, 1, 1, tzinfo=timezone.utc)).days


def jugador(circ, abreviado):
    """'P. Berezina' -> estado del jugador (el más reciente si hay varios con apellido e inicial)."""
    partes = str(abreviado).replace(".", ". ").split()
    if len(partes) < 2:
        return None
    clave = E.norm(partes[-1]) + "|" + E.norm(partes[0])[:1]
    cands = [ESTADO[circ]["jugadores"][k] for k in ESTADO[circ]["indice"].get(clave, [])
             if k in ESTADO[circ]["jugadores"]]
    return max(cands, key=lambda j: j["dia"]) if cands else None


def prob_saque(circ, a, b, sup="Hard"):
    """Prob. de que a gane un punto sacando contra b (con la incertidumbre del modelo)."""
    v0, tau, v0s = ESTADO[circ]["params"]
    mu = ESTADO[circ]["mu"].get(sup, 0.6)
    def comp(j):
        dt = max(0, DIA - j["dia"])
        s = j["sup"].get(sup, {"s": 0.0, "vs": v0s, "r": 0.0, "vr": v0s, "dia": j["dia"]})
        dts = max(0, DIA - s["dia"])
        return (j["s"], min(v0, j["vs"] + tau * dt), j["r"], min(v0, j["vr"] + tau * dt),
                s["s"], min(v0s, s["vs"] + tau * dts), s["r"], min(v0s, s["vr"] + tau * dts))
    ca, cb = comp(a), comp(b)
    th = mu + ca[0] + ca[4] - cb[2] - cb[6]
    V = ca[1] + ca[5] + cb[3] + cb[7]
    return 1 / (1 + math.exp(-th / math.sqrt(1 + math.pi * V / 8)))


CACHE_SUP = "data/tenis/api_tennis/superficies.json"
try:
    SUP_API = json.load(open(CACHE_SUP))
except (FileNotFoundError, ValueError):
    SUP_API = {}


def superficie(circ, torneo, tournament_key=None):
    """1) tournament_surface de get_draw (API-Tennis), guardado en CACHE_SUP; 2) última edición del
    torneo en el historial; 3) pista dura."""
    import re
    if tournament_key is not None:
        k = str(tournament_key)
        if k not in SUP_API:
            SUP_API[k] = A.superficie_torneo(k)           # una petición por torneo nuevo
        s = SUP_API.get(k)
        if s:
            s = str(s).strip().lower()            # "Hard (Indoor)", "Clay", "Grass", "Carpet"...
            for pref, sup in (("hard", "Hard"), ("clay", "Clay"), ("grass", "Grass"), ("carpet", "Hard"),
                              ("indoor", "Hard")):
                if s.startswith(pref):
                    return sup
    base = E.norm(re.sub(r"\s+\d+$", "", str(torneo).strip()))
    return ESTADO[circ].get("superficies", {}).get(base, "Hard")


def fuerzas(p):
    circ = A.circuito(p)
    if circ is None:
        return None
    a, b = jugador(circ, p.get("event_first_player")), jugador(circ, p.get("event_second_player"))
    if a is None or b is None:
        return circ, None, None, (a is not None, b is not None)
    s = superficie(circ, p.get("tournament_name"), p.get("tournament_key"))
    return circ, K.redondear(prob_saque(circ, a, b, s)), K.redondear(prob_saque(circ, b, a, s)), (True, True)


def sin_margen(o1, o2):
    try:
        i1, i2 = 1 / float(o1), 1 / float(o2)
        return i1 / (i1 + i2)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def cuota_ganador_previa(cuotas, key):
    """Mediana de casas en 'Home/Away' -> prob. sin margen del primer jugador."""
    ev = cuotas.get(str(key)) if isinstance(cuotas, dict) else None
    if not ev:
        return None, 0
    ha = ev.get("Home/Away") or {}
    casa, fuera = ha.get("Home") or {}, ha.get("Away") or {}
    comunes = [c for c in casa if c in fuera]
    ps = [sin_margen(casa[c], fuera[c]) for c in comunes]
    ps = [x for x in ps if x]
    return (statistics.median(ps), len(ps)) if ps else (None, 0)


def mercados_directo(odds):
    """Agrupa las cuotas en directo NO suspendidas: {(nombre, línea): {tipo: cuota}}."""
    g = {}
    for o in odds or []:
        if str(o.get("suspended", "")).lower() == "yes":
            continue
        g.setdefault((o.get("odd_name"), o.get("handicap")), {})[o.get("type")] = o.get("value")
    return g


def main():
    fecha = HOY.strftime("%Y-%m-%d")
    lin = [f"# Pronósticos con API-Tennis, {HOY:%d/%m/%Y %H:%M} UTC\n",
           "Ganador: la mejor predicción es la cuota (mediana de casas sin margen). Sets y juegos: modelo de",
           "puntos. En juego: calculadora desde el marcador contra la cuota en directo. En las pruebas, el modelo",
           "acertó MENOS que la cuota antes del partido: las diferencias son para vigilar, no para apostar a ciegas.\n"]
    fijos = A.partidos_dia(fecha)
    try:
        cuotas = A.cuotas_dia(fecha)
    except RuntimeError as e:
        cuotas, lin = {}, lin + [f"(cuotas del día no disponibles: {e})\n"]
    vivos = A.marcadores()
    try:
        vodds = A.cuotas_directo()
    except RuntimeError:
        vodds = {}
    nombres_mercado = set()
    # ---- en juego
    lin += ["## En juego\n", "| partido | tipo | marcador | modelo: gana 1º | cuota en directo: gana 1º | modelo: más de X juegos "
            "(cuota) | sets más probables |", "|---|---|---|---|---|---|---|"]
    for p in vivos:
        f = fuerzas(p)
        e = A.estado(p)
        if f is None or e is None or f[1] is None:
            continue
        circ, pa, pb, _ = f
        r = K.partido_desde(pa, pb, e["mejor_de"], e["sa"], e["sb"], e["ga"], e["gb"], e["a_saca"], e["xa"], e["xb"],
                            e["previos"])
        ev = vodds.get(str(p.get("event_key")), {}) if isinstance(vodds, dict) else {}
        mk = mercados_directo(ev.get("live_odds"))
        nombres_mercado |= {k[0] for k in mk}
        # nombres reales de API-Tennis (prueba del 30/09/2026): "To Win", "Total Games in Match", "Set Betting"
        gan = None
        for (n, h), tipos in mk.items():
            if n in ("To Win", "Home/Away") and len(tipos) == 2:
                v = [tipos.get("Home", tipos.get("1")), tipos.get("Away", tipos.get("2"))]
                if None in v:
                    v = list(tipos.values())
                gan = sin_margen(v[0], v[1])
        tot = []
        for (n, h), tipos in mk.items():
            if n in ("Total Games in Match", "Total Games") and "Over" in tipos and "Under" in tipos:
                linea = float(h)
                pm = sum(v for k, v in r["total"].items() if k > linea)
                tot.append(f"{linea}: {pm:.0%} ({sin_margen(tipos['Over'], tipos['Under']):.0%})")
        sets = sorted(r["sets"].items(), key=lambda kv: -kv[1])[:2]
        for (n, h), tipos in mk.items():
            if n == "Set Betting" and tipos:
                inv = {k: 1 / float(v) for k, v in tipos.items() if v and float(v) > 1}
                s = sum(inv.values())
                sets = [(tuple(int(x) for x in k.replace("-", ":").split(":")), v / s) for k, v in inv.items()
                        if ":" in k.replace("-", ":")]
                sets = sorted(((ab, r["sets"].get(ab, 0), pc) for ab, pc in sets), key=lambda z: -z[1])[:2]
                sets = [((a, b), f"{pm:.0%} (cuota {pc:.0%})") for (a, b), pm, pc in sets]
                break
        marc = f"{e['sa']}-{e['sb']}, {e['ga']}-{e['gb']}, {p.get('event_game_result')}"
        lin.append(f"| {p.get('event_first_player')} vs {p.get('event_second_player')} | {p.get('event_type_type')} | {marc} | "
                   f"{r['gana_A']:.0%} | {'' if gan is None else f'{gan:.0%}'} | {'; '.join(tot[:3])} | "
                   f"{', '.join(f'{a}-{b} ' + (v if isinstance(v, str) else f'{v:.0%}') for (a, b), v in sets)} |")
    # ---- próximos
    lin += ["\n## Próximos de hoy\n", "| hora (Berlín) | torneo | partido | **pronóstico** | prob. | fuente | modelo: gana 1º | "
            "modelo: juegos esperados | modelo: más de 21,5 |", "|---|---|---|---|---|---|---|---|---|"]
    for p in sorted(fijos, key=lambda x: str(x.get("event_time"))):
        if str(p.get("event_live")) == "1" or p.get("event_winner") or str(p.get("event_status", "")).strip():
            continue
        f = fuerzas(p)
        if f is None:
            continue
        circ, pa, pb, conocidos = f
        pm = pmod = None
        mo = tm = m21 = ""
        if pa is not None:
            g, tot, dif = K.partido(pa, pb, A.mejor_de(p))
            pmod = g
            mo = f"{g:.0%}"
            tm = f"{sum(k * v for k, v in tot.items()):.1f}"
            m21 = f"{sum(v for k, v in tot.items() if k > 21.5):.0%}"
        pm, ncasas = cuota_ganador_previa(cuotas, p.get("event_key"))
        base, fuente = (pm, f"cuota ({ncasas} casas)") if pm is not None else (pmod, "modelo")
        if base is None:
            continue
        uno, dos = p.get("event_first_player"), p.get("event_second_player")
        pron, prob = (uno, base) if base >= 0.5 else (dos, 1 - base)
        lin.append(f"| {p.get('event_time')} | {p.get('tournament_name')} | {uno} vs {dos} | **{pron}** | {prob:.0%} | {fuente} | "
                   f"{mo} | {tm} | {m21} |")
    lin.append(f"\nMercados en directo vistos: {sorted(x for x in nombres_mercado if x)}")
    import os
    os.makedirs(os.path.dirname(CACHE_SUP), exist_ok=True)
    json.dump(SUP_API, open(CACHE_SUP, "w"), indent=0, sort_keys=True)
    vistas = {}
    for v in SUP_API.values():
        vistas[str(v)] = vistas.get(str(v), 0) + 1
    lin.append(f"Superficies de API-Tennis (get_draw) conocidas: {vistas}")
    salida = f"modelos/tenis/pronosticos/api_{HOY:%Y-%m-%d_%H%M}.md"
    open(salida, "w").write("\n".join(lin) + "\n")
    print("\n".join(lin[:40]))


if __name__ == "__main__":
    main()
