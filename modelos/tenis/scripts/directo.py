"""
Pronóstico EN DIRECTO (30/09/2026). Marcador de ESPN (API pública sin clave:
site.api.espn.com/apis/site/v2/sports/tennis/{atp,wta}/scoreboard; sets y
juegos, sin puntos ni quién saca), fuerza de cada jugador del modelo de
puntos (probabilidad de ganar un punto al saque, antes del partido) y la
cadena de Markov desde el marcador actual (markov_tenis.partido_desde; sin
saber quién saca se promedian los dos casos).

Da, para cada partido en juego: prob. de ganar, marcador en sets, total de
juegos (líneas 19,5 a 25,5) y hándicap de juegos. Escribe
modelos/tenis/pronosticos/directo_<fecha-hora>.md.
Uso: python3 modelos/tenis/scripts/directo.py [wta|atp ...]
"""
import sys

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, "modelos/tenis/scripts")
import elo_tenis as E  # noqa: E402
import markov_tenis as K  # noqa: E402
import modelo_puntos as P  # noqa: E402

URL = "https://site.api.espn.com/apis/site/v2/sports/tennis/{}/scoreboard"


def en_juego(circuito):
    j = requests.get(URL.format(circuito), timeout=30).json()
    out = []
    for ev in j.get("events", []):
        for g in ev.get("groupings", []):
            slug = g.get("grouping", {}).get("slug", "")
            # el enlace de ATP también devuelve los cuadros femeninos de torneos mixtos (China Open)
            if "single" not in slug or (circuito == "atp") == ("women" in slug):
                continue
            for c in g.get("competitions", []):
                if c.get("status", {}).get("type", {}).get("state") != "in":
                    continue
                cs = c.get("competitors", [])
                if len(cs) != 2 or any("/" in x["athlete"].get("displayName", "") for x in cs):
                    continue
                a, b = cs
                la = [s.get("value", 0) for s in a.get("linescores", [])]
                lb = [s.get("value", 0) for s in b.get("linescores", [])]
                n = max(len(la), len(lb))
                la, lb = la + [0] * (n - len(la)), lb + [0] * (n - len(lb))
                sa = sum(1 for x, y in zip(la[:-1], lb[:-1]) if x > y)
                sb = sum(1 for x, y in zip(la[:-1], lb[:-1]) if y > x)
                out.append({"torneo": ev.get("name"), "A": a["athlete"]["displayName"].strip(),
                            "B": b["athlete"]["displayName"].strip(), "sa": sa, "sb": sb,
                            "ga": int(la[-1]) if n else 0, "gb": int(lb[-1]) if n else 0,
                            "previos": (int(sum(la[:-1])), int(sum(lb[:-1]))),
                            # ESPN pone 5 sets en todo el ATP: solo los Grand Slams masculinos son a 5
                            "mejor_de": 5 if circuito == "atp" and any(
                                s in ev.get("name", "") for s in ("Australian Open", "Roland Garros",
                                                                   "French Open", "Wimbledon", "US Open")) else 3,
                            "nota": (c.get("notes") or [{}])[0].get("text", "")})
    return out


def clave(nombre, conocidos):
    """Clave de jugador; ESPN escribe los nombres chinos al revés ("Yuan Yue" por "Yue Yuan")."""
    k = E.norm(nombre)
    if k not in conocidos:
        partes = nombre.split()
        if len(partes) >= 2:
            k2 = E.norm(" ".join(partes[1:] + partes[:1]))
            if k2 in conocidos:
                return k2
    return k


def fuerzas(circuito, partidos):
    """Prob. de punto al saque de cada jugador para cada partido, en pista dura, antes de hoy."""
    d0 = E.historial(circuito, itf=(circuito == "atp"))
    todos = set(d0["w"]) | set(d0["l"])
    filas = []
    for i, m in enumerate(partidos):
        f = {c: np.nan for c in d0.columns}
        f.update({"tourney_id": f"directo-{i}", "tourney_name": m["torneo"], "inicio": pd.Timestamp.now().normalize(),
                  "orden": 6, "sup": "Hard", "surface": "Hard", "round": "R32", "winner_name": m["A"],
                  "loser_name": m["B"], "w": clave(m["A"], todos), "l": clave(m["B"], todos), "actualiza": False,
                  "score": "nan"})
        filas.append(f)
    d = pd.concat([d0, pd.DataFrame(filas)], ignore_index=True)
    r = P.pasar(d, *P.PARAMS[circuito])
    n = len(partidos)
    conocidos = [(clave(m["A"], todos) in todos, clave(m["B"], todos) in todos) for m in partidos]
    return (P.prob_punto(r["th_w"][-n:], r["v_w"][-n:]), P.prob_punto(r["th_l"][-n:], r["v_l"][-n:]), conocidos)


def main():
    circuitos = sys.argv[1:] or ["wta", "atp"]
    ahora = pd.Timestamp.now(tz="UTC")
    lin = [f"# En directo, {ahora:%d/%m/%Y %H:%M} UTC\n",
           "Marcador de ESPN (sin puntos ni saque: se promedia quién saca). Probabilidades del modelo de puntos",
           "desde el marcador actual. En Kalshi el modelo acertó menos que el precio antes del partido: esto es",
           "una referencia para comparar con la cuota en directo, no una recomendación.\n"]
    for c in circuitos:
        ps = en_juego(c)
        if not ps:
            lin.append(f"## {c.upper()}: ningún partido individual en juego\n")
            continue
        pa, pb, conocidos = fuerzas(c, ps)
        lin += [f"## {c.upper()}\n", "| torneo | partido | marcador | gana A | sets más probables | total juegos: "
                "más de 19,5 / 21,5 / 23,5 / 25,5 | A -2,5 / -4,5 juegos | ¿historial? |",
                "|---|---|---|---|---|---|---|---|"]
        for m, x, y, (ka, kb) in zip(ps, pa, pb, conocidos):
            r = K.partido_desde(K.redondear(x), K.redondear(y), int(m["mejor_de"]), m["sa"], m["sb"], m["ga"], m["gb"],
                                None, 0, 0, m["previos"])
            sets = sorted(r["sets"].items(), key=lambda kv: -kv[1])[:2]
            tot = " / ".join(f"{sum(v for k, v in r['total'].items() if k > l):.0%}" for l in (19.5, 21.5, 23.5, 25.5))
            hc = " / ".join(f"{sum(v for k, v in r['dif'].items() if k > l):.0%}" for l in (2.5, 4.5))
            marc = f"{m['sa']}-{m['sb']} sets, {m['ga']}-{m['gb']}"
            lin.append(f"| {m['torneo']} | {m['A']} vs {m['B']} | {marc} | {r['gana_A']:.0%} | "
                       f"{', '.join(f'{a}-{b} {v:.0%}' for (a, b), v in sets)} | {tot} | {hc} | "
                       f"{'sí' if ka and kb else 'NO (' + ('A' if not ka else 'B') + ')'} |")
        lin.append("")
    salida = f"modelos/tenis/pronosticos/directo_{ahora:%Y-%m-%d_%H%M}.md"
    open(salida, "w").write("\n".join(lin) + "\n")
    print("\n".join(lin))
    print("guardado en", salida)


if __name__ == "__main__":
    main()
