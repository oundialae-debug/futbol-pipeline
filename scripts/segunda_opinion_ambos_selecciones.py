"""
Segunda opinión de ambos marcan para Inglaterra-España y Chequia-Croacia
(26/09/2026) con la IA de ambos marcan del proyecto, variante "solo precio"
(la más elegida en walk_forward_ambos.py: 10 de 21 meses).

Entrenada con TODOS los partidos de club con precio previo de football-data
(los 7 rasgos mkt_, 5 semillas). Para esta noche los rasgos salen de las cuotas
cosechadas hoy (mediana de casas sin margen, data/nations_league_hoy.csv):
1X2, más de 2.5 y el ambos marcan implícito del Poisson ajustado a ambos.

Límites: solo ha visto partidos de club; en esencia es el mercado
reinterpretado con lo aprendido en clubes, no información nueva. Además se
enseña cómo le fue a esta variante contra el precio en los clubes (último 25%).
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M
from apuesta_ambos_marcan import rasgos_mercado
from btts_implicito import ajustar
from cuota_como_variable import MKT

SEMILLAS = (0, 1, 2, 3, 4)
PARTIDOS = ["England - Spain", "Czech Republic - Croatia"]


def rasgos_hoy(partido):
    c = pd.read_csv("data/nations_league_hoy.csv")
    c = c[c.partido == partido]
    def sin_margen(mercado):
        g = c[c.mercado == mercado]
        tot = (1 / g.mediana).sum()
        return {l: 1 / o / tot for l, o in zip(g.lado, g.mediana)}
    r, o = sin_margen("Full Time Result"), sin_margen("Total Goals 2.5")
    btts = sin_margen("Both Teams To Score").get("Yes", np.nan)
    f = {"mkt_p_local": r["Home"], "mkt_p_empate": r["Draw"], "mkt_p_visitante": r["Away"],
         "mkt_p_mas_2_5": o["Over"]}
    f["mkt_lambda_l"], f["mkt_lambda_v"] = ajustar(f["mkt_p_local"], f["mkt_p_empate"],
                                                   f["mkt_p_visitante"], f["mkt_p_mas_2_5"])
    f["mkt_p_btts_implicito"] = (1 - np.exp(-f["mkt_lambda_l"])) * (1 - np.exp(-f["mkt_lambda_v"]))
    return f, btts


def main():
    hist = M.cargar()
    bt = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    bt = bt.merge(rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    bt = bt[bt.ambos_marcan.notna() & bt[MKT].notna().all(axis=1)].reset_index(drop=True)
    y = bt.ambos_marcan.values.astype(int)

    # control en clubes: último 25% fuera de muestra, contra el propio implícito
    corte = int(len(bt) * 0.75)
    ent, val = bt.iloc[:corte], bt.iloc[corte:]
    p_val = np.mean([M.probabilidades(M.entrenar(ent[MKT].values, y[:corte], 2, semilla=s),
                                      val[MKT].values, 2)[:, 1] for s in SEMILLAS], axis=0)
    yv = y[corte:]
    d = 2 * (val.mkt_p_btts_implicito.values - yv) ** 2 - 2 * (p_val - yv) ** 2
    print(f"Clubes: {len(bt)} partidos con precio previo. Control (último 25%, {len(val)}): "
          f"IA solo precio vs ambos marcan implícito del precio {d.mean()/(d.std(ddof=1)/np.sqrt(len(d))):+.2f}s")

    modelos = [M.entrenar(bt[MKT].values, y, 2, semilla=s) for s in SEMILLAS]
    lineas = ["", "## Segunda opinión: IA de ambos marcan (variante solo precio)", "",
              f"Entrenada con {len(bt)} partidos de club; rasgos de esta noche sacados de las cuotas "
              "de hoy. Solo ha visto clubes: es el mercado reinterpretado, no información nueva. "
              f"Control en clubes (último 25%): {d.mean()/(d.std(ddof=1)/np.sqrt(len(d))):+.2f}s "
              "frente al ambos marcan implícito del propio precio.", "",
              "| partido | IA (solo precio) | implícito del 1X2+2.5 | mercado ambos marcan | modelo de selecciones |",
              "|---|---|---|---|---|"]
    for partido in PARTIDOS:
        f, btts_mkt = rasgos_hoy(partido)
        x = np.array([[f[c] for c in MKT]])
        p = float(np.mean([M.probabilidades(m, x, 2)[:, 1] for m in modelos]))
        print(f"{partido}: IA {p*100:.1f}%  implícito {f['mkt_p_btts_implicito']*100:.1f}%  "
              f"mercado {btts_mkt*100:.1f}%  (lambdas {f['mkt_lambda_l']:.2f}-{f['mkt_lambda_v']:.2f})")
        lineas.append(f"| {partido} | {p*100:.1f}% | {f['mkt_p_btts_implicito']*100:.1f}% | "
                      f"{btts_mkt*100:.1f}% | ver arriba |")
    with open("pronosticos_selecciones.md", "a") as fh:
        fh.write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    main()
