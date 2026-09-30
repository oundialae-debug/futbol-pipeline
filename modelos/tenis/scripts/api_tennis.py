"""
Conector de API-Tennis (api-tennis.com), cuenta del usuario (30/09/2026).
Clave en la variable de entorno API_TENNIS_KEY (nunca en el código ni en el chat).

- marcadores(): partidos en juego (get_livescore) con el estado que necesita la calculadora:
  sets ganados, juegos del set en curso, puntos del juego en curso y quién saca.
- cuotas_directo(match_key): cuotas en directo (get_live_odds) tal cual.
- estado(partido): traduce un partido de get_livescore al marcador de markov_tenis.partido_desde.

Campos según la documentación (sin probar todavía con datos reales): event_key,
event_first_player, event_second_player, event_serve ("First Player"/"Second Player"),
event_game_result ("30 - 15"), event_status ("Set 2"), scores [{score_first, score_second,
score_set}], event_type_type ("Atp Singles", "Itf Women Singles"...), tournament_name.
"""
import os

import requests

URL = "https://api.api-tennis.com/tennis/"
PUNTOS = {"0": 0, "15": 1, "30": 2, "40": 3, "A": 4, "AD": 4}


def _pedir(metodo, **params):
    clave = os.environ.get("API_TENNIS_KEY")
    if not clave:
        raise RuntimeError("Falta API_TENNIS_KEY en el entorno (ajustes del entorno -> Edit).")
    try:
        r = requests.get(URL, params={"method": metodo, "APIkey": clave, **params}, timeout=30)
    except requests.RequestException as e:
        # el mensaje de requests incluye la URL, y la URL lleva la clave: no se muestra
        raise RuntimeError(f"API-Tennis sin respuesta en {metodo} ({type(e).__name__})") from None
    if r.status_code != 200:
        raise RuntimeError(f"API-Tennis devolvió HTTP {r.status_code} en {metodo}")
    j = r.json()
    if str(j.get("success")) not in ("1", "True", "true"):
        raise RuntimeError(f"API-Tennis devolvió error en {metodo}: {str(j)[:200]}")
    return j.get("result", [])


def marcadores():
    return _pedir("get_livescore")


def cuotas_directo(match_key=None):
    return _pedir("get_live_odds", **({"match_key": match_key} if match_key else {}))


def circuito(p):
    t = str(p.get("event_type_type", "")).lower()
    if "double" in t or "/" in str(p.get("event_first_player", "")):
        return None                                   # dobles: sin modelo
    if "wta" in t or "women" in t:
        return "wta"
    if "atp" in t or "men" in t or "challenger" in t:
        return "atp"
    return None


def mejor_de(p):
    t = str(p.get("tournament_name", "")).lower()
    slam = any(s in t for s in ("australian open", "roland garros", "french open", "wimbledon", "us open"))
    return 5 if slam and circuito(p) == "atp" else 3


def estado(p):
    """Marcador para markov_tenis.partido_desde, o None si no se puede leer."""
    sets = sorted(p.get("scores") or [], key=lambda s: int(s.get("score_set", 0)))
    try:
        actual = int(str(p.get("event_status", "")).lower().replace("set", "").strip())
    except ValueError:
        return None
    sa = sb = ja = jb = 0
    ga = gb = 0
    for s in sets:
        a, b = int(float(s.get("score_first") or 0)), int(float(s.get("score_second") or 0))
        if int(s.get("score_set", 0)) < actual:
            sa, sb, ja, jb = sa + (a > b), sb + (b > a), ja + a, jb + b
        elif int(s.get("score_set", 0)) == actual:
            ga, gb = a, b
    partes = [x.strip() for x in str(p.get("event_game_result", "0 - 0")).split("-")]
    en_tb = ga == 6 and gb == 6
    try:
        xa, xb = ((int(partes[0]), int(partes[1])) if en_tb else
                  (PUNTOS.get(partes[0].upper(), 0), PUNTOS.get(partes[1].upper(), 0)))
    except (ValueError, IndexError):
        xa = xb = 0
    if not en_tb:                                     # la "A" (ventaja) solo existe en juegos normales
        if xa == 4 and xb < 3:
            xa = 3
        if xb == 4 and xa < 3:
            xb = 3
        if xa == 4:
            xb = 3
        if xb == 4:
            xa = 3
    saque = str(p.get("event_serve", "")).lower()
    a_saca = True if saque.startswith("first") else False if saque.startswith("second") else None
    if en_tb and a_saca is not None:
        # en el tie-break el cálculo necesita quién sacó el PRIMER punto (orden A, B, B, A, A...)
        n = xa + xb
        a_saca = a_saca if (n % 4 == 0 or n % 4 == 3) else not a_saca
    return {"sa": sa, "sb": sb, "ga": ga, "gb": gb, "xa": xa, "xb": xb, "a_saca": a_saca,
            "previos": (ja, jb), "mejor_de": mejor_de(p)}


def partidos_dia(fecha):
    return _pedir("get_fixtures", date_start=fecha, date_stop=fecha)


def cuotas_dia(fecha):
    return _pedir("get_odds", date_start=fecha, date_stop=fecha)


def superficie_torneo(tournament_key):
    """Superficie del torneo ('Hard', 'Clay', 'Grass'...) del campo tournament_surface de get_draw
    (el único método que la trae; get_fixtures, get_livescore y get_tournaments no). None si no viene."""
    try:
        r = _pedir("get_draw", tournament_key=tournament_key)
    except RuntimeError:
        return None
    def buscar(x):
        if isinstance(x, dict):
            if x.get("tournament_surface"):
                return x["tournament_surface"]
            for v in x.values():
                s = buscar(v)
                if s:
                    return s
        elif isinstance(x, list):
            for v in x:
                s = buscar(v)
                if s:
                    return s
        return None
    return buscar(r)
