"""
Foto de la fuerza de cada jugador al final del historial (modelo de puntos), para
pronosticar rápido sin recalcular todo el historial (p. ej. en GitHub Actions cada 5
minutos). Guarda data/tenis/estado_puntos_<circuito>.json con, por jugador (clave
elo_tenis.norm del nombre completo): saque, resto, varianzas, último día, desviaciones
por superficie, y un índice "apellido|inicial" -> jugadores (API-Tennis abrevia los
nombres: "P. Berezina"). ATP incluye Challenger e ITF masculino; WTA incluye ITF femenino.
"""
import json
import sys

sys.path.insert(0, "modelos/tenis/scripts")
import cruce_fuentes as C  # noqa: E402
import elo_tenis as E  # noqa: E402
import modelo_puntos as P  # noqa: E402


def clave_torneo(nombre):
    """'W15 Monastir 28' -> 'w15monastir'; 'Mouilleron-Le-Captif' -> 'mouilleronlecaptif'."""
    import re
    return E.norm(re.sub(r"\s+\d+$", "", str(nombre).strip()))


def main():
    for circuito in ("atp", "wta"):
        d = E.historial(circuito, itf=(circuito == "atp"))
        r = P.pasar(d, *P.PARAMS[circuito])
        nombres = {}
        for n in list(d["winner_name"]) + list(d["loser_name"]):
            nombres.setdefault(E.norm(n), n)
        indice = {}
        for k, n in nombres.items():
            ck = C.clave_completo(n)
            if ck:
                indice.setdefault(ck, []).append(k)
        jug = {k: {"s": v[0], "vs": v[1], "r": v[2], "vr": v[3], "dia": int(v[4]), "nombre": nombres.get(k, k),
                   "sup": {}} for k, v in r["estado"].items()}
        for (k, s), v in r["estado_sup"].items():
            if k in jug:
                jug[k]["sup"][s] = {"s": v[0], "vs": v[1], "r": v[2], "vr": v[3], "dia": int(v[4])}
        # torneo -> superficie de su última edición (API-Tennis no da la superficie)
        sup = {}
        for n, s in zip(d["tourney_name"].astype(str), d["sup"]):
            sup[clave_torneo(n)] = s
        import glob
        import pandas as pd
        patron = "*ongoing*" if circuito == "atp" else "wta_ongoing*"
        for f in glob.glob(f"data/tenis/tennismylife/{patron}"):
            if circuito == "atp" and "wta" in f:
                continue
            o = pd.read_csv(f, usecols=["tourney_name", "surface"], low_memory=False).dropna()
            for n, s in zip(o["tourney_name"], o["surface"]):
                sup[clave_torneo(n)] = "Hard" if s == "Carpet" else s     # torneos en curso esta semana
        salida = {"params": P.PARAMS[circuito], "mu": r["mu"], "hasta": str(d["inicio"].max().date()),
                  "jugadores": jug, "indice": indice, "superficies": sup}
        json.dump(salida, open(f"data/tenis/estado_puntos_{circuito}.json", "w"))
        print(circuito, len(jug), "jugadores, hasta", salida["hasta"])


if __name__ == "__main__":
    main()
