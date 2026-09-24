"""
TODAS las combinaciones de las 8 variables candidatas, no solo sola+todas

`experimentos_rasgos.py` decidió limitarse a "cada candidata sola + todas
juntas" (10 configs) para no gastar demasiadas pasadas de 5 semillas. Pedido
explícito: probar las 256 combinaciones posibles (2^8) del conjunto de
candidatas, y medir ACIERTO (hit-rate) además de sigmas de Brier -- las dos
métricas pueden moverse en direcciones distintas (comprobado: árbitro+
calidad_plantilla mejora sigmas en resultado y tarjetas pero EMPEORA su
acierto frente a base+elo solo).

Con 256 configuraciones x 5 mercados, 5 semillas por config sale demasiado
caro (>1h). Se usa 2 semillas como cribado -- ruido de semilla mayor que el
estándar del proyecto (5), así que esto es un cribado, no una conclusión
definitiva. Los mejores candidatos que salgan aquí se reevalúan con el
protocolo completo de 5 semillas (evaluar_mercados.py / experimentos_rasgos.py)
antes de declarar nada.
"""
import os
import sys
import time
import itertools
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rasgos
import modelo_xgboost as M
import evaluar_mercados as EM

NUCLEO = ["base", "elo"]
CANDIDATAS = ["h2h", "h2h_profundo", "tabla", "boxscore", "arbitro", "clima",
             "rotacion", "calidad_plantilla"]
SEMILLAS_CRIBADO = (0, 1)


def todas_las_combinaciones():
    vistas = []
    for r in range(len(CANDIDATAS) + 1):
        vistas.extend(itertools.combinations(CANDIDATAS, r))
    return vistas


def evaluar_config(nombre, cfg, base, cols, ent, fecha_corte, cuotas):
    pmer_todos = EM.mercado_por_partido(cuotas, cfg)
    if pmer_todos is None:
        return None
    val = base[pd.to_datetime(base.fecha) > fecha_corte]
    val = val[val.match_id.isin(pmer_todos.index)]
    if len(val) < 20:
        return None
    y = val[nombre].values.astype(int)
    y_ent = ent[nombre].values.astype(int)
    if len(np.unique(y_ent)) < cfg["n_clases"]:
        return None
    preds = []
    for s in SEMILLAS_CRIBADO:
        modelo = M.entrenar(ent[cols].values, y_ent, cfg["n_clases"], semilla=s)
        p = M.probabilidades(modelo, val[cols].values, cfg["n_clases"])
        preds.append(p if cfg["n_clases"] == 3 else p[:, 1])
    pn = np.mean(preds, axis=0)

    if cfg["n_clases"] == 3:
        pm = pmer_todos.loc[val.match_id][[f"p_{l}" for l in cfg["lados"]]].values
        acierto_modelo = (pn.argmax(axis=1) == y).mean()
        acierto_mercado = (pm.argmax(axis=1) == y).mean()
    else:
        pm = pmer_todos.loc[val.match_id].values
        acierto_modelo = ((pn > 0.5).astype(int) == y).mean()
        acierto_mercado = ((pm > 0.5).astype(int) == y).mean()

    b_modelo = EM.brier(pn, y, cfg["n_clases"])
    b_mercado = EM.brier(pm, y, cfg["n_clases"])
    dif = b_mercado - b_modelo
    ee = dif.std(ddof=1) / np.sqrt(len(dif)) if len(dif) > 1 else np.nan
    sigmas = float(dif.mean() / ee) if ee else 0.0

    return {"n": len(val), "sigmas": sigmas, "acierto_modelo": acierto_modelo,
           "acierto_mercado": acierto_mercado,
           "acierto_dif": acierto_modelo - acierto_mercado}


def main():
    t0 = time.time()
    hist = M.cargar()
    if hist is None:
        return
    base_completa = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    grupos = rasgos.grupos_rasgo(base_completa)
    cuotas = EM.cargar_cuotas_crudas()
    if cuotas is None:
        print("Sin cuotas. Nada que evaluar.")
        return

    combos = todas_las_combinaciones()
    print(f"{len(combos)} combinaciones a probar, {SEMILLAS_CRIBADO} semillas "
          f"(cribado, no protocolo completo de 5).\n")

    filas = []
    for i, extra in enumerate(combos):
        nombre_config = "+".join(NUCLEO + list(extra)) if extra else "+".join(NUCLEO)
        cols = sum((grupos[g] for g in NUCLEO + list(extra)), [])
        base = base_completa[base_completa[cols].notna().all(axis=1)].reset_index(drop=True)
        if len(base) < M.MINIMO_ENTRENAMIENTO:
            continue
        corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
        ent = base.iloc[:corte]
        fecha_corte = pd.to_datetime(ent.fecha.max())

        for nombre, cfg in EM.MERCADOS.items():
            r = evaluar_config(nombre, cfg, base, cols, ent, fecha_corte, cuotas)
            if r is None:
                continue
            filas.append({"config": nombre_config, "n_extra": len(extra),
                         "mercado": nombre, **r})
        if (i + 1) % 32 == 0:
            tr = pd.DataFrame(filas)
            print(f"  [{i+1}/{len(combos)}] {time.time()-t0:.0f}s transcurridos")

    tabla = pd.DataFrame(filas)
    tabla.to_csv("data/barrido_combinatorio.csv", index=False)
    print(f"\nEscrito data/barrido_combinatorio.csv ({len(tabla)} filas, "
          f"{time.time()-t0:.0f}s totales)\n")

    print("=== Mejor config por SUMA de sigmas (todos los mercados) ===")
    suma = tabla.groupby("config")["sigmas"].sum().sort_values(ascending=False)
    print(suma.head(10))

    print("\n=== Mejor config por SUMA de acierto_dif (modelo - mercado) ===")
    suma_ac = tabla.groupby("config")["acierto_dif"].sum().sort_values(ascending=False)
    print(suma_ac.head(10))

    print("\n=== Por mercado, mejor sigmas y mejor acierto ===")
    for mercado, g in tabla.groupby("mercado"):
        mejor_s = g.loc[g["sigmas"].idxmax()]
        mejor_a = g.loc[g["acierto_dif"].idxmax()]
        print(f"  {mercado:20s}  sigmas: {mejor_s['config']:40s} {mejor_s['sigmas']:+.2f}s   "
              f"acierto: {mejor_a['config']:40s} {mejor_a['acierto_dif']*100:+.1f}pp")


if __name__ == "__main__":
    main()
