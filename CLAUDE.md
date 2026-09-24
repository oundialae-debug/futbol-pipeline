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

## Box-score (22/09/2026): las 7 variables nuevas no ayudaron

Backfill completo (2537 de 2539 partidos) de las 7 variables por-jugador de
`/box-score` (faltas recibidas, duelos, xG evitado por el portero...).
`evaluar_mercados.py` con los datos completos, mismos 212 partidos fuera de
muestra que el baseline sin box-score:

| mercado | sin box-score | con box-score |
|---|---|---|
| resultado | -3.01s | -3.30s |
| mas_2_5 | -1.44s | -1.41s |
| ambos_marcan | -1.91s | -2.48s |
| mas_9_5_corners | -1.62s | -1.53s |
| mas_4_5_tarjetas | -1.40s | -1.95s |

Tres mercados empeoraron, dos quedaron igual. Ninguno mejoró. El peso óptimo
de mezcla mercado+modelo sale 0,00 en 4 de 5 (el quinto, mas_2_5, sale 0,05
con intervalo [0,00, 0,60] -- incluye cero). Más variables con la misma
cantidad de partidos de entrenamiento no compró señal, compró sobreajuste.
No reabrir "más variables por-jugador" como vía salvo con más partidos, no
solo más columnas.

## Experimentos de rasgos, uno a uno (23/09/2026)

El error del primer intento: probar box-score, H2H y tabla siempre TODOS
JUNTOS no dice cuál empuja y cuál estorba. `scripts/experimentos_rasgos.py`
prueba cada grupo solo y combinado, con la misma maquinaria de
`evaluar_mercados.py` (5 semillas, mismo corte temporal). Núcleo fijo:
base + Elo (85 rasgos, 2239 partidos utilizables).

| mercado | base+elo | +h2h | +tabla | +boxscore | mejor combo |
|---|---|---|---|---|---|
| resultado | -2.97s | -2.99s | -2.95s | -3.34s | tabla sola (-2.95s) |
| mas_2_5 | -1.09s | -1.21s | -1.22s | -1.37s | **base+elo sola** |
| ambos_marcan | -2.19s | -2.24s | -2.26s | -2.40s | h2h+tabla (-2.08s) |
| mas_9_5_corners | -1.29s | -1.21s | -0.94s | -1.37s | tabla sola (-0.94s) |
| mas_4_5_tarjetas | -1.21s | -1.22s | -1.53s | -1.78s | **base+elo sola** |

## Árbitro, clima y rotación (23/09/2026): árbitro es la mejor variable probada

Comprobado antes de gastar cuota (sondeo_matches.py, sondeo_lineups.py):
`/matches/{id}` da árbitro y previsión meteorológica en partidos viejos, no
solo próximos (confirmado hasta 13 meses atrás), y `/lineups/{id}` también.
Backfill de árbitro+clima completo en una pasada: 2539/2539 partidos, 91%
cobertura de árbitro, 95% de clima. Lineups pendiente.

`arbitro_tarjetas_media`: tarjetas medias de CADA árbitro usando solo sus
apariciones anteriores (misma regla anti-fuga que Elo/H2H/tabla). Probado
solo contra base+elo (212 partidos, mismo corte):

| mercado | base+elo | +arbitro | +clima | +arbitro+tabla | +arbitro+h2h |
|---|---|---|---|---|---|
| resultado | -2.97s | -3.09s | -2.84s* | -3.17s | -3.19s |
| mas_2_5 | -1.09s | **-0.85s** | -1.01s* | -1.03s | -0.93s |
| ambos_marcan | -2.19s | **-1.73s** | -2.25s* | -1.85s | -1.78s |
| mas_9_5_corners | -1.29s | -1.19s | -1.38s* | -0.91s | -1.32s |
| mas_4_5_tarjetas | -1.21s | -1.49s | -1.43s* | -1.77s | -1.63s |

(*clima usa 199 partidos y corte de fecha distinto por su propia
cobertura -- no comparar en punto exacto, solo dirección.)

**Árbitro solo mejora 3 de 5 mercados de forma clara** (mas_2_5 y
ambos_marcan sobre todo) y es la única variable de toda esta ronda con
suma neta de sigmas positiva sobre base+elo (-8.35 contra -8.75). Lo
contraintuitivo: mezclarlo con tabla o H2H lo EMPEORA en 4 de 5 mercados
(solo mejora córners un poco) -- más columnas con las mismas 2239 filas
de entrenamiento sigue comprando sobreajuste, incluso cuando una de las
columnas nuevas es buena. `columnas_rasgo_default()` pasa a ser
**base + elo + árbitro únicamente**; h2h y tabla se quedan fuera del set
de producción por primera vez desde que se añadieron, aunque siguen en el
código. Ninguna combinación bate al mercado (todas siguen entre -0.85s y
-3.19s, hace falta +2s), pero es la mejor base encontrada hasta ahora.

Rotación (titulares que cambian respecto al partido anterior del mismo
equipo, por ID de jugador): backfill completo (2510/2539 partidos, 2442
con rotación calculable). Probada sola y con árbitro:

| mercado | base+elo | +rotacion | +arbitro | +arbitro+rotacion |
|---|---|---|---|---|
| resultado | -2.97s | -3.07s | -3.09s | -3.13s |
| mas_2_5 | -1.09s | -1.13s | -0.85s | -0.95s |
| ambos_marcan | -2.19s | -2.31s | -1.73s | -1.98s |
| mas_9_5_corners | -1.29s | -1.29s | -1.19s | -1.20s |
| mas_4_5_tarjetas | -1.21s | **-1.03s** | -1.49s | -1.54s |

