"""
¿Mejora el modelo oficial de ambos marcan con el xG/xA de los JUGADORES que
salen de titulares? (28/09/2026)

El modelo ya tiene el xG del EQUIPO (media de sus últimos partidos, m_expected_goals).
Lo nuevo es quién juega HOY: para cada titular (historico_lineups.csv), su xG y
su xA por 90 minutos en sus apariciones ANTERIORES (últimas 10, en cualquier
equipo de nuestras ligas; data/historico_xg_jugador.csv), encogido hacia la media
de su posición con 270 minutos. Rasgos por equipo:
  xi_xg90, xi_xa90   suma de los titulares (el ataque que sale al campo)
  xi_conocidos       cuántos titulares tienen dato
y loc_/vis_/dif_. Anti-fuga: solo apariciones con fecha anterior al partido.

Prueba: la misma mes a mes que fijó el modelo oficial (modelo_ambos_marcan.py,
predecir_mes), con y sin estos rasgos, solo en los meses con datos de xG por
jugador. Brier emparejado partido a partido.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A
import modelo_xgboost as M

VENTANA = 10
K_MIN = 270.0


def rasgos_xi():
    x = pd.read_csv("data/historico_xg_jugador.csv")
    x = x[x.jugador_id.notna()].copy()
    h = pd.read_csv("data/historico_partidos.csv")[["match_id", "fecha", "local_id", "visitante_id"]]
    x = x.merge(h[["match_id", "fecha"]], on="match_id")
    for c in ("minutos", "expectedGoals", "expectedAssists"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x[x.minutos > 0].sort_values("fecha")
    x["jugador_id"] = x.jugador_id.astype(int)
    x[["expectedGoals", "expectedAssists"]] = x[["expectedGoals", "expectedAssists"]].fillna(0)
    g = x.groupby("jugador_id")
    for c, n in (("minutos", "min"), ("expectedGoals", "xg"), ("expectedAssists", "xa")):
        x[f"prev_{n}"] = g[c].transform(lambda s: s.shift(1).rolling(VENTANA, min_periods=1).sum())
    pos = x.groupby("posicion")[["expectedGoals", "expectedAssists", "minutos"]].sum()
    tasa = {p: (r.expectedGoals / r.minutos * 90, r.expectedAssists / r.minutos * 90) for p, r in pos.iterrows()}
    mu_g = x.posicion.map(lambda p: tasa.get(p, (0.1, 0.1))[0])
    mu_a = x.posicion.map(lambda p: tasa.get(p, (0.1, 0.1))[1])
    pm = x.prev_min.fillna(0)
    x["xg90"] = (x.prev_xg.fillna(0) * 90 + mu_g * K_MIN) / (pm + K_MIN)
    x["xa90"] = (x.prev_xa.fillna(0) * 90 + mu_a * K_MIN) / (pm + K_MIN)
    x["conocido"] = pm > 0
    # titulares: los del once CONFIRMADO de /lineups (historico_lineups.csv) cuando
    # existe; si no, los que el box-score no marca como suplentes. Revisión del
    # 28/09: el box-score marca a veces más de 11 "no suplentes" (hasta 25 en un
    # partido), así que la fuente buena es la alineación.
    lu = pd.read_csv("data/historico_lineups.csv")
    filas = []
    for _, r in lu.iterrows():
        for lado in ("local", "visitante"):
            ids = str(r[f"{lado}_ids"]) if pd.notna(r[f"{lado}_ids"]) else ""
            for j in ids.split("|"):
                if j.strip().isdigit():
                    filas.append((r.match_id, lado, int(j)))
    once = pd.DataFrame(filas, columns=["match_id", "lado", "jugador_id"])
    once = once.merge(h[["match_id", "local_id", "visitante_id"]], on="match_id")
    once["equipo_id"] = np.where(once.lado == "local", once.local_id, once.visitante_id)
    x = x.merge(once[["match_id", "jugador_id"]].assign(en_once=True), on=["match_id", "jugador_id"], how="left")
    con_once = set(once.match_id)
    tit = x[np.where(x.match_id.isin(con_once), x.en_once.fillna(False).astype(bool),
                     x.suplente.astype(str).str.lower() == "false")]
    t = tit.groupby(["match_id", "equipo_id"]).agg(xi_xg90=("xg90", "sum"), xi_xa90=("xa90", "sum"),
                                                     xi_conocidos=("conocido", "sum")).reset_index()
    out = h[["match_id", "local_id", "visitante_id"]]
    for lado, col in (("loc", "local_id"), ("vis", "visitante_id")):
        out = out.merge(t.rename(columns={"equipo_id": col, **{c: f"{lado}_{c}" for c in ("xi_xg90", "xi_xa90", "xi_conocidos")}}),
                        on=["match_id", col], how="left")
    for c in ("xi_xg90", "xi_xa90"):
        out[f"dif_{c}"] = out[f"loc_{c}"] - out[f"vis_{c}"]
    cols = [c for c in out.columns if c.startswith(("loc_xi", "vis_xi", "dif_xi"))]
    return out[["match_id"] + cols], cols


def main():
    A.SEMILLAS = (0, 1, 2, 3, 4)
    bt, cols = A.preparar()
    xi, extra = rasgos_xi()
    bt = bt.merge(xi, on="match_id", how="left")
    cob = bt.groupby("mes").loc_xi_xg90.apply(lambda s: s.notna().mean())
    meses = [m for m, n in bt.mes.value_counts().sort_index().items()
             if n >= 20 and cob.get(m, 0) >= 0.5]
    print(f"Rasgos nuevos: {extra}\nMeses con xG por jugador (>=50% de partidos): {meses}")
    import os
    if os.environ.get("ENTRENO") == "desde_xg":
        # los dos brazos entrenan SOLO con partidos que tienen xG por jugador: mide
        # lo que aportan los rasgos sin que 2/3 de filas vacías los diluyan
        bt = bt[bt.mes >= meses[0]].reset_index(drop=True)
        meses = meses[2:]
        print(f"Entrenamiento solo desde {bt.mes.min()}; se prueban {meses}")
    filas = []
    for m in meses:
        a = A.predecir_mes(bt, cols, m)
        b = A.predecir_mes(bt, cols, m, extra=extra)
        filas.append(a[["match_id", "mes", "ambos_marcan", "p_ambos"]].merge(
            b[["match_id", "p_ambos"]].rename(columns={"p_ambos": "p_xi"}), on="match_id"))
        y = filas[-1].ambos_marcan
        d = (filas[-1].p_ambos - y) ** 2 - (filas[-1].p_xi - y) ** 2
        print(f"  {m}: n={len(y)}  mejora con xG de jugadores {d.mean()*100:+.2f} pts de Brier", flush=True)
    t = pd.concat(filas)
    d = (t.p_ambos - t.ambos_marcan) ** 2 - (t.p_xi - t.ambos_marcan) ** 2
    s = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    print(f"\nTOTAL {len(t)} partidos: oficial+xG jugadores vs oficial {s:+.2f}s "
          f"(Brier oficial {((t.p_ambos-t.ambos_marcan)**2).mean():.4f}, con xG {((t.p_xi-t.ambos_marcan)**2).mean():.4f})")
    import os
    t.to_csv(f"data/experimento_xg_jugador{'_' + os.environ['ENTRENO'] if os.environ.get('ENTRENO') else ''}.csv", index=False)


if __name__ == "__main__":
    main()
