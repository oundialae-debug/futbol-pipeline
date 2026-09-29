"""
Segunda auditoría externa, paso 3 (29/09/2026): Elo con regresión a la media
entre temporadas y ancla para los que cambian de liga. Sin API. No toca
rasgos.py: el Elo alternativo se calcula aquí y SUSTITUYE a loc_elo, vis_elo y
dif_elo solo dentro de esta prueba.

La auditoría señaló que el Elo actual (rasgos.calcular_elo):
  - arranca en 1500 para todos en 2022/23, sin calentamiento;
  - no regresa a la media entre temporadas (un equipo que cambió media
    plantilla conserva su rating entero);
  - los ascendidos entran como equipo medio (1500), aunque casi siempre
    son de la parte baja.

Variantes FIJADAS ANTES (mismo K=20 y ventaja local 60):
  V1  regresión: en el primer partido de cada equipo en una temporada nueva,
      su rating se acerca 1/3 a la media de su liga (la de ahora).
  V2  V1 + ancla: un equipo que llega a una liga que no jugaba la temporada
      anterior, o que aparece por primera vez, empieza en el percentil 20 de
      esa liga (ascendido); si baja de LaLiga a Segunda, en el percentil 80.
Mes a mes sep-2024..sep-2026 contra el oficial, 5 semillas, Brier y log
loss, meses mejor, y contra el ambos marcan real. Con 2 intentos, listón
~+2.2s. Se da también un control sin el modelo: cuánto predice el 1X2 cada
Elo por sí solo (logística sobre dif_elo), para ver si el Elo en sí mejora.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import modelo_ambos_marcan as A
import modelo_xgboost as M

K, VENTAJA, REGRESION = 20.0, 60.0, 1 / 3
LALIGA, SEGUNDA = 119924, 120775
EPS = 1e-4


def elo(hist, ancla):
    orden = hist.sort_values("fecha")
    r, liga_de, temp_de = {}, {}, {}
    salida = []
    for f in orden.itertuples():
        for eq in (f.local_id, f.visitante_id):
            liga, temp = f.liga_id, f.temporada
            if temp_de.get(eq) != temp:                       # primer partido de su temporada
                en_liga = [r[e] for e, lg in liga_de.items() if lg == liga and e in r and e != eq]
                media = np.mean(en_liga) if en_liga else 1500.0
                antes = liga_de.get(eq)
                if eq not in r:
                    r[eq] = np.percentile(en_liga, 20) if (ancla and len(en_liga) >= 5) else 1500.0
                elif antes != liga and ancla and len(en_liga) >= 5:
                    r[eq] = np.percentile(en_liga, 80 if (antes == LALIGA and liga == SEGUNDA) else 20)
                else:
                    r[eq] = media + (1 - REGRESION) * (r[eq] - media)
                liga_de[eq], temp_de[eq] = liga, temp
        rl, rv = r[f.local_id], r[f.visitante_id]
        salida.append((f.match_id, rl, rv))
        if pd.isna(f.goles_l) or pd.isna(f.goles_v):
            continue
        d = abs(f.goles_l - f.goles_v)
        g = 1.0 if d <= 1 else (1.5 if d == 2 else (11 + d) / 8.0)
        esp = 1.0 / (1.0 + 10 ** (-(rl + VENTAJA - rv) / 400.0))
        real = 1.0 if f.goles_l > f.goles_v else (0.5 if f.goles_l == f.goles_v else 0.0)
        c = K * g * (real - esp)
        r[f.local_id], r[f.visitante_id] = rl + c, rv - c
    return pd.DataFrame(salida, columns=["match_id", "loc_elo", "vis_elo"]).assign(
        dif_elo=lambda d: d.loc_elo - d.vis_elo)


def sig(d):
    d = np.asarray(d, float)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def main():
    bt, cols = A.preparar()
    M.TEMPORADA_MINIMA = A.TEMPORADA_MINIMA
    hist = M.cargar()
    variantes = {"V1 regresión": elo(hist, False), "V2 regresión+ancla": elo(hist, True)}
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    base = pd.concat([A.predecir_mes(bt, cols, m) for m in meses])
    y = base[A.OBJETIVO].values
    lo = lambda p: -(y * np.log(np.clip(p, EPS, 1)) + (1 - y) * np.log(np.clip(1 - p, EPS, 1)))
    import evaluar_mercados as EM
    c = EM.cargar_cuotas_crudas()
    b = c[c.familia == "Both Teams To Score"]
    piv = b.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
    piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
    piv["p"] = (1 / piv.yes) / (1 / piv.yes + 1 / piv.no)
    real = piv.groupby("match_id").p.median()
    en = base.match_id.isin(real.index).values
    yr, pr = y[en], base.match_id[en].map(real).values
    print(f"{len(base)} partidos, {len(meses)} meses. Oficial contra el ambos marcan real ({en.sum()}): "
          f"{sig((pr - yr)**2 - (base.p_ambos.values[en] - yr)**2):+.2f}s\n")
    # control: ¿predice mejor el resultado cada Elo por sí solo? (logística 1X2 local gana/no, mes a mes)
    h = hist.set_index("match_id")
    for nombre, e in [("actual", bt[["match_id", "loc_elo", "vis_elo", "dif_elo"]])] + list(variantes.items()):
        d = bt[["match_id", "mes"]].merge(e, on="match_id")
        d["gana_local"] = (h.loc[d.match_id, "goles_l"].values > h.loc[d.match_id, "goles_v"].values).astype(int)
        ps, ys = [], []
        for m in meses:
            tr, te = d[d.mes < m], d[d.mes == m]
            lr = LogisticRegression().fit(tr[["dif_elo"]], tr.gana_local)
            ps.append(lr.predict_proba(te[["dif_elo"]])[:, 1]); ys.append(te.gana_local.values)
        ps, ys = np.concatenate(ps), np.concatenate(ys)
        print(f"Control, Elo {nombre:20s} solo para 'gana el local': Brier {((ps-ys)**2).mean():.4f}")
    print()
    for nombre, e in variantes.items():
        v = bt.drop(columns=["loc_elo", "vis_elo", "dif_elo"]).merge(e, on="match_id", how="left")
        p = pd.concat([A.predecir_mes(v, cols, m) for m in meses])
        p = p.set_index("match_id").loc[base.match_id].reset_index()
        db = (base.p_ambos.values - y) ** 2 - (p.p_ambos.values - y) ** 2
        dl = lo(base.p_ambos.values) - lo(p.p_ambos.values)
        mes = sum(((base[base.mes == m].p_ambos - base[base.mes == m][A.OBJETIVO]) ** 2).mean() >
                  ((p[p.mes == m].p_ambos - p[p.mes == m][A.OBJETIVO]) ** 2).mean() for m in meses)
        ini = (base.mes >= "2026-08").values
        vr = sig((pr - yr) ** 2 - (p.p_ambos.values[en] - yr) ** 2)
        print(f"{nombre:20s} vs oficial: Brier {sig(db):+.2f}s  log loss {sig(dl):+.2f}s  mejor en {mes}/{len(meses)} meses  "
              f"arranque 2026/27 {db[ini].mean()*100:+.2f} pts  | contra el real {vr:+.2f}s", flush=True)


if __name__ == "__main__":
    main()
