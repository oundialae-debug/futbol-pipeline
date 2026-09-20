# El sesgo favorito-marginado: existe, y no se puede cobrar

*20 de septiembre de 2026. 6.699 resultados de 147 partidos ya jugados de las
seis ligas, con cuotas previas de hasta 50 casas.*

## El hallazgo

Durante todo el proyecto medimos la calibración del mercado con el consenso
restringido al 15%-85%, y salía perfecta: sesgo de 0.00 puntos, ningún tramo
por encima de 0.6 sigmas. La conclusión fue "el mercado está bien calibrado,
no hay nada que explotar".

Esa conclusión estaba condicionada por un filtro nuestro. El rango 15%-85%
excluía justo la zona donde la literatura sitúa el fallo clásico de los
mercados de apuestas. Al ensanchar a 2%-98% aparece esto:

| Consenso dice | Pasa de verdad | Sesgo | Sigmas | n |
|---|---|---|---|---|
| 8% | 4% | **-4.02 pts** | **-3.90** | 343 |
| 13% | 9% | -3.34 pts | -2.43 | 449 |
| 23% | 22% | -0.70 pts | -0.58 | 1184 |
| 41% | 41% | -0.40 pts | -0.31 | 1525 |
| 58% | 58% | +0.04 pts | +0.03 | 1434 |
| 78% | 79% | +1.62 pts | +1.25 | 985 |
| 87% | 90% | +3.17 pts | +2.25 | 431 |
| 92% | 96% | **+3.91 pts** | **+3.69** | 333 |

No es un tramo suelto que se sale por azar: es un **gradiente monótono** a lo
largo de ocho tramos, de -3.90 a +3.69 sigmas, sin una sola inversión. Los
resultados improbables salen menos de lo que el mercado dice; los favoritos
claros, más.

Es el sesgo favorito-marginado de manual, y está aquí.

## Por qué no se puede cobrar

Apostando con la cuota que ofrece una casa cualquiera:

| Tramo | Cuota media | Aciertos | Retorno real |
|---|---|---|---|
| 5-10% | 12.75 | 4.1% | **-49.60%** |
| 10-15% | 7.64 | 8.7% | -32.83% |
| 15-30% | 4.24 | 22.7% | -6.92% |
| 50-70% | 1.63 | 58.6% | -5.50% |
| 85-90% | 1.08 | 91.0% | -1.71% |
| 90-95% | 1.03 | 95.6% | **-1.46%** |

El gradiente se ve igual de claro en el dinero: apostar a marginados pierde
la mitad de lo apostado, apostar a favoritos pierde el 1.5%. Pero **incluso
el mejor tramo pierde**.

Y cogiendo la MEJOR cuota de entre todas las casas, sobre los 777 favoritos
con consenso por encima del 85%:

    cuota media  1.0768
    aciertos     92.92%
    retorno      -0.01% por apuesta   (+-1.51 pts, agrupando por partido)

Cero. El sesgo vale unos 3.9 puntos de probabilidad a favor del favorito, y
el margen combinado se come exactamente esos 3.9 puntos.

## La lectura

Esto no es mala suerte ni una medición imprecisa. Es lo que cabe esperar de
un mercado maduro: el sesgo favorito-marginado lleva décadas documentado, las
casas lo conocen, y tienen el margen colocado justo donde lo neutraliza.

El sesgo sobrevive porque a las casas les conviene que sobreviva -- los
apostantes aficionados prefieren las cuotas altas -- pero el precio está
puesto de forma que aprovecharlo no rente.

## Lo que además lo haría inviable en la práctica

- **776 de los 777 favoritos vienen de Total Goals** (tipo "Over 0.5 goles" a
  cuota 1.08). Un solo caso de Full Time Result.
- A cuota 1.077 hay que arriesgar 1.300 euros para ganar 100.
- Y ese -0.01% exige la mejor cuota de entre cincuenta casas, que es
  justamente lo que no se tiene con dos o tres cuentas.

## Qué queda abierto

El margen de error es de +-1.51 puntos, así que a dos sigmas el intervalo va
de -3% a +3%. No se puede descartar que exista un +1% o +2% real ahí dentro.
Pero para distinguirlo del cero harían falta del orden de diez veces más
partidos, y aun encontrándolo, a cuota 1.08 y necesitando cincuenta cuentas,
no sería aprovechable.

## Cómo se encontró

Merece anotarse porque es el método, no la suerte: el hallazgo apareció al
darse cuenta de que **una decisión nuestra de filtrado estaba determinando la
conclusión**. El filtro 15%-85% tenía una buena razón (el valor RELATIVO se
dispara al dividir entre probabilidades pequeñas) pero se estaba aplicando a
una medición que no lo necesitaba: la calibración se mide en puntos
absolutos.

Conviene desconfiar de cualquier conclusión que dependa de un parámetro
elegido por nosotros, y probar a moverlo.
