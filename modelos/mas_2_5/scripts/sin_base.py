"""
Modelos SIN ningún bloque de base (petición del usuario, 24/09/2026): solo
combinaciones de elo, tabla, cp_ataque, cp_defensa, cp_minutos y h2h_reciente
(63 combinaciones + liga_id). Mismo protocolo que seleccion_combinaciones.py:
se elige en el tramo de selección y la prueba final se mira una vez.
"""
import sys, io, contextlib, itertools, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
src = open("scripts/seleccion_combinaciones.py", encoding="utf-8").read().split("# ---------- 1.")[0]
with contextlib.redirect_stdout(io.StringIO()):
    exec(src)
cols = lambda ex: list(dict.fromkeys(["liga_id"] + sum((G[e] for e in ex), [])))
filas = []
for k in range(1, len(EXTRAS) + 1):
    for ex in itertools.combinations(EXTRAS, k):
        filas.append(("+".join(ex), brier_partido(predecir(cols(ex), ent_sel, sel), sel).mean()))
t = pd.DataFrame(filas, columns=["config", "brier_sel"]).sort_values("brier_sel").reset_index(drop=True)
t.to_csv("data/sin_base.csv", index=False)
print("Top 5 en selección (sin base):")
print(t.head(5).to_string(index=False))
elegido = t.config.iloc[0].split("+")

y = prueba[OBJ].values.astype(int)
pmer = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS[OBJ])
cc = prueba.match_id.isin(pmer.index).values
pm = pmer.loc[prueba.match_id[cc]].values
bm = 2 * (pm - y[cc]) ** 2
cfg = {"base_clasica+elo+g/a (mejor con base)": cols_de("base_clasica", ["elo", "cp_ataque"]),
       f"SIN BASE elegido ({'+'.join(elegido)})": cols(elegido),
       "SIN BASE todo (las 6)": cols(EXTRAS),
       "SIN BASE elo+tabla+g/a": cols(["elo", "tabla", "cp_ataque"])}
P = {n: predecir(c, ent_fin, prueba) for n, c in cfg.items()}
ref = 2 * (P["base_clasica+elo+g/a (mejor con base)"] - y) ** 2
print(f"\nPRUEBA FINAL {len(y)} partidos ({cc.sum()} con cuota)")
for n, p in P.items():
    b = 2 * (p - y) ** 2
    vs = sig(ref - b) if b is not ref else 0.0
    print(f"{n:52s} vs mejor con base {vs:+.2f}s  vs mercado {sig(bm - b[cc]):+.2f}s  "
          f"acierto {((p[cc] > .5) == y[cc]).mean()*100:.1f}%")
print(f"mercado acierto {((pm > .5) == y[cc]).mean()*100:.1f}%")
