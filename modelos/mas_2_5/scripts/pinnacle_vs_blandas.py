"""
Casas blandas contra Pinnacle en Más/Menos 2.5 (25/09/2026). Sin modelo.

Pinnacle es la casa más afinada: su probabilidad sin margen se toma como la
"justa". Se apuesta donde otra cuota paga más que esa probabilidad justa
(valor = p_justa x cuota - 1 > umbral). Se miran las tres temporadas POR
SEPARADO: una estrategia real debe salir en las tres, no en la suma.

Casas: Bet365 (misma foto que Pinnacle en football-data: cuotas del viernes
para el fin de semana, así que son casi simultáneas), la media (Avg) y la
máxima de ~40 casas (Max, optimista: puede mezclar momentos distintos).
Comprobación extra: si de verdad hay valor, las apuestas deberían batir
también la cuota de CIERRE de Pinnacle (CLV), no solo ganar por suerte.
"""
import glob
import numpy as np, pandas as pd

DIV = {"E0": "Premier", "SP1": "La Liga", "SP2": "Segunda", "I1": "Serie A", "D1": "Bundesliga", "F1": "Ligue 1"}
filas = []
for f in sorted(glob.glob("data/football_data/*.csv")):
    d = pd.read_csv(f, encoding="utf-8-sig", on_bad_lines="skip").dropna(subset=["FTHG", "FTAG"])
    div, t = f.split("/")[-1][:-4].split("_")
    d["liga"], d["temporada"] = DIV[div], f"20{t[:2]}/{t[2:]}"
    filas.append(d)
d = pd.concat(filas, ignore_index=True)
d["y"] = (d.FTHG + d.FTAG > 2.5).astype(int)
inv_o, inv_u = 1 / d["P>2.5"], 1 / d["P<2.5"]
d["p_justa"] = inv_o / (inv_o + inv_u)
d["margen_pin"] = inv_o + inv_u - 1
d = d.dropna(subset=["p_justa"])
tiene_cierre = d["PC>2.5"].notna() & d["PC<2.5"].notna()
ic_o, ic_u = 1 / d["PC>2.5"], 1 / d["PC<2.5"]
d["p_cierre"] = ic_o / (ic_o + ic_u)

print(f"{len(d)} partidos con Pinnacle; margen medio de Pinnacle {d.margen_pin.mean()*100:.2f}%")
print(d.groupby("temporada").size().to_string(), "\n")


def sig(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else np.nan


print(f"{'casa':7s} {'umbral':>6s} {'temporada':>9s} {'apuestas':>8s} {'rentab.':>8s} {'±':>6s} {'sigmas':>7s} {'bate cierre':>11s}")
for casa in ("B365", "Avg", "Max"):
    for umbral in (0.0, 0.02, 0.04):
        for temp in sorted(d.temporada.unique()) + ["todas"]:
            g = d if temp == "todas" else d[d.temporada == temp]
            vo = g.p_justa * g[f"{casa}>2.5"] - 1
            vu = (1 - g.p_justa) * g[f"{casa}<2.5"] - 1
            over, under = (vo > umbral) & (vo >= vu), (vu > umbral) & (vu > vo)
            ret = np.concatenate([(g.y[over] * g[f"{casa}>2.5"][over] - 1).values,
                                  ((1 - g.y[under]) * g[f"{casa}<2.5"][under] - 1).values])
            # CLV: ¿la cuota cogida paga más que la probabilidad justa de CIERRE?
            clv = np.concatenate([(g.p_cierre[over] * g[f"{casa}>2.5"][over] - 1).dropna().values,
                                  ((1 - g.p_cierre[under]) * g[f"{casa}<2.5"][under] - 1).dropna().values])
            if len(ret) < 20:
                print(f"{casa:7s} {umbral:>6.0%} {temp:>9s} {len(ret):8d}  (pocas)")
                continue
            print(f"{casa:7s} {umbral:>6.0%} {temp:>9s} {len(ret):8d} {ret.mean()*100:+7.2f}% "
                  f"{ret.std(ddof=1)/np.sqrt(len(ret))*100:5.2f} {sig(ret):+6.2f}s "
                  f"{(clv > 0).mean()*100 if len(clv) else np.nan:9.0f}%")
        print()
