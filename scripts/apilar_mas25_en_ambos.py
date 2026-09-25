"""
La salida del mejor modelo de más de 2.5 como variable del mejor modelo de
ambos marcan (25/09/2026, idea del usuario).

Mejores modelos hoy (cuota_como_variable.py): producción + 7 rasgos de
mercado (mkt_) en los dos. El de más de 2.5 aprende de SU objetivo (goles
totales), que dice algo distinto de ambos marcan: un 3-0 es "más de 2.5" y
"no ambos marcan".

TRAMPA A EVITAR: si la probabilidad de más de 2.5 de un partido de
entrenamiento sale de un modelo que ya vio ese partido, la variable "sabe"
el resultado (en entrenamiento acierta demasiado y en validación no) y el
apilado sale inflado sin avisar. Por eso:
  - entrenamiento: predicción FUERA DE MUESTRA, 5 bloques seguidos por
    fecha; cada bloque se predice con un modelo entrenado en los otros 4
  - validación: modelo de más de 2.5 entrenado con TODO el entrenamiento
Así la variable tiene la misma "calidad" en entrenamiento y en validación.

Comparaciones (5 semillas, mismos partidos): ambos marcan con y sin la
variable apilada, emparejado en toda la validación, y cada uno contra el
mercado de ambos marcan cosechado.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM
from cuota_como_variable import MKT, sig, predecir

BLOQUES = 5


def main():
    hist = M.cargar()
    base_todo = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    prod = rasgos.columnas_rasgo_default(base_todo)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    mk = fd.rename(columns={c.replace("mkt_", ""): c for c in MKT})[["match_id"] + MKT]
    base_todo = base_todo.merge(mk, on="match_id", how="left")
    cols = prod + MKT
    base, ent_todo, fecha_corte = M.partir(base_todo, prod)
    val = base[(pd.to_datetime(base.fecha) > fecha_corte) & base[MKT].notna().all(axis=1)].copy()

    # 1. probabilidad de más de 2.5, fuera de muestra en entrenamiento
    ent = ent_todo[ent_todo[M.ORIGEN_OBJETIVO["mas_2_5"]].notna()].reset_index(drop=True)
    oof = np.full(len(ent), np.nan)
    trozos = np.array_split(np.arange(len(ent)), BLOQUES)
    for i, idx in enumerate(trozos):
        resto = ent.drop(index=idx)
        oof[idx] = predecir(resto, ent.iloc[idx], cols, "mas_2_5", 2)
        print(f"  bloque {i+1}/{BLOQUES} de más de 2.5 fuera de muestra")
    ent["stack_p_mas_2_5"] = oof
    val["stack_p_mas_2_5"] = predecir(ent, val, cols, "mas_2_5", 2)

    # comprobación: la variable apilada debe acertar parecido en entrenamiento y en validación
    b_e = EM.brier(ent.stack_p_mas_2_5.values, ent.mas_2_5.values.astype(int), 2).mean()
    b_v = EM.brier(val.stack_p_mas_2_5.values, val.mas_2_5.values.astype(int), 2).mean()
    print(f"\nBrier de la variable apilada: entrenamiento {b_e:.4f}  validación {b_v:.4f} "
          f"(si el de entrenamiento fuera mucho menor, habría fuga)\n")

    # 2. ambos marcan con y sin la variable apilada
    ent_a = ent_todo[ent_todo[M.ORIGEN_OBJETIVO["ambos_marcan"]].notna()].merge(
        ent[["match_id", "stack_p_mas_2_5"]], on="match_id", how="left")
    v = val[val[M.ORIGEN_OBJETIVO["ambos_marcan"]].notna()]
    y = v.ambos_marcan.values.astype(int)
    configs = {"ambos sin apilar": cols, "ambos + p(más de 2.5)": cols + ["stack_p_mas_2_5"]}
    b = {k: EM.brier(predecir(ent_a, v, c, "ambos_marcan", 2), y, 2) for k, c in configs.items()}
    print(f"ambos marcan, {len(v)} partidos de validación:")
    print(f"  con p(más de 2.5) vs sin ella: {sig(b['ambos sin apilar'] - b['ambos + p(más de 2.5)']):+.2f}s")
    ph = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS["ambos_marcan"])
    cc = v.match_id.isin(ph.index).values
    bm = EM.brier(ph.loc[v.match_id[cc]].values, y[cc], 2)
    for k in configs:
        d = bm - b[k][cc]
        rng = np.random.default_rng(0)
        peor = np.mean([rng.choice(d, len(d)).mean() <= 0 for _ in range(5000)])
        print(f"  {k:24s} contra el mercado (n={cc.sum()}): {sig(d):+.2f}s  "
              f"(bootstrap: peor que el mercado en el {peor*100:.0f}%)")


if __name__ == "__main__":
    main()
