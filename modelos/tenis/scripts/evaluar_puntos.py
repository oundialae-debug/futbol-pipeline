"""
Modelo de puntos contra el Elo y contra el cierre, ganador del partido.
Ventana móvil (30/09/2026): cada año Y de 2021 a 2026 se juzga con una capa
de calibración (logística de pocos parámetros) ajustada SOLO con los años
anteriores a Y que tienen cuota. Nada del año Y se usa para ajustar.

Comparaciones, en log-loss por partido (negativo = el primero es mejor):
- puntos solo contra Elo solo (¿predice mejor el modelo nuevo?)
- puntos solo contra mercado en bruto
- mezcla mercado+puntos contra mercado recalibrado (¿aporta algo al precio?)
Partidos completos; mercado = Pinnacle sin margen o, si falta, Betfair.
Escribe data/tenis/evaluar_puntos.md.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/tenis/scripts")
import cruce_fuentes as C  # noqa: E402
import elo_tenis as E  # noqa: E402
import evaluar_elo as V  # noqa: E402
import markov_tenis as K  # noqa: E402
import modelo_puntos as P  # noqa: E402

C_ELO = {"atp": 250.0, "wta": 350.0}


def construir():
    partes = []
    for circuito in ("atp", "wta"):
        hist, _ = P.calcular(circuito, P.PARAMS[circuito])
        elo = E.calcular(hist, C_ELO[circuito])
        hist["p_elo"] = E.prob_ganador(elo, 0.25)
        hist["kw"] = hist["winner_name"].map(C.clave_completo)
        hist["kl"] = hist["loser_name"].map(C.clave_completo)
        td = C.cargar_td(circuito)
        td = td[td["Comment"] == "Completed"].copy()
        td["p_mkt"], td["fuente_mkt"] = V.mercado(td)
        f = hist[["kw", "kl", "inicio"]].copy()
        f["fila_hist"] = hist.index
        ok, _, _ = C.cruzar(td, f)
        ok = ok.drop_duplicates("i")
        ok = ok[ok["p_mkt"].notna()].reset_index(drop=True)
        h = hist.loc[ok["fila_hist"].values].reset_index(drop=True)
        ok["p_elo"] = h["p_elo"].values
        bo = np.where(pd.to_numeric(ok["Best of"], errors="coerce") == 5, 5, 3)
        ok["p_puntos"] = [K.partido(K.redondear(a), K.redondear(b), int(m))[0]
                          for a, b, m in zip(h["p_w"].values, h["p_l"].values, bo)]
        ok["circuito"] = circuito
        partes.append(ok)
    d = pd.concat(partes, ignore_index=True)
    d["año"] = d["fecha"].dt.year
    return d


def ll(p):
    return -np.log(np.clip(p, 1e-6, 1 - 1e-6))


def sig(a, b):
    x = a - b
    return x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def main():
    d = construir()
    rng = np.random.default_rng(3)
    a_gana = rng.random(len(d)) < 0.5                       # lado A al azar para ajustar la capa
    d["y"] = a_gana.astype(int)
    for c in ("p_mkt", "p_puntos", "p_elo"):
        d[f"{c}_A"] = np.where(a_gana, d[c], 1 - d[c])
        d[f"l_{c}"] = V.logit(d[f"{c}_A"])
    out = ["# Modelo de puntos contra Elo y contra el cierre (ganador del partido)\n",
           "Generado por `modelos/tenis/scripts/evaluar_puntos.py`. Ventana móvil: cada año se juzga",
           "con una capa ajustada solo con los años anteriores. Log-loss: negativo = el primero es mejor.\n",
           "| año | partidos | puntos - Elo | puntos - mercado | mezcla - mercado recalibrado | "
           "peso mercado / puntos en la mezcla |", "|---|---|---|---|---|---|"]
    acum = {k: [] for k in ("pe", "pm", "mix")}
    for año in range(2021, 2027):
        tr, te = d[d["año"] < año], d[d["año"] == año]
        if len(te) < 200:
            continue
        y = te["y"].values
        def llA(p): return -(y * np.log(np.clip(p, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-6, 1)))
        base = LogisticRegression(C=1e6).fit(tr[["l_p_mkt"]], tr["y"]).predict_proba(te[["l_p_mkt"]])[:, 1]
        mm = LogisticRegression(C=1e6).fit(tr[["l_p_mkt", "l_p_puntos"]], tr["y"])
        mix = mm.predict_proba(te[["l_p_mkt", "l_p_puntos"]])[:, 1]
        pe = llA(te["p_puntos_A"].values) - llA(te["p_elo_A"].values)
        pm = llA(te["p_puntos_A"].values) - llA(te["p_mkt_A"].values)
        mx = llA(mix) - llA(base)
        for k, x in (("pe", pe), ("pm", pm), ("mix", mx)):
            acum[k].append(x)
        f = lambda x: f"{x.mean():+.4f} ({x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f})"  # noqa: E731
        out.append(f"| {año} | {len(te)} | {f(pe)} | {f(pm)} | {f(mx)} | "
                   f"{mm.coef_[0][0]:+.2f} / {mm.coef_[0][1]:+.2f} |")
    f = lambda x: f"{x.mean():+.4f} ({x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):+.2f})"  # noqa: E731
    out.append(f"| **2021-2026** | {sum(len(x) for x in acum['pe'])} | {f(np.concatenate(acum['pe']))} | "
               f"{f(np.concatenate(acum['pm']))} | {f(np.concatenate(acum['mix']))} | |")
    out.append("\nAcierto del ganador 2021-2026: puntos {:.1%}, Elo {:.1%}, mercado {:.1%}.".format(
        (d[d.año >= 2021].p_puntos > 0.5).mean(), (d[d.año >= 2021].p_elo > 0.5).mean(),
        (d[d.año >= 2021].p_mkt > 0.5).mean()))
    open("data/tenis/evaluar_puntos.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
