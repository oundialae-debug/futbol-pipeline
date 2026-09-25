"""
LA PRUEBA QUE DECIDE: ¿es nuestra probabilidad mejor que la de la casa?

POR QUÉ ESTA Y NO OTRA
----------------------
`modelo_xgboost.py` compara contra la frecuencia de la liga y contra los
rasgos barajados. Eso demuestra que el modelo aprendió ALGO, no que sirva para
apostar. Para apostar solo importa una comparación: nuestra probabilidad
contra la del mercado, sobre los mismos partidos, fuera de muestra.

Un modelo con Brier 0.63 parece decente hasta que la casa saca 0.58. Entonces
cada apuesta que le hagas es dinero regalado, por muy bonito que sea el
modelo.

CÓMO SE MIDE LIMPIO
-------------------
1. Solo partidos POSTERIORES al corte de entrenamiento. Si el modelo vio el
   partido, su acierto no significa nada.
2. La probabilidad del mercado se desmarigina (normalizar 1/cuota a que sume
   1), que es su opinión sin el peaje.
3. El error se agrupa POR PARTIDO. Aquí cada partido es una observación y ya
   está, pero se calcula el error de la diferencia emparejada: el mismo
   partido lo acierta o lo falla los dos, y comparar medias sueltas infla el
   margen de error.
4. Se compara la DIFERENCIA de Brier partido a partido, no dos medias. Es la
   prueba emparejada, que es mucho más sensible y es la correcta aquí.

LO QUE ESCRIBE
--------------
`data/validacion_modelo.json`, que es lo que mira `boletin.py` para decidir si
abre la puerta. Nadie se da el visto bueno a sí mismo: el modelo no escribe su
propia validación.
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rasgos
import modelo_xgboost as M

RUTA_CUOTAS = "data/backtest_valor.csv"
RUTA_SALIDA = "data/validacion_modelo.json"
SIGMAS_MINIMAS = 2.0

LADOS = ["home", "draw", "away"]     # mismo orden que resultado: 0,1,2


def probabilidad_mercado(cuotas):
    """{lado: cuota} -> probabilidades desmarginadas, o None."""
    if set(cuotas) != set(LADOS) or any(c <= 1 for c in cuotas.values()):
        return None
    inv = np.array([1 / cuotas[l] for l in LADOS])
    return inv / inv.sum()


def main():
    if not os.path.exists(RUTA_CUOTAS):
        print(f"Falta {RUTA_CUOTAS}")
        return
    hist = M.cargar()
    if hist is None:
        return

    base = rasgos.construir(hist).sort_values("fecha")
    cols = rasgos.columnas_rasgo_default(base)
    base, ent, fecha_corte = M.partir(base.reset_index(drop=True), cols)
    ent = ent[ent[M.ORIGEN_OBJETIVO["resultado"]].notna()]
    val = base[pd.to_datetime(base.fecha) > fecha_corte]
    print(f"Entrenamiento hasta {fecha_corte.date()}. "
          f"Solo se evaluan partidos posteriores.\n")

    m = M.entrenar(ent[cols].values, ent["resultado"].values.astype(int), 3)

    # --- probabilidad del mercado, por partido ---
    # Las DOS fuentes: backtest_valor.csv (se sobrescribe) y
    # cuotas_cosechadas.csv (acumula). Si solo se leyera la primera, la fuente
    # que crece se quedaria fuera sin dar ningun error.
    import aporta_algo as A
    mercado = A.probabilidades_de_mercado()
    if mercado is None or mercado.empty:
        print("Sin cuotas de 1X2 utilizables.")
        return
    print(f"Mercado: {len(mercado)} partidos con 1X2.")

    # --- cruce: partidos con cuotas Y posteriores al corte ---
    val = val[val.match_id.isin(mercado.index)]
    val = val[pd.to_datetime(val.fecha) > fecha_corte]
    if len(val) < 20:
        print(f"\nSolo {len(val)} partidos con cuotas fuera de muestra. "
              f"No alcanza para decidir nada.")
        json.dump({"bate_al_mercado": False, "partidos": int(len(val)),
                   "motivo": f"solo {len(val)} partidos evaluables"},
                  open(RUTA_SALIDA, "w"), indent=2)
        return

    pm = mercado.loc[val.match_id].values
    pn = M.probabilidades(m, val[cols].values, 3)
    y = val["resultado"].values.astype(int)
    uno = np.zeros((len(y), 3)); uno[np.arange(len(y)), y] = 1

    b_nuestro = ((pn - uno) ** 2).sum(axis=1)
    b_mercado = ((pm - uno) ** 2).sum(axis=1)
    dif = b_mercado - b_nuestro          # positivo = somos MEJORES
    ee = dif.std(ddof=1) / np.sqrt(len(dif))
    sigmas = dif.mean() / ee if ee else 0.0

    print(f"\n{len(val)} partidos fuera de muestra CON cuotas\n")
    print(f"  Brier del mercado : {b_mercado.mean():.4f}")
    print(f"  Brier nuestro     : {b_nuestro.mean():.4f}")
    print(f"  diferencia        : {dif.mean():+.4f}  "
          f"(+ = mejores)  ±{ee:.4f}  ->  {sigmas:+.2f} sigmas")

    bate = bool(dif.mean() > 0 and sigmas >= SIGMAS_MINIMAS)
    motivo = (f"Brier {b_nuestro.mean():.4f} contra {b_mercado.mean():.4f} "
              f"del mercado")
    json.dump({"bate_al_mercado": bate, "sigmas": float(sigmas),
               "partidos": int(len(val)), "brier_modelo": float(b_nuestro.mean()),
               "brier_mercado": float(b_mercado.mean()), "motivo": motivo},
              open(RUTA_SALIDA, "w"), indent=2)

    print()
    if bate:
        print(f"  PUERTA ABIERTA: batimos al mercado por {sigmas:.2f} sigmas.")
    elif dif.mean() > 0:
        print(f"  PUERTA CERRADA: vamos por delante pero solo "
              f"{sigmas:.2f} sigmas. No se distingue del azar.")
    else:
        print(f"  PUERTA CERRADA: el mercado es MEJOR que el modelo. "
              f"Apostarle es regalar dinero.")
    print(f"\nEscrito {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
