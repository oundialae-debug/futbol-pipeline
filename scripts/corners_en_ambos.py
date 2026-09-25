"""
¿Qué pintan los córners en el mejor modelo de ambos marcan? (25/09/2026)

Mejor modelo de ambos marcan: producción (99) + precio (7 mkt_) = 106
rasgos. Seis son de córners (media de los últimos 8 partidos, a favor y en
contra, local/visitante/diferencia). Tres preguntas:

  1. Importancia: ¿qué puesto ocupan entre los 106? (ganancia media de
     XGBoost, 5 semillas)
  2. Quitarlos: ambos marcan SIN los 6 de córners, emparejado.
  3. Apilar: la probabilidad del mejor modelo de más de 9.5 córners como
     variable, fuera de muestra en entrenamiento (mismo método que
     apilar_mas25_en_ambos.py, para que la variable no "sepa" el resultado).
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
    corners = [c for c in cols if "_m_corners" in c or "_m_contra_corners" in c]
    base, ent_todo, fecha_corte = M.partir(base_todo, prod)
    val = base[(pd.to_datetime(base.fecha) > fecha_corte) & base[MKT].notna().all(axis=1)].copy()

    # 1. importancia en el modelo de ambos marcan
    ent_a = ent_todo[ent_todo[M.ORIGEN_OBJETIVO["ambos_marcan"]].notna()].reset_index(drop=True)
    imp = np.zeros(len(cols))
    for s in EM.SEMILLAS:
        m = M.entrenar(ent_a[cols].values, ent_a.ambos_marcan.values.astype(int), 2, semilla=s)
        sc = m.get_booster().get_score(importance_type="gain")
        imp += np.array([sc.get(f"f{i}", 0.0) for i in range(len(cols))])
    rank = pd.Series(imp / len(EM.SEMILLAS), index=cols).sort_values(ascending=False)
    pos = {c: list(rank.index).index(c) + 1 for c in cols}
    print(f"Importancia en ambos marcan ({len(cols)} rasgos, ganancia media):")
    print("  top 10: " + ", ".join(f"{i+1}. {c}" for i, c in enumerate(rank.index[:10])))
    for c in corners:
        print(f"  {c:26s} puesto {pos[c]:3d} de {len(cols)}  ({rank[c]/rank.sum()*100:.1f}% de la ganancia)")
    print(f"  los 6 de córners juntos: {rank[corners].sum()/rank.sum()*100:.1f}% de la ganancia "
          f"(si pesaran lo que su número: {6/len(cols)*100:.1f}%)\n")

    # 2 y 3. quitar córners / apilar el modelo de córners
    ent_c = ent_todo[ent_todo[M.ORIGEN_OBJETIVO["mas_9_5_corners"]].notna()].reset_index(drop=True)
    oof = np.full(len(ent_c), np.nan)
    for idx in np.array_split(np.arange(len(ent_c)), BLOQUES):
        oof[idx] = predecir(ent_c.drop(index=idx), ent_c.iloc[idx], cols, "mas_9_5_corners", 2)
    ent_c["stack_p_corners"] = oof
    val["stack_p_corners"] = predecir(ent_c, val, cols, "mas_9_5_corners", 2)
    b_e = EM.brier(ent_c.stack_p_corners.values, ent_c.mas_9_5_corners.values.astype(int), 2).mean()
    vc = val[val.mas_9_5_corners.notna()]
    b_v = EM.brier(vc.stack_p_corners.values, vc.mas_9_5_corners.values.astype(int), 2).mean()
    print(f"Variable apilada de córners: Brier entrenamiento {b_e:.4f}  validación {b_v:.4f} (sin fuga si parecidos)\n")

    ent_a = ent_a.merge(ent_c[["match_id", "stack_p_corners"]], on="match_id", how="left")
    v = val[val[M.ORIGEN_OBJETIVO["ambos_marcan"]].notna()]
    y = v.ambos_marcan.values.astype(int)
    configs = {"ambos (106 rasgos)": cols,
               "ambos SIN córners (100)": [c for c in cols if c not in corners],
               "ambos + p(más de 9.5 córners)": cols + ["stack_p_corners"]}
    b = {k: EM.brier(predecir(ent_a, v, c, "ambos_marcan", 2), y, 2) for k, c in configs.items()}
    ref = b["ambos (106 rasgos)"]
    ph = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS["ambos_marcan"])
    cc = v.match_id.isin(ph.index).values
    bm = EM.brier(ph.loc[v.match_id[cc]].values, y[cc], 2)
    print(f"ambos marcan, {len(v)} partidos (positivo = mejor que el modelo de 106):")
    for k in configs:
        vs = "" if k == "ambos (106 rasgos)" else f"{sig(ref - b[k]):+.2f}s"
        print(f"  {k:32s} vs 106: {vs:>7s}   contra el mercado (n={cc.sum()}): {sig(bm - b[k][cc]):+.2f}s")


if __name__ == "__main__":
    main()
