# Qué 8 casas abrir: 9,58 puntos de diferencia en cada apuesta

Esto sale de comprobar por qué una simulación daba un resultado imposible, y
es lo más accionable que ha salido del proyecto. No depende del modelo, ni de
que haya ventaja, ni de nada que esté por demostrar.

## El margen del 1X2, casa por casa

233 partidos, 54 casas. El margen es lo que cobra esa casa en **cada apuesta**
que le hagas, antes de acertar o fallar.

| Casa | Partidos | Margen |
|---|---|---|
| 20Bet | 231 | **3,16%** |
| Ivibet | 231 | 3,17% |
| TonyBet | 231 | 3,17% |
| 1xBet | 232 | 3,20% |
| Megapari | 232 | 3,26% |
| Betano | 229 | 3,83% |
| Marathonbet | 231 | 3,84% |
| Stake.com | 217 | 4,01% |
| … | | |
| Unibet | 233 | 6,81% |
| Ladbrokes | 233 | 7,23% |
| 888sport | 233 | 8,34% |
| **William Hill** | 233 | **12,74%** |

**De 3,16% a 12,74%. Casi diez puntos de diferencia, en cada apuesta.**

Eso no es un detalle: es más grande que cualquier ventaja que un modelo pueda
esperar tener. Apostar en William Hill con un modelo excelente pierde más que
apostar en 20Bet con uno mediocre.

## Qué cambia esto

Cogiendo la mejor cuota de las **8 más baratas**, el margen combinado baja a
**+1,24%**. Con las 8 que usó la simulación (elegidas por frecuencia en los
datos, no por precio) era **3,23%**.

Elegir bien las cuentas **divide el peaje por dos y medio**, y es gratis.

> Aviso honesto: ese +1,24% sale negativo en el 7,3% de los partidos, o sea
> imposible. Parte de esa mejora es el problema de las cuotas no simultáneas,
> no dinero real. El número creíble está entre el 1,5% y el 2%.

## Y lo que NO se puede hacer

Cogiendo la mejor cuota de **las 54 casas**, el margen sale **-0,54%**:
beneficio garantizado en el **45,9% de los partidos**. Eso no existe.

Es la demostración más clara que tenemos de que las cuotas de distintas casas
en esta API **no son simultáneas**. Cualquier estrategia basada en "la mejor
cuota de muchas casas" está cobrando precios que nunca estuvieron vivos a la
vez.

Con ocho casas el efecto es pequeño (imposible solo en el 1,7% cuando se eligen
por frecuencia). Con cincuenta y cuatro es fantasía pura.

## Lo que esto NO arregla

Bajar el peaje del 3,2% al 1,5% no crea ventaja: baja el listón que el modelo
tiene que superar. Nuestro modelo está **por debajo del mercado**, así que
sigue sin haber apuesta. Pero si alguna vez la hay, esta tabla es la
diferencia entre cobrarla y regalarla.
