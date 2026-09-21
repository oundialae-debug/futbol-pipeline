# Middling: cómo funciona y cuánto se podría ganar, medido

## La mecánica

Un mismo partido cotiza varias líneas de Total Goals a la vez. Se apuestan
dos, con un hueco entre ellas:

    Apuesta 1:  OVER  2.5    (gana con 3 goles o más)
    Apuesta 2:  UNDER 3.5    (gana con 3 goles o menos)

El número 3 está en las dos. Si el partido acaba en **exactamente 3 goles**,
ganas las dos apuestas -- eso es el "middle". Si no, ganas una y pierdes otra.

    0,1,2 goles   -> pierdes la Over, ganas la Under   (pérdida pequeña)
    3 goles       -> ganas las DOS                      (el premio)
    4+ goles      -> ganas la Over, pierdes la Under    (pérdida pequeña)

No es arbitraje: en el caso normal (no caer en el hueco) se pierde un poco,
porque las dos cuotas juntas cuestan más del 100% de probabilidad -- es el
margen de la casa. El middling apuesta a que el marcador caiga en una franja
concreta, con premio si acierta.

## Cuánto se podría ganar: medido con 2.004 partidos reales

Primera versión de este cálculo tenía un fallo: la probabilidad de "caer en
el medio" salía 100% en todos los casos, porque el código promediaba una
lista ya filtrada por los partidos que SÍ habían caído ahí. Corregido,
calculando sobre el histórico completo:

| Hueco | P(cae en el medio), real | Mejor cuota del mercado (fantasía) | Una sola casa (real) |
|---|---|---|---|
| Over 1.5 / Under 2.5 | 23,0% | −5,84% (−1,34σ) | **−9,70% (−2,38σ)** |
| Over 2.5 / Under 3.5 | 23,1% | −0,87% (−0,24σ) | **−4,71% (−1,35σ)** |
| Over 3.5 / Under 4.5 | 15,5% | +4,96% (+0,91σ) | −0,58% (−0,12σ) |
| Over 4.5 / Under 5.5 | 9,2% | +23,80% (+1,32σ, n=20) | +6,39% (n=19, no fiable) |

La columna "mejor cuota del mercado" es la misma fantasía que ya desmontamos
con el arbitraje: coge la mejor de todas las casas a la vez, cosa que no
puedes hacer de verdad. La columna que importa es **"una sola casa"** -- las
dos patas puestas en la misma cuenta, que es lo único ejecutable.

Ahí, en el hueco más frecuente (2.5/3.5, que acierta el 23% de las veces):
**−4,71%, a −1,35 sigmas.** Pierde dinero, y la línea 1.5/2.5 pierde peor
(−9,70%, −2,38 sigmas -- eso sí es significativo, y en el sentido malo).

Las dos combinaciones que parecen ganar (3.5/4.5 y 4.5/5.5) tienen entre 19 y
20 partidos: exactamente el tipo de muestra minúscula que las notas de este
repo piden no enseñar sin avisar. Con esa n, tanto +6% como −15% son
compatibles con el ruido.

## Por qué pierde, estructuralmente

El middling no escapa al margen de la casa: lo reparte de otra forma. Cuando
compras Over 2.5 y Under 3.5 en la misma casa, esas dos cuotas juntas siguen
costando más del 100% de probabilidad implícita -- el margen normal del
mercado de goles (~6%). El hueco de 3 goles no es gratis: lo pagas en el
precio de las otras dos franjas. Estás comprando una apuesta con más varianza
(gano mucho o pierdo poco, en vez de ganar poco muchas veces), no una con
mejor valor esperado.

## Veredicto

No es mejor que apostar a ciegas en el mismo mercado (Total Goals ya daba
−6,45% a secas). El middling con una sola casa pierde en el hueco más común
y no hay muestra suficiente para creerse los huecos que parecen ganar.

Es una figura de apuesta con forma distinta -- más suerte de "todo o casi
nada"-- no una ventaja. Como el arbitraje, muere por el mismo motivo de
fondo: el margen del mercado no se puede esquivar reorganizando cómo se
reparte la apuesta.
