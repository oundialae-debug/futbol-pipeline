"""
La cuota de cierre como VARIABLE del modelo (25/09/2026, idea del usuario).

El 24/09 no se pudo probar: las cuotas cosechadas solo cubrían el periodo de
validación, no el de entrenamiento. Con football-data.co.uk
(cuotas_football_data.py + btts_implicito.py) hay precio de cierre para
5.671 de 5.694 partidos, entrenamiento incluido.

Rasgos de mercado (prefijo mkt_): p_local, p_empate, p_visitante,
p_mas_2_5 (sin margen), lambda_l, lambda_v y p_btts_implicito (Poisson
ajustado al 1X2 + más/menos 2.5). Son precios de antes del pitido: no hay
fuga por construcción.

Tres modelos, mismos partidos de validación, 5 semillas, entrenamiento con
huecos (M.partir):
  produccion           los 99 rasgos de siempre
  produccion+mercado   + los 7 rasgos mkt_
  solo mercado         solo los 7 rasgos mkt_ (¿el modelo añade algo al precio?)
Comparaciones:
  - contra el cierre de football-data (resultado y más de 2.5), toda la
    validación con precio
  - contra lo cosechado de Highlightly (los 5 mercados, ~219 partidos):
    para ambos marcan, córners y tarjetas es el único precio real que hay
  - produccion+mercado contra produccion, emparejado, toda la validación
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

MKT = ["mkt_p_local", "mkt_p_empate", "mkt_p_visitante", "mkt_p_mas_2_5",
       "mkt_lambda_l", "mkt_lambda_v", "mkt_p_btts_implicito"]
FD_COLS = {"resultado": ["p_local", "p_empate", "p_visitante"], "mas_2_5": ["p_mas_2_5"]}


def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def predecir(ent, val, cols, nombre, n):
    y = ent[nombre].values.astype(int)
    ps = []
    for s in EM.SEMILLAS:
        p = M.probabilidades(M.entrenar(ent[cols].values, y, n, semilla=s), val[cols].values, n)
        ps.append(p if n == 3 else p[:, 1])
    return np.mean(ps, axis=0)


def main():
    hist = M.cargar()
    base_todo = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    prod = rasgos.columnas_rasgo_default(base_todo)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    mk = fd.rename(columns={c.replace("mkt_", ""): c for c in MKT})[["match_id"] + MKT]
    base_todo = base_todo.merge(mk, on="match_id", how="left")
    base, ent_todo, fecha_corte = M.partir(base_todo, prod)
    val = base[(pd.to_datetime(base.fecha) > fecha_corte) & base[MKT].notna().all(axis=1)]
    fdi = fd.set_index("match_id")
    cuotas = EM.cargar_cuotas_crudas()
    configs = {"produccion": prod, "produccion+mercado": prod + MKT, "solo mercado": MKT}
    print(f"Validación: {len(val)} partidos con precio (posteriores al {fecha_corte.date()}).\n")

    filas = []
    for nombre, cfg in EM.MERCADOS.items():
        n = cfg["n_clases"]
        v = val[val[M.ORIGEN_OBJETIVO[nombre]].notna()]
        ent = ent_todo[ent_todo[M.ORIGEN_OBJETIVO[nombre]].notna()]
        y = v[nombre].values.astype(int)
        b = {k: EM.brier(predecir(ent, v, c, nombre, n), y, n) for k, c in configs.items()}
        print(f"== {nombre} ({len(v)} partidos) ==")
        print(f"  produccion+mercado vs produccion: {sig(b['produccion'] - b['produccion+mercado']):+.2f}s")
        refs = []
        if nombre in FD_COLS:
            pm = fdi.loc[v.match_id, FD_COLS[nombre]].values
            refs.append(("cierre football-data", np.ones(len(v), bool), pm if n == 3 else pm[:, 0]))
        ph = EM.mercado_por_partido(cuotas, cfg)
        cc = v.match_id.isin(ph.index).values
        pmh = (ph.loc[v.match_id[cc]][[f"p_{l}" for l in cfg["lados"]]].values if n == 3
               else ph.loc[v.match_id[cc]].values)
        refs.append(("cosechado Highlightly", cc, pmh))
        for ref, msk, pm in refs:
            bm = EM.brier(pm, y[msk], n)
            linea = "  ".join(f"{k} {sig(bm - b[k][msk]):+.2f}s" for k in configs)
            print(f"  contra {ref:22s} (n={msk.sum():3d}): {linea}")
            filas += [{"mercado": nombre, "referencia": ref, "n": int(msk.sum()), "modelo": k,
                       "sigmas": sig(bm - b[k][msk])} for k in configs]
        print()
    pd.DataFrame(filas).to_csv("data/cuota_como_variable.csv", index=False)
    print("Escrito data/cuota_como_variable.csv  (positivo = el modelo gana al mercado)")


if __name__ == "__main__":
    main()
