"""
Ranking de cada variable del usuario y su combinación
porterías + g/a + h2h (24/09/2026), sobre la prueba final de
seleccion_combinaciones.py. OJO: estas configs se eligen DESPUÉS de haber
visto la prueba, así que sus números están algo inflados por selección.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
src = open("scripts/seleccion_combinaciones.py", encoding="utf-8").read().split("# ---------- 1.")[0]
with contextlib.redirect_stdout(io.StringIO()):
    exec(src)
y = prueba[OBJ].values.astype(int)
pmer = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS[OBJ])
cc = prueba.match_id.isin(pmer.index).values
pm = pmer.loc[prueba.match_id[cc]].values
bm = 2 * (pm - y[cc]) ** 2
bb = lambda nuc, ex: brier_partido(predecir(cols_de(nuc, ex), ent_fin, prueba), prueba)

print("== RANKING (prueba final, positivo = ayuda) ==")
for nuc in ("base_clasica", "base_cf"):
    ref, todo = bb(nuc, []), bb(nuc, EXTRAS)
    print(f"-- sobre {nuc} --")
    for e in EXTRAS:
        sola = sig(ref - bb(nuc, [e]))
        quitar = sig(bb(nuc, [x for x in EXTRAS if x != e]) - todo)
        print(f"  {e:13s} sola {sola:+.2f}s   quitarla del conjunto {quitar:+.2f}s")
print(f"base_cf vs base_clasica (solas): {sig(bb('base_clasica', []) - bb('base_cf', [])):+.2f}s\n")

U = ["cp_defensa", "cp_ataque", "h2h_reciente"]
cfg = {"base_clasica+elo (referencia)": ("base_clasica", ["elo"]),
       "base_clasica+elo+g/a": ("base_clasica", ["elo", "cp_ataque"]),
       "USUARIO base_clasica+porterias+g/a+h2h": ("base_clasica", U),
       "USUARIO base_clasica+elo+porterias+g/a+h2h": ("base_clasica", ["elo"] + U),
       "USUARIO base_cf+porterias+g/a+h2h": ("base_cf", U)}
P = {n: predecir(cols_de(*c), ent_fin, prueba) for n, c in cfg.items()}
ref = 2 * (P["base_clasica+elo (referencia)"] - y) ** 2
print("== COMBINACIONES ==")
for n, p in P.items():
    b = 2 * (p - y) ** 2
    vs = sig(ref - b) if n != "base_clasica+elo (referencia)" else 0.0
    print(f"{n:44s} vs ref {vs:+.2f}s  vs mercado {sig(bm - b[cc]):+.2f}s  "
          f"acierto {((p[cc] > .5) == y[cc]).mean()*100:.1f}%")
print(f"mercado: acierto {((pm > .5) == y[cc]).mean()*100:.1f}%   n={len(y)} ({cc.sum()} con cuota)")
