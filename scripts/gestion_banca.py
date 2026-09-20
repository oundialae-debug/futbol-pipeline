"""
CUÁNTO APOSTAR EN CADA APUESTA

LO PRIMERO, QUE NO SE OLVIDE
----------------------------
El stake NO crea ventaja. Si la ventaja es negativa, apostar el 3% de la banca
solo cambia la velocidad a la que se pierde, no el destino. Todo lo de aquí
abajo sirve para una cosa: sacarle el máximo a una ventaja que YA existe, y
sobrevivir a la mala racha mientras tanto.

Por eso este módulo tiene una puerta al principio (`decidir`) que se NIEGA a
apostar cuando la ventaja estimada no supera al error del propio modelo.

LOS TRES SISTEMAS
-----------------
  fijo       siempre el mismo % de la banca. Simple, no usa la ventaja.
  kelly      el % matemáticamente óptimo para crecer a largo plazo.
  kelly/n    Kelly dividido. Es lo que usa cualquiera que apueste en serio.

Kelly completo es óptimo SOLO si conoces la probabilidad exacta. Nosotros la
estimamos, y un error del 2% en la probabilidad con Kelly entero puede llevar
a apostar el triple de lo debido. Kelly entero además tiene caídas brutales:
por construcción, la banca baja a la mitad alguna vez con probabilidad 1/2.

Por eso se usa Kelly partido (1/4 suele ser lo sensato): crece casi igual y
la caída máxima se hunde.

LA FÓRMULA
----------
    f = (p * c - 1) / (c - 1)

donde p es tu probabilidad y c la cuota decimal. El numerador es la ventaja:
si es <= 0, no hay apuesta. `p * c` es lo que cobras de media por cada euro.

SOBRE EL 3% QUE PEDÍAS
----------------------
Un 3% fijo equivale a Kelly entero sobre una ventaja del 3% a cuota 2.00.
O sea que como stake fijo es razonable, pero se queda corto cuando la ventaja
es grande y se pasa cuando es pequeña. `comparar_sistemas` lo mide.
"""
from dataclasses import dataclass


FRACCION_KELLY = 0.25       # Kelly partido en cuatro
TOPE_POR_APUESTA = 0.05     # nunca más del 5% de la banca, pase lo que pase
VENTAJA_MINIMA = 0.02       # por debajo de esto no se apuesta


@dataclass
class Apuesta:
    descripcion: str
    probabilidad: float      # la nuestra
    cuota: float             # decimal, de la casa
    error_modelo: float = 0.0   # incertidumbre de `probabilidad`, en puntos


def ventaja(p, cuota):
    """Lo que ganas de media por euro apostado. 0.05 = +5%."""
    return p * cuota - 1.0


def kelly(p, cuota):
    """Fracción de banca que maximiza el crecimiento. 0 si no hay ventaja."""
    if cuota <= 1.0:
        return 0.0
    v = ventaja(p, cuota)
    return max(0.0, v / (cuota - 1.0))


def decidir(ap: Apuesta, fraccion=FRACCION_KELLY, tope=TOPE_POR_APUESTA,
            ventaja_minima=VENTAJA_MINIMA):
    """
    Qué fracción de la banca jugarse, y por qué.

    LA PUERTA: si la ventaja no supera al error del modelo, no se apuesta.
    Una ventaja del 3% con un modelo que se equivoca un 5% no es una ventaja,
    es ruido con buena presentación. Este es el filtro que habría evitado la
    mitad de los errores de este repositorio.
    """
    v = ventaja(ap.probabilidad, ap.cuota)
    # el error en la probabilidad se traduce a error en la ventaja
    error_en_ventaja = ap.error_modelo * ap.cuota

    if v <= 0:
        return 0.0, f"sin ventaja ({v*100:+.2f}%)"
    if v < ventaja_minima:
        return 0.0, f"ventaja {v*100:+.2f}% por debajo del mínimo {ventaja_minima*100:.1f}%"
    if error_en_ventaja >= v:
        return 0.0, (f"ventaja {v*100:+.2f}% menor que el error del modelo "
                     f"(±{error_en_ventaja*100:.2f}%): es ruido")

    f = kelly(ap.probabilidad, ap.cuota) * fraccion
    if f > tope:
        return tope, f"Kelly/{1/fraccion:.0f} daría {f*100:.2f}%, topado al {tope*100:.1f}%"
    return f, f"Kelly/{1/fraccion:.0f} sobre ventaja {v*100:+.2f}%"


def simular(apuestas_ganadoras, cuota, n, sistema, banca=1000.0,
            fijo=0.03, fraccion=FRACCION_KELLY, p_modelo=None):
    """
    Pasa una secuencia de resultados por un sistema de stake y devuelve la
    banca final y la caída máxima.

    `apuestas_ganadoras` es una lista de booleanos ya resueltos, así que esto
    NO predice nada: solo mide qué le habría pasado al dinero.
    """
    p = p_modelo if p_modelo is not None else (sum(apuestas_ganadoras) / n)
    pico = banca
    caida = 0.0
    for gana in apuestas_ganadoras:
        if sistema == "fijo":
            f = fijo
        elif sistema == "kelly":
            f = kelly(p, cuota)
        else:
            f = min(kelly(p, cuota) * fraccion, TOPE_POR_APUESTA)
        puesto = banca * f
        banca += puesto * (cuota - 1) if gana else -puesto
        pico = max(pico, banca)
        caida = max(caida, (pico - banca) / pico if pico else 0)
        if banca <= 0.01:
            return 0.0, 1.0
    return banca, caida


