"""
Modelo de ganador de partido con variables que el Elo no ve, contra el
cierre. ATP y WTA juntos (con marca de circuito).

Protocolo fijado ANTES de mirar resultados (30/09/2026):
- Cada configuración (mercado + grupos de variables) se entrena con
  2020-2022 y se puntúa en 2023. La de mejor log-loss en 2023 es la ELEGIDA.
- La elegida se reentrena con 2020-2023 y se juzga en 2024-2025 (contra
  Pinnacle) y 2026 (contra Betfair Exchange). Las demás se enseñan en la
  prueba solo como información: no cuentan.
- Comparador exigente: "mercado recalibrado" (logística sobre logit del
  cierre, corrige el sesgo favorito-marginado). Una variable solo vale si
  mejora ESO. También se da la comparación con el mercado en bruto.
- Partidos completos para métricas; apuestas con retiradas (gana quien avanza).
- Modelos: logística con L2 (variables estandarizadas, huecos a la media) y
  XGBoost (5 semillas, parámetros conservadores fijos).

Escribe data/tenis/modelo_tenis.md.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

sys.path.insert(0, "modelos/tenis/scripts")
import cruce_fuentes as C  # noqa: E402
import elo_tenis as E  # noqa: E402
import evaluar_elo as V  # noqa: E402
import rasgos_tenis as R  # noqa: E402

D = "data/tenis"
C_ELO = {"atp": 250.0, "wta": 350.0}          # elegidos en evaluar_elo.py con 2020-2023
GRUPOS = {
    "elo": ["elo", "elo_s"],
    "saque": ["spw", "rpw", "ace", "df", "in1", "bps", "n_saque"],
    "fatiga": ["t_partidos", "t_sets", "t_min", "min_ant", "p30", "descanso"],
    "perfil": ["rank", "pts", "edad", "alt", "zurdo"],
    "h2h": ["h2h"],
}
CONFIGS = [[], ["elo"], ["saque"], ["fatiga"], ["perfil"], ["h2h"],
           ["elo", "saque"], ["saque", "fatiga"], ["elo", "saque", "fatiga"], list(GRUPOS)]


def construir():
    filas = []
    for circuito in ("atp", "wta"):
        hist = E.historial(circuito)
        hist["kw"] = hist["winner_name"].map(C.clave_completo)
        hist["kl"] = hist["loser_name"].map(C.clave_completo)
        elo = E.calcular(hist, C_ELO[circuito])
        ras = R.calcular(hist)
        ras["elo_w"], ras["elo_l"] = elo["elo_w"], elo["elo_l"]
        ras["elo_s_w"], ras["elo_s_l"] = elo["elo_sw"], elo["elo_sl"]
        td = C.cargar_td(circuito)
        td = td[td["Comment"] != "Walkover"].copy()
        td["p_mkt"], td["fuente_mkt"] = V.mercado(td)
        f = hist[["kw", "kl", "inicio"]].copy()
        f["fila_hist"] = hist.index
        ok, _, _ = C.cruzar(td, f)
        ok = ok.drop_duplicates("i")
        ok = ok[ok["p_mkt"].notna()].reset_index(drop=True)
        r = ras.loc[ok["fila_hist"].values].reset_index(drop=True)
        ok = pd.concat([ok, r], axis=1)
        ok["wta"] = float(circuito == "wta")
        ok["bo5"] = (pd.to_numeric(ok["Best of"], errors="coerce") == 5).astype(float)
        filas.append(ok)
    d = pd.concat(filas, ignore_index=True)
    # orientación al azar: A gana con prob. 1/2
    a_gana = np.random.default_rng(11).random(len(d)) < 0.5
    d["y"] = a_gana.astype(int)
    d["m"] = V.logit(np.where(a_gana, d["p_mkt"], 1 - d["p_mkt"]))
    signo = np.where(a_gana, 1.0, -1.0)
    for vs in GRUPOS.values():
        for v in vs:
            d[f"d_{v}"] = signo * (d[f"{v}_w"] - d[f"{v}_l"])
    d["d_zurdo_x"] = d["zurdo_w"] * (1 - d["zurdo_l"]) + d["zurdo_l"] * (1 - d["zurdo_w"])  # zurdo contra diestro
    return d, a_gana


def columnas(grupos):
    cols = ["m", "wta", "bo5"]
    for g in grupos:
        cols += [f"d_{v}" for v in GRUPOS[g]]
    return cols


def ajustar_predecir(tr, te, cols, tipo):
    if tipo == "logistica":
        mu, sd = tr[cols].mean(), tr[cols].std().replace(0, 1)
        Xtr = ((tr[cols] - mu) / sd).fillna(0).values
        Xte = ((te[cols] - mu) / sd).fillna(0).values
        mod = LogisticRegression(C=1.0, max_iter=2000).fit(Xtr, tr["y"])
        return mod.predict_proba(Xte)[:, 1]
    ps = []
    for semilla in range(5):
        mod = XGBClassifier(n_estimators=400, learning_rate=0.03, max_depth=2, min_child_weight=20,
                            subsample=0.8, colsample_bytree=0.8, reg_lambda=5, random_state=semilla,
                            eval_metric="logloss")
        mod.fit(tr[cols], tr["y"])
        ps.append(mod.predict_proba(te[cols])[:, 1])
    return np.mean(ps, axis=0)


def ll(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def sig(a, b):
    x = a - b
    return x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def apuestas(te, p, umbral=0.0):
    ret = []
    for (_, r), pa in zip(te.iterrows(), p):
        casa = "PS" if r["fuente_mkt"] == "Pinnacle" else "BFE"
        a_es_ganador = r["y"] == 1
        c_a = r[f"cuota_w_{casa}"] if a_es_ganador else r[f"cuota_l_{casa}"]
        c_b = r[f"cuota_l_{casa}"] if a_es_ganador else r[f"cuota_w_{casa}"]
        va, vb = pa * c_a - 1, (1 - pa) * c_b - 1
        if max(va, vb) <= umbral:
            continue
        if va >= vb:
            ret.append(c_a - 1 if a_es_ganador else -1.0)
        else:
            ret.append(c_b - 1 if not a_es_ganador else -1.0)
    x = np.array(ret)
    return len(x), x.mean() if len(x) else np.nan, x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else np.nan


def main():
    d, _ = construir()
    comp = d[d["Comment"] == "Completed"]
    t22 = comp[comp["fecha"] < "2023-01-01"]
    v23 = comp[(comp["fecha"] >= "2023-01-01") & (comp["fecha"] < "2024-01-01")]
    t23 = comp[comp["fecha"] < "2024-01-01"]
    prueba = comp[comp["fecha"] >= "2024-01-01"]
    out = ["# Modelo con saque, fatiga, perfil y cara a cara, contra el cierre\n",
           "Generado por `modelos/tenis/scripts/modelo_tenis.py`. Entrena 2020-2022, elige en 2023,",
           "reentrena 2020-2023 y juzga en 2024-2026. Log-loss: más bajo es mejor; diferencias",
           "negativas = el modelo es mejor. Sigmas del error emparejado partido a partido.\n",
           f"Partidos completos: entrenamiento 2020-2022 {len(t22)}, elección 2023 {len(v23)}, "
           f"prueba 2024-2026 {len(prueba)}.\n",
           "## Elección (2023)\n", "| configuración | modelo | log-loss 2023 | contra mercado recalibrado (sigmas) |",
           "|---|---|---|---|"]
    base23 = ajustar_predecir(t22, v23, ["m", "wta", "bo5"], "logistica")
    puntos = []
    for g in CONFIGS:
        for tipo in ("logistica", "xgboost"):
            p = ajustar_predecir(t22, v23, columnas(g), tipo)
            dif, s = sig(ll(v23["y"].values, p), ll(v23["y"].values, base23))
            nombre = "+".join(g) or "solo mercado"
            puntos.append((ll(v23["y"].values, p).mean(), nombre, tipo, g))
            out.append(f"| {nombre} | {tipo} | {ll(v23['y'].values, p).mean():.4f} | {dif:+.4f} ({s:+.2f}) |")
    _, nombre_e, tipo_e, g_e = min(puntos)
    out.append(f"\n**Elegida: {nombre_e} ({tipo_e}).**\n")
    out += ["## Prueba (2024-2026)\n",
            "| configuración | modelo | tramo | partidos | contra mercado recalibrado | contra mercado en bruto | elegida |",
            "|---|---|---|---|---|---|---|"]
    base = ajustar_predecir(t23, prueba, ["m", "wta", "bo5"], "logistica")
    y = prueba["y"].values
    bruto = 1 / (1 + np.exp(-prueba["m"].values))
    tramos = {"2024-2025 Pinnacle": (prueba["fuente_mkt"] == "Pinnacle").values,
              "2026 Betfair": (prueba["fuente_mkt"] == "Betfair").values & (prueba["fecha"] >= "2026-01-01").values}
    pred_e = None
    for g in CONFIGS:
        for tipo in ("logistica", "xgboost"):
            p = ajustar_predecir(t23, prueba, columnas(g), tipo)
            nombre = "+".join(g) or "solo mercado"
            es = nombre == nombre_e and tipo == tipo_e
            if es:
                pred_e = p
            for tn, m in tramos.items():
                d1, s1 = sig(ll(y[m], p[m]), ll(y[m], base[m]))
                d2, s2 = sig(ll(y[m], p[m]), ll(y[m], bruto[m]))
                out.append(f"| {nombre} | {tipo} | {tn} | {m.sum()} | {d1:+.4f} ({s1:+.2f}) | {d2:+.4f} ({s2:+.2f}) | "
                           f"{'**sí**' if es else ''} |")
    out += ["\n## Apuestas de la elegida en la prueba (retiradas incluidas; Betfair sin comisión)\n",
            "| umbral de valor | apuestas | rendimiento | sigmas |", "|---|---|---|---|"]
    todo = d[d["fecha"] >= "2024-01-01"]
    p_todo = ajustar_predecir(t23, todo, columnas(g_e), tipo_e)
    for u in (0.0, 0.02, 0.05):
        n, r, s = apuestas(todo, p_todo, u)
        out.append(f"| > {u:.0%} | {n} | {r:+.2%} | {s:+.2f} |")
    open(f"{D}/modelo_tenis.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
