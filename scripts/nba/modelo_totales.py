"""NBA totales: modelo con ritmo, eficiencia, descanso, bajas y arbitros, contra el cierre de MGM.

Datos: Kaggle eoinamoore (box-score por equipo y jugador, 2021-22..2025-26; cruzado con
nuestra API: marcador identico en el 99.97% de 6.921 partidos) + cierre MGM (Kaggle).
Sin gastar API.

Regla anti-fuga: todo rasgo de un partido sale SOLO de partidos anteriores (shift antes
de acumular). Las bajas usan quien jugo de verdad: en la NBA las bajas se conocen antes
del salto (lista de inactivos) y el cierre ya las lleva dentro, asi que es la misma
informacion que tiene el precio contra el que se compara.

Prueba: reentreno MENSUAL (lo que funciono en futbol), prueba 2024-25 y 2025-26.
"""
import os
import numpy as np
import pandas as pd
import xgboost as xgb

import rasgos_nba

x, R = rasgos_nba.construir()
MERCADO = os.environ.get("MERCADO", "totales")
if MERCADO == "totales":
    x["linea"] = x.total_over_points
    x["total"] = x.homeScore + x.awayScore
    x["cuota_mas"], x["cuota_menos"] = x.total_over_decimal_odds, x.total_under_decimal_odds
else:  # handicap: "total" = diferencia local-visitante; "linea" = diferencia que da la casa
    x = x.dropna(subset=["spread_home_points"]).reset_index(drop=True)
    x["linea"] = -x.spread_home_points
    x["total"] = x.homeScore - x.awayScore
    x["cuota_mas"], x["cuota_menos"] = x.spread_home_decimal_odds, x.spread_away_decimal_odds
x["resto"] = x.total - x.linea
print(f"MERCADO: {MERCADO}")
print(f"partidos con linea y rasgos: {len(x)} | con arbitros: {x.arbitros.notna().mean():.0%}")

F_SIN = ["l_" + r for r in R] + ["v_" + r for r in R] + ["arbitros"]
CONFIGS = {
    "base (ritmo, eficiencia, descanso)": [f for f in F_SIN if "baja" not in f and f != "arbitros"],
    "+bajas": [f for f in F_SIN if f != "arbitros"],
    "+bajas+arbitros": F_SIN,
    "+bajas+elo+calidad de los que juegan": [f for f in F_SIN if f != "arbitros"],
}
NUEVAS = ["f_prod", "f_pm", "min_conocidos", "elo"]
for k in list(CONFIGS)[:3]:
    CONFIGS[k] = [f for f in CONFIGS[k] if not any(f.endswith(n) for n in NUEVAS)]
PARAMS = dict(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.8,
              colsample_bytree=0.8, min_child_weight=20, reg_lambda=5)


def walk_forward(feats, objetivo, con_linea):
    cols = feats + (["linea"] if con_linea else [])
    x["mes"] = x.fecha.dt.to_period("M")
    pru = x[x.temp >= 2025]
    preds = pd.Series(index=pru.index, dtype=float)
    for mes in sorted(pru.mes.unique()):
        ent = x[x.fecha < mes.start_time]
        idx = pru.index[pru.mes == mes]
        ps = []
        for semilla in range(5):
            m = xgb.XGBRegressor(**PARAMS, random_state=semilla)
            m.fit(ent[cols], ent[objetivo])
            ps.append(m.predict(x.loc[idx, cols]))
        preds[idx] = np.mean(ps, axis=0)
    return preds


def evaluar(nombre, dif):
    """dif = prediccion de (total - linea). >0 apuesta over."""
    s = x.loc[dif.index]
    c = np.corrcoef(dif, s.resto)[0, 1]
    # Spearman ademas de Pearson: con colas gordas (|real - linea| > 40 en ~3% de partidos)
    # Pearson engana. El 28/09 dio +0.100 (+4.38s) con Spearman 0.005 y deciles planos.
    cs = pd.Series(np.asarray(dif)).corr(pd.Series(np.asarray(s.resto)), method="spearman")
    print(f"\n{nombre}: corr(pred, real-linea) {c:+.3f} ({c*np.sqrt(len(s)):+.2f}s), "
          f"Spearman {cs:+.3f} ({cs*np.sqrt(len(s)):+.2f}s), n={len(s)}")
    for u in [0, 1, 2, 3, 4]:
        k = dif.abs() > u
        ss, dd = s[k], dif[k]
        over = dd > 0
        gana = np.where(over, ss.total > ss.linea, ss.total < ss.linea)
        empate = ss.total == ss.linea
        cuota = np.where(over, ss.cuota_mas, ss.cuota_menos)
        gan = np.where(empate, 0, np.where(gana, cuota - 1, -1.0))
        if len(gan) < 30:
            continue
        print(f"   |pred| > {u}: n={len(gan):4d} acierto {gana[~empate].mean():.1%} "
              f"roi {gan.mean():+.2%} ({gan.mean()/gan.std(ddof=1)*np.sqrt(len(gan)):+.2f}s)")


rmse = lambda e: float(np.sqrt(np.mean(e ** 2)))
pru = x[x.temp >= 2025]
print(f"prueba (2024-25 y 2025-26): {len(pru)} partidos | RMSE de la linea {rmse(pru.resto):.2f}")
for nombre, feats in CONFIGS.items():
    if os.environ.get("SOLO") and os.environ["SOLO"] not in nombre:
        continue
    p_total = walk_forward(feats, "total", con_linea=False)
    print(f"\n### {nombre} ({len(feats)} rasgos)  RMSE modelo {rmse(p_total - pru.total):.2f}")
    evaluar("  A) modelo sin linea: pred_total - linea", p_total - pru.linea)
    p_resto = walk_forward(feats, "resto", con_linea=True)
    evaluar("  B) modelo con linea, predice (real - linea)", p_resto)
    if os.environ.get("GUARDAR") and "calidad" in nombre:
        pru.assign(p_resto=p_resto, p_total=p_total).to_pickle(os.environ["GUARDAR"])
