"""
Quitar de la "base" lo que no aporta, en el mejor modelo de ambos marcan
(25/09/2026, petición del usuario).

Mejor modelo: producción (99) + precio (7 mkt_) = 106 rasgos; la base son
70 (21 medidas de forma x loc/vis/dif, partidos_previos, descanso, liga).
Se quita por MEDIDA entera (sus 3 columnas loc_/vis_/dif_ a la vez): quitar
loc_ y dejar dif_ rompe la pareja (ver "Poda por importancia" en CLAUDE.md,
que ya falló por eso cortando columna a columna).

Sin contaminar la prueba final:
  entrenamiento  lo anterior al tramo de selección
  selección      el último 25% del entrenamiento: aquí se decide qué sale
  prueba final   los 568 partidos de validación de siempre, UNA vez al final,
                 reentrenando con entrenamiento+selección
Eliminación hacia atrás: en cada paso se quita la medida cuya ausencia
baja más el Brier de selección; se para cuando quitar cualquiera lo sube.
"""
import sys, time
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM
from cuota_como_variable import MKT, sig, predecir


def main():
    t0 = time.time()
    hist = M.cargar()
    base_todo = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    prod = rasgos.columnas_rasgo_default(base_todo)
    grupos = rasgos.grupos_rasgo(base_todo)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    mk = fd.rename(columns={c.replace("mkt_", ""): c for c in MKT})[["match_id"] + MKT]
    base_todo = base_todo.merge(mk, on="match_id", how="left")
    cols = prod + MKT
    base_cols = [c for c in grupos["base"] if c in cols]
    unidades = {}
    for c in base_cols:
        clave = c.split("_", 1)[1] if c.startswith(("loc_", "vis_", "dif_")) else c
        unidades.setdefault(clave, []).append(c)
    print(f"{len(cols)} rasgos; base {len(base_cols)} en {len(unidades)} medidas.")

    base, ent_todo, fecha_corte = M.partir(base_todo, prod)
    ent = ent_todo[ent_todo[M.ORIGEN_OBJETIVO["ambos_marcan"]].notna()].reset_index(drop=True)
    n_sel = int(len(ent) * 0.25)
    e1, sel = ent.iloc[:-n_sel], ent.iloc[-n_sel:]
    val = base[(pd.to_datetime(base.fecha) > fecha_corte) & base[MKT].notna().all(axis=1)]
    val = val[val[M.ORIGEN_OBJETIVO["ambos_marcan"]].notna()]
    print(f"entrenamiento {len(e1)} | selección {len(sel)} ({str(sel.fecha.min())[:10]} a "
          f"{str(sel.fecha.max())[:10]}) | prueba final {len(val)}\n")

    ys = sel.ambos_marcan.values.astype(int)
    bri = lambda cs: EM.brier(predecir(e1, sel, cs, "ambos_marcan", 2), ys, 2)
    fuera = []
    actual = bri(cols)
    print(f"Paso 0: 106 rasgos, Brier selección {actual.mean():.4f}")
    paso = 0
    while True:
        paso += 1
        res = {}
        for u in unidades:
            if u in fuera:
                continue
            quitar = set(sum((unidades[x] for x in fuera + [u]), []))
            res[u] = bri([c for c in cols if c not in quitar])
        mejor = min(res, key=lambda u: res[u].mean())
        if res[mejor].mean() >= actual.mean():
            print(f"Paso {paso}: quitar cualquiera sube el Brier (la menos mala, {mejor}, "
                  f"da {res[mejor].mean():.4f}). Fin.  ({time.time()-t0:.0f}s)")
            break
        print(f"Paso {paso}: fuera {mejor:24s} Brier selección {res[mejor].mean():.4f} "
              f"({sig(actual - res[mejor]):+.2f}s sobre el paso anterior)  ({time.time()-t0:.0f}s)")
        fuera.append(mejor)
        actual = res[mejor]

    quitar = set(sum((unidades[x] for x in fuera), []))
    podado = [c for c in cols if c not in quitar]
    print(f"\nFuera {len(fuera)} medidas ({len(quitar)} columnas): {fuera}")
    print(f"Modelo podado: {len(podado)} rasgos.\n")

    # prueba final, una vez
    y = val.ambos_marcan.values.astype(int)
    b = {"completo (106)": EM.brier(predecir(ent, val, cols, "ambos_marcan", 2), y, 2),
         f"podado ({len(podado)})": EM.brier(predecir(ent, val, podado, "ambos_marcan", 2), y, 2)}
    ph = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS["ambos_marcan"])
    cc = val.match_id.isin(ph.index).values
    bm = EM.brier(ph.loc[val.match_id[cc]].values, y[cc], 2)
    k0, k1 = list(b)
    print(f"PRUEBA FINAL ({len(val)} partidos): podado vs completo {sig(b[k0] - b[k1]):+.2f}s")
    for k in b:
        print(f"  {k:16s} contra el mercado (n={cc.sum()}): {sig(bm - b[k][cc]):+.2f}s")


if __name__ == "__main__":
    main()
