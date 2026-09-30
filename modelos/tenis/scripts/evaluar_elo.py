"""
Elo contra el cierre del mercado, ATP y WTA, en los partidos de tennis-data.

Regla fijada ANTES de mirar resultados (30/09/2026):
- 2020-2023: se eligen los parámetros del Elo (c y peso de superficie w) por
  log-loss del propio Elo, y se ajusta la mezcla mercado+Elo.
- 2024-2026: solo se juzga, sin tocar nada. 2024-2025 contra Pinnacle sin
  margen; 2026 contra Betfair Exchange sin margen (Pinnacle ya no está).
- Walkovers fuera. Métricas en partidos completos; las apuestas incluyen
  retiradas liquidadas como en tennis-data (gana quien avanza).
- Un partido = una observación (independientes). Errores en sigmas del
  error emparejado partido a partido.

Emparejamiento tennis-data -> historial: el de cruce_fuentes.py. Los
partidos con ganador al revés entre fuentes se descartan.

Escribe data/tenis/evaluar_elo.md.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import cruce_fuentes as C  # noqa: E402
import elo_tenis as E  # noqa: E402

D = "data/tenis"
REJILLA_C = (150.0, 250.0, 350.0)
REJILLA_W = (0.0, 0.25, 0.5, 0.75)
CORTE = pd.Timestamp("2024-01-01")


def mercado(td):
    """Probabilidad sin margen del que ganó: Pinnacle, y si falta, Betfair Exchange."""
    out = pd.Series(np.nan, index=td.index)
    fuente = pd.Series("", index=td.index)
    for casa, nombre in (("PS", "Pinnacle"), ("BFE", "Betfair")):
        if f"{casa}W" not in td:
            continue
        w, l = pd.to_numeric(td[f"{casa}W"], errors="coerce"), pd.to_numeric(td[f"{casa}L"], errors="coerce")
        ok = (w > 1) & (l > 1) & out.isna()
        out[ok] = (1 / w[ok]) / (1 / w[ok] + 1 / l[ok])
        fuente[ok] = nombre
        td[f"cuota_w_{casa}"], td[f"cuota_l_{casa}"] = w, l
    return out, fuente


def preparar(circuito):
    hist = E.historial(circuito)
    hist["kw"] = hist["winner_name"].map(C.clave_completo)
    hist["kl"] = hist["loser_name"].map(C.clave_completo)
    td = C.cargar_td(circuito)
    td = td[td["Comment"] != "Walkover"].copy()
    td["p_mkt"], td["fuente_mkt"] = mercado(td)
    elos = {c: E.calcular(hist, c) for c in REJILLA_C}
    f = hist.copy()
    f["fila_hist"] = f.index
    ok, cambiado, falta = C.cruzar(td, f[["kw", "kl", "inicio", "fila_hist", "round", "tourney_level"]])
    ok = ok.drop_duplicates("i")
    for c, e in elos.items():
        ee = e.loc[ok["fila_hist"].values].reset_index(drop=True)
        for w in REJILLA_W:
            ok[f"p_elo_{int(c)}_{w}"] = E.prob_ganador(ee, w).values
    ok["n_min"] = np.minimum(elos[250.0].loc[ok["fila_hist"].values, "n_w"].values,
                             elos[250.0].loc[ok["fila_hist"].values, "n_l"].values)
    return ok, len(td), len(cambiado), len(falta)


def ll(p):
    return -np.log(np.clip(p, 1e-6, 1 - 1e-6))


def emparejado(a, b):
    d = a - b
    return d.mean(), d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def orientar(df, cols, semilla=7):
    """Lado A al azar: y = gana A. Hace falta para ajustar la mezcla (con 'ganador' y=1 siempre)."""
    r = np.random.default_rng(semilla).random(len(df)) < 0.5
    y = r.astype(int)
    out = {c: np.where(r, df[c], 1 - df[c]) for c in cols}
    return y, out


def logistica(X, y):
    X = np.column_stack([np.ones(len(X))] + [X])
    b = np.zeros(X.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ b))
        H = X.T @ (X * (p * (1 - p))[:, None])
        paso = np.linalg.solve(H + 1e-9 * np.eye(len(b)), X.T @ (y - p))
        b += paso
        if np.abs(paso).max() < 1e-10:
            break
    return b


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def apuestas(g, col, umbral):
    """Apuesta al lado con p_elo*cuota-1 > umbral, a la cuota de la fuente del mercado de ese partido."""
    filas = []
    for _, r in g.iterrows():
        casa = "PS" if r["fuente_mkt"] == "Pinnacle" else "BFE"
        cw, cl = r[f"cuota_w_{casa}"], r[f"cuota_l_{casa}"]
        pw = r[col]
        vw, vl = pw * cw - 1, (1 - pw) * cl - 1
        if max(vw, vl) <= umbral:
            continue
        filas.append(cw - 1 if vw >= vl else -1.0)
    x = np.array(filas)
    if len(x) < 2:
        return len(x), np.nan, np.nan
    return len(x), x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def main():
    out = ["# Elo contra el cierre del mercado (ganador del partido)\n",
           "Generado por `modelos/tenis/scripts/evaluar_elo.py`. Parámetros y mezcla elegidos SOLO con",
           "2020-2023; 2024-2026 no se tocó para elegir nada. Log-loss: más bajo es mejor.",
           "Diferencia = Elo - mercado; negativa = Elo mejor. Sigmas del error emparejado.\n"]
    for circuito in ("atp", "wta"):
        ok, n_td, n_camb, n_falta = preparar(circuito)
        ok = ok[ok["p_mkt"].notna()].copy()
        comp = ok[ok["Comment"] == "Completed"]
        eleg = comp[comp["fecha"] < CORTE]
        prueba = comp[comp["fecha"] >= CORTE]
        # elección de parámetros en 2020-2023
        mejor = min(((c, w) for c in REJILLA_C for w in REJILLA_W),
                    key=lambda cw: ll(eleg[f"p_elo_{int(cw[0])}_{cw[1]}"]).mean())
        col = f"p_elo_{int(mejor[0])}_{mejor[1]}"
        # mezcla mercado + Elo ajustada en 2020-2023
        y, o = orientar(eleg, ["p_mkt", col])
        b = logistica(np.column_stack([logit(o["p_mkt"]), logit(o[col])]), y)
        # b[0] (lado A al azar) debe ser ~0 por simetría; se usa 0 para que p(ganador) sea coherente
        ok["p_mezcla"] = 1 / (1 + np.exp(-(b[1] * logit(ok["p_mkt"]) + b[2] * logit(ok[col]))))
        comp = ok[ok["Comment"] == "Completed"]
        eleg = comp[comp["fecha"] < CORTE]
        prueba = comp[comp["fecha"] >= CORTE]
        out.append(f"## {circuito.upper()}\n")
        out.append(f"tennis-data sin walkovers: {n_td}. Emparejados con el historial: {len(ok) + 0} con mercado "
                   f"(ganador al revés, fuera: {n_camb}; sin encontrar: {n_falta}).")
        out.append(f"Elegido con 2020-2023: c={mejor[0]:.0f}, peso superficie w={mejor[1]}. "
                   f"Mezcla: {b[1]:.3f}·logit(mercado) + {b[2]:.3f}·logit(Elo) (constante {b[0]:+.3f}).\n")
        out += ["| tramo | referencia | partidos | log-loss Elo | log-loss mercado | Elo - mercado (sigmas) | "
                "mezcla - mercado (sigmas) | acierto Elo | acierto mercado |",
                "|---|---|---|---|---|---|---|---|---|"]
        tramos = [("2020-2023 (elección)", eleg, None),
                  ("2024-2025 (prueba)", prueba[prueba["fecha"] < "2026-01-01"], None),
                  ("2026 (prueba)", prueba[prueba["fecha"] >= "2026-01-01"], None)]
        for nombre, g, _ in tramos:
            for ref in sorted(g["fuente_mkt"].unique()):
                h = g[g["fuente_mkt"] == ref]
                if len(h) < 50:
                    continue
                d1, s1 = emparejado(ll(h[col]), ll(h["p_mkt"]))
                d2, s2 = emparejado(ll(h["p_mezcla"]), ll(h["p_mkt"]))
                out.append(f"| {nombre} | {ref} | {len(h)} | {ll(h[col]).mean():.4f} | {ll(h['p_mkt']).mean():.4f} | "
                           f"{d1:+.4f} ({s1:+.2f}) | {d2:+.4f} ({s2:+.2f}) | {(h[col] > 0.5).mean():.1%} | "
                           f"{(h['p_mkt'] > 0.5).mean():.1%} |")
        out += ["\nApuestas en la PRUEBA (2024-2026, retiradas incluidas), al lado con valor según el Elo, "
                "a la cuota de cierre de la referencia (Betfair sin comisión):\n",
                "| regla | modelo | apuestas | rendimiento | sigmas |", "|---|---|---|---|---|"]
        pr = ok[ok["fecha"] >= CORTE]
        for modelo in (col, "p_mezcla"):
            for u in (0.0, 0.05):
                n, r, s = apuestas(pr, modelo, u)
                out.append(f"| valor > {u:.0%} | {'Elo' if modelo == col else 'mezcla'} | {n} | {r:+.2%} | {s:+.2f} |")
        out.append("")
    open(f"{D}/evaluar_elo.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
