# Notas para trabajar en este repositorio

Escrito el 20 de septiembre de 2026, después de un día en el que casi todos
los fallos encontrados tenían la misma forma: **funcionaban sin decir que
estaban mal**. Ninguno dio un error. Daban ausencias, o números con buena
pinta que eran falsos.

Esa es la regla de fondo: aquí los fallos no gritan, callan. Lo que sigue son
las comprobaciones concretas que los habrían pillado.

## Antes de empujar código

- **Ejecuta `python3 scripts/prueba_humo.py`.** No basta `py_compile`: pasa la
  sintaxis y revienta en producción. Pasó con un `{a:.3f}` sobre un valor que
  había pasado a ser un diccionario. El ajuste del modelo y la escritura de
  informes no tocan la red, así que se prueban en local sin clave de API.
- **Si tocas la clasificación de mercados, comprueba el nombre EXACTO contra
  datos reales** (`censo_mercados_crudo.py`). La API devuelve
  `"First Team To Score"` con T mayúscula; el código buscaba `"to"` y ese
  mercado no apareció ni una vez en 137.301 filas. Cero error, cero filas.

## Filtros y valores por defecto

- **Un filtro que acepta cuando no puede comprobar no es un filtro.** Había un
  `if not pais: return True` para dar el beneficio de la duda: coló la Premier
  de Jamaica, la Serie A de Brasil, la Segunda de Uruguay y una Liga de El
  Salvador. Ante la duda, descartar y decirlo.
- **Una reserva que devuelve el dato equivocado es peor que no devolver
  nada**, porque lo que sale parece una respuesta. Un `candidatos = corriendo
  or vivos` eligió un partido ya TERMINADO para medir si las cuotas se movían.
- **Identifica las ligas por ID, nunca por nombre.** Hay Serie A en Italia y
  en Brasil, Premier League en Inglaterra y en Jamaica.

## Conclusiones

- **No excluyas una familia entera por una parte complicada.** Dejé fuera el
  hándicap asiático completo porque las líneas de cuarto (±0.25, ±0.75) parten
  la apuesta en dos mitades. Las líneas 0 y ±0.5 son simples, y son
  exactamente el Sin Empate y la Doble Oportunidad: dos mercados que se habían
  pedido y dos de los más baratos de la API. Excluye lo complicado, no su
  familia.
- **Un resolutor nuevo se comprueba contra uno viejo, partido a partido.**
  Un hándicap orientado al revés no da error: da números plausibles e
  invertidos. Antes de dar cifras, el AH 0 y el ±0.5 se contrastaron con el
  1X2 del mismo partido (100% de coincidencia en 110-126 partidos) y se exigió
  monotonía dentro de cada partido: cubrir tiene que ser más fácil cuanto mayor
  el hándicap (147/147). Eso es lo que permite creerse el resto.

- **Pregunta siempre qué parámetro elegido por ti sostiene la conclusión, y
  muévelo.** Durante horas la conclusión fue "el mercado está perfectamente
  calibrado". Lo cierto era "perfectamente calibrado **en el rango 15%-85% que
  yo decidí mirar**". Al ensanchar a 2%-98% apareció el sesgo
  favorito-marginado a 3.90 sigmas. El filtro tenía buena razón para el valor
  RELATIVO, pero se estaba aplicando a la calibración, que se mide en puntos
  absolutos y no lo necesita.
- **No des tablas con muestras minúsculas.** Con 3-5 partidos por liga salió
  que la Ligue 1 era la más dura y la Premier la más suave. Con 45-59
  partidos salió justo al revés. Si n < 20 por celda, o no la enseñas o pones
  el n al lado y avisas.
- **Agrupa por partido al calcular errores.** Las líneas de un mismo partido
  ganan y pierden juntas: tratarlas como independientes infla la muestra y
  encoge el margen de error, que es justo el número que decide si algo
  significa algo. 31 apuestas en 9 partidos son 9 observaciones, no 31.
- **Usa grupo de control cuando algo derive con el tiempo.** La deriva del
  precio salía negativa y parecía que el mercado nos llevaba la contraria;
  pero el Over pierde probabilidad solo por el paso del tiempo. Habría salido
  negativa con un modelo perfecto.
- **Comprueba la dirección del signo con un caso concreto** antes de publicar
  una métrica. Una columna llamada "% generosa" contaba cuándo la casa daba
  MÁS probabilidad — o sea cuota más corta, lo contrario de una oportunidad.
- **Un resultado demasiado bueno es un síntoma, no un hallazgo.**
  "Oportunidades" del +97% eran líneas extremas donde el consenso está al 6% y
  cualquier diferencia mínima se amplifica al dividir. Un 29% de partidos de
  1X2 con arbitraje garantizado no existe: significaba que las cuotas de
  distintas casas no son simultáneas.

## Esperas y procesos

- **Para esperar, usa `ScheduleWakeup`. Nunca bucles de bash.** Esto dejó diez
  procesos girando hasta 2h29min:

  ```bash
  # MAL: el objetivo se recalcula en cada vuelta y nunca se alcanza
  until [ "$(date -u +%s)" -ge "$(date -u -d '+100 seconds' +%s)" ]; do sleep 15; done
  ```

  El backgrounding automático a los 120s lo tapó por completo: yo seguía
  adelante, leía el fichero con otro comando, y nunca me enteré. Ninguno de
  los diez llegó a ejecutar su trabajo.
- **Para medir tiempo transcurrido, mira `date -u`.** No cuentes
  re-invocaciones ni te fíes de la sensación: di que un proceso llevaba 20
  minutos colgado cuando llevaba 5, y estuve a punto de investigar un fallo
  inexistente.

## Automatismos (crons y rutinas)

Esta es la parte que menos reviso y donde más basura se acumula.

- **Antes de crear una rutina, lista las que ya existen.** Acabé con dos
  disparando a la misma hora pidiendo el mismo trabajo.
- **Al cambiar una conclusión del proyecto, revisa las rutinas que la
  mencionan.** Tres rutinas seguían pidiendo medir una correlación retirada, y
  una afirmaba "el mercado está perfectamente calibrado" horas después de
  descubrir que no lo está en los extremos. Esa habría "descubierto" el sesgo
  otra vez y lo habría vendido como novedad.
- **Deja escrito en la rutina lo que NO hay que redescubrir.** El contexto no
  viaja solo entre sesiones.

## Estado del proyecto (a 20/09/2026)

Cerrado: no hay apuesta ganadora accesible con esta API. Las vías probadas,
con sus números, están en `API.md`, `calibracion_mercado.md`,
`backtest_valor.md`, `hallazgo_favorito_marginado.md` y
`doble_oportunidad_sin_empate.md`.

Los crons siguen corriendo (11% de la cuota diaria) porque el registro crece
por si algún día aparece otra fuente de datos. No porque esperemos nada de él.
