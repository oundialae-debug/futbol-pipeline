# ¿Hay algún mercado donde el precio esté MAL, o solo caro?

La pregunta que había que hacer antes de montar nada, y que no hice.

## Por qué esta es la pregunta

Yo había propuesto los córners con este razonamiento:

> "En el 1X2 compites contra un precio pulido por millones. En córners
> compites contra la regresión de alguien. Un precio crudo SÍ puede estar
> equivocado más de un 6%."

Eso es una hipótesis comprobable, y los datos para comprobarla ya estaban en
`data/backtest_valor.csv`. Bastaba comparar dos números:

- **esperado**: lo que perderías apostando a ciegas contra un precio PERFECTO.
  Es solo el margen: `-margen / (1 + margen)`.
- **medido**: lo que se perdió de verdad.

Si un mercado pierde justo su margen, el precio es correcto y la única barrera
es el peaje. Si pierde MÁS, el precio además está torcido, y entonces el otro
lado de esa apuesta es dinero.

## El resultado

169.407 cotizaciones, 147 partidos. Errores agrupados por partido.

    mercado                casas  margen  esperado   medido   hueco  sigmas
    Asian Handicap          17.7   6.26%    -5.89%  -10.22%  -4.33%   -2.86
    Total Goals             24.7   5.88%    -5.55%   -6.45%  -0.90%   -0.51
    Both Teams To Score     28.4   6.99%    -6.53%   -7.17%  -0.63%   -0.43
    Odd or Even             27.3   6.90%    -6.45%   -6.26%  +0.19%   +1.00
    Total Corners            6.5   8.72%    -8.02%   -7.30%  +0.72%   +0.70
    Full Time Result        47.8   6.01%    -5.67%   -1.98%  +3.69%   +1.24

**Córners: +0.72%, a 0.70 sigmas.** El precio de los córners es exacto. Pierde
lo que cuesta el margen y ni un punto más. La hipótesis de "precio crudo en
mercado no vigilado" queda falsada por datos que ya teníamos.

Y falsada en el sitio donde más debería haberse cumplido: 6,5 casas es el
mercado menos vigilado con consenso medible de toda la API.

## El único hueco real, y por qué tampoco sirve

El hándicap asiático pierde 4,33 puntos más que su margen (-2.86 sigmas). Ya
sabemos qué es: las líneas hondas, el sesgo favorito-marginado de
`hallazgo_favorito_marginado.md` y `doble_oportunidad_sin_empate.md`. El lado
que DA hándicap pierde un 20,29%; el que lo RECIBE, que sería el lado a
apostar, está en **-1,38% (±4,10)**. El hueco existe pero está justo del lado
que no se puede cobrar.

El +3.69% del 1X2 es ruido: 1,24 sigmas sobre 146 partidos.

## Lo que esto cierra

No hay en esta API un mercado con el precio torcido. Los caros son caros
porque cobran más, no porque acierten menos. Un modelo mejor no ayuda donde el
precio ya es correcto: solo cambia quién paga el peaje.

## La lección de método

La hipótesis era razonable y estaba mal. Lo que la mató no fue montar el
modelo de córners -- eso habría costado dos semanas de recolección -- sino
preguntarse qué número la falsaría y buscarlo en lo que ya había.

Antes de construir un modelo para batir un precio, mide si ese precio está
mal. Si no lo está, el modelo no tiene nada que corregir.
