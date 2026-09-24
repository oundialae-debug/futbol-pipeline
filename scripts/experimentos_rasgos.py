"""
CADA VARIABLE NUEVA, SOLA, Y LUEGO COMBINADA -- NO SOLO ACUMULADA

Los últimos añadidos (box-score, H2H, tabla) se venían probando siempre
TODOS JUNTOS porque `columnas_rasgo()` los mezcla de golpe. Eso contesta
"¿la combinación actual mejora?" pero no "¿cuál de las nuevas es la que
empuja, y cuál la que estorba?" -- que es lo que hace falta para decidir
qué se queda y qué se quita antes de gastar más cuota en variables nuevas
(árbitro, tiempo, alineación).

Usa exactamente la misma maquinaria que evaluar_mercados.py (mismos
mercados, mismo entrenamiento a 5 semillas, mismo corte temporal, mismo
criterio de significación) para que los números sean comparables entre
configuraciones.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rasgos
import modelo_xgboost as M
import evaluar_mercados as EM

# "base" y "elo" son el núcleo ya establecido antes de esta ronda de
# experimentos (probado, documentado, se queda siempre). Lo demás se prueba
# solo y combinado.
NUCLEO = ["base", "elo"]
CANDIDATAS = ["h2h", "h2h_profundo", "tabla", "boxscore", "arbitro", "clima",
             "rotacion", "calidad_plantilla"]


def configuraciones():
    """
    Con 3 candidatas el conjunto potencia completo (8 configs) era
    manejable. Con 6 serían 64 -- demasiadas pasadas de 5 semillas x 5
    mercados para lo que aporta. Se prueba cada candidata SOLA contra el
    núcleo (para saber cuál empuja y cuál estorba, que es el objetivo real)
    y la combinación de TODAS juntas (para ver si se refuerzan o se
    estorban entre ellas). Si el resultado pide explorar un subconjunto
    intermedio, se añade a mano, no por fuerza bruta.
    """
    vistas = [[]]
    vistas.extend([c] for c in CANDIDATAS)
    vistas.append(list(CANDIDATAS))
    return vistas


def main():
    hist = M.cargar()
    if hist is None:
        return
    base_completa = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    grupos = rasgos.grupos_rasgo(base_completa)
    for g, cols in grupos.items():
        print(f"  grupo {g:10s}: {len(cols)} columnas")
    print()

    cuotas = EM.cargar_cuotas_crudas()
    if cuotas is None:
        print("Sin cuotas de ningún tipo. Nada que evaluar.")
        return

    filas = []
    for extra in configuraciones():
        nombre_config = "+".join(NUCLEO + extra) if extra else "+".join(NUCLEO)
        cols = sum((grupos[g] for g in NUCLEO + extra), [])
        base = base_completa[base_completa[cols].notna().all(axis=1)].reset_index(drop=True)
        if len(base) < M.MINIMO_ENTRENAMIENTO:
            print(f"[{nombre_config}] solo {len(base)} filas utilizables -- se omite")
            continue
        corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
        ent = base.iloc[:corte]
        fecha_corte = pd.to_datetime(ent.fecha.max())

        print(f"=== {nombre_config} ({len(cols)} rasgos, {len(base)} partidos "
              f"utilizables, entreno hasta {fecha_corte.date()}) ===")
        for nombre, cfg in EM.MERCADOS.items():
            y_ent = ent[nombre].values.astype(int)
            if len(np.unique(y_ent)) < cfg["n_clases"]:
                print(f"  {nombre:20s}  sin ambas clases en entrenamiento")
                continue
            r = EM.evaluar_uno(nombre, cfg, base, cols, ent, fecha_corte, cuotas)
            if not r["evaluable"]:
                print(f"  {nombre:20s}  NO EVALUABLE -- {r['motivo']}")
                continue
            print(f"  {nombre:20s}  n={r['partidos']:4d}  "
                  f"modelo {r['brier_modelo']:.4f}  mercado {r['brier_mercado']:.4f}  "
                  f"{r['sigmas']:+.2f}s")
            filas.append({"config": nombre_config, "mercado": nombre,
                         "n": r["partidos"], "sigmas": r["sigmas"],
                         "brier_modelo": r["brier_modelo"]})
        print()

    tabla = pd.DataFrame(filas)
    tabla.to_csv("data/experimentos_rasgos.csv", index=False)
    print("Escrito data/experimentos_rasgos.csv\n")

    print("Mejor configuración por mercado (mayor sigmas, es decir, menos peor):")
    for mercado, g in tabla.groupby("mercado"):
        mejor = g.loc[g["sigmas"].idxmax()]
        print(f"  {mercado:20s}  {mejor['config']:30s}  {mejor['sigmas']:+.2f}s")


if __name__ == "__main__":
    main()
