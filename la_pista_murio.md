# La pista de la mezcla murió al crecer la muestra

## Lo que parecía

Con **89 partidos**, mezclar la probabilidad del mercado con la del modelo
bajaba el Brier de forma clara:

    peso al modelo     Brier
              0.00    0.6558   <- solo mercado
              0.43    0.6457   <- óptimo
              1.00    0.6639   <- solo modelo

Curva suave, mínimo bien marcado en el medio, mejora del 1,5%. Dije entonces
que era "la forma de una señal real" y que el bootstrap [0,00 – 0,98] no
permitía demostrarlo. Eso segundo era lo importante y estuve a punto de que se
me pasara.

## Lo que es

Cosechando las cuotas que faltaban, la misma prueba con **168 partidos**:

    peso al modelo     Brier
              0.00    0.5762   <- solo mercado
              0.10    0.5756   <- óptimo
              0.20    0.5761
              0.50    0.5837
              1.00    0.6166   <- solo modelo

    peso óptimo w = 0.10   ->   Brier 0.5756  (mercado solo: 0.5762)
    bootstrap 95%: [0.00, 0.48]
    el peso sale CERO en el 35% de los remuestreos

El peso óptimo cayó de **0,43 a 0,10**. La mejora pasó de 1,5% a **0,01%** --
seis diezmilésimas de Brier, que no es nada. Y el cero aparece ahora en un
tercio de los remuestreos, cuando antes aparecía en el 9%.

## Lo que hay que retener

**El número se movió en la dirección mala al doblar la muestra.** Esa es la
firma de un hallazgo falso, no de uno pequeño: un efecto real se queda donde
está y solo estrecha su intervalo. Uno inventado se encoge hacia cero.

Si hubiéramos tenido prisa por cobrar la pista, habríamos puesto dinero sobre
una curva bonita dibujada por 89 partidos.

También cambió el Brier del mercado (0,6558 -> 0,5762) porque el conjunto de
partidos es otro, más grande y con más partidos fáciles. Por eso las dos
tablas no son comparables entre sí columna a columna: lo comparable es la
FORMA de cada una, y la segunda ya no tiene mínimo en el medio.

## Dónde queda el proyecto

El modelo no aporta información que el precio no lleve ya dentro. Con 168
partidos eso ya no es "no se puede saber": es que el hueco, si existe, es más
pequeño que 0,48 de peso y que seis diezmilésimas de Brier.

La cosecha diaria de cuotas sigue corriendo, porque caducan a los 28 días y no
cuesta nada. Si en ocho semanas el intervalo se separa del cero, será noticia.
Después de esto, no lo espero.
