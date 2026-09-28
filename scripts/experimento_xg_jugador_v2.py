"""
xG por jugador, segunda vuelta: ¿el problema era CÓMO se le dio al modelo?
(28/09/2026, pregunta del usuario tras el +0.89s de experimento_xg_jugador.py)

La primera versión daba la suma de xG/xA por 90 del once, que se parece en un
75% al xG medio del equipo que el modelo ya tiene. Tres formas nuevas, FIJADAS
ANTES de ejecutar (no se prueba ninguna más sobre estos partidos):

  A  desviacion  lo que NO repite el modelo: el xG/xA del once de hoy MENOS la
                 media del once de ese equipo en sus 5 partidos anteriores
                 (bajas, rotaciones, vueltas de lesionados). loc_/vis_/dif_.
  B  portero     el portero titular: goles evitados por 90 (expectedGoalsPrevented)
                 en sus 10 apariciones anteriores, encogido hacia 0 con 270'.
                 La parte defensiva que la primera versión no tenía.
  C  combinada   ambos marcan es un suceso DOBLE. Una sola variable ya cruzada:
                 lambda_local = xG90 del once local x (xG que concede el
                 visitante, m_contra_expected_goals) / 1.35, igual al revés, y
                 p = (1 - e^-lambda_l)(1 - e^-lambda_v). Así el árbol no tiene
                 que descubrir la interacción.
Misma prueba mes a mes contra el modelo oficial. Con 3 intentos, el listón
honesto sube: una sola por encima de +2s podría ser suerte (hace falta ~+2.4s).
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A

VENTANA, K_MIN, VENTANA_EQUIPO, XG_LIGA = 10, 270.0, 5, 1.35


def tabla_jugadores():
    x = pd.read_csv("data/historico_xg_jugador.csv")
    x = x[x.jugador_id.notna()].copy()
    h = pd.read_csv("data/historico_partidos.csv")[["match_id", "fecha", "local_id", "visitante_id"]]
    x = x.merge(h[["match_id", "fecha"]], on="match_id")
    for c in ("minutos", "expectedGoals", "expectedAssists", "expectedGoalsPrevented"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x[x.minutos > 0].sort_values("fecha")
    x["jugador_id"] = x.jugador_id.astype(int)
    x[["expectedGoals", "expectedAssists"]] = x[["expectedGoals", "expectedAssists"]].fillna(0)
    g = x.groupby("jugador_id")
    prev = lambda c: g[c].transform(lambda s: s.shift(1).rolling(VENTANA, min_periods=1).sum())
    x["pm"], x["pxg"], x["pxa"] = prev("minutos").fillna(0), prev("expectedGoals").fillna(0), prev("expectedAssists").fillna(0)
    x["pgp"] = g["expectedGoalsPrevented"].transform(lambda s: s.fillna(0).shift(1).rolling(VENTANA, min_periods=1).sum()).fillna(0)
    pos = x.groupby("posicion")[["expectedGoals", "expectedAssists", "minutos"]].sum()
    mu_g = x.posicion.map((pos.expectedGoals / pos.minutos * 90).to_dict()).fillna(0.1)
    mu_a = x.posicion.map((pos.expectedAssists / pos.minutos * 90).to_dict()).fillna(0.1)
    x["xg90"] = (x.pxg * 90 + mu_g * K_MIN) / (x.pm + K_MIN)
    x["xa90"] = (x.pxa * 90 + mu_a * K_MIN) / (x.pm + K_MIN)
    x["gp90"] = (x.pgp * 90) / (x.pm + K_MIN)
    # titulares del once confirmado (historico_lineups); si falta, el box-score
    lu = pd.read_csv("data/historico_lineups.csv")
    once = [(r.match_id, int(j)) for r in lu.itertuples() for lado in ("local_ids", "visitante_ids")
            if isinstance(getattr(r, lado), str) for j in getattr(r, lado).split("|") if j.strip().isdigit()]
    once = pd.DataFrame(once, columns=["match_id", "jugador_id"]).assign(en_once=True)
    x = x.merge(once, on=["match_id", "jugador_id"], how="left")
    tiene = x.match_id.isin(set(once.match_id))
    x["titular"] = np.where(tiene, x.en_once.fillna(False).astype(bool), x.suplente.astype(str).str.lower() == "false")
    return x[x.titular], h


def rasgos():
    t, h = tabla_jugadores()
    eq = t.groupby(["match_id", "equipo_id"]).agg(xi_xg90=("xg90", "sum"), xi_xa90=("xa90", "sum")).reset_index()
    gk = t[t.posicion == "Goalkeeper"].groupby(["match_id", "equipo_id"]).gp90.first().rename("gk_gp90").reset_index()
    eq = eq.merge(gk, on=["match_id", "equipo_id"], how="left").merge(h[["match_id", "fecha"]], on="match_id")
    eq = eq.sort_values("fecha")
    ge = eq.groupby("equipo_id")
    for c in ("xi_xg90", "xi_xa90"):
        eq[f"dev_{c}"] = eq[c] - ge[c].transform(lambda s: s.shift(1).rolling(VENTANA_EQUIPO, min_periods=2).mean())
    out = h[["match_id", "local_id", "visitante_id"]]
    for lado, col in (("loc", "local_id"), ("vis", "visitante_id")):
        cols = ["xi_xg90", "xi_xa90", "gk_gp90", "dev_xi_xg90", "dev_xi_xa90"]
        out = out.merge(eq[["match_id", "equipo_id"] + cols].rename(
            columns={"equipo_id": col, **{c: f"{lado}_{c}" for c in cols}}), on=["match_id", col], how="left")
    for c in ("dev_xi_xg90", "dev_xi_xa90"):
        out[f"dif_{c}"] = out[f"loc_{c}"] - out[f"vis_{c}"]
    return out.drop(columns=["local_id", "visitante_id"])


def main():
    bt, cols = A.preparar()
    bt = bt.merge(rasgos(), on="match_id", how="left")
    lam_l = bt.loc_xi_xg90 * bt.vis_m_contra_expected_goals / XG_LIGA
    lam_v = bt.vis_xi_xg90 * bt.loc_m_contra_expected_goals / XG_LIGA
    bt["p_btts_xi"] = (1 - np.exp(-lam_l)) * (1 - np.exp(-lam_v))
    variantes = {
        "A desviacion": ["loc_dev_xi_xg90", "vis_dev_xi_xg90", "dif_dev_xi_xg90",
                         "loc_dev_xi_xa90", "vis_dev_xi_xa90", "dif_dev_xi_xa90"],
        "B portero": ["loc_gk_gp90", "vis_gk_gp90"],
        "C combinada": ["p_btts_xi"],
    }
    cob = bt.groupby("mes").loc_xi_xg90.apply(lambda s: s.notna().mean())
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if n >= 20 and cob.get(m, 0) >= 0.5]
    print(f"Meses: {meses[0]}..{meses[-1]} ({len(meses)})")
    base = pd.concat([A.predecir_mes(bt, cols, m) for m in meses])
    y = base.ambos_marcan.values
    for nombre, extra in variantes.items():
        v = pd.concat([A.predecir_mes(bt, cols, m, extra=extra) for m in meses])
        d = (base.p_ambos.values - y) ** 2 - (v.p_ambos.values - y) ** 2
        pos = sum(((base[base.mes == m].p_ambos.values - base[base.mes == m].ambos_marcan.values) ** 2).mean() >
                  ((v[v.mes == m].p_ambos.values - v[v.mes == m].ambos_marcan.values) ** 2).mean() for m in meses)
        print(f"{nombre:14s} vs oficial {d.mean()/(d.std(ddof=1)/np.sqrt(len(d))):+.2f}s  "
              f"(Brier {((v.p_ambos.values - y)**2).mean():.4f} vs {((base.p_ambos.values - y)**2).mean():.4f}; "
              f"mejora en {pos}/{len(meses)} meses)", flush=True)


if __name__ == "__main__":
    main()
