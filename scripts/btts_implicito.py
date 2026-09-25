"""
Ambos marcan IMPLÍCITO en el precio de 1X2 y más/menos 2.5 (25/09/2026).

football-data.co.uk no trae ambos marcan. Pero el 1X2 y el más/menos 2.5 de
cierre dicen cuántos goles espera el mercado de cada equipo. Por partido se
buscan los dos goles esperados (lambda local, lambda visitante) de un
Poisson independiente que mejor reproducen p_local, p_empate, p_visitante y
p_mas_2_5, y de ahí:  P(ambos marcan) = (1 - e^-lambda_l)(1 - e^-lambda_v).

El Poisson independiente es una aproximación (subestima empates y 0-0). Se
comprueba ANTES de usarlo contra las cuotas reales de ambos marcan
cosechadas de Highlightly, partido a partido.

Salida: añade lambda_l, lambda_v y p_btts_implicito a
data/cuotas_historicas_fd.csv.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

RUTA_FD = "data/cuotas_historicas_fd.csv"
G = np.arange(11)


def probs(ll, lv):
    m = np.outer(poisson.pmf(G, ll), poisson.pmf(G, lv))
    tot = np.add.outer(G, G)
    return (np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum(), m[tot > 2.5].sum())


def ajustar(p_l, p_e, p_v, p_o):
    obj = np.array([p_l, p_e, p_v, p_o])
    ok = ~np.isnan(obj)

    def err(x):
        return ((np.array(probs(*np.exp(x))) - obj)[ok] ** 2).sum()
    r = minimize(err, np.log([1.4, 1.1]), method="Nelder-Mead",
                 options={"xatol": 1e-4, "fatol": 1e-9})
    return np.exp(r.x)


def main():
    fd = pd.read_csv(RUTA_FD)
    lam = [ajustar(a, b, c, d) if not np.isnan([a, b, c]).any() else (np.nan, np.nan)
           for a, b, c, d in zip(fd.p_local, fd.p_empate, fd.p_visitante, fd.p_mas_2_5)]
    fd["lambda_l"], fd["lambda_v"] = zip(*lam)
    fd["p_btts_implicito"] = (1 - np.exp(-fd.lambda_l)) * (1 - np.exp(-fd.lambda_v))
    fd.to_csv(RUTA_FD, index=False)
    print(f"Ajustados {fd.lambda_l.notna().sum()} partidos. Escrito {RUTA_FD}")

    # comprobación contra ambos marcan REAL cosechado
    import evaluar_mercados as EM
    pm = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS["ambos_marcan"])
    h = pd.read_csv("data/historico_partidos.csv").set_index("match_id")
    d = fd.set_index("match_id").join(pm.rename("p_btts_real"), how="inner").dropna(
        subset=["p_btts_implicito", "p_btts_real"])
    d = d[d.index.isin(h.index)]
    y = ((h.loc[d.index, "goles_l"] > 0) & (h.loc[d.index, "goles_v"] > 0)).astype(int).values
    dif = d.p_btts_implicito - d.p_btts_real
    b_imp = 2 * (d.p_btts_implicito.values - y) ** 2
    b_real = 2 * (d.p_btts_real.values - y) ** 2
    e = b_real - b_imp
    print(f"\nComprobación contra ambos marcan REAL ({len(d)} partidos con las dos cosas):")
    print(f"  diferencia media {dif.mean()*100:+.1f} puntos (sesgo), "
          f"{dif.abs().mean()*100:.1f} puntos en valor absoluto")
    print(f"  correlación {np.corrcoef(d.p_btts_implicito, d.p_btts_real)[0,1]:.3f}")
    print(f"  Brier implícito {b_imp.mean():.4f}  real {b_real.mean():.4f}  "
          f"(implícito vs real: {e.mean()/(e.std(ddof=1)/np.sqrt(len(e))):+.2f}s)")
    print(f"  tasa real de ambos marcan {y.mean()*100:.1f}%, implícito medio "
          f"{d.p_btts_implicito.mean()*100:.1f}%, real medio {d.p_btts_real.mean()*100:.1f}%")


if __name__ == "__main__":
    main()
