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

**Backfill completo (3478/3478 jugadores, terminado en una pasada): la
apuesta salió bien.** Cobertura de titulares pasó de 1,85 a 10,2 de 11
por equipo. Con cobertura completa:

| mercado | base+elo | +calidad (100%) | +arbitro | +arbitro+calidad |
|---|---|---|---|---|
| resultado | -2.97s | **-2.38s** | -3.09s | -2.55s |
| mas_2_5 | -1.09s | -0.98s | -0.85s | -0.87s |
| ambos_marcan | -2.19s | **-1.59s** | -1.73s | -1.01s |
| mas_9_5_corners | -1.29s | -1.40s | -1.19s | -1.55s |
| mas_4_5_tarjetas | -1.21s | -1.82s | -1.49s | -2.14s |

Suma de sigmas: base+elo -8.75, árbitro solo -8.35, **calidad_plantilla
sola -8.17**, **árbitro+calidad_plantilla -8.12 (la mejor combinación de
todo el proyecto)**. calidad_plantilla ya es mejor variable individual
que árbitro. `columnas_rasgo_default()` pasa a ser
**base + elo + árbitro + calidad_plantilla**.

Sigue sin batir a ningún mercado (hace falta +2s, estamos en -0.87s a
-2.55s) y la mezcla con el mercado en 1X2 (`aporta_algo.py`) sigue en
peso óptimo 0,00 -- pero el cero ahora sale en el 64% de los remuestreos
(antes 75% con solo árbitro, 83% en la primera versión del modelo). Es la
primera vez en toda la sesión que ese número baja en vez de subir al
mejorar el modelo. Vigilar: si sigue bajando al crecer la muestra de
cuotas cosechadas, podría ser la primera pista real del proyecto -- pero
con un solo punto de datos no se declara nada, exactamente la misma
disciplina que ya enterró la mezcla vieja cuando el número subió en vez
de bajar.

Barrido de qué más sumar encima de árbitro+calidad_plantilla (suma -8.12):
+tabla -8.12 (empate), +rotación -8.12 (empate), +h2h_profundo -8.00
(peor), +h2h -7.84 (peor), +clima -8.73 (peor, y menos partidos
utilizables). Nada mejora la combinación actual. Se queda como está.

## Ronda de variables cerrada (24/09/2026): superficie de la API agotada

`/standings` y `/teams/statistics/{id}` son las dos rutas que quedaban de
las 25 de `docs/openapi_highlightly.json` sin probar. Descartadas sin
gastar llamada, directo de la spec: ninguna tiene un parámetro de fecha
FINAL (`/standings` no tiene fecha en absoluto -- solo `leagueId`+
`season`, un snapshot de HOY; `/teams/statistics/{id}` solo tiene
`fromDate`, sin `toDate`). Las dos son "estadísticas hasta hoy", no
"estadísticas hasta la fecha X" -- estructuralmente imposibles de usar
para un partido histórico sin meter información posterior a ese partido.
`/standings` además es redundante con `calcular_tabla()`, que ya calcula
posición y puntos sin fuga desde el propio histórico.

Con esto, las rutas de la API con alguna promesa de variable histórica
sin fuga están agotadas: box-score, árbitro, clima, alineaciones/rotación,
H2H (propio y profundo vía API), y calidad de plantilla vía jugadores.
De siete vías probadas esta ronda (23-24/09), una funcionó de verdad
(calidad de plantilla) y otra parcialmente (árbitro). Las cinco restantes
(box-score, H2H, H2H profundo, tabla, rotación, clima) se probaron con
rigor y no ayudan, solas o combinadas con lo que sí funciona.

Modelo de producción actual: base + Elo + árbitro + calidad de plantilla.
Mejor resultado conseguido: -0.87s a -2.55s según mercado (necesita +2s
para batir al mercado). No es un hallazgo -- es el mejor punto de partida
que ha tenido el proyecto para si aparece más muestra o una fuente de
datos genuinamente distinta (el scouting en vivo, aparcado hasta que
vuelva la competición, sigue siendo la única vía no explorada).

