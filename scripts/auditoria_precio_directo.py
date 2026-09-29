"""
Auditoría externa, punto 7 (29/09/2026): el precio con el que se ENTRENA no es
el mismo con el que se pronostica EN DIRECTO.

  entrenamiento: previa de football-data (Pinnacle/Betfair), 1X2 y más/menos 2.5
  directo (ambos_marcan_hoy.py): mediana de las casas de Highlightly en el
          momento, misma construcción (sin margen, Poisson para el implícito)

Fijado antes: en los partidos con las DOS fuentes (cosechado de Highlightly,
ago-sep 2026), (1) cuánto difieren las 7 variables de precio, y (2) el modelo
oficial entrenado con todo lo anterior a ago-2026 predice esos partidos con una
fuente y con la otra: cuánto cambia la probabilidad, el Brier, el log loss, el
resultado contra el ambos marcan real y cuántas apuestas cambian de lado.
Sin API.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A
import modelo_xgboost as M
import evaluar_mercados as EM
from btts_implicito import ajustar

EPS = 1e-4


def sin_margen(d, lados):
    med = d.groupby("lado").cuota.median()
    if not set(lados) <= set(med.index) or (med[list(lados)] <= 1).any():
        return None
    inv = 1 / med[list(lados)]
    return (inv / inv.sum()).to_dict(), med.to_dict()


def precio_directo():
    c = EM.cargar_cuotas_crudas()
    filas = []
    for mid, d in c[c.mercado.isin(["Full Time Result", "Total Goals 2.5", "Both Teams To Score"])].groupby("match_id"):
        r = sin_margen(d[d.mercado == "Full Time Result"], ("home", "draw", "away"))
        o = sin_margen(d[d.mercado == "Total Goals 2.5"], ("over", "under"))
        b = sin_margen(d[d.mercado == "Both Teams To Score"], ("yes", "no"))
        if not r or not o:
            continue
        pl, pe, pv, po = r[0]["home"], r[0]["draw"], r[0]["away"], o[0]["over"]
        ll_, lv = ajustar(pl, pe, pv, po)
        filas.append({"match_id": mid, "mkt_p_local": pl, "mkt_p_empate": pe, "mkt_p_visitante": pv,
                      "mkt_p_mas_2_5": po, "mkt_lambda_l": ll_, "mkt_lambda_v": lv,
                      "mkt_p_btts_implicito": (1 - np.exp(-ll_)) * (1 - np.exp(-lv)),
                      "p_real": b[0]["yes"] if b else np.nan,
                      "cuota_si": b[1]["yes"] if b else np.nan, "cuota_no": b[1]["no"] if b else np.nan})
    return pd.DataFrame(filas)


def main():
    bt, cols = A.preparar()
    hl = precio_directo()
    test = bt[bt.match_id.isin(hl.match_id) & bt[A.MKT].notna().all(axis=1)].copy()
    hl = hl[hl.match_id.isin(test.match_id)].set_index("match_id")
    print(f"Partidos con las dos fuentes y resultado: {len(test)} ({test.mes.min()}..{test.mes.max()})\n")
    print("1. Diferencia entre las dos fuentes (Highlightly - football-data previa):")
    fd = test.set_index("match_id")[A.MKT]
    for c in A.MKT:
        d = hl.loc[fd.index, c] - fd[c]
        print(f"   {c:22s} media {d.mean():+.4f}  |dif| media {d.abs().mean():.4f}  máx {d.abs().max():.3f}  "
              f"correlación {np.corrcoef(hl.loc[fd.index, c], fd[c])[0, 1]:.3f}")
    ent = bt[(bt.mes < test.mes.min()) & bt.goles_l.notna()]
    y = ent[A.OBJETIVO].values.astype(int)
    X_fd = test[cols].values
    X_hl = test[cols].copy()
    for c in A.MKT:
        X_hl[c] = test.match_id.map(hl[c]).values
    X_hl = X_hl.values
    p_fd = np.mean([M.probabilidades(A.entrenar(ent[cols].values, y, semilla=s), X_fd, 2)[:, 1] for s in A.SEMILLAS], axis=0)
    p_hl = np.mean([M.probabilidades(A.entrenar(ent[cols].values, y, semilla=s), X_hl, 2)[:, 1] for s in A.SEMILLAS], axis=0)
    yt = test[A.OBJETIVO].values
    dp = p_hl - p_fd
    print(f"\n2. Modelo oficial (entrenado hasta {test.mes.min()}) con cada fuente de precio:")
    print(f"   cambio de probabilidad: media {dp.mean()*100:+.2f} pts, |cambio| medio {np.abs(dp).mean()*100:.2f} pts, "
          f"máx {np.abs(dp).max()*100:.1f} pts; >3 pts en {np.mean(np.abs(dp) > .03):.0%} de los partidos")
    br = lambda p: (p - yt) ** 2
    lo = lambda p: -(yt * np.log(np.clip(p, EPS, 1)) + (1 - yt) * np.log(np.clip(1 - p, EPS, 1)))
    s = lambda d: d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    print(f"   Brier: football-data {br(p_fd).mean():.4f}, Highlightly {br(p_hl).mean():.4f} "
          f"(Highlightly vs fd {s(br(p_fd) - br(p_hl)):+.2f}s); log loss {lo(p_fd).mean():.4f} vs {lo(p_hl).mean():.4f}")
    real = test.match_id.map(hl.p_real).values
    ok = ~np.isnan(real)
    for n, p in (("football-data", p_fd), ("Highlightly", p_hl)):
        print(f"   contra el ambos marcan real ({ok.sum()} partidos), precio {n:13s}: "
              f"{s(br(real)[ok] - br(p)[ok]):+.2f}s")
    cs, cn = test.match_id.map(hl.cuota_si).values, test.match_id.map(hl.cuota_no).values
    def apuesta(p):
        vs, vn = p * cs - 1, (1 - p) * cn - 1
        lado = np.where(vs >= vn, "si", "no")
        ve = np.maximum(vs, vn)
        return lado, ve > 0
    la, aa = apuesta(p_fd)
    lb, ab = apuesta(p_hl)
    m = ok & ~np.isnan(cs)
    print(f"   apuestas (VE>0): {aa[m].sum()} con football-data, {ab[m].sum()} con Highlightly; "
          f"cambian (se apuesta con una y no con la otra, o cambia el lado): {((aa != ab) | (aa & ab & (la != lb)))[m].sum()}")
    pd.DataFrame({"match_id": test.match_id.values, "p_fd": p_fd, "p_hl": p_hl, "y": yt}).to_csv(
        "data/auditoria_precio_directo.csv", index=False)


if __name__ == "__main__":
    main()
