"""
¿Ayuda saber cuántos titulares son nuevos respecto a la temporada anterior?
(hipótesis del usuario, 24/09/2026: al arrancar temporada cambian jugadores,
entrenadores y momento; el modelo no lo ve).

Hipótesis declarada ANTES de mirar: si ayuda, debe ayudar sobre todo al
INICIO de temporada (ago-sep 2026), no a final de 2025/26.

A = base_clasica+elo+cp_ataque (el mejor hasta ahora)
B = A + plantilla_nueva (fracción y número de titulares nuevos, loc/vis/dif)
Y el mismo par sobre base_clasica+elo, para ver que no depende de cp_ataque.
Mismos tramos que seleccion_combinaciones.py, 5 semillas, Brier emparejado.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
src = open("scripts/seleccion_combinaciones.py", encoding="utf-8").read().split("# ---------- 1.")[0]
with contextlib.redirect_stdout(io.StringIO()):
    exec(src)

# 1. ¿la variable tiene sentido? media de nuevos por mes (con alineación)
m = bc[bc.loc_pn_frac.notna()].copy()
m["mes"] = pd.to_datetime(m.fecha, utc=True).dt.strftime("%Y-%m")
print("Titulares nuevos (fracción media del once local) por mes:")
print(m.groupby("mes").loc_pn_frac.agg(["mean", "count"]).round(3).to_string())
print(f"cobertura en partidos fijos: {bc.loc[fijo, 'loc_pn_frac'].notna().mean()*100:.1f}%\n")

y = prueba[OBJ].values.astype(int)
pmer = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS[OBJ])
cc = prueba.match_id.isin(pmer.index).values
pm = pmer.reindex(prueba.match_id).values
bm = 2 * (pm - y) ** 2
ini = (pd.to_datetime(prueba.fecha, utc=True) >= INICIO_2627).values

for extras in (["elo", "cp_ataque"], ["elo"]):
    nA = "base_clasica+" + "+".join(extras)
    sA = brier_partido(predecir(cols_de("base_clasica", extras), ent_sel, sel), sel)
    sB = brier_partido(predecir(cols_de("base_clasica", extras + ["plantilla_nueva"]), ent_sel, sel), sel)
    pA = predecir(cols_de("base_clasica", extras), ent_fin, prueba)
    pB = predecir(cols_de("base_clasica", extras + ["plantilla_nueva"]), ent_fin, prueba)
    bA, bB = 2 * (pA - y) ** 2, 2 * (pB - y) ** 2
    print(f"== {nA}  vs  +plantilla_nueva (positivo = la nueva variable ayuda) ==")
    print(f"  selección ({len(sel)}, mar-abr 2026)          {sig(sA - sB):+.2f}s")
    print(f"  prueba, final 2025/26 ({(~ini).sum()})         {sig(bA[~ini] - bB[~ini]):+.2f}s")
    print(f"  prueba, inicio 2026/27 ({ini.sum()})        {sig(bA[ini] - bB[ini]):+.2f}s")
    print(f"  prueba, todo ({len(y)})                  {sig(bA - bB):+.2f}s")
    for n, p, b in ((nA, pA, bA), ("+plantilla_nueva", pB, bB)):
        print(f"  contra el mercado {n:28s} {sig(bm[cc] - b[cc]):+.2f}s  acierto "
              f"{((p[cc] > .5) == y[cc]).mean()*100:.1f}%")
    print()
print(f"mercado acierto {((pm[cc] > .5) == y[cc]).mean()*100:.1f}%  ({cc.sum()} con cuota)")
