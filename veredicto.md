# ¿Se puede ganar dinero con esta API, GitHub y una IA?

No. Y esta vez no es una vía cerrada más: es la prueba que las resume todas.

## La prueba definitiva

Hasta ahora probábamos REGLAS: apostar donde hay valor contra el consenso,
apostar favoritos, apostar cuotas cortas, apostar lo que dice el modelo de
tarjetas. Todas perdían. Pero siempre quedaba la duda de si el fallo era la
regla y no el mercado.

Así que medimos lo de debajo de todas las reglas: **qué pasa si apuestas a
ciegas, todas las cuotas, en cada casa por separado.** 169.407 cotizaciones,
147 partidos, 51 casas. Errores agrupados por partido.

    Casumo Sport        -5.80%   (-1.62 sigmas)   <- la MENOS mala
    Mostbet             -3.31%   (-1.69)
    FanDuel             -3.94%   (-2.15)
    Betway              -3.96%   (-2.32)
    ...
    bet365              -6.84%   (-5.24)
    William Hill        -8.13%   (-9.38)
    BetVictor           -9.48%   (-9.62)
    Parimatch           -9.51%   (-9.64)

**Ni una sola de las 46 casas con muestra suficiente está por encima de
cero.** Ninguna. Cuarenta y cuatro de las cuarenta y seis pasan de -2 sigmas.
El rango entero va de -3.3% a -9.7%.

Eso es el suelo. Cualquier regla de selección tiene que remontar entre tres y
diez puntos **antes** de empezar a ganar, y ninguna de las que hemos probado
remonta ni uno.

## Por qué, estructuralmente

No es que no hayamos buscado bastante. Es que la información va en la
dirección contraria.

**Nosotros tenemos las cuotas y el resultado. Ellos tienen todo lo demás:**
alineaciones, lesiones, el árbitro designado, el viaje, el estado del campo,
la rotación por competición europea, y sobre todo el dinero — quién apuesta
qué, y cuánto pesa el que suele acertar.

Estamos intentando corregir un precio con menos datos que quien lo puso. Lo
único que la API nos da y ellos no tienen es... nada. Nos da su propia
respuesta. Estamos corrigiendo el examen con la hoja de soluciones delante e
insistiendo en que está mal.

Y encima de eso, el margen: 3.81% en el mercado más barato con una cuenta.

## Lo que sí hemos medido bien

El mercado está **perfectamente calibrado entre el 15% y el 85%**. Lo medimos
al punto. La única desviación real es el sesgo favorito-marginado en los
extremos (3.9 puntos de probabilidad, monótono a lo largo de ocho tramos, de
-3.90 a +3.69 sigmas). Es un sesgo real y está bien medido.

Y no se cobra: con la mejor cuota de 50 casas sobre 777 favoritos sale
**-0.01%**. El precio está puesto exactamente donde el margen se come el
sesgo. Es lo que cabe esperar de un mercado con décadas de gente lista
mirándolo.

## Qué haría falta para que esto cambiara

Ninguna de las tres depende de programar mejor:

1. **Datos que el mercado tarde en incorporar.** Alineaciones confirmadas una
   hora antes, lesiones de última hora, xG por jugador. Esta API no los sirve.
2. **Cuotas simultáneas y reales.** Las de aquí no lo son — lo demostramos con
   el 29% de partidos con arbitraje imposible. Sin simultaneidad, comparar
   casas entre sí es medir ruido.
3. **Ligas o mercados que nadie vigile.** Con diez mercados y las cinco
   grandes ligas europeas, estamos justo donde más ojos hay.

Y aunque aparecieran las tres, queda el problema que ya señalaste: la casa
blanda y tolerante con el que gana no existe. Es blanda porque no vigila, y en
cuanto vigila, limita.

## Veredicto

Con esta API, GitHub y un modelo, la respuesta es no. No por falta de esfuerzo
ni de técnica: por falta de información que el mercado no tenga ya.

Lo que sí ha salido de aquí es un método que funciona —  medir en vez de
opinar, agrupar por partido, mover el parámetro propio antes de creerse una
conclusión, desconfiar de lo que sale demasiado bien. Está en `CLAUDE.md` y
sirve para cualquier cosa que se mida contra la realidad.
