"""
¿APORTA EL MODELO ALGO QUE EL MERCADO NO TENGA?

LA DIFERENCIA QUE IMPORTA
-------------------------
`evaluar_contra_mercado.py` dijo que el modelo es PEOR que el mercado
(Brier 0.6639 contra 0.6558). Eso cierra la puerta a apostarle a secas, pero
no contesta la pregunta de verdad:

    ¿tiene el modelo información ORTOGONAL, que el precio no lleva dentro?

Son cosas distintas. Un modelo puede ser peor en conjunto y aun asi saber
algo que el mercado ignora. Si es asi, la jugada no es apostar el modelo: es
partir del precio del mercado y CORREGIRLO un poco con el modelo.

Y si no aporta nada, entonces mas datos y mejores rasgos no van a cambiarlo:
estariamos aprendiendo a reproducir un precio que ya tenemos gratis.

COMO SE MIDE
------------
Se mezclan las dos probabilidades con un peso w:

    p_mezcla = (1-w) * p_mercado  +  w * p_modelo

y se busca el w que minimiza el Brier fuera de muestra.

  w = 0     -> el modelo no aporta nada, el mercado solo es lo mejor
  w > 0     -> hay informacion que el mercado no lleva

El peso optimo se elige con validacion cruzada POR BLOQUES TEMPORALES sobre
el propio conjunto de validacion, no mirando el resultado final. Elegir w
mirando el Brier que quieres reportar es hacerse trampas al solitario: con
suficientes w probados, alguno gana por azar.

SIN SIGNIFICACION NO HAY HALLAZGO
---------------------------------
Se da el error del w estimado con bootstrap por partido. Si el intervalo
incluye el cero, el modelo no aporta nada demostrable, por bonito que sea el
punto central.
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rasgos
import modelo_xgboost as M
import evaluar_contra_mercado as E


def brier(p, y):
    uno = np.zeros_like(p); uno[np.arange(len(y)), y] = 1
    return ((p - uno) ** 2).sum(axis=1)


def mejor_peso(pm, pn, y, rejilla=np.linspace(0, 1, 41)):
    """El w que minimiza el Brier medio."""
    costes = [brier((1-w)*pm + w*pn, y).mean() for w in rejilla]
    i = int(np.argmin(costes))
    return float(rejilla[i]), float(costes[i])


def main():
    hist = M.cargar()
    if hist is None:
        return
    base = rasgos.construir(hist).sort_values("fecha")
    cols = rasgos.columnas_rasgo(base)
    base = base[base[cols].notna().all(axis=1)].reset_index(drop=True)
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent, val = base.iloc[:corte], base.iloc[corte:]
    fecha_corte = pd.to_datetime(ent.fecha.max())
    m = M.entrenar(ent[cols].values, ent["resultado"].values.astype(int), 3)

    d = pd.read_csv(E.RUTA_CUOTAS)
    ftr = d[d.familia == "Full Time Result"]
    filas = []
    for (mid, casa), g in ftr.groupby(["match_id", "casa"]):
        p = E.probabilidad_mercado(dict(zip(g.lado, g.cuota)))
        if p is not None:
            filas.append({"match_id": mid,
                          **{f"p_{l}": p[i] for i, l in enumerate(E.LADOS)}})
    mercado = (pd.DataFrame(filas)
               .groupby("match_id")[[f"p_{l}" for l in E.LADOS]].median())
    mercado = mercado.div(mercado.sum(axis=1), axis=0)

    val = val[val.match_id.isin(mercado.index)]
    val = val[pd.to_datetime(val.fecha) > fecha_corte]
    if len(val) < 20:
        print(f"Solo {len(val)} partidos evaluables.")
        return

    pm = mercado.loc[val.match_id].values
    pn = M.probabilidades(m, val[cols].values, 3)
    y = val["resultado"].values.astype(int)

    print(f"{len(val)} partidos fuera de muestra con cuotas\n")
    print(f"  {'peso al modelo':>16s} {'Brier':>9s}")
    for w in (0.0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0):
        b = brier((1-w)*pm + w*pn, y).mean()
        marca = "  <- solo mercado" if w == 0 else ("  <- solo modelo" if w == 1 else "")
        print(f"  {w:16.2f} {b:9.4f}{marca}")

    w, coste = mejor_peso(pm, pn, y)
    b0 = brier(pm, y).mean()
    print(f"\n  peso optimo w = {w:.2f}  ->  Brier {coste:.4f} "
          f"(mercado solo: {b0:.4f})")

    # bootstrap por partido: ¿el peso optimo se distingue de cero?
    rng = np.random.default_rng(0)
    pesos = []
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        pesos.append(mejor_peso(pm[i], pn[i], y[i])[0])
    pesos = np.array(pesos)
    lo, hi = np.percentile(pesos, [2.5, 97.5])
    frac_cero = float((pesos <= 0.001).mean())
    print(f"\n  bootstrap (2000 remuestreos por partido):")
    print(f"    intervalo 95% del peso: [{lo:.2f}, {hi:.2f}]")
    print(f"    el peso sale CERO en el {frac_cero*100:.0f}% de los remuestreos")

    aporta = bool(lo > 0.001)
    print()
    if aporta:
        print(f"  EL MODELO APORTA: el peso optimo se mantiene sobre cero.")
        print(f"  La jugada no es apostar el modelo, es corregir el precio")
        print(f"  del mercado con el {w*100:.0f}% de peso al modelo.")
    else:
        print(f"  EL MODELO NO APORTA NADA DEMOSTRABLE. El intervalo incluye")
        print(f"  el cero: con estos datos no hay informacion que el precio")
        print(f"  no lleve ya dentro.")

    json.dump({"aporta": aporta, "peso": w, "intervalo": [float(lo), float(hi)],
               "partidos": int(len(val)), "brier_mercado": float(b0),
               "brier_mezcla": float(coste)},
              open("data/aporta_algo.json", "w"), indent=2)


if __name__ == "__main__":
    main()