Rotación sola solo ayuda en tarjetas, empeora las demás. Sumada a árbitro,
lo empeora en 4 de 5 -- mismo patrón que tabla y h2h: la única variable
que sobrevive a combinarse sin perder es ninguna, árbitro gana siempre
solo. No entra en `columnas_rasgo_default()`.

**Box-score empeora los 5 mercados en TODAS las combinaciones donde
aparece**, aislado o mezclado. Confirma el hallazgo del 22/09 con una
prueba limpia -- se quita del set de columnas por defecto
(`modelo_xgboost.cargar()` deja de fusionar `historico_boxscore.csv`; el
backfill queda parado, sin sentido seguir gastando cuota en él).

H2H y tabla, solos, son mixtos: cada uno ayuda en una línea (tabla en
córners, marginal) y empeora en las demás. Ninguna combinación bate al
mercado ni se acerca (todas entre -0.9s y -3.3s, hace falta +2s). Esto no
es "encontramos algo", es "sabemos mejor cuál duele menos". Se mantiene
h2h y tabla en el código por ser gratis y no dañar de forma consistente,
pero ninguno se declara hallazgo.

## H2H profundo vía /head-2-head (24/09/2026): mejor cobertura, mismo techo

`calcular_h2h()` solo veía enfrentamientos dentro de los 13 meses del
propio histórico -- mediana 0-1 partidos previos por par, 52% de pares sin
historia. La API tiene una ruta dedicada, `/head-2-head`, con las últimas
10 confrontaciones REALES entre dos equipos. Comprobado con Real
Madrid-Barcelona (`sondeo_h2h.py`): 7 de esas 10 son de ANTES de nuestra
ventana, hasta abril de 2024. Backfill por PAR de equipo (1218 pares, no
2539 partidos -- la mitad de llamadas), completo en una pasada: 9206
confrontaciones reales, mediana 7 partidos previos por par (antes 0-1).

Filtrado con más cuidado que el resto: la API da "las últimas 10 A DÍA DE
HOY", no "las últimas 10 antes de cada partido del histórico" -- así que
`calcular_h2h_profundo()` descarta explícitamente cualquier confrontación
con fecha posterior al partido que se está evaluando, no se fía del orden
que da la API.

| mercado | base+elo | +h2h_profundo | +arbitro | +arbitro+h2h_profundo |
|---|---|---|---|---|
| resultado | -2.97s | **-2.83s** | -3.09s | -3.12s |
| mas_2_5 | -1.09s | -1.19s | -0.85s | -0.96s |
| ambos_marcan | -2.19s | -2.33s | -1.73s | -1.72s |
| mas_9_5_corners | -1.29s | -1.22s | -1.19s | -1.17s |
| mas_4_5_tarjetas | -1.21s | -1.35s | -1.49s | -1.75s |

H2H profundo solo mejora `resultado` (la mejor mejora individual vista en
esa línea de toda la ronda), pero empeora las otras 3 de 5. Combinado con
árbitro, la suma neta sigue siendo peor que árbitro solo (-8.72 contra
-8.35) -- daña menos que tabla/h2h/rotación al combinarse (ambos_marcan y
córners casi no se mueven), pero no lo suficiente para ganarle a "árbitro
solo". Mismo veredicto que todo lo demás: mejor cobertura no fue mejor
señal. No entra en `columnas_rasgo_default()`.

## Calidad de plantilla (24/09/2026): el mejor resultado de toda la sesión

Cruza quién JUEGA de verdad (alineaciones, ya backfilleadas) con lo que
rindió cada jugador en su temporada ANTERIOR ya cerrada -- minutos y
goles+asistencias medios de los titulares con dato conocido, con un
contador de cuántos de los 11 son conocidos (media, no suma, para no
confundir "equipo bueno" con "equipo con más jugadores en la muestra").
`sondeo_jugador_stats.py` (24/09) confirmó que la API rompe limpio por
temporada y que la anterior es un hecho fijo, sin fuga posible.

Backfill de validación con SOLO 500 de los 3478 jugadores únicos
(priorizados por frecuencia de aparición): 74% de los partidos ya tienen
al menos 1 titular conocido, media 1,85 de 11 por equipo.

| mercado | base+elo | +calidad_plantilla | +arbitro | +arbitro+calidad |
|---|---|---|---|---|
| resultado | -2.97s | **-2.76s** | -3.09s | **-2.89s** |
| mas_2_5 | -1.09s | -1.27s | -0.85s | -1.23s |
| ambos_marcan | -2.19s | -2.17s | -1.73s | -1.78s |
| mas_9_5_corners | -1.29s | **-1.06s** | -1.19s | -1.19s |
| mas_4_5_tarjetas | -1.21s | **-1.17s** | -1.49s | **-1.40s** |

**Sola, mejora 3 de 5 mercados de forma clara** (suma de sigmas -8.43
contra -8.75 de base+elo, +0.32 neto) -- con solo el 14% de los
jugadores cubiertos. Es el mejor resultado individual de toda la sesión
después de árbitro, y el único que mejora `resultado` Y `mas_9_5_corners`
Y `mas_4_5_tarjetas` a la vez. Combinada con árbitro, la suma es -8.49 --
peor que árbitro solo (-8.35) pero mejor que cualquier otra combinación
probada con árbitro, y `resultado` mejora notablemente en la combinación
(-3.09s -> -2.89s).

Con solo 14% de cobertura ya compite con las mejores variables de la
sesión: se lanza el backfill COMPLETO (los ~2978 jugadores restantes) en
vez de cerrar la vía aquí -- es la única variable de toda la ronda donde
más cobertura parece razonable esperar que ayude más, no que sume ruido.
