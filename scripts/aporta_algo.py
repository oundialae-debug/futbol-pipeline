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


def cargar_cuotas_1x2():
    """
    Las cuotas de 1X2 de las DOS fuentes, en un solo sitio.

    `backtest_valor.csv` las guarda ya clasificadas (familia/lado en
    minusculas) y SE SOBRESCRIBE en cada pasada. `cuotas_cosechadas.csv` las
    guarda crudas como vienen de la API ("Home"/"Draw"/"Away") y ACUMULA.

    Hay que leer las dos y normalizar el lado, porque si no, la fuente que
    crece se quedaria fuera sin dar ningun error. Los duplicados se quitan por
    (partido, casa, lado): el mismo precio en las dos fuentes es un precio, no
    dos opiniones.
    """
    trozos = []
    if os.path.exists(E.RUTA_CUOTAS):
        d = pd.read_csv(E.RUTA_CUOTAS)
        d = d[d.familia == "Full Time Result"][["match_id", "casa", "lado",
                                                "cuota"]]
        trozos.append(d)
    ruta_cosecha = "data/cuotas_cosechadas.csv"
    if os.path.exists(ruta_cosecha):
        c = pd.read_csv(ruta_cosecha)
        c = c[c.mercado == "Full Time Result"][["match_id", "casa", "lado",
                                                "cuota"]]
        trozos.append(c)
    if not trozos:
        return None
    d = pd.concat(trozos, ignore_index=True)
    d["lado"] = d["lado"].astype(str).str.strip().str.lower()
    d = d[d.lado.isin(E.LADOS)]
    return d.drop_duplicates(["match_id", "casa", "lado"])


def probabilidades_de_mercado():
    """Probabilidad desmarginada por partido: mediana entre casas."""
    d = cargar_cuotas_1x2()
    if d is None or d.empty:
        return None
    filas = []
    for (mid, casa), g in d.groupby(["match_id", "casa"]):
        p = E.probabilidad_mercado(dict(zip(g.lado, g.cuota)))
        if p is not None:
            filas.append({"match_id": mid,
                          **{f"p_{l}": p[i] for i, l in enumerate(E.LADOS)}})
    if not filas:
        return None
    m = (pd.DataFrame(filas)
         .groupby("match_id")[[f"p_{l}" for l in E.LADOS]].median())
    return m.div(m.sum(axis=1), axis=0)


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
    cols = rasgos.columnas_rasgo_default(base)
    base, ent, fecha_corte = M.partir(base.reset_index(drop=True), cols)
    ent = ent[ent[M.ORIGEN_OBJETIVO["resultado"]].notna()]
    val = base[pd.to_datetime(base.fecha) > fecha_corte]
    m = M.entrenar(ent[cols].values, ent["resultado"].values.astype(int), 3)

    mercado = probabilidades_de_mercado()
    if mercado is None or mercado.empty:
        print("Sin cuotas de 1X2 utilizables.")
        return
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
