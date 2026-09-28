"""NBA ganador (moneyline): modelo contra el cierre de MGM, apostando solo con cuota >= 1.4.

Mismos rasgos que totales (rasgos_nba.py), reentreno mensual, prueba 2024-25 y 2025-26.
Dos versiones: A) sin el precio; B) con el precio como variable (lo que mas ayudo en futbol).
Brier emparejado por partido contra la probabilidad del mercado sin margen.
"""
import numpy as np
import pandas as pd
import xgboost as xgb

import rasgos_nba

x, R = rasgos_nba.construir()
x = x.dropna(subset=["money_home_decimal_odds", "money_away_decimal_odds"]).reset_index(drop=True)
x["gana_local"] = (x.homeScore > x.awayScore).astype(int)
ih, ia = 1 / x.money_home_decimal_odds, 1 / x.money_away_decimal_odds
x["p_mkt"] = ih / (ih + ia)
x["logit_mkt"] = np.log(x.p_mkt / (1 - x.p_mkt))
F = ["l_" + r for r in R] + ["v_" + r for r in R]
PARAMS = dict(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.8,
              colsample_bytree=0.8, min_child_weight=20, reg_lambda=5)
x["mes"] = x.fecha.dt.to_period("M")
pru = x[x.temp >= 2025].copy()
print(f"partidos: {len(x)}, prueba {len(pru)}")


def walk_forward(cols):
    p = pd.Series(index=pru.index, dtype=float)
    for mes in sorted(pru.mes.unique()):
        ent = x[x.fecha < mes.start_time]
        idx = pru.index[pru.mes == mes]
        ps = [xgb.XGBClassifier(**PARAMS, random_state=s).fit(ent[cols], ent.gana_local)
              .predict_proba(x.loc[idx, cols])[:, 1] for s in range(5)]
        p[idx] = np.mean(ps, axis=0)
    return p


def informe(nombre, p):
    y = pru.gana_local
    d = (pru.p_mkt - y) ** 2 - (p - y) ** 2  # >0: el modelo mejor que el mercado
    print(f"\n### {nombre}")
    print(f"  Brier modelo {((p-y)**2).mean():.4f} | mercado {((pru.p_mkt-y)**2).mean():.4f} | "
          f"diferencia {d.mean()/d.std(ddof=1)*np.sqrt(len(d)):+.2f}s")
    print(f"  acierto del favorito: modelo {((p > .5) == y).mean():.1%} | mercado {((pru.p_mkt > .5) == y).mean():.1%}")
    ev_l = p * pru.money_home_decimal_odds - 1
    ev_v = (1 - p) * pru.money_away_decimal_odds - 1
    local = ev_l >= ev_v
    ev = np.where(local, ev_l, ev_v)
    cuota = np.where(local, pru.money_home_decimal_odds, pru.money_away_decimal_odds)
    gana = np.where(local, y == 1, y == 0)
    for u in [0, 0.03, 0.06]:
        for lo, hi in [(1.4, 99), (1.4, 2.5)]:
            k = (ev > u) & (cuota >= lo) & (cuota < hi)
            g = np.where(gana[k], cuota[k] - 1, -1.0)
            if len(g) < 30:
                continue
            print(f"  VE>{u:.0%} cuota {lo}-{hi}: n={len(g):4d} acierto {gana[k].mean():.1%} "
                  f"cuota media {cuota[k].mean():.2f} roi {g.mean():+.2%} ({g.mean()/g.std(ddof=1)*np.sqrt(len(g)):+.2f}s)")


NUEVAS = ["f_prod", "f_pm", "min_conocidos", "elo"]
VIEJAS = [f for f in F if not any(f.endswith(n) for n in NUEVAS)]
informe("A0) sin precio, sin elo ni calidad (como antes)", walk_forward(VIEJAS))
informe("A1) sin precio, con elo y calidad de los que juegan", walk_forward(F))
informe("B1) con precio, con elo y calidad", walk_forward(F + ["logit_mkt"]))
