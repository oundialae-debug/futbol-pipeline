"""
Modelo contra el cierre de Pinnacle en TODA la validación (25/09/2026).

Hasta hoy, "contra el mercado" eran ~219 partidos: las cuotas cosechadas de
Highlightly empiezan el 24/08/2026. Con football-data.co.uk
(cuotas_football_data.py) hay precio de cierre para casi todo el histórico,
así que la validación entera (574 partidos, final de 2025/26 + inicio de
2026/27) tiene precio. Solo 1X2 y más de 2.5: football-data no trae ambos
marcan (comprobado en las cabeceras, data/football_data/columnas.md).

Antes de creerse nada: en los partidos que tienen las dos fuentes, el
precio de football-data tiene que parecerse al cosechado de Highlightly
(mismo partido, mismo mercado). Si no, el emparejamiento o la orientación
local/visitante está mal y los números saldrían plausibles y falsos.
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

RUTA_FD = "data/cuotas_historicas_fd.csv"


def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def main():
    fd = pd.read_csv(RUTA_FD).set_index("match_id")
    cuotas = EM.cargar_cuotas_crudas()

    # 1. comprobación contra la fuente vieja, partido a partido
    print("Comprobación: football-data contra lo cosechado de Highlightly")
    for nombre, cols_fd in (("resultado", ["p_local", "p_empate", "p_visitante"]),
                            ("mas_2_5", ["p_mas_2_5"])):
        cfg = EM.MERCADOS[nombre]
        pm = EM.mercado_por_partido(cuotas, cfg)
        comun = pm.index.intersection(fd.dropna(subset=cols_fd).index)
        a = (pm.loc[comun][[f"p_{l}" for l in cfg["lados"]]].values if cfg["n_clases"] == 3
             else pm.loc[comun].values.reshape(-1, 1))
        b = fd.loc[comun, cols_fd].values
        corr = np.corrcoef(a[:, 0], b[:, 0])[0, 1]
        print(f"  {nombre:10s} {len(comun):4d} partidos en común, diferencia media "
              f"{np.abs(a - b).mean()*100:.1f} puntos, correlación {corr:.3f}")

    # 2. modelo contra Pinnacle en toda la validación
    hist = M.cargar()
    base_todo = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    cols = rasgos.columnas_rasgo_default(base_todo)
    base, ent_todo, fecha_corte = M.partir(base_todo, cols)
    val = base[pd.to_datetime(base.fecha) > fecha_corte]
    f_ini = pd.Timestamp("2026-07-01", tz="UTC")
    print(f"\nValidación: {len(val)} partidos posteriores al {fecha_corte.date()}\n")
    print(f"{'mercado':10s} {'tramo':16s} {'n':>4s} {'modelo':>7s} {'mercado':>8s} {'sigmas':>7s}  fuente")
    for nombre, cols_fd in (("resultado", ["p_local", "p_empate", "p_visitante"]),
                            ("mas_2_5", ["p_mas_2_5"])):
        cfg = EM.MERCADOS[nombre]
        n = cfg["n_clases"]
        v = val[val.match_id.isin(fd.dropna(subset=cols_fd).index)]
        ent = ent_todo[ent_todo[M.ORIGEN_OBJETIVO[nombre]].notna()]
        y = v[nombre].values.astype(int)
        ps = []
        for s in EM.SEMILLAS:
            p = M.probabilidades(M.entrenar(ent[cols].values, ent[nombre].values.astype(int), n, semilla=s),
                                 v[cols].values, n)
            ps.append(p if n == 3 else p[:, 1])
        pn = np.mean(ps, axis=0)
        pm = fd.loc[v.match_id, cols_fd].values
        if n == 2:
            pm = pm[:, 0]
        bn, bm = EM.brier(pn, y, n), EM.brier(pm, y, n)
        fuentes = fd.loc[v.match_id, "fuente_1x2" if n == 3 else "fuente_mas_2_5"].value_counts().to_dict()
        fv = pd.to_datetime(v.fecha, utc=True).values
        for tramo, m in (("final 2025/26", fv < f_ini.to_datetime64()),
                         ("inicio 2026/27", fv >= f_ini.to_datetime64()),
                         ("todo", np.ones(len(y), bool))):
            print(f"{nombre:10s} {tramo:16s} {m.sum():4d} {bn[m].mean():7.4f} {bm[m].mean():8.4f} "
                  f"{sig(bm[m] - bn[m]):+6.2f}s  {fuentes if tramo == 'todo' else ''}")


if __name__ == "__main__":
    main()
