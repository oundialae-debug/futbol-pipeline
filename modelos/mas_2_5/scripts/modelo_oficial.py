"""
MODELO OFICIAL de Más/Menos 2.5 goles (29/09/2026).

Qué es (elegido en las pruebas documentadas en CLAUDE.md de esta carpeta):
  p = 50% XGBoost de 28 rasgos  +  50% logística de tres sumas
  - XGBoost 28: tiros a puerta, tiros fuera, pases, puntos (medias de 8,
    propios y del rival, loc/vis/dif), liga y g/a por 90 de delanteros y
    medios titulares (temporada anterior). 5 semillas.
  - logística: suma de xG/90 + xA/90 de los 22 titulares (box-score, desde
    abr 2025), suma de tiros a puerta de los dos equipos y suma de g/a.
  - Entrenado con TODO lo jugado (desde 2022/23; lo que no tenga un dato
    entra con hueco).
  Mes a mes, oct 2025 - sep 2026: -0.48s contra la media de casas (empate
  práctico: acierta 58.4%, igual que la casa). NO bate a la casa.

Modos:
  python scripts/modelo_oficial.py pronosticar PARTIDOS.csv [CUOTAS.csv]
      PARTIDOS.csv con el formato de data/ambos_hoy/partidos.csv del repo
      padre (match_id, fecha, local_id, local, visitante_id, visitante y, si
      ya hay once, local_ids/local_formacion/visitante_ids/...). CUOTAS.csv
      como data/ambos_hoy/cuotas.csv (se usa "Total Goals 2.5").
      Añade esos partidos al histórico SIN resultado, calcula sus rasgos solo
      con partidos anteriores, entrena con todo lo jugado y predice.
      Escribe data/pronostico_mas25.md y .csv.
  python scripts/modelo_oficial.py comprobar
      Hace lo mismo con los partidos de sep 2026 como si fueran futuros
      (quita su resultado) y los compara con la cuota media de football-data.
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import modelo_xgboost as M, rasgos_mas25 as R

SEMILLAS = range(5)
SUMAS = ["xga_suma", "tiros_suma", "ga_suma"]


def rasgos(hist):
    bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"),
                     pd.read_csv("data/historico_h2h_profundo.csv"))
    bc = bc.merge(R.xg_xa_jugador(hist), on="match_id", how="left")
    bc["xga_suma"] = bc.loc_xg90 + bc.vis_xg90 + bc.loc_xa90 + bc.vis_xa90
    bc["tiros_suma"] = (bc.loc_m_shots_on_target + bc.vis_m_shots_on_target
                        + bc.loc_m_contra_shots_on_target + bc.vis_m_contra_shots_on_target)
    bc["ga_suma"] = bc.loc_cp_del_ga90 + bc.vis_cp_del_ga90
    return bc


def entrenar_y_predecir(hist, ids_futuros):
    """hist incluye los partidos futuros SIN goles; se entrena con el resto."""
    bc = rasgos(hist)
    cols = R.columnas_produccion(bc)
    futuro = bc.match_id.isin(ids_futuros)
    ent = bc[~futuro & bc.goles_l.notna() & bc.goles_v.notna()]
    val = bc[futuro].copy()
    y = ent.mas_2_5.values.astype(int)
    px = np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s), val[cols].values, 2)[:, 1]
                  for s in SEMILLAS], axis=0)
    e = ent.dropna(subset=SUMAS)
    sc = StandardScaler().fit(e[SUMAS])
    lr = LogisticRegression().fit(sc.transform(e[SUMAS]), e.mas_2_5.astype(int))
    pl = lr.predict_proba(sc.transform(val[SUMAS].fillna(e[SUMAS].mean())))[:, 1]
    val["p_mas25"] = (px + pl) / 2
    val["p_xgb"], val["p_logistica"] = px, pl
    val["con_once"] = val.loc_cp_conocidos.fillna(0) > 0
    print(f"Entrenado con {len(ent)} partidos jugados; {len(val)} a predecir.")
    return val


def cargar_hist():
    with contextlib.redirect_stdout(io.StringIO()):
        return M.cargar()


def mercado_de_cuotas(cuotas):
    c = cuotas[cuotas.mercado == "Total Goals 2.5"].copy()
    c["lado"] = c.lado.str.lower()
    filas = []
    for (mid, casa), g in c.groupby(["match_id", "casa"]):
        d = dict(zip(g.lado, g.cuota))
        if {"over", "under"} <= set(d) and min(d["over"], d["under"]) > 1:
            po = (1 / d["over"]) / (1 / d["over"] + 1 / d["under"])
            filas.append((mid, po, d["over"], d["under"]))
    if not filas:
        return pd.DataFrame(columns=["match_id", "p_mercado", "cuota_mas", "cuota_menos"])
    m = pd.DataFrame(filas, columns=["match_id", "p", "o", "u"])
    return m.groupby("match_id").agg(p_mercado=("p", "median"), cuota_mas=("o", "median"),
                                     cuota_menos=("u", "median")).reset_index()


def pronosticar(ruta_partidos, ruta_cuotas=None):
    hist = cargar_hist()
    nuevos = pd.read_csv(ruta_partidos)
    nuevos = nuevos[~nuevos.match_id.isin(hist.match_id)].copy()
    if nuevos.empty:
        print("Ningún partido nuevo (ya están todos en el histórico)."); return
    f = pd.to_datetime(nuevos.fecha, utc=True)
    nuevos["temporada"] = np.where(f.dt.month >= 7, f.dt.year, f.dt.year - 1)
    ult = hist.sort_values("fecha").drop_duplicates("local_id", keep="last").set_index("local_id")
    nuevos["liga_id"] = nuevos.local_id.map(ult.liga_id)
    nuevos["liga"] = nuevos.local_id.map(ult.liga)
    nuevos["goles_l"] = nuevos["goles_v"] = np.nan
    sin_liga = nuevos.liga_id.isna().sum()
    if sin_liga:
        print(f"[!] {sin_liga} partidos con un local que no está en el histórico: se omiten.")
        nuevos = nuevos[nuevos.liga_id.notna()]
    keep = [c for c in nuevos.columns if c in hist.columns]
    hist = pd.concat([hist, nuevos[keep]], ignore_index=True)
    val = entrenar_y_predecir(hist, set(nuevos.match_id))
    val = val.merge(nuevos[["match_id", "local", "visitante", "fecha"]], on="match_id", suffixes=("", "_n"))
    if ruta_cuotas:
        val = val.merge(mercado_de_cuotas(pd.read_csv(ruta_cuotas)), on="match_id", how="left")
    else:
        val["p_mercado"] = val["cuota_mas"] = val["cuota_menos"] = np.nan
    val["lado"] = np.where(val.p_mas25 >= 0.5, "más", "menos")
    p_lado = np.where(val.lado == "más", val.p_mas25, 1 - val.p_mas25)
    val["cuota_minima"] = 1 / p_lado
    cuota_lado = np.where(val.lado == "más", val.cuota_mas, val.cuota_menos)
    val["ve"] = p_lado * cuota_lado - 1
    salida = val[["match_id", "fecha_n", "local", "visitante", "p_mas25", "p_mercado", "lado",
                  "cuota_minima", "cuota_mas", "cuota_menos", "ve", "con_once"]].rename(columns={"fecha_n": "fecha"})
    salida.to_csv("data/pronostico_mas25.csv", index=False)
    lin = ["# Más/Menos 2.5, modelo oficial\n",
           "Modelo: 50% XGBoost 28 + 50% logística (xG+xA de los titulares, tiros, g/a). "
           "Mes a mes a -0.48s de la casa: **no la bate**; esto no es una recomendación de apuesta.\n",
           "| partido | fecha | modelo: más | casa: más | lado | cuota mínima | cuota mediana | VE | once |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in salida.itertuples():
        cm = r.cuota_mas if r.lado == "más" else r.cuota_menos
        lin.append(f"| {r.local} - {r.visitante} | {str(r.fecha)[:16]} | {r.p_mas25*100:.0f}% | "
                   f"{'-' if pd.isna(r.p_mercado) else f'{r.p_mercado*100:.0f}%'} | {r.lado} | {r.cuota_minima:.2f} | "
                   f"{'-' if pd.isna(cm) else f'{cm:.2f}'} | {'-' if pd.isna(r.ve) else f'{r.ve*100:+.1f}%'} | "
                   f"{'sí' if r.con_once else 'sin once'} |")
    open("data/pronostico_mas25.md", "w", encoding="utf-8").write("\n".join(lin) + "\n")
    print("\n".join(lin))


def comprobar():
    hist = cargar_hist()
    f = pd.to_datetime(hist.fecha, format="mixed", utc=True)
    ids = set(hist.loc[(f >= "2026-09-01") & hist.goles_l.notna(), "match_id"])
    reales = hist.set_index("match_id").loc[list(ids), ["goles_l", "goles_v"]]
    h2 = hist.copy()
    h2.loc[h2.match_id.isin(ids), ["goles_l", "goles_v"]] = np.nan     # como si no se hubieran jugado
    val = entrenar_y_predecir(h2, ids).set_index("match_id")
    y = ((reales.goles_l + reales.goles_v) > 2.5).astype(int).reindex(val.index)
    fd = pd.read_csv("data/cuotas_football_data.csv").set_index("match_id")
    pm = ((1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])).reindex(val.index)
    ok = pm.notna()
    b, bm = 2 * (val.p_mas25 - y) ** 2, 2 * (pm - y) ** 2
    d = (bm - b)[ok]
    print(f"sep 2026, {ok.sum()} partidos con cuota: Brier modelo {b[ok].mean():.4f}, casa {bm[ok].mean():.4f}, "
          f"modelo vs casa {d.mean()/(d.std(ddof=1)/np.sqrt(len(d))):+.2f}s; acierto modelo "
          f"{((val.p_mas25[ok] > .5) == y[ok]).mean()*100:.1f}% casa {((pm[ok] > .5) == y[ok]).mean()*100:.1f}%")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "pronosticar":
        pronosticar(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif len(sys.argv) >= 2 and sys.argv[1] == "comprobar":
        comprobar()
    else:
        print(__doc__)
