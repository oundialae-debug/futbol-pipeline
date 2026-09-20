"""
¿ESTÁ BIEN CALIBRADO EL MERCADO?

Es la pregunta que decide si este proyecto tiene sentido, y se contesta sin
modelo ninguno: cuando el consenso de las casas dice 30%, ¿pasa el 30% de las
veces?

Un sesgo sistemático sería explotable aunque nuestro pronóstico fuera peor
que el suyo: bastaría con apostar siempre al lado que el mercado infravalora.
Es la única ventaja que no exige ser mejor que nadie.

POR QUÉ CALIBRACIÓN Y NO ACIERTO
--------------------------------
Medir "cuánto acierta el mercado" por liga no sirve para decidir: un mercado
puede acertar poco porque esa liga es impredecible, no porque esté mal
cotizada. La Premier sale con peor Brier que la Ligue 1 y eso no significa
que la Premier esté peor cotizada, sino que está más igualada.

La calibración no tiene ese problema. Si el mercado dice 30% y pasa el 38%,
está equivocado, sea la liga que sea.

CÓMO LEER EL RESULTADO
----------------------
El sesgo es lo que pasa menos lo que se decía. Al lado va su error típico:
con menos de dos sigmas no se distingue de la casualidad, y conviene no
emocionarse con un tramo suelto que se salga -- mirando ocho tramos, que uno
dé 1.5 sigmas es lo normal.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timezone

RUTA_ENTRADA = "data/backtest_valor.csv"
RUTA_INFORME = "calibracion_mercado.md"


def main():
    if not os.path.exists(RUTA_ENTRADA):
        print(f"Falta {RUTA_ENTRADA}: hay que correr el backtest primero")
        return
    d = pd.read_csv(RUTA_ENTRADA)

    # Una fila por (partido, mercado, lado). El consenso es el mismo para
    # todas las casas de esa fila, así que contarlo una vez por casa
    # multiplicaría la muestra por cincuenta sin añadir información.
    u = d.groupby(["match_id", "liga", "familia", "mercado", "lado"]).agg(
        consenso=("consenso", "median"), resultado=("resultado", "median")).reset_index()
    u = u[u["resultado"] != 0.5]      # los empates no puntúan

    tramos = [0, .2, .3, .4, .5, .6, .7, .8, 1.0]
    u["tramo"] = pd.cut(u["consenso"], tramos)
    g = u.groupby("tramo", observed=True).agg(
        n=("resultado", "size"), dice=("consenso", "mean"), pasa=("resultado", "mean"))
    g["sesgo"] = (g["pasa"] - g["dice"]) * 100
    g["error"] = np.sqrt(g["pasa"] * (1 - g["pasa"]) / g["n"]) * 100
    g["sigmas"] = g["sesgo"] / g["error"]

    lineas = [
        f"# Calibración del mercado -- "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"{len(u)} resultados de {u['match_id'].nunique()} partidos ya jugados.\n",
        "Cuando el consenso de las casas dice 30%, ¿pasa el 30% de las veces? "
        "Un sesgo sistemático sería la única ventaja que no exige ser mejor "
        "que nadie: bastaría con apostar al lado que el mercado infravalora.\n",
        "| Dice | Pasa | Casos | Sesgo | Sigmas |",
        "|---|---|---|---|---|",
    ]
    for _, f in g.iterrows():
        lineas.append(f"| {f['dice']*100:.0f}% | {f['pasa']*100:.0f}% | "
                      f"{int(f['n'])} | {f['sesgo']:+.2f} pts | {f['sigmas']:+.2f} |")

    peor = g["sigmas"].abs().max()
    lineas.append("")
    if peor < 2:
        lineas += [
            f"**Ningún tramo se desvía más de {peor:.2f} sigmas.** El mercado "
            "está bien calibrado en todo el rango: no hay un hueco donde "
            "infravalore nada de forma sistemática.\n",
            "> Eso deja una sola vía para ganar: tener un pronóstico MEJOR que "
            "el consenso de cincuenta casas profesionales, y además por un "
            "margen mayor que el 4-6% que cobran. No es que sea difícil: es "
            "que hay que batir al agregado de todos los que viven de esto.\n",
        ]
    else:
        tramo = g["sigmas"].abs().idxmax()
        lineas += [
            f"**El tramo {tramo} se desvía {g.loc[tramo, 'sigmas']:+.2f} "
            f"sigmas** ({g.loc[tramo, 'sesgo']:+.2f} puntos). Merece seguirlo "
            "con más partidos antes de creérselo: mirando ocho tramos, que uno "
            "se salga es esperable.\n",
        ]

    # por mercado, por si alguno se descuelga aunque el conjunto esté fino
    lineas += ["\n## Por mercado\n", "| Mercado | Casos | Sesgo medio | Sigmas |",
               "|---|---|---|---|"]
    for fam, sub in u.groupby("familia"):
        if len(sub) < 100:
            continue
        sesgo = (sub["resultado"].mean() - sub["consenso"].mean()) * 100
        err = np.sqrt(sub["resultado"].mean() * (1 - sub["resultado"].mean())
                      / len(sub)) * 100
        lineas.append(f"| {fam} | {len(sub)} | {sesgo:+.2f} pts | "
                      f"{sesgo/err if err else 0:+.2f} |")

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