## Acierto (hit-rate) además de Brier, y barrido de las 256 combinaciones (24/09/2026)

Pregunta que faltaba responder: todos los "mejora" de arriba se miden en
Brier (calibración). ¿El modelo acierta el resultado más veces que el
mercado, aunque pierda en Brier? Comprobado directamente (mismos 212
partidos, base+elo vs árbitro+calidad_plantilla vs el mercado):

| mercado | acierto base+elo | acierto árbitro+calidad (viejo) | acierto mercado |
|---|---|---|---|
| resultado | 46.7% | 45.3% | 51.4% |
| mas_2_5 | 59.4% | 60.8% | 65.6% |
| ambos_marcan | 53.3% | 59.0% | 58.5% |
| mas_9_5_corners | 53.8% | 52.8% | 58.5% |
| mas_4_5_tarjetas | 68.2% | 62.2% | 64.7% |

**El Brier y el acierto pueden moverse en direcciones distintas.** En
`resultado` y `tarjetas`, árbitro+calidad_plantilla mejoraba el Brier
frente a base+elo pero EMPEORABA el acierto (mejor calibrado, más veces
equivocado en el ganador). Solo `ambos_marcan` mejoraba las dos cosas a
la vez. Ninguna config bate al mercado en acierto tampoco: no es "el
modelo elige mejor pero se explica peor", pierde en las dos métricas.

**Barrido de las 256 combinaciones posibles de las 8 candidatas**
(`barrido_combinatorio.py`, cribado a 2 semillas por coste -- 256 x 5
mercados x 5 semillas completas habría tardado >1h; los mejores
candidatos del cribado se reevaluaron después con el protocolo completo
de 5 semillas antes de creerse nada, igual que exige este documento).

El barrido encontró algo que la ronda anterior no pudo ver: esa ronda
solo probó sumar cada candidata SOLA encima de árbitro+calidad_plantilla
("+h2h -7.84 peor", "+tabla -8.12 empate", etc., ver sección anterior).
Nunca probó combinarlas ENTRE ELLAS. Con el protocolo completo de 5
semillas, confirmado:

| config | suma sigmas | suma (acierto modelo - acierto mercado) |
|---|---|---|
| base+elo solo | -8.76 | -17.3pp |
| árbitro+calidad_plantilla (config anterior) | -8.12 | -18.5pp |
| h2h+h2h_profundo+tabla+calidad_plantilla (sin árbitro) | -7.94 | -14.1pp |
| **árbitro+h2h+h2h_profundo+tabla+calidad_plantilla (nueva default)** | **-7.93** | **-13.8pp** |
| las 8 candidatas juntas (kitchen sink) | -10.17 | -17.6pp (peor, y menos partidos por la cobertura de clima) |

La nueva combinación gana en 4 de 5 mercados en acierto frente a la
config anterior (empate en ambos_marcan), y en 3 de 5 en sigmas. Sigue
sin batir al mercado en ningún mercado (haría falta +2s; estamos en
-0.95s a -2.46s) y el acierto sigue perdiendo en las 5 líneas -- esto
NO es un hallazgo, es la mejor base encontrada hasta ahora, con las DOS
métricas moviéndose a la vez por primera vez en vez de solo el Brier.

`columnas_rasgo_default()` pasa a ser **base + elo + árbitro + h2h +
h2h_profundo + tabla + calidad_plantilla**. Box-score, clima y rotación
siguen fuera (el barrido de las 256 confirma que empeoran en
prácticamente todas las combinaciones donde aparecen, incluida la de
las 8 juntas).

El bootstrap de `aporta_algo.py` (peso óptimo de mezcla en 1X2) sale
cero en el 66% de los remuestreos con la nueva config (recalculado tras
corregir el bug de `grupos_rasgo()` de más abajo) -- no es comparable
directamente con el 64% de la config anterior (es una combinación de
rasgos distinta, no el mismo modelo con más cuotas). Se reinicia el
seguimiento de esa cifra desde este punto, con el 66% como referencia.

## Hiperparámetros de XGBoost: revisados, sin mejora (24/09/2026)