def comparar_sistemas(acierto_real, cuota, n=500, repeticiones=2000,
                     banca=1000.0):
    """
    Con una tasa de acierto y una cuota, ¿qué hace cada sistema?

    MUCHAS SIMULACIONES, NO UNA. Una sola secuencia mide la suerte de esa
    secuencia, no el sistema: con ventaja CERO, una tirada afortunada acaba un
    45% arriba y parece que el sistema funciona. Se devuelve la MEDIANA y el
    porcentaje de veces que se acaba por debajo de la banca inicial, que es lo
    que de verdad te va a pasar.

    Las tres reciben la MISMA secuencia en cada repetición, para que la
    comparación entre sistemas no mida además ruido distinto en cada uno.
    """
    import random
    from statistics import median
    acum = {s: {"finales": [], "caidas": []}
            for s in ("fijo", "kelly", "kelly_partido")}
    for semilla in range(repeticiones):
        r = random.Random(semilla)
        seq = [r.random() < acierto_real for _ in range(n)]
        for s in acum:
            final, caida = simular(seq, cuota, n, s, banca=banca,
                                   p_modelo=acierto_real)
            acum[s]["finales"].append(final)
            acum[s]["caidas"].append(caida)
    fuera = {"ventaja_real": ventaja(acierto_real, cuota)}
    for s, d in acum.items():
        fs = d["finales"]
        fuera[s] = {
            "mediana": median(fs),
            "peor_10pct": sorted(fs)[len(fs) // 10],
            "prob_perder": sum(1 for x in fs if x < banca) / len(fs),
            "caida_maxima": median(d["caidas"]),
        }
    return fuera


if __name__ == "__main__":
    print("COMPROBACIONES CON CASOS DONDE LA RESPUESTA SE SABE\n")

    # 1. Sin ventaja no se apuesta, por bonita que sea la cuota
    a = Apuesta("cuota justa", probabilidad=0.50, cuota=2.00)
    f, por = decidir(a)
    print(f"  p=50% cuota 2.00 (justa)        -> {f*100:5.2f}%  {por}")
    assert f == 0.0

    # 2. Ventaja real y limpia: sí se apuesta
    a = Apuesta("ventaja clara", probabilidad=0.55, cuota=2.00,
                error_modelo=0.01)
    f, por = decidir(a)
    print(f"  p=55% cuota 2.00 err±1pt        -> {f*100:5.2f}%  {por}")
    assert 0 < f <= TOPE_POR_APUESTA

    # 3. LA PUERTA: misma ventaja, pero el modelo no es de fiar
    a = Apuesta("ventaja ahogada por el error", probabilidad=0.55, cuota=2.00,
                error_modelo=0.06)
    f, por = decidir(a)
    print(f"  p=55% cuota 2.00 err±6pt        -> {f*100:5.2f}%  {por}")
    assert f == 0.0, "tiene que negarse: el error se come la ventaja"

    # 4. Cuota corta con ventaja grande: Kelly pediría muchísimo, el tope manda
    a = Apuesta("cuota corta", probabilidad=0.80, cuota=1.40,
                error_modelo=0.01)
    f, por = decidir(a)
    print(f"  p=80% cuota 1.40 err±1pt        -> {f*100:5.2f}%  {por}")
    assert f <= TOPE_POR_APUESTA

    print("\n\nQUÉ LE PASA AL DINERO (500 apuestas, banca 1000, "
          "2000 simulaciones)\n")
    print("  mediana = lo normal.  peor 10% = te pasa una de cada diez veces.")
    print("  'pierde' = en qué porcentaje de las simulaciones acabas por "
          "debajo de 1000.\n")
    for etiqueta, acierto, cuota in [
        ("ventaja real +4%  (cuota 2.00)", 0.52, 2.00),
        ("SIN ventaja       (cuota 2.00)", 0.50, 2.00),
        ("desventaja -4%    (cuota 2.00)", 0.48, 2.00),
        ("ventaja +3% a cuota corta 1.50", 0.6867, 1.50),
    ]:
        r = comparar_sistemas(acierto, cuota)
        print(f"  {etiqueta}")
        print(f"      {'sistema':16s} {'mediana':>10s} {'peor 10%':>10s} "
              f"{'pierde':>8s} {'caída':>8s}")
        for s, nombre in (("fijo", "fijo 3%"), ("kelly", "Kelly"),
                          ("kelly_partido", "Kelly/4")):
            d = r[s]
            print(f"      {nombre:16s} {d['mediana']:10,.0f} "
                  f"{d['peor_10pct']:10,.0f} {d['prob_perder']*100:7.1f}% "
                  f"{d['caida_maxima']*100:7.1f}%")
        print()

    print("  Kelly y Kelly/4 aparecen en 1.000 y 0% cuando no hay ventaja")
    print("  porque SE NIEGAN A APOSTAR: la fórmula da cero. El 3% fijo sí")
    print("  apuesta, y ahí se ve lo que cuesta: pierde en la mayoría de")
    print("  simulaciones y se come caídas enormes para acabar igual o peor.")
    print("\n  Ningún sistema de stake convierte una apuesta mala en buena.")
