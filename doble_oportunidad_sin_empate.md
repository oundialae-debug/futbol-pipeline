# Doble Oportunidad, Sin Empate y Más/Menos goles

Respuesta a "¿has probado el Doble oportunidad, Apuestas sin empate o el
Más/Menos goles?". Los tres estaban sin probar o mal probados, y uno de ellos
por un error mío.

## Dónde viven estos mercados

Esta API sirve exactamente diez mercados y ninguno se llama "Doble
Oportunidad" ni "Sin Empate". Pero son idénticos a dos líneas del hándicap
asiático:

    Sin Empate (Draw No Bet)   =  Asian Handicap 0      (el empate devuelve)
    Doble Oportunidad 1X       =  Asian Handicap +0.5   (vale ganar o empatar)

Yo había excluido el hándicap asiático **entero** del backtest, cuando solo
las líneas de cuarto (±0.25, ±0.75) tienen la regla de partir la apuesta en
dos mitades. Las líneas 0 y ±0.5 son simples. Esa exclusión de más dejó fuera
justo los dos mercados que se preguntaban, y encima de los más baratos.

Más/Menos goles sí estaba probado a fondo: es Total Goals, 134.882 filas,
**-9.48%**.

## Antes de dar ningún número: comprobar que el resolutor no miente

Un hándicap mal orientado no da error. Da números plausibles y del revés, que
es el peor modo de fallo posible. Comprobado contra el 1X2 del mismo partido,
que es el mercado que más hemos mirado:

    AH 0  home   vs  gana=1 / empata=0.5        110 partidos   100.00%
    AH 0  away   vs  gana=1 / empata=0.5        110 partidos   100.00%
    home +0.5    vs  gana o empata              117 partidos   100.00%
    away +0.5    vs  gana o empata              126 partidos   100.00%
    home -0.5    vs  gana seco                  126 partidos   100.00%
    away -0.5    vs  gana seco                  117 partidos   100.00%

Y monotonía dentro de cada partido: cubrir tiene que ser más fácil cuanto
mayor es el hándicap. **147/147 partidos coherentes.**

Además el reparto de mercados confirma la orientación: hay 4.664 mercados
"-1/+1" frente a 3.016 "+1/-1". El local es más veces el que da hándicap, que
es lo que cabe esperar con ventaja de campo. El primer número es el del local.

## Los números

Errores agrupados por partido: las líneas de un mismo partido ganan y pierden
juntas.

### Con la cuota de una casa cualquiera

    SIN EMPATE (AH 0)            2.590 cuotas / 113 partidos   -3.37%  (+-2.33, -1.45s)
    DOBLE OPORTUNIDAD (+0.5)     5.005 cuotas / 146 partidos   -4.86%  (+-4.20, -1.16s)
    Más/Menos goles                    134.882 filas           -9.48%

Son los dos mercados **más baratos** que hemos medido. Margen de una casa:
5.75% en el Sin Empate, 6.35% en la Doble Oportunidad.

### Cogiendo la mejor cuota de entre todas las casas

    SIN EMPATE             226 cuotas / 113 partidos   +0.33%  (+-2.86, +0.12s)
    DOBLE OPORTUNIDAD      262 cuotas / 146 partidos   -0.51%  (+-4.24, -0.12s)

Cero, otra vez. Con 11,5 y 19,1 casas por mercado el margen combinado baja a
2.21% y 1.03%, y ahí se acaba: el precio queda exactamente en el punto donde
no se gana ni se pierde. Y eso **exige tener cuenta en todas esas casas**, que
es justo lo que no se puede.

### Filtrar por "valor contra el consenso" lo empeora

    SIN EMPATE, valor > 0        102 cuotas /  42 partidos   -9.61%
    DOBLE OPORTUNIDAD, valor > 0  96 cuotas /  53 partidos  -22.36%

Igual que en todo lo demás: batir al consenso no es señal de acierto, es un
indicador indirecto de que la línea es marginada.

## Lo único con señal, y por qué tampoco sirve

Separando los dos lados del hándicap:

    lado que DA el hándicap (cuota 3.18)   -20.29%  (+-6.30, -3.22 sigmas)
    lado que lo RECIBE     (cuota 1.56)     -1.38%  (+-4.10, -0.34 sigmas)

El lado largo pierde veinte puntos y el corto está en cero. La casa no reparte
su margen entre los dos lados: se lo cobra casi entero al lado de cuota larga.
Es el mismo sesgo favorito-marginado de `hallazgo_favorito_marginado.md`,
medido otra vez y por otro camino.

No se cobra, por lo de siempre: para ganar habría que apostar el lado corto, y
ese lado está en **-1.38% (+-4.10)** con una casa y en **+2.02% (+-3.93)**
cogiendo la mejor de todas. Medio sigma. Y la mejor cuota entre casas ya
sabemos que es un espejismo: las cuotas de distintas casas no son simultáneas
(29% de partidos de 1X2 con arbitraje imposible, en `API.md`).

## Conclusión

Sin Empate y Doble Oportunidad son los mercados más baratos de esta API, y por
eso merecían la prueba que no les había hecho. Pero acaban donde todos: el
margen se come el sesgo justo. Ningún corte llega a un sigma por el lado
bueno.
