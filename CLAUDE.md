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

## Antes de afirmar que algo NO existe

- **Lee la especificación entera antes de decir "la API no da eso".** Escribí
  en `veredicto.md` que no había alineaciones. Están en `/lineups`, desde
  siempre, y encima ya salían en mi propia tabla de refrescos de `API.md`. La
  especificación tiene **25 rutas**; el proyecto usaba seis. Está guardada en
  `docs/openapi_highlightly.json`: mírala.
- **Un 404 en la ruta que te inventaste no prueba que el dato no exista.**
  Pedí `/referees`, dio 404, y lo di por inexistente. El árbitro viene dentro
  de `/matches/{id}`, junto con el tiempo que hará, el estadio y las
  predicciones de la propia API.
- **Mira la respuesta ENTERA de lo que ya pides.** Llevábamos el proyecto
  entero llamando a `/statistics` para sacar las faltas, sin ver que la misma
  respuesta traía 39 estadísticas por equipo, xG incluido. Ya la estábamos
  pagando.
- Una ausencia afirmada sin comprobar es el peor caso de la regla de arriba:
  no da error, cierra líneas de trabajo enteras, y nadie se entera.

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

- **La vigilancia de una liga no se mide en un partido futuro.** El censo de
  ligas blandas marco Rumania Liga II (3 casas) y Mexico Liga MX (6 casas)
  como candidatas mirando UN partido a varios dias vista. Las cuotas previas
  se rellenan progresivamente durante dias (documentado en la API); un
  partido lejano puede tener 3 casas puestas y llegar a 40 el dia del
  pitido. Analizando partidos YA JUGADOS de esas mismas ligas: 41,6 y 30,4
  casas de media. Casi diez veces mas. La vigilancia se mide sobre partidos
  cerrados, nunca sobre una foto de un partido que aun no ha terminado de
  cotizar.
- **Cuando un numero sale demasiado bueno, hay que perseguir QUE partido lo
  empuja, no solo cuantos sigmas da.** Mexico Liga MX salio +20,41% a ciegas,
  +1,33 sigmas sobre 31 partidos. Un solo partido (una sorpresa a cuota
  12.50) aportaba 6,76 de los 24,0 puntos de la media. Quitandolo, la
  significacion cae a 0,82 sigmas. No es un dato falso -- el marcador y la
  cuota eran correctos -- es una muestra de 31 partidos que un solo resultado
  puede mover casi siete puntos enteros. Ni se declaro hallazgo ni se
  descarto: se dejo escrito que hace falta mas muestra antes de que el
  numero signifique algo.

- **Si al crecer la muestra el número se mueve hacia cero, era falso.** Un
  efecto real se queda donde está y solo estrecha su intervalo. Con 89
  partidos, mezclar mercado y modelo daba peso óptimo 0,43 y una mejora del
  1,5% de Brier, con curva suave y mínimo marcado. Con 168 partidos: peso
  0,10, mejora 0,01%, y el cero aparece en el 35% de los remuestreos en vez
  del 9%. Lo que salvó de apostar sobre eso fue haber dado el intervalo del
  bootstrap junto al punto central, y haberlo llamado pista y no hallazgo.
  **Confirmado el 21/09 con 212 partidos: peso óptimo 0,00, Brier de la
  mezcla igual al del mercado solo, cero en el 76% de los remuestreos. La
  pista murió del todo. Cerrado: no reabrir "la mezcla" salvo con una
  fuente de datos nueva, no con más partidos de la misma.**

- **Antes de montar un modelo para batir un precio, mide si ese precio está
  mal.** Propuse los córners porque "en un mercado no vigilado el precio es
  crudo y puede estar equivocado más de un 6%". Comprobable en cinco minutos
  con datos que ya estaban en disco: se compara lo que perderías contra un
  precio PERFECTO (`-margen/(1+margen)`) con lo que se perdió de verdad. En
  córners el hueco es **+0.72%, a 0.70 sigmas**: el precio es exacto, solo
  caro. Dos semanas de recolección ahorradas por una resta. Si el precio no
  está torcido, un modelo mejor no tiene nada que corregir.

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
