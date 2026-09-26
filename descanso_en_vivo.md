# Tarjetas al descanso -- 2026-09-26 19:36 UTC

Modelo: nivel propio de cada liga -0.068*k por tarjeta al descanso, phi=1.23, ajustado sobre 363 partidos de 6 ligas.
Niveles: Segunda División 3.21, La Liga 3.05, Premier League 2.68, (otras) 2.67, Bundesliga 2.67, Serie A 2.33, Ligue 1 2.09.
Validación fuera de muestra (línea 4.5): Brier 0.1839 frente a 0.2404 de la tasa base (+23.5%).

> El recuento del descanso es **información pública**: las casas también lo
> ven. La hipótesis original -- que sus modelos supongan persistencia cuando
> la correlación real es negativa -- está RETIRADA: ese -0.171 salía de un
> fichero de solo La Liga, y sobre 363 partidos de seis ligas la correlación
> es -0.016, o sea nada. Lo que queda es tener bien el nivel de cada liga,
> que es calibración, no ventaja.

*Consumo de API hoy: 910 llamadas en 67 pasadas, sobre un tope de 6000 (15%). El plan da 7.500 al día.*

> ⚠ Las cuotas en vivo se refrescan **cada 10 minutos** (documentación de la API) y no traen marca de tiempo. El precio de abajo puede ser de antes de las últimas tarjetas del primer tiempo, y puede no existir ya en la casa. El valor sirve para comparar modelos, no como dinero cogible.

> ⚠ **Llamadas fallidas:** HTTP 429 x2. Un 429 es límite de peticiones: hay huecos en el registro de esta pasada.

*Ningún partido en el descanso ahora mismo.*
