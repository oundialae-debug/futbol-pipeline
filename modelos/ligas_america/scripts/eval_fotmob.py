"""
¿Mejoran las variables de FotMob (xG, xGOT, ocasiones, remates a puerta,
toques en área, nota) al modelo completo? Mismo protocolo que modelo_goles:
mes a mes, entrenando con todo lo anterior (3 ligas juntas), Brier
emparejado partido a partido en las ligas que tengan FotMob.
env LIGAS_PRUEBA=ARG[,BRA,MEX]  DESDE=2024-07
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelo_goles as G, fotmob_rasgos as R

PRUEBA = os.environ.get("LIGAS_PRUEBA", "ARG").split(",")
DESDE = os.environ.get("DESDE", "2024-07")

d = G.construir()
d = d[d.liga != "COLB"].reset_index(drop=True)
d, n = R.rasgos(d)
print(f"{n} partidos de FotMob cruzados")
cj, fm = G.columnas_juego(d), R.columnas(d)
brazos = {"completo": G.MKT + cj, "completo_fm": G.MKT + cj + fm, "mercado_fm": G.MKT + fm}
out = []
for mes in sorted(m for m in d.mes.unique() if m >= DESDE):
    pasado = d[d.mes < mes]
    test = d[(d.mes == mes) & d.liga.isin(PRUEBA) & d.m_pl.notna() & d.fm_l_m_af_xg.notna() & d.fm_v_m_af_xg.notna()]
    if test.empty:
        continue
    for obj, y in G.OBJETIVOS.items():
        t = test[["liga", "fecha", "Home", "Away", y]].rename(columns={y: "y"}).assign(objetivo=obj, mes=mes)
        ult = pasado[pasado.fecha > test.fecha.min() - pd.Timedelta(days=365)]
        t["base"] = test.liga.map(ult.groupby("liga")[y].mean()).values
        for b, cols in brazos.items():
            t[b] = G.predecir(pasado, test, cols, y)
        out.append(t)
    print(" ", mes, len(test), flush=True)
r = pd.concat(out)
r.to_csv(os.path.join(G.CARPETA, "data", "walk_forward_fotmob.csv"), index=False)
lin = ["# Con y sin FotMob (xG, xGOT, ocasiones, remates a puerta, toques en área, nota)\n",
       f"Mes a mes desde {DESDE}, entreno con las 3 ligas, prueba en {PRUEBA} (partidos con FotMob en los dos equipos). "
       "Sigmas del Brier emparejado, positivo = el brazo de la izquierda es mejor.\n",
       "| objetivo | liga | n | Brier base | completo | completo+FotMob | mercado+FotMob | FotMob vs sin | completo+FotMob vs base |",
       "|---|---|---|---|---|---|---|---|---|"]
for obj in G.OBJETIVOS:
    for liga in PRUEBA + (["todas"] if len(PRUEBA) > 1 else []):
        s = r[(r.objetivo == obj) & ((r.liga == liga) | (liga == "todas"))]
        e = {b: (s[b] - s.y) ** 2 for b in ["base"] + list(brazos)}
        lin.append(f"| {obj} | {liga} | {len(s)} | {e['base'].mean():.4f} | {e['completo'].mean():.4f} | "
                   f"{e['completo_fm'].mean():.4f} | {e['mercado_fm'].mean():.4f} | "
                   f"{G.sig(e['completo'] - e['completo_fm']):+.2f}s | {G.sig(e['base'] - e['completo_fm']):+.2f}s |")
txt = "\n".join(lin) + "\n"
open(os.path.join(G.CARPETA, "evaluacion_fotmob.md"), "w").write(txt)
print(txt)
