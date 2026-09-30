"""
Apuestas en PAPEL de la señal "vigilar el menos" (juegos_directo.py), cruzadas con el resultado
final (data/tenis/api_tennis/resultados/*.csv, de get_fixtures). Regla fijada antes de mirar:
- una apuesta por partido: la PRIMERA pasada en que sale la señal;
- 1 unidad al menos de esa línea, a la cuota del menos de esa pasada (cuota de la API, no de
  Luckia); gana si juegos totales < línea;
- solo partidos acabados de forma normal ("Finished"); retiradas fuera (la casa suele anular).
Controles: mismo partido y momento, apostar SIEMPRE el menos / el más de la línea principal
(primera pasada de cada partido), y Brier del modelo frente al mercado en esa misma línea.
Escribe data/tenis/api_tennis/evaluacion_juegos.md.
"""
import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import juegos_directo as J  # noqa: E402

SAL = "data/tenis/api_tennis/evaluacion_juegos.md"


def cargar():
    regs = [pd.read_csv(f) for f in sorted(glob.glob("data/tenis/api_tennis/registro/*.csv"))]
    res = [pd.read_csv(f) for f in sorted(glob.glob("data/tenis/api_tennis/resultados/*.csv"))]
    if not regs or not res:
        return None, None
    res = pd.concat(res).drop_duplicates("event_key", keep="last")
    return pd.concat(regs), res[res.estado == "Finished"]


def resumen(nombre, g):
    if g.empty:
        return f"| {nombre} | 0 | | | |"
    n = len(g)
    m, s = g.benef.mean(), g.benef.std(ddof=1) if n > 1 else float("nan")
    sig = m / (s / np.sqrt(n)) if n > 1 and s > 0 else float("nan")
    return f"| {nombre} | {n} | {g.gana.mean():.0%} | {m:+.1%} | {sig:+.2f} |"


def main():
    reg, res = cargar()
    lin = ["# Más/menos juegos en directo: apuestas en papel\n"]
    if reg is None:
        open(SAL, "w").write("\n".join(lin + ["Sin resultados todavía.\n"]))
        return
    p = J.principales(reg).merge(res[["event_key", "juegos_totales"]], on="event_key")
    p["cuota_menos"] = p.cuota_rival.astype(float)
    p["cuota_mas"] = p.cuota.astype(float)
    p["menos_gana"] = p.juegos_totales < p.linea
    primera = p.groupby("event_key").first().reset_index()
    sen = p[p.senal].groupby("event_key").first().reset_index()

    def apuesta(g, lado):
        g = g.copy()
        g["gana"] = g.menos_gana if lado == "menos" else ~g.menos_gana & (g.juegos_totales != g.linea)
        c = g.cuota_menos if lado == "menos" else g.cuota_mas
        g["benef"] = np.where(g.gana, c - 1, -1.0)
        return g

    s = apuesta(sen, "menos")
    lin += [f"Partidos acabados con cuota de juegos en el registro: **{len(primera)}**. Una apuesta por partido "
            "(se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. "
            "Con menos de 20 apuestas el número no significa nada.\n",
            "| estrategia | apuestas | aciertos | beneficio medio | sigmas |", "|---|---|---|---|---|",
            resumen("**señal: vigilar el menos**", s),
            resumen("control: siempre el menos (1ª pasada)", apuesta(primera, "menos")),
            resumen("control: siempre el más (1ª pasada)", apuesta(primera, "mas"))]
    if len(primera):
        y = (~primera.menos_gana).astype(float)
        bm = ((primera.prob_modelo.astype(float) - y) ** 2).mean()
        bk = ((primera.prob_mercado.astype(float) - y) ** 2).mean()
        sesgo = primera.prob_modelo.astype(float).mean() - y.mean()
        lin += ["", f"Brier del 'más' en la línea principal (1ª pasada): modelo {bm:.4f}, mercado {bk:.4f} "
                f"(menor es mejor). El modelo da al más {sesgo:+.1%} sobre lo que pasa de verdad."]
    if len(s):
        lin += ["", "## Señales", "", "| partido | línea | cuota menos | juegos | resultado |", "|---|---|---|---|---|"]
        for _, r in s.iterrows():
            lin.append(f"| {J.torneo(r.tipo, r.torneo)}: {r.jugador1} vs {r.jugador2} | {r.linea:g} | "
                       f"{r.cuota_menos:.2f} | {r.juegos_totales} | {'gana' if r.gana else 'pierde'} |")
    open(SAL, "w").write("\n".join(lin) + "\n")
    print(f"evaluación: {len(primera)} partidos, {len(s)} señales")


if __name__ == "__main__":
    main()