Toda la sesión giró en torno a QUÉ variables entran (111 rasgos ahora,
frente a los ~70 con los que se afinó `min_child_weight=20,
reg_lambda=5, max_depth=2` el 21/09). Regularización y variables son
ejes distintos -- más columnas con la misma regularización podría
sobreajustar, así que se revisó con una rejilla (max_depth 2/3,
min_child_weight 20/30/50, reg_lambda 5/10/20 -- 18 combinaciones,
protocolo completo de 5 semillas, mismo conjunto de rasgos de
producción de hoy) antes de tocar nada.

**Los valores actuales ya eran los mejores de la rejilla.** Cualquier
aumento de min_child_weight o reg_lambda empeoró la suma de sigmas
(de -7.9 hasta -9.4 en el peor caso) y el acierto. max_depth=3 no
mejoró sobre max_depth=2 con la misma regularización. No hay cambio
que aplicar -- se deja escrito para no repetir esta rejilla sin una
razón nueva (más partidos de entrenamiento sí podría justificar menos
regularización más adelante; con los mismos ~1700 partidos de
entrenamiento de hoy, no).

## Peso por recencia: probado, sin mejora (24/09/2026)

Idea: dar más peso a los partidos recientes al entrenar (`sample_weight`
con decaimiento exponencial), por si el fútbol de hace 13 meses aporta
menos que el de la semana pasada. Probado con vida media 730/365/180
días contra peso uniforme (protocolo completo de 5 semillas, rasgos de
producción):

  sin decaimiento (actual)        sigmas -7.91   acierto -15.6pp
  vida media 730d (peso min 0.81) sigmas -8.18   acierto -11.3pp
  vida media 365d (peso min 0.65) sigmas -8.80   acierto -18.9pp
  vida media 180d (peso min 0.42) sigmas -9.07   acierto -24.1pp

Cualquier decaimiento real (365d o menos) empeora las dos métricas con
claridad. El de 730d es casi plano (peso mínimo 0.81) y da una señal
mixta -- ruido, no una pista real: con solo ~13 meses de historial y
~1700 partidos de entrenamiento, restarle peso a una parte ya escasa de
los datos no compensa. Peso uniforme se queda. Junto con la rejilla de
hiperparámetros de arriba, el patrón es el mismo: el cuello de botella
de este proyecto es la CANTIDAD de partidos, no el ajuste del modelo --
cualquier técnica que reduzca el training set efectivo (más
regularización, menos peso a partidos viejos) empeora, no mejora.

## Bug en grupos_rasgo(): "elo" colaba box-score desde el 23/09 (24/09/2026)

Investigando la idea de forma reciente (ver siguiente sección) salieron
números que no cuadraban con los ya documentados para la config de
producción de hoy. La causa: `grupos_rasgo()` clasificaba con
`elif "elo" in c`, una comprobación de SUBCADENA. "duelos_totales" y
"duelos_ganados_pct" (dos medidas de `/box-score`, `du**elo**s`)
contienen "elo" -- sus 12 columnas (`loc_/vis_/dif_m_duelos_totales`,
`..._duelos_ganados_pct`, propias y `contra_`) caían en el grupo "elo"
en vez de en "boxscore".

**Alcance real:** el grupo "elo" está en `NUCLEO` (`experimentos_rasgos.py`
y `barrido_combinatorio.py`) y en TODAS las configs de producción desde
que `grupos_rasgo()` existe (23/09). Eso significa que cada vez que este
documento dijo "base+elo" o "sin box-score", en realidad llevaba colados
esos 12 columnas de box-score. La conclusión "box-score empeora las 5
líneas en TODAS las combinaciones" (sección "Árbitro, clima y rotación")
seguía siendo cierta -- las otras 30 columnas de box-score, sumadas
ENCIMA de esa base ya contaminada, seguían empeorando -- pero nunca se
probó "cero box-score" de verdad hasta hoy.

