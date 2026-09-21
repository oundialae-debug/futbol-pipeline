# ¿Hay arbitraje? Medido en la mejor condición posible, y no

## Qué es el arbitraje (surebet)

Coger cuotas de distintas casas para los tres resultados de un partido tal
que `1/cuota_local + 1/cuota_empate + 1/cuota_visitante < 1`. Repartiendo el
dinero en proporción inversa a cada cuota, ganas lo mismo pase lo que pase.
Es la única apuesta que en teoría no depende de acertar nada.

Es una estrategia real y la usa gente ("arbers"). El problema no es que no
exista en general: es que **con esta fuente de datos no se puede ejecutar**, y
aquí está medido por qué, en la condición más favorable que se puede armar.

## La prueba, en las mejores condiciones que tenemos

Todo lo cosechado ayer vino de **una sola pasada**, mismo instante exacto
(`cosechado` idéntico en las 208 filas). Es el único momento en que podemos
estar razonablemente seguros de que las cuotas se pidieron a la vez.

Restringido a las 8 casas más baratas ya identificadas (20Bet, Ivibet,
TonyBet, 1xBet, Megapari, Betano, Marathonbet, Stake.com):

    Partidos en la pasada:                    208
    "Arbitrajes" aparentes (margen < 0):        17  (8,2%)
    Mejor "beneficio" aparente:               4,62%

Si esto fuera arbitraje de verdad, sería la mejor noticia del proyecto. No lo
es. Mirando el detalle de un partido:

    casa          lado   cuota
    TonyBet       away   1.46
    20Bet         away   1.46
    Marathonbet   away   1.48
    Stake.com     away   1.47
    Ivibet        away   1.46
    1xBet         away   1.50   <- la que "rompe" el arbitraje
    Megapari      away   1.50

Siete casas, prácticamente todas de acuerdo en 1,46-1,48, y una o dos que se
salen un poco. Eso no es un mercado ineficiente: es **redondeo y actualización
asíncrona**. Las casas actualizan sus líneas en momentos ligeramente distintos
dentro de la ventana de refresco (varias veces al día, sin marca de tiempo,
según `API.md`). Nuestra "pasada simultánea" solo garantiza que NOSOTROS
pedimos los datos a la vez, no que las CASAS los actualizaron a la vez.

## Por qué esto ya lo sabíamos, con más fuerza

Con las 54 casas, el margen combinado daba -0,54% y "arbitraje" imposible en
el 45,9% de los partidos (`que_casas_abrir.md`). Aquí, restringido a 8 casas y
a una sola pasada simultánea -- el mejor caso que se puede construir -- baja al
8,2%, pero **no desaparece**. Si fuera un mercado real, tendría que ser 0%: el
1X2 es el mercado más líquido que existe.

Que no llegue a cero ni en las mejores condiciones es la prueba de que el
problema no es "poca simultaneidad entre pasadas distintas": es que **esta
API no sirve el precio en tiempo real con marca de tiempo**, que es el
requisito mínimo para que el arbitraje exista fuera del papel.

## Por qué tampoco funcionaría con datos perfectos

Aunque la fuente diera precios en vivo con marca de tiempo, quedan tres
problemas que no son de datos:

- **Las casas cierran o limitan a los arbers rápido.** Ya lo vimos en
  `casas_descolgadas.md`: una casa blanda y tolerante con quien gana no
  existe. El arbitraje es la señal más fácil de detectar para una casa,
  porque implica apostar SIEMPRE al mismo lado del margen.
- **Riesgo de pata (leg risk).** Entre que pones la primera apuesta y la
  segunda, la cuota puede moverse. Con cuotas que se refrescan cada 10 minutos
  y sin API de apuesta automática, ese hueco es enorme comparado con lo que
  usa un arber real (milisegundos).
- **Los límites de apuesta son bajos justo donde hay margen.** Las
  oportunidades de arbitraje reales suelen aparecer en líneas de baja
  liquidez, que son las que antes limitan.

## Veredicto

No. Ni con las 54 casas, ni con las 8 más baratas, ni en la única pasada
verdaderamente simultánea que tenemos. Lo que parece arbitraje es reloj
desincronizado entre casas, no precio mal puesto. Y aunque existiera de
verdad, no hay forma de ejecutarlo con esta API ni con 8 cuentas sin que te
cierren.
