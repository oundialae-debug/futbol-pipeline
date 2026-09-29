"""
Evaluación mes a mes de Colombia Primera B (sin cuotas: solo brazo "juego").
Referencia: tasa de la liga en los 365 días anteriores. Dos entrenamientos:
con las 4 ligas juntas y solo con la Primera B.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelo_goles as G

d = G.construir()
cj = G.columnas_juego(d)
meses = sorted(m for m in d[d.liga == "COLB"].mes.unique() if m >= "2024-01")
out = []
for mes in meses:
    pasado, test = d[d.mes < mes], d[(d.mes == mes) & (d.liga == "COLB")]
    for obj, y in G.OBJETIVOS.items():
        t = test[["fecha", "Home", "Away", y]].rename(columns={y: "y"}).assign(objetivo=obj)
        ult = pasado[(pasado.liga == "COLB") & (pasado.fecha > test.fecha.min() - pd.Timedelta(days=365))]
        t["base"] = ult[y].mean()
        t["juntas"] = G.predecir(pasado, test, cj, y)
        t["sola"] = G.predecir(pasado[pasado.liga == "COLB"], test, cj, y)
        out.append(t)
    print(" ", mes, len(test), flush=True)
r = pd.concat(out)
r.to_csv(os.path.join(G.CARPETA, "data", "walk_forward_colb.csv"), index=False)
lin = ["# Colombia Primera B: evaluación mes a mes (sin cuotas)\n",
       "| objetivo | n | tasa | Brier base | Brier juntas | Brier sola | juntas vs base | sola vs base |", "|---|---|---|---|---|---|---|---|"]
for obj in G.OBJETIVOS:
    s = r[r.objetivo == obj]
    e = {b: (s[b] - s.y) ** 2 for b in ("base", "juntas", "sola")}
    lin.append(f"| {obj} | {len(s)} | {s.y.mean():.3f} | {e['base'].mean():.4f} | {e['juntas'].mean():.4f} | "
               f"{e['sola'].mean():.4f} | {G.sig(e['base']-e['juntas']):+.2f}s | {G.sig(e['base']-e['sola']):+.2f}s |")
txt = "\n".join(lin) + "\n"
open(os.path.join(G.CARPETA, "evaluacion_colb.md"), "w").write(txt)
print(txt)