**Corregido:** `elif "elo" in c` -> `elif c.endswith("_elo")`. Se separa
además un grupo `duelos` propio (las 12+12 columnas de ventana larga y
corta) para poder probarlo aislado del resto de box-score, siguiendo la
misma disciplina que ya está escrita en este documento ("no excluyas una
familia entera por una parte complicada"). Probado con el protocolo
completo de 5 semillas: **duelos, añadido a la config de producción
completa, la empeora** (sigmas -8.72 -> -8.90, acierto -15.3pp ->
-22.8pp, mismo proceso, comparación directa). Se queda fuera. La
decisión de excluir box-score entero sigue siendo correcta, ahora
probada de verdad y no por accidente.

**Números CORREGIDOS de la config de producción de hoy** (base + elo +
árbitro + h2h + h2h_profundo + tabla + calidad_plantilla, 99 rasgos,
2239 partidos -- antes decía 111/123 rasgos por la contaminación):

  resultado         -2.44s   acierto 45.8% vs mercado 51.4% (-5.7pp)
  mas_2_5           -1.17s   acierto 61.8% vs mercado 65.6% (-3.8pp)
  ambos_marcan      -0.77s   acierto 58.5% vs mercado 58.5% (+0.0pp)
  mas_9_5_corners   -1.66s   acierto 54.2% vs mercado 58.5% (-4.2pp)
  mas_4_5_tarjetas  -2.77s   acierto 61.2% vs mercado 64.7% (-3.5pp)
  SUMA sigmas -8.81, SUMA acierto_dif -17.2pp

Estos números son PEORES que los -7.93s/-13.8pp documentados ayer (la
contaminación estaba ayudando un poco). Verificado que la conclusión
que importa NO cambia: la config de hoy (con h2h+h2h_profundo+tabla)
sigue batiendo a la de ayer (solo árbitro+calidad) bajo la agrupación
corregida -- sigmas -8.72 vs -8.99, acierto -15.3pp vs -19.5pp (cifras
ligeramente distintas a las de arriba por ruido de proceso, mismo
orden de magnitud). El barrido de las 256 combinaciones NO se relanza:
la contaminación era una constante añadida a las 256 por igual (todas
incluían "elo"), así que el ORDEN relativo entre combinaciones debería
seguir siendo válido aunque los valores absolutos de aquella tabla ya
no lo sean. Si se necesita un número absoluto exacto de algo del
barrido, no fiarse de `data/barrido_combinatorio.csv` -- está calculado
con el bug.

**Lección:** revisar un `in` sobre texto libre por colisiones de
subcadena antes de usarlo para agrupar/filtrar columnas -- exactamente
el mismo tipo de fallo silencioso que "First Team To Score" con
mayúscula al principio de este documento. No dio error, dio números
buenos y equivocados durante dos días.

## Forma reciente (ventana corta): probada, sin mejora (24/09/2026)

Petición del usuario, lógica de fútbol legítima: el rendimiento de hace
8 meses no debería pesar igual que el de los últimos 3 partidos. Ya se
había probado (y descartado) dar menos peso a FILAS DE ENTRENAMIENTO
viejas ("Peso por recencia", arriba) -- esto es distinto: una variable
NUEVA, media móvil de ventana corta (3 partidos, `forma_reciente()` en
rasgos.py, prefijo `r_`) además de la que ya existe (`m_`, ventana 8),
dejando que el modelo decida cuánto pesa cada una en vez de imponerlo.
Misma regla anti-fuga (`shift(1)` antes de `rolling`), comprobado con
`comprobar_sin_fuga`.

Probada de dos formas, protocolo completo de 5 semillas, agrupación ya
corregida (ver bug de arriba):

  base+elo                                    sigmas -9.49  acierto -19.8pp
  +forma_reciente completa (90 columnas)      sigmas -11.90 acierto -31.7pp
  +forma_reciente mínima (solo puntos+goles, 6 columnas)  sigmas -10.07  acierto -21.1pp

  produccion                                  sigmas -8.72  acierto -15.3pp
  produccion+forma_reciente completa          sigmas -11.32 acierto -30.3pp
  produccion+forma_reciente mínima            sigmas -9.23  acierto -17.2pp

**Empeora en las dos versiones, no solo por exceso de columnas.** La
versión mínima (6 columnas: puntos y goles en los últimos 3 partidos)
descarta la hipótesis de que el daño era sobreajuste por las otras 84
columnas -- la señal de "forma de las últimas 3 jornadas" en sí misma
no aporta. Explicación más probable: el Elo ya es sensible a la forma
reciente (se actualiza partido a partido, una racha ya mueve el
rating) y `m_puntos` (ventana 8) ya cubre el medio plazo; una ventana
de solo 3 partidos es demasiado ruidosa (varianza alta con tan pocos
partidos por muestra) para añadir información que esas dos no den ya.
No entra en `columnas_rasgo_default()`. La lógica de fútbol era
razonable -- la comprobación con datos reales es la que manda.

**Repregunta del usuario, con razón:** ¿cómo va a ser ruido la forma
reciente si un equipo arrasando la liga (su ejemplo: el Barça este
inicio) obviamente va a golear al siguiente rival? Comprobado en vez de
solo argumentado:

1. **Correlación real entre ventana corta y larga: 0,70-0,72**
   (`loc_m_puntos` vs `loc_r_puntos`, `vis_` igual; Elo vs r_puntos:
   0,59). Confirma la explicación: la ventana de 3 no es ruido en el
   sentido de "no informa", es en gran parte la MISMA información que
   ya llevan Elo y la ventana de 8 -- un equipo arrasando ya tiene Elo
   alto y m_puntos alto, porque ambos usan partidos recientes también.
   Añadirla en bruto duplica señal correlacionada y solo suma varianza
   con ~1700 partidos de entrenamiento.

2. **Se probó la parte que NO es redundante: `momentum = r_puntos -
   m_puntos`** (puntos y goles de los últimos 3 MENOS la base de 8 --
   "¿el equipo rinde por encima o por debajo de su propio nivel ya
   establecido AHORA MISMO?", que es literalmente lo que describe el
   ejemplo del Barça). Resultado, protocolo completo de 5 semillas:

     produccion            resultado -2.42s/45.3%  mas_2_5 -1.24s/63.2%  ambos_marcan -0.68s/59.0%  corners -1.63s/55.7%  tarjetas -2.75s/60.2%
     produccion+momentum   resultado -2.57s/46.2%  mas_2_5 -1.13s/61.8%  ambos_marcan -0.84s/59.9%  corners -1.71s/54.7%  tarjetas -2.90s/60.2%

   Mezclado: mejora acierto en resultado y ambos_marcan, empeora en
   mas_2_5 y corners, tarjetas sin cambio. Nada consistente en ninguna
   dirección -- a diferencia de la versión en bruto (que empeoraba las
   5 líneas con claridad), esto es RUIDO estadístico alrededor de cero,
   no un empeoramiento sistemático. No entra en producción (no hay
   nada que declarar con esto), pero es una respuesta distinta a "no
   sirve": es "puede que haya algo, 2239 partidos no bastan para verlo".

3. **La razón de fondo, la más importante:** que la forma reciente
   prediga bien el PARTIDO no significa que nos dé ventaja sobre la
   CASA. El Barça arrasando no es un secreto -- las casas también lo
   ven, y por eso su cuota para golear ya está corta. Este proyecto no
   mide "¿la forma reciente predice fútbol?" (sí, obviamente) sino
   "¿nos da información que el precio no lleve ya dentro?", que es una
   pregunta distinta y más difícil. Es la misma razón por la que el
   Elo -- una de las variables más predictivas que existen en fútbol,
   documentada como tal en este mismo fichero -- tampoco basta para
   batir al mercado solo.

## Auditoría de bugs de subcadena, y poda por importancia: sin cambios (24/09/2026)

**Auditoría:** el bug de "elo"/"duelos" es del tipo que suele repetirse
-- se revisaron los demás `"x" in c` de `grupos_rasgo()` (`tabla_`,
`rotacion`, `calidad_`, `duelos`) y del resto de `scripts/*.py` a mano.
Ninguno tiene colisión real: los otros usos son sobre descripciones de
estado de partido ("finish", "weather", "card"...), no clasificación de
columnas con nombres parecidos entre sí. Limpio.

**Poda por importancia:** si "más columnas sin más filas compra
sobreajuste" es el patrón de toda la sesión, ¿ayuda quedarse solo con
las variables más importantes de las 99 actuales? Importancia media
(gain de XGBoost, 5 mercados x 5 semillas) rankeada, probado top-K
recortando por ese ranking, protocolo completo de 5 semillas:

  top-20   sigmas -10.89  acierto -20.0pp
  top-30   sigmas -11.06  acierto -15.7pp
  top-40   sigmas -10.10  acierto -19.4pp
  top-60   sigmas -10.58  acierto -18.6pp
  top-80   sigmas  -8.57  acierto -15.4pp
  top-99 (todas)  sigmas -8.90  acierto -15.8pp

**Sin patrón limpio.** No es monótono (top-40 mejor que top-30 y top-60,
top-80 mejor que top-99 y que todo lo demás) -- son saltos del tamaño
del ruido de proceso ya visto en otras pruebas de esta sesión (0.1-1.2
sigmas entre corridas nominalmente idénticas), no una tendencia real.
top-80 parece ligeramente mejor que el set completo pero la diferencia
(-8.57 vs -8.90) no se distingue del ruido. Explicación probable: cortar
por ranking de importancia rompe tríos loc_/vis_/dif_ que solo aportan
juntos (si dif_elo rankea alto pero loc_elo no entra en el top-K, se
pierde la mitad de la pareja). No se cambia `columnas_rasgo_default()`
-- ni evidencia de que ayude ni de que dañe con claridad.

## Sondeo: "gol de equipo en la 1ª parte" no existe en esta API (24/09/2026)

Pregunta del usuario sobre un mercado concreto. Comprobado con datos
crudos de `/odds` (mismo patrón que `censo_mercados_crudo.py`), en tres
tandas:

1. Calendario futuro sin filtrar por liga: 151 mercados distintos, cero
  relacionados con medio tiempo -- pero el primer intento tenía un fallo
  de filtro (falsos positivos con "Both/First Team To Score", que
  contienen "to score" pero no tienen nada que ver con la 1ª parte) y
  campos de la API mal leídos (bookmakerName/values[].value/values[].odd,
  no bookmaker/name/handicap -- de ahí que saliera "casas=1" en todo).
2. Corregido, y filtrado a partidos de calendario.csv en las 5 grandes
  ligas (Premier League, La Liga, Serie A, Bundesliga, Ligue 1): dio
  "0 mercados" -- esos partidos estaban a 15-25 días vista y las cuotas
  previas se rellenan progresivamente durante días (ya documentado en
  este mismo fichero). Nada que ver con que el mercado no exista.
3. Repetido con partidos YA JUGADOS de esas mismas 5 ligas
  (`historico_partidos.csv`, los más recientes): esta vez con cobertura
  real (hasta 50 casas en Full Time Result), **207 mercados distintos,
  ninguno de medio tiempo/1ª parte**.
4. A petición del usuario, repetido en la UEFA Nations League (id 5039
  -- esta API la reconoce con `leagueName=UEFA Nations League` exacto,
  "Nations League" sin más no encuentra nada). 26 partidos próximos, 20
  sondeados, **195 mercados distintos, tampoco ninguno de medio tiempo**.

**Conclusión:** ni en las 5 grandes ligas europeas ni en la UEFA Nations
League ofrece esta API (con las casas que cubre) un mercado de "equipo
X marca en la 1ª parte". Lo más cercano que sí existe es **First Team To
Score** (quién marca primero en TODO el partido, sin restricción de
tiempo) -- un mercado distinto. Con cientos de nombres de mercado
vistos entre las dos tandas y ninguno de medio tiempo, no parece que
esta API/estas casas lo vendan, más que un problema de muestra.

Nota técnica para el futuro: `/leagues` acepta `leagueName` (coincidencia
exacta del nombre en la API, no libre) y `/matches` acepta `leagueId`+
`date` (un día por llamada) -- útil si hace falta sondear otra
competición internacional que este proyecto no tenga configurada.
