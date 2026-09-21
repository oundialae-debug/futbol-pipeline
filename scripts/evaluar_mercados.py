"""
LOS CINCO MERCADOS QUE YA MODELAMOS, TODOS CONTRA EL MERCADO REAL A LA VEZ

POR QUÉ ESTE FICHERO, Y NO SOLO evaluar_contra_mercado.py
------------------------------------------------------------
evaluar_contra_mercado.py solo mide 1X2. El modelo ya predice cinco cosas
(resultado, más de 2.5 goles, ambos marcan, más de 9.5 córners, más de 4.5
tarjetas) pero solo una se comprobaba contra el precio real. Esto cierra ese
hueco: la misma prueba, para las cinco, en la misma pasada.

DOS FUENTES DE CUOTAS, FUSIONADAS
-----------------------------------
backtest_valor.csv (se sobrescribe cada vez) y cuotas_cosechadas.csv (acumula
a diario) no tienen los mismos partidos ni el mismo mercado disponible --
Total Cards, por ejemplo, solo está en la segunda porque backtest_valor.py
nunca encontró casas suficientes para guardarlo. Juntar las dos y quitar
duplicados por (partido, casa, lado) es obligatorio o se pierde información
que ya tenemos pagada.

PARA CADA MERCADO
------------------
1. Probabilidad del mercado: mediana desmarginada entre casas (cuotas
   idénticas cuentan una vez -- son la misma marca, no dos opiniones).
2. Brier del modelo y del mercado sobre los MISMOS partidos, fuera de
   muestra, con fecha posterior al corte de entrenamiento.
3. Diferencia emparejada partido a partido -> sigmas. Nunca comparar dos
   medias sueltas: el mismo partido se acierta o se falla en los dos a la
   vez, y eso encoge el error si no se hace emparejado.
4. Peso óptimo de MEZCLA (modelo + mercado) y su intervalo por bootstrap,
   igual que aporta_algo.py -- para no repetir el error de declarar hallazgo
   con un punto central bonito y sin mirar el intervalo.

SIN SIGNIFICACIÓN NO HAY HALLAZGO, en las cinco
-------------------------------------------------
El veredicto de cada mercado exige sigmas >= 2 para "bate al mercado", igual
que evaluar_contra_mercado.py. Un punto central positivo con muestra chica no
cuenta -- ya nos pasó con México Liga MX y con la pista de la mezcla.
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rasgos
import modelo_xgboost as M

RUTA_SALIDA = "data/validacion_mercados.json"
SIGMAS_MINIMAS = 2.0

# familia de cuotas, mercado exacto (None = un único mercado sin líneas),
# lado positivo (el que coincide con el objetivo == 1)
MERCADOS = {
    "resultado": {"familia": "Full Time Result", "mercado": None,
                 "lados": ["home", "draw", "away"], "n_clases": 3},
    "mas_2_5": {"familia": "Total Goals", "mercado": "Total Goals 2.5",
               "lados": ["over", "under"], "positivo": "over", "n_clases": 2},
    "ambos_marcan": {"familia": "Both Teams To Score", "mercado": None,
                     "lados": ["yes", "no"], "positivo": "yes", "n_clases": 2},
    "mas_9_5_corners": {"familia": "Total Corners", "mercado": "Total Corners 9.5",
                        "lados": ["over", "under"], "positivo": "over", "n_clases": 2},
    "mas_4_5_tarjetas": {"familia": "Total Cards", "mercado": "Total Cards 4.5",
                         "lados": ["over", "under"], "positivo": "over", "n_clases": 2},
}


def cargar_cuotas_crudas():
    """Las dos fuentes juntas, sin filtrar todavía por familia."""
    trozos = []
    if os.path.exists("data/backtest_valor.csv"):
        d = pd.read_csv("data/backtest_valor.csv")
        trozos.append(d[["match_id", "familia", "mercado", "casa", "lado", "cuota"]])
    if os.path.exists("data/cuotas_cosechadas.csv"):
        c = pd.read_csv("data/cuotas_cosechadas.csv")
        c = c.rename(columns={"mercado": "mercado_api"})
        c["familia"] = c["mercado_api"].str.extract(r"^([A-Za-z ]+?)(?:\s+[\d.]+)?$")[0].str.strip()
        # familias sin línea en el nombre (Full Time Result, Both Teams To
        # Score) no llevan número que quitar; con línea, el mercado_api YA
        # es el nombre completo con línea y sirve tal cual como "mercado".
        c["mercado"] = c["mercado_api"]
        c["lado"] = c["lado"].astype(str).str.strip().str.lower()
        trozos.append(c[["match_id", "familia", "mercado", "casa", "lado", "cuota"]])
    if not trozos:
        return None
    d = pd.concat(trozos, ignore_index=True)
    d["lado"] = d["lado"].astype(str).str.strip().str.lower()
    return d.drop_duplicates(["match_id", "mercado", "casa", "lado"])


def probabilidad_binaria(cuotas, positivo, negativo):
    if set(cuotas) != {positivo, negativo} or any(c <= 1 for c in cuotas.values()):
        return None
    inv_p, inv_n = 1 / cuotas[positivo], 1 / cuotas[negativo]
    return inv_p / (inv_p + inv_n)


def mercado_por_partido(d, cfg):
    """Serie match_id -> probabilidad del lado positivo (o vector 3-clases)."""
    sub = d[d.familia == cfg["familia"]]
    if cfg["mercado"]:
        sub = sub[sub.mercado == cfg["mercado"]]
    if sub.empty:
        return None
    if cfg["n_clases"] == 3:
        filas = []
        for (mid, casa), g in sub.groupby(["match_id", "casa"]):
            cuotas = dict(zip(g.lado, g.cuota))
            if set(cuotas) != set(cfg["lados"]) or any(v <= 1 for v in cuotas.values()):
                continue
            inv = np.array([1 / cuotas[l] for l in cfg["lados"]])
            p = inv / inv.sum()
            filas.append({"match_id": mid, **{f"p_{l}": p[i]
                          for i, l in enumerate(cfg["lados"])}})
        if not filas:
            return None
        m = pd.DataFrame(filas).groupby("match_id")[[f"p_{l}" for l in cfg["lados"]]].median()
        return m.div(m.sum(axis=1), axis=0)
    else:
        pos, neg = cfg["positivo"], [l for l in cfg["lados"] if l != cfg["positivo"]][0]
        filas = {}
        for (mid, casa), g in sub.groupby(["match_id", "casa"]):
            cuotas = dict(zip(g.lado, g.cuota))
            p = probabilidad_binaria(cuotas, pos, neg)
            if p is not None:
                filas.setdefault(mid, []).append(p)
        if not filas:
            return None
        return pd.Series({mid: float(np.median(ps)) for mid, ps in filas.items()})


def brier(p, y, n_clases):
    if n_clases == 3:
        uno = np.zeros_like(p); uno[np.arange(len(y)), y] = 1
        return ((p - uno) ** 2).sum(axis=1)
    p2 = np.column_stack([1 - p, p])
    uno = np.zeros_like(p2); uno[np.arange(len(y)), y] = 1
    return ((p2 - uno) ** 2).sum(axis=1)


def mejor_peso(pm, pn, y, n_clases, rejilla=np.linspace(0, 1, 21)):
    def mezclar(w):
        if n_clases == 3:
            return (1 - w) * pm + w * pn
        return (1 - w) * pm + w * pn
    costes = [brier(mezclar(w), y, n_clases).mean() for w in rejilla]
    i = int(np.argmin(costes))
    return float(rejilla[i]), float(costes[i])


def evaluar_uno(nombre, cfg, base, cols, m, fecha_corte, cuotas):
    pmer_todos = mercado_por_partido(cuotas, cfg)
    if pmer_todos is None:
        return {"evaluable": False, "motivo": "sin cuotas para este mercado"}

    val = base[pd.to_datetime(base.fecha) > fecha_corte]
    val = val[val.match_id.isin(pmer_todos.index if cfg["n_clases"] == 3
                                else pmer_todos.index)]
    if len(val) < 20:
        return {"evaluable": False, "motivo": f"solo {len(val)} partidos evaluables"}

    y = val[nombre].values.astype(int)
    pn_bruto = M.probabilidades(m, val[cols].values, cfg["n_clases"])
    pn = pn_bruto if cfg["n_clases"] == 3 else pn_bruto[:, 1]

    if cfg["n_clases"] == 3:
        pm = pmer_todos.loc[val.match_id][[f"p_{l}" for l in cfg["lados"]]].values
    else:
        pm = pmer_todos.loc[val.match_id].values

    b_modelo = brier(pn, y, cfg["n_clases"])
    b_mercado = brier(pm, y, cfg["n_clases"])
    dif = b_mercado - b_modelo
    ee = dif.std(ddof=1) / np.sqrt(len(dif)) if len(dif) > 1 else np.nan
    sigmas = float(dif.mean() / ee) if ee else 0.0

    w, coste_mezcla = mejor_peso(pm, pn, y, cfg["n_clases"])
    rng = np.random.default_rng(0)
    pesos = []
    for _ in range(500):
        i = rng.integers(0, len(y), len(y))
        pesos.append(mejor_peso(pm[i], pn[i], y[i], cfg["n_clases"])[0])
    lo, hi = np.percentile(pesos, [2.5, 97.5])

    bate = bool(dif.mean() > 0 and sigmas >= SIGMAS_MINIMAS)
    return {
        "evaluable": True, "partidos": int(len(val)),
        "brier_modelo": float(b_modelo.mean()), "brier_mercado": float(b_mercado.mean()),
        "sigmas": sigmas, "bate_al_mercado": bate,
        "peso_mezcla_optimo": w, "brier_mezcla": coste_mezcla,
        "intervalo_peso_95": [float(lo), float(hi)],
    }


def main():
    hist = M.cargar()
    if hist is None:
        return
    base = rasgos.construir(hist).sort_values("fecha")
    cols = rasgos.columnas_rasgo(base)
    base = base[base[cols].notna().all(axis=1)].reset_index(drop=True)
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent = base.iloc[:corte]
    fecha_corte = pd.to_datetime(ent.fecha.max())

    cuotas = cargar_cuotas_crudas()
    if cuotas is None:
        print("Sin cuotas de ningún tipo. Nada que evaluar.")
        return

    print(f"Entrenamiento hasta {fecha_corte.date()}. "
          f"{len(base) - corte} partidos posteriores disponibles.\n")

    resultados = {}
    for nombre, cfg in MERCADOS.items():
        y_ent = ent[nombre].values.astype(int)
        if len(np.unique(y_ent)) < cfg["n_clases"]:
            resultados[nombre] = {"evaluable": False, "motivo": "sin ambas clases en entrenamiento"}
            continue
        m = M.entrenar(ent[cols].values, y_ent, cfg["n_clases"])
        r = evaluar_uno(nombre, cfg, base, cols, m, fecha_corte, cuotas)
        resultados[nombre] = r

        if not r["evaluable"]:
            print(f"  {nombre:20s}  NO EVALUABLE -- {r['motivo']}")
            continue
        marca = "BATE AL MERCADO" if r["bate_al_mercado"] else "no bate"
        print(f"  {nombre:20s}  n={r['partidos']:4d}  "
              f"modelo {r['brier_modelo']:.4f}  mercado {r['brier_mercado']:.4f}  "
              f"{r['sigmas']:+.2f}s  [{marca}]")
        print(f"  {'':20s}  mezcla: peso optimo {r['peso_mezcla_optimo']:.2f}, "
              f"intervalo 95% [{r['intervalo_peso_95'][0]:.2f}, "
              f"{r['intervalo_peso_95'][1]:.2f}]")

    json.dump(resultados, open(RUTA_SALIDA, "w"), indent=2)
    print(f"\nEscrito {RUTA_SALIDA}")

    algo_bate = any(r.get("bate_al_mercado") for r in resultados.values())
    algo_con_intervalo_positivo = [n for n, r in resultados.items()
                                   if r.get("evaluable") and r["intervalo_peso_95"][0] > 0]
    print()
    if algo_bate:
        print("AL MENOS UN MERCADO BATE AL MERCADO CON SIGNIFICACIÓN. Revisar cuál.")
    elif algo_con_intervalo_positivo:
        print(f"Ninguno bate al mercado solo, pero el intervalo de mezcla no "
              f"incluye el cero en: {algo_con_intervalo_positivo}. Pista, no "
              f"hallazgo -- exige más muestra antes de creérselo.")
    else:
        print("Ningún mercado aporta nada demostrable hoy.")


if __name__ == "__main__":
    main()
