"""
TU PLAN EXACTO, EJECUTADO SOBRE PARTIDOS REALES

EL PLAN
-------
  1. un modelo que pronostica futbol
  2. buscar value bets en TUS 8 casas
  3. apostar con Kelly partido

El razonamiento es correcto: si el modelo es mejor que el mercado, eso gana
dinero a largo plazo. La pregunta no es si el plan es bueno -- lo es -- sino
si nuestro modelo cumple la condicion de la que cuelga todo.

Asi que en vez de discutirlo, se ejecuta. Mismo modelo, mismas cuotas reales,
168 partidos que el modelo NO vio al entrenar, y se resuelve contra lo que
paso de verdad.

LAS TRES PIEZAS NO SE MULTIPLICAN: SON UNA CADENA
--------------------------------------------------
Esto es lo que el plan esconde y lo que esta simulacion hace visible.

  - El STAKE no crea ventaja. Kelly sobre ventaja negativa pierde mas
    despacio, no gana. Ya medido en gestion_banca.py.
  - Las 8 CASAS no crean ventaja. Bajan el peaje del 6,2% al ~2,7%. Bajan el
    liston que el modelo tiene que superar; no le ayudan a superarlo.
  - Las VALUE BETS no crean ventaja, y son el caso sutil: "value" significa
    "la cuota paga mas de lo que dice MI modelo". Si el modelo es peor que el
    mercado, ese filtro selecciona justo los partidos donde el modelo esta
    MAS equivocado.

La tercera es contraintuitiva, asi que la simulacion la mide aparte,
comparando apostar con filtro de valor contra apostar a ciegas.

EL CONTRAFACTUAL
----------------
Tambien se simula que pasaria si el modelo fuera mejor de lo que es, subiendo
artificialmente su calidad. Asi se ve cuanta mejora haria falta para que el
plan gane, que es el numero util: dice si estamos cerca o lejos.

UNA SOLA TRAYECTORIA NO DICE NADA
---------------------------------
La primera version de este fichero enseñaba UNA secuencia de 226 apuestas y
daba la banca final como si fuera el resultado. Con Kelly y caidas del 70%,
esa cifra es casi toda suerte del orden en que cayeron los partidos.

Se vio porque el contrafactual se contradecia: con empujon del 2% el modelo
seguia siendo PEOR que el mercado en Brier (0.5921 contra 0.5762) y aun asi
"ganaba" un 32%. Eso es imposible -- no se puede ganar apostando contra un
precio con un modelo peor que ese precio -- asi que la cifra era ruido.

Ahora se remuestrean los partidos con reposicion muchas veces y se da la
MEDIANA, el peor 10% y en que porcentaje de trayectorias se acaba perdiendo.
La comprobacion de coherencia (el Brier del modelo empujado contra el del
mercado) se imprime al lado, para que no vuelva a colar un imposible.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rasgos
import modelo_xgboost as M
import evaluar_contra_mercado as E
import aporta_algo as A
import gestion_banca as gb

BANCA_INICIAL = 1000.0
# 8 casas. Si no coinciden con las tuyas da igual para esta prueba: lo que
# importa es CUANTAS son, porque de eso depende el margen que pagas.
N_CASAS = 8


def cuotas_por_partido(casas_permitidas):
    """{match_id: {lado: (mejor_cuota, casa)}} usando solo esas casas."""
    d = A.cargar_cuotas_1x2()
    d = d[d.casa.isin(casas_permitidas)]
    fuera = {}
    for (mid, lado), g in d.groupby(["match_id", "lado"]):
        i = g.cuota.idxmax()
        fuera.setdefault(mid, {})[lado] = (g.loc[i, "cuota"], g.loc[i, "casa"])
    return fuera


def simular(val, pn, mejores, umbral_valor, usar_valor=True,
            empujon=0.0, banca=BANCA_INICIAL):
    """
    Recorre los partidos en orden y apuesta.

    `empujon` mueve la probabilidad del modelo HACIA el resultado real, para
    simular un modelo mejor del que tenemos. Con 0.0 es el modelo real. Es
    trampa a proposito y solo sirve para el contrafactual.
    """
    banca_actual = banca
    pico = banca
    caida = 0.0
    apuestas = aciertos = 0
    historial = [banca]
    for fila in range(len(val)):
        mid = val.iloc[fila]["match_id"]
        y = int(val.iloc[fila]["resultado"])
        if mid not in mejores:
            continue
        p = pn[fila].copy()
        if empujon:
            p = p * (1 - empujon)
            p[y] += empujon
        for i, lado in enumerate(E.LADOS):
            if lado not in mejores[mid]:
                continue
            cuota, casa = mejores[mid][lado]
            if usar_valor:
                ap = gb.Apuesta(f"{mid}", p[i], cuota, error_modelo=0.0)
                f, _ = gb.decidir(ap, ventaja_minima=umbral_valor)
            else:
                f = 0.01     # a ciegas: 1% fijo a todo
            if f <= 0:
                continue
            puesto = banca_actual * f
            gano = (i == y)
            banca_actual += puesto * (cuota - 1) if gano else -puesto
            apuestas += 1
            aciertos += gano
            pico = max(pico, banca_actual)
            caida = max(caida, (pico - banca_actual) / pico if pico else 0)
            historial.append(banca_actual)
            if banca_actual <= 1:
                return 0.0, apuestas, aciertos, 1.0
    return banca_actual, apuestas, aciertos, caida


def main():
    hist = M.cargar()
    base = rasgos.construir(hist).sort_values("fecha")
    cols = rasgos.columnas_rasgo(base)
    base = base[base[cols].notna().all(axis=1)].reset_index(drop=True)
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent, val = base.iloc[:corte], base.iloc[corte:]
    fecha_corte = pd.to_datetime(ent.fecha.max())
    m = M.entrenar(ent[cols].values, ent["resultado"].values.astype(int), 3)

    d = A.cargar_cuotas_1x2()
    top = d.casa.value_counts().head(N_CASAS).index.tolist()
    mejores = cuotas_por_partido(top)

    val = val[val.match_id.isin(mejores)]
    val = val[pd.to_datetime(val.fecha) > fecha_corte].reset_index(drop=True)
    pn = M.probabilidades(m, val[cols].values, 3)

    print(f"{len(val)} partidos fuera de muestra")
    print(f"8 casas: {', '.join(top)}\n")

    y = val["resultado"].values.astype(int)
    uno = np.zeros((len(y), 3)); uno[np.arange(len(y)), y] = 1
    mercado = A.probabilidades_de_mercado()
    pm = mercado.loc[val.match_id].values
    brier_mercado = ((pm - uno) ** 2).sum(axis=1).mean()

    def reparto(umbral, usar_valor=True, empujon=0.0, reps=400):
        """Remuestrea los partidos con reposicion y devuelve el reparto."""
        rng = np.random.default_rng(0)
        finales, caidas, napuestas = [], [], []
        for _ in range(reps):
            i = rng.integers(0, len(val), len(val))
            b, n, a, c = simular(val.iloc[i].reset_index(drop=True), pn[i],
                                 mejores, umbral, usar_valor, empujon)
            finales.append(b); caidas.append(c); napuestas.append(n)
        f = np.sort(finales)
        return {"mediana": float(np.median(f)),
                "peor10": float(f[len(f)//10]),
                "mejor10": float(f[-len(f)//10]),
                "pierde": float((f < BANCA_INICIAL).mean()),
                "caida": float(np.median(caidas)),
                "apuestas": int(np.median(napuestas))}

    print("TU PLAN, TAL CUAL (modelo real + value bets + Kelly/4)")
    print("400 remuestreos de los mismos partidos. Banca inicial 1.000 EUR.\n")
    print(f"  {'umbral':>7s} {'apuestas':>9s} {'mediana':>10s} {'peor 10%':>10s} "
          f"{'mejor 10%':>10s} {'pierde':>8s} {'caida':>7s}")
    for u in (0.02, 0.05, 0.10, 0.20):
        r = reparto(u)
        print(f"  {u*100:6.0f}% {r['apuestas']:9d} {r['mediana']:10,.0f} "
              f"{r['peor10']:10,.0f} {r['mejor10']:10,.0f} "
              f"{r['pierde']*100:7.1f}% {r['caida']*100:6.1f}%")
    r0 = reparto(0, usar_valor=False)
    print(f"\n  {'ciegas':>7s} {r0['apuestas']:9d} {r0['mediana']:10,.0f} "
          f"{r0['peor10']:10,.0f} {r0['mejor10']:10,.0f} "
          f"{r0['pierde']*100:7.1f}% {r0['caida']*100:6.1f}%")
    print("\n  Si el filtro de valor deja la mediana PEOR que apostar a")
    print("  ciegas, es que selecciona los partidos donde el modelo mas se")
    print("  equivoca. Ese es el caso.")

    print("\n\nCONTRAFACTUAL: ¿cuanto tendria que mejorar el modelo?\n")
    print("  El 'empujon' anade informacion CORRECTA a la probabilidad del")
    print("  modelo. Es un oraculo, no una mejora realista: 2 puntos de")
    print("  informacion pura valen mucho mas que 'afinar un 2% el modelo'.\n")
    print(f"  {'empujon':>8s} {'Brier':>7s} {'vs mercado':>11s} "
          f"{'mediana':>10s} {'pierde':>8s}")
    for e in (0.00, 0.02, 0.05, 0.10, 0.15):
        p = pn * (1 - e); p[np.arange(len(y)), y] += e
        b = ((p - uno) ** 2).sum(axis=1).mean()
        r = reparto(0.02, empujon=e)
        estado = "MEJOR" if b < brier_mercado else "peor"
        print(f"  {e*100:7.0f}% {b:7.4f} {estado:>11s} "
              f"{r['mediana']:10,.0f} {r['pierde']*100:7.1f}%")
    print(f"\n  (Brier del mercado: {brier_mercado:.4f}. Un modelo PEOR que el")
    print("  mercado no puede ganar dinero apostando contra sus precios: si")
    print("  una fila dice lo contrario, es ruido de la trayectoria.)")


if __name__ == "__main__":
    main()
