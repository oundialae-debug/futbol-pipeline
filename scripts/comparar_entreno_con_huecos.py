"""
¿Entrenar aceptando rasgos vacíos mejora el modelo? (25/09/2026)

Al añadir 2024/25 al histórico, evaluar_mercados.py tiraba 2.221 de sus
2.223 partidos: exigía TODOS los rasgos también al entrenar, y 2024/25 casi
no trae xG. La prueba de ambos_marcan (modelos/ambos_marcan) sí entrenaba
con huecos y ahí mejoraba el arranque de temporada a +3.5 sigmas.

Mismos partidos de validación en las dos variantes (los completos,
posteriores al corte). Solo cambia el entrenamiento:
  estricto:   solo partidos con todos los rasgos (lo de siempre)
  con huecos: todo lo anterior al corte, con NaN donde falte algo
Dos comparaciones por mercado, 5 semillas:
  - modelo contra modelo, Brier emparejado sobre TODA la validación
    (no hace falta cuota para esto)
  - cada variante contra el mercado, sobre los partidos con cuota
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM


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
    cols = rasgos.columnas_rasgo_default(base_todo)
    base, ent_huecos, fecha_corte = EM.partir(base_todo, cols, con_huecos=True)
    _, ent_estricto, _ = EM.partir(base_todo, cols, con_huecos=False)
    val = base[pd.to_datetime(base.fecha) > fecha_corte]
    cuotas = EM.cargar_cuotas_crudas()
    print(f"Corte {fecha_corte.date()}. Validación: {len(val)} partidos completos.")
    print(f"Entrenamiento: estricto {len(ent_estricto)} | con huecos {len(ent_huecos)}\n")
    print(f"{'mercado':18s} {'n':>4s} {'huecos vs estricto':>19s} {'n cuota':>8s} "
          f"{'estricto vs merc':>17s} {'huecos vs merc':>15s}")
    suma = {"estricto": 0.0, "huecos": 0.0}
    filas = []
    for nombre, cfg in EM.MERCADOS.items():
        n = cfg["n_clases"]
        origen = EM.ORIGEN_OBJETIVO[nombre]
        v = val[val[origen].notna()]
        y = v[nombre].values.astype(int)
        b = {}
        for clave, ent in (("estricto", ent_estricto), ("huecos", ent_huecos)):
            ent = ent[ent[origen].notna()]
            b[clave] = EM.brier(predecir(ent, v, cols, nombre, n), y, n)
        pmer = EM.mercado_por_partido(cuotas, cfg)
        cc = v.match_id.isin(pmer.index).values
        pm = (pmer.loc[v.match_id[cc]][[f"p_{l}" for l in cfg["lados"]]].values if n == 3
              else pmer.loc[v.match_id[cc]].values)
        bm = EM.brier(pm, y[cc], n)
        s_est, s_hue = sig(bm - b["estricto"][cc]), sig(bm - b["huecos"][cc])
        suma["estricto"] += s_est
        suma["huecos"] += s_hue
        s_par = sig(b["estricto"] - b["huecos"])
        print(f"{nombre:18s} {len(v):4d} {s_par:+18.2f}s {cc.sum():8d} {s_est:+16.2f}s {s_hue:+14.2f}s")
        filas.append({"mercado": nombre, "n_validacion": len(v), "huecos_vs_estricto": s_par,
                      "n_cuota": int(cc.sum()), "estricto_vs_mercado": s_est,
                      "huecos_vs_mercado": s_hue})
    print(f"\nSuma de sigmas contra el mercado: estricto {suma['estricto']:+.2f}  "
          f"con huecos {suma['huecos']:+.2f}")
    pd.DataFrame(filas).to_csv("data/comparar_entreno_con_huecos.csv", index=False)
    print("Escrito data/comparar_entreno_con_huecos.csv")


if __name__ == "__main__":
    main()
