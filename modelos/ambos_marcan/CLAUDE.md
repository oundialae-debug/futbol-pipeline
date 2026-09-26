# Ambos Marcan -- offshoot enfocado de futbol-pipeline

Creado el 24/09/2026 a partir del repo padre (`futbol-pipeline`, carpeta
raíz de este mismo repositorio). Contiene solo lo necesario para entrenar
y evaluar el modelo del mercado **Both Teams To Score (ambos marcan)** --
es el mercado más cerca de competir con el mercado de los cinco que sigue
el proyecto padre.

## Por qué existe esta carpeta

`ambos_marcan` llevaba dos días siendo el mercado con mejor sigma de los
cinco modelados (-0.77s, el menos negativo). Petición del usuario: aislar
todo lo necesario para seguir mejorando específicamente ese mercado sin
arrastrar los otros cuatro. No se pudo crear un repositorio de GitHub
nuevo (la integración de esta sesión no tiene permiso para crear repos,
403 "Resource not accessible by integration") -- esto es la alternativa:
una carpeta autocontenida dentro del mismo repo, con su propio CLAUDE.md.

## Qué hay aquí, y qué NO

- `scripts/rasgos.py`, `scripts/modelo_xgboost.py`, `scripts/evaluar_mercados.py`:
  copia exacta de la versión del 24/09 del repo padre. Funcionan con rutas
  relativas (`data/...`), así que hay que ejecutarlos desde ESTA carpeta
  (`cd modelos/ambos_marcan && python3 scripts/...`), no desde la raíz del
  repo.
- `scripts/prueba_humo.py`: **nuevo, no es una copia**. El prueba_humo.py
  del repo padre prueba `descanso_en_vivo.py` (el modelo de tarjetas al
  descanso), que no tiene nada que ver con esto -- copiarlo tal cual habría
  sido una prueba de humo que no prueba nada de lo que hay aquí. Este
  construye los rasgos, comprueba que no hay fuga, y entrena un modelo
  real sobre datos reales, sin tocar la red.
- `data/*.csv`: históricos completos (partidos, árbitro/clima, lineups,
  stats de jugador, h2h profundo) -- se necesitan enteros para construir
  CUALQUIER rasgo, no solo los de ambos_marcan.
- `data/cuotas_cosechadas.csv` y `data/backtest_valor.csv`: **filtrados a
  SOLO "Both Teams To Score"** (15.976 y 8.340 filas respectivamente, de
  777.525 y 169.407 en el repo padre) -- el resto de mercados no hace
  falta aquí y el fichero completo pesaba 86MB. Por eso
  `evaluar_mercados.py` dice "sin cuotas" para resultado/mas_2_5/corners/
  tarjetas: es a propósito, no un fallo.
- **NO está `historico_boxscore.csv`**: ya se probó (dos veces, con y sin
  el bug de "elo"/"duelos") y siempre empeora. `modelo_xgboost.cargar()`
  sigue soportando fusionarlo si algún día hiciera falta reabrir esa vía
  (se omite en silencio si el fichero no existe, no rompe nada), pero no
  se copia aquí para no arrastrar una vía ya cerrada.
- **NO hay workflows de GitHub Actions ni la clave de la API**
  (`HIGHLIGHTLY_API_KEY`): no se puede copiar un secreto entre repos/carpetas
  desde esta sesión. Si hace falta cosechar cuotas nuevas o ampliar el
  histórico, hay que hacerlo desde el repo padre (que sí tiene los
  workflows y el secreto) y volver a copiar/filtrar los CSV a esta carpeta
  a mano.

## Estado del modelo (24/09/2026, heredado del repo padre)

Config de producción: **base + Elo + árbitro + h2h + h2h_profundo + tabla
+ calidad_plantilla** (99 rasgos, `columnas_rasgo_default()` en
`rasgos.py`). Resultado en `ambos_marcan`:

    sigmas: -0.77s   (el objetivo son +2s para "batir al mercado")
    acierto: 58.5% modelo vs 58.5% mercado (empate)
    mezcla modelo+mercado: peso óptimo 0.20, intervalo 95% [0.00, 0.95]
    (el intervalo incluye el cero -- no es un hallazgo, pero es el único
    de los 5 mercados originales donde el peso óptimo no es 0.00)

Verificado corriendo `prueba_humo.py` y `evaluar_mercados.py` en esta
misma carpeta el 24/09: reproduce exactamente estos números.

## Qué variables ayudaron, y qué NO -- no redescubrir esto

Probado con el protocolo del repo padre (5 semillas, mismo corte
temporal, sigmas Y acierto, nunca solo Brier) a lo largo de la sesión del
24/09. Tabla completa, de mejor a peor sigma para `ambos_marcan`:

| Configuración | Sigmas |
|---|---|
| árbitro + h2h + h2h_profundo + tabla + calidad_plantilla (actual) | -0.77s |
| árbitro + calidad_plantilla | -1.01s |
| calidad_plantilla sola (cobertura 100%) | -1.59s |
| árbitro solo | -1.73s |
| árbitro + h2h_profundo | -1.72s |
| árbitro + h2h | -1.78s |
| árbitro + tabla | -1.85s |
| árbitro + rotación | -1.98s |
| base + Elo (sin nada) | -2.19s |
| + h2h + tabla juntas | -2.08s |
| + h2h sola | -2.24s |
| + tabla sola | -2.26s |
| + rotación sola | -2.31s |
| + h2h_profundo solo | -2.33s |
| + box-score | -2.48s |

**Solo dos variables movieron la aguja de verdad: árbitro (primero) y
calidad_plantilla con cobertura completa (segundo, el mayor salto).**
Todo lo demás probado específicamente para este mercado o en general
**no ayudó o ayudó muy poco, y ninguno sobrevivió a combinarse con el
resto salvo tabla/h2h/h2h_profundo sumadas TODAS juntas** (nunca solas):

- **Box-score** (7 variables por-jugador de `/box-score`): empeora
  siempre, en todas las combinaciones probadas. Cerrado dos veces.
- **Duelos** (`duelos_totales`/`duelos_ganados_pct`, parte de box-score,
  se coló sin querer en el grupo "elo" por un bug de subcadena --
  corregido el 24/09): probado aislado tras corregir el bug, también
  empeora. Sigue cerrado.
- **H2H, tabla, rotación, h2h_profundo, solos**: mixtos, ninguno bate a
  base+elo con claridad, y sumados a árbitro lo EMPEORAN individualmente
  -- solo ayudan cuando van los tres juntos (h2h+h2h_profundo+tabla) además
  de árbitro+calidad, que es la config actual.
- **Clima**: mayormente negativo, y menos partidos utilizables por su
  cobertura parcial.
- **Forma reciente** (media móvil de ventana corta, 3 partidos, además de
  la de 8 que ya existe): probada completa y en versión mínima (solo
  puntos+goles), las dos empeoran con claridad. Motivo: correlación
  0.70-0.72 con la ventana larga que ya existe -- no es ruido sin
  sentido, es información mayormente redundante con Elo y `m_puntos`.
- **Momentum** (`r_puntos - m_puntos`, la parte de forma reciente que NO
  es redundante): probado a petición del usuario tras cuestionar lo
  anterior con razón (ejemplo del Barça arrasando la liga). Resultado
  mezclado, sin dirección clara -- ni ayuda ni daña de forma consistente,
  a diferencia de la versión en bruto. No es un "no sirve", es "2239
  partidos no bastan para verlo si hay algo".
- **btts_tasa** (proporción de los últimos 8 partidos de cada equipo
  donde él Y el rival marcaron -- variable pensada específicamente para
  ESTE mercado, distinta de la media de goles ya existente): sola contra
  base+elo mejora un poco el Brier pero no el acierto; sumada a la config
  completa, el acierto EMPEORA (pasa de empatar con el mercado a perder
  por -0.9pp). Mismo patrón que h2h/tabla/rotación: ayuda aislada, no
  sobrevive a combinarse.
- **Hiperparámetros de XGBoost**: revisados con una rejilla de 18
  combinaciones (max_depth, min_child_weight, reg_lambda) -- los actuales
  ya eran los mejores. Más regularización empeora con este tamaño de
  muestra (~1700 partidos de entrenamiento).
- **Peso por recencia en el entrenamiento** (dar más peso a partidos
  recientes vía `sample_weight`): probado con tres velocidades de
  decaimiento, todas empeoran. El cuello de botella es la cantidad de
  partidos, no qué tan viejos son.
- **Poda por importancia** (quedarse solo con las variables más
  importantes del ranking de XGBoost): sin patrón limpio, los saltos
  entre distintos tamaños de recorte son ruido de proceso, no señal.

## Disciplina a mantener (heredada del repo padre, no repetirla de cero)

- **Protocolo de 5 semillas siempre**, nunca una sola -- el ruido entre
  semillas es del mismo orden que muchas de las "mejoras" que se buscan.
- **Sigmas Y acierto, nunca solo Brier** -- pueden moverse en direcciones
  distintas (ver tabla de arriba, calidad_plantilla mejoraba Brier en
  algunos mercados pero no siempre el acierto).
- **Toda variable nueva pasa `comprobar_sin_fuga` antes de creerse nada**
  -- shift(1) antes de cualquier rolling, sin excepciones.
- **Revisar colisiones de subcadena** al clasificar columnas por nombre
  (`grupos_rasgo()` en `rasgos.py`) -- el bug de "elo"/"duelos" costó dos
  días de números contaminados. Usar `endswith`/`startswith` con el
  prefijo completo, nunca `"x" in c` suelto.
- **Que algo prediga bien el partido no significa que dé ventaja sobre
  la cuota** -- el mercado también ve la forma reciente, el Elo, etc.
  La pregunta que importa es siempre "¿esto da información que el precio
  no lleve ya dentro?", no "¿esto predice fútbol?".
- **+2 sigmas es el umbral para declarar que algo bate al mercado.** Con
  -0.77s todavía muy lejos. Nada de lo de arriba es un hallazgo, es "la
  mejor base encontrada hasta ahora".

## Qué falta probar (ideas no cerradas, a diferencia de las de arriba)

- Más cobertura de `calidad_plantilla` en jugadores nuevos que aparezcan
  en alineaciones futuras (el backfill del repo padre es reanudable).
- El scouting en vivo (aparcado en el repo padre hasta que vuelva la
  competición) -- sigue siendo la única fuente de datos genuinamente
  nueva no explorada, aplicable aquí igual que a los otros mercados.

## Poisson ataque/defensa: probado, sin efecto (24/09/2026)

La idea de la lista de arriba, ya probada: `lambda_local = (loc_m_goles +
vis_m_goles_contra) / 2`, `lambda_visit` igual al revés, `P(marca) =
1-exp(-lambda)`, `poisson_p_btts = P(marca local) * P(marca visitante)`
(independencia). Correlación con el resultado real de ambos_marcan:
**0.043** -- casi nula antes de meterla en ningún modelo.

Protocolo de 5 semillas, foco en ambos_marcan:

| config | sigmas | acierto |
|---|---|---|
| base+elo | -1.96s | 54.2% |
| base+elo+poisson_btts | -1.87s | 54.7% |
| producción | -0.68s | 59.0% |
| producción+poisson_btts | -0.74s | 59.0% (empate) |

Cambios del tamaño del ruido de proceso en las dos direcciones -- ni
ayuda ni perjudica con claridad. **Razón distinta a por qué fallaron
h2h/tabla/rotación solas:** esta variable está construida ÚNICAMENTE a
partir de columnas que XGBoost ya tenía en bruto (`m_goles`,
`m_goles_contra`, ya en el grupo "base"). No es información nueva, es
una transformación matemática (producto de dos exponenciales) de la
misma información -- y un modelo de árboles ya puede aproximar esa
interacción combinando splits sin que se la demos pre-cocinada. Lo que
sí funcionó en esta sesión (árbitro, calidad_plantilla) siempre traía
una fuente de datos GENUINAMENTE distinta, no una fórmula sobre datos
ya presentes. Lección para la próxima idea: preguntar primero "¿esto
usa un dato que el modelo no tenía ya en alguna forma?" antes de
construirlo -- btts_tasa (más arriba) sí pasaba esa prueba (era una
tasa histórica del evento conjunto, no derivable de m_goles solo) y por
eso al menos mejoraba un poco aislada, aunque tampoco sobrevivió a
combinarse. No entra en el modelo.

## Seis ideas del usuario, probadas una a una (24/09/2026)

Petición explícita: árbitro con ventana, H2H con decaimiento temporal,
goles a favor/en contra de tabla, impacto de jugadores concretos,
local/visitante separado, y momentum de ventana 5. Protocolo de 5
semillas, foco en ambos_marcan (script:
`scripts/experimentos_seis_ideas.py`).

| Variable | Sola vs base+elo (-1.96s) | Sumada/sustituida en producción (-0.68s) |
|---|---|---|
| 1. Árbitro ventana 10 (tarjetas+goles) | -1.47s | -0.74s (empeora) |
| 2. H2H reciente (máx 5, 2 años, doble peso último año) | -1.90s (ruido) | -0.72s (ruido) |
| 3. Tabla: goles a favor/en contra de temporada | -1.96s (sin cambio) | -0.95s (empeora) |
| 4. Impacto de jugador concreto (goles del equipo cuando juega) | -2.34s (empeora) | -1.21s (empeora bastante) |
| 5. Local/visitante separado (goles casa/fuera no mezclados) | -2.20s (empeora, y -149 partidos utilizables) | -1.10s (empeora) |
| 6. Momentum ventana 5 (antes probado con ventana 3) | -2.10s (empeora) | -0.95s (empeora) |
| **7. Árbitro ventana 20** (repetición de la 1 con más ventana) | **-1.33s (la mejor variable individual del día)** | **-0.63s (mejora, pero 0.05 sigmas -- del tamaño del ruido de proceso)** |
| 8. Las 6 juntas (árbitro=ventana20) | -1.58s | -1.37s (empeora bastante) |

**Ninguna sobrevive a combinarse con el resto**, mismo patrón de toda la
sesión. La única con una dirección consistente y creciente es el
**árbitro por ventana**: ventana 20 > ventana 10 > sin ventana (expandiendo
todo el historial), tanto sola como sustituyendo al árbitro actual en
producción. La mejora sustituyendo en producción (-0.68s -> -0.63s) es
del tamaño del ruido ya visto entre corridas idénticas en el repo padre
(0.1-1.2 sigmas) -- dirección correcta, no un hallazgo. **Juntar las 6
a la vez empeora**, igual que "las 8 candidatas juntas" del barrido del
repo padre: demasiadas columnas nuevas saturan ~1700 partidos de
entrenamiento.

Ninguna entra en el modelo. Si se quisiera perseguir esto más, el
candidato es el árbitro por ventana -- probar ventana 15/25/30 para ver
si el patrón sigue mejorando o ya tocó techo en 20.

## Cuota de mercado como variable: imposible con el método estándar, y por qué (24/09/2026)

Petición del usuario: añadir la cuota media de las casas como una
variable más del modelo (no como comparación posterior, como columna de
entrada). Comprobado ANTES de construir nada (mismo principio de
"mide antes de montar el modelo" del repo padre): **las 251 cuotas de
ambos_marcan cosechadas van del 24 de agosto al 20 de septiembre de
2026 -- CERO caen antes del 24 de abril**, que es donde corta el
entrenamiento estándar (75/25 sobre los ~2239 partidos utilizables). El
modelo vería esa columna vacía/constante en el 100% de sus 1679 filas
de entrenamiento -- no hay forma de que aprenda nada de una variable
sin variación en toda la muestra de entrenamiento.

**Experimento aparte, a petición del usuario, con el aviso de muestra
pequeña por delante:** restringido a los 212 partidos que SÍ tienen
cuota de ambos_marcan Y todos los rasgos de producción, con su propio
corte temporal 70/30 dentro de esa ventana (entreno=148, valido=64 --
10-20 veces menos que el resto del proyecto, script:
`scripts/experimentos_cuota_feature.py`):

  produccion (sin cuota)        Brier 0.4842  -0.86s  acierto 59.4%
  produccion + cuota_mercado    Brier 0.4842  -0.86s  acierto 59.4%  (IDÉNTICO)

**Con la regularización estándar (`min_child_weight=20`, calibrada para
~1700 filas), el modelo no pudo usar la columna nueva en absoluto** --
con solo 148 filas de entrenamiento no hay margen para que un split
adicional gane algo, así que ni siquiera se diferenció el árbol.
Repetido con regularización ligera (`min_child_weight=5`, ajustada a
148 filas):

  produccion (sin cuota)        Brier 0.5630  -2.43s  acierto 50.0%
  produccion + cuota_mercado    Brier 0.5593  -2.32s  acierto 53.1%

Aquí SÍ se ve diferencia -- la cuota aporta algo cuando se le deja
sitio. Pero el conjunto entero se hunde frente a la versión con
regularización normal (Brier 0.56 vs 0.48): con solo 148 filas, aflojar
la regularización lo suficiente para aprovechar una columna nueva
también deja que sobreajuste las otras 99. **No hay término medio bueno
con esta cantidad de datos.** Conclusión: la idea en sí tiene mérito
(la cuota SÍ lleva información que el resto de rasgos no capturaba del
todo), pero no hay manera honesta de probarla bien hasta que la cosecha
diaria de cuotas acumule meses que solapen con el periodo de
entrenamiento, no solo con el de validación. Revisar cuando
`data/cuotas_cosechadas.csv` tenga cuotas de antes de abril de 2026.

## Las 42 combinaciones (≥3 variables) de las 6 ideas: ninguna gana, y por qué el barrido crudo mentía (24/09/2026)

Petición del usuario: probar TODAS las combinaciones de tamaño 3 en
adelante de las 6 variables (árbitro ventana 20, h2h reciente, tabla
goles, impacto jugador, localía, momentum5) sumadas a producción --
C(6,3)+C(6,4)+C(6,5)+C(6,6) = 42 combinaciones
(`scripts/experimentos_combinaciones.py`, protocolo de 5 semillas, foco
en ambos_marcan, resultados completos en
`data/combinaciones_seis_variables.csv`).

**El barrido crudo, leído tal cual, parecía dar un ganador:**
`árbitro_v20+h2h_reciente+tabla_goles+localía` salía con -0.667s, mejor
que el -0.68s de la producción estándar. Pero esa lectura estaba mal
planteada, y el propio proceso de comprobarlo es la parte que vale la
pena dejar escrita.

**El error: `localía` reduce la muestra de 2239 a 2090 partidos** (su
`min_periods=3` exige más historial específico de casa/fuera del que
algunos equipos tienen pronto en la temporada). Eso cambia también
DÓNDE cae el corte de validación 75/25, así que el "-0.68s de
producción" contra el que se comparaba no es el número correcto de
referencia -- es el de OTRA muestra. Comparando producción SOLA (sin
ninguna variable nueva) en esa MISMA submuestra de 2090 partidos:

    produccion sola (submuestra de localia, n=2090):  -0.93s   acierto 61.3% vs 59.3% (+2.0pp)
    mejor combo del barrido (mismo n=2090):            -0.667s  acierto 57.7% vs 59.3% (-1.6pp)

**Producción sola gana en acierto con claridad** (61.3% contra 57.7%,
en los mismos partidos exactos) aunque pierda en sigmas -- exactamente
el tipo de contradicción Brier/acierto que este documento y el del repo
padre llevan avisando desde el principio: mirar solo una métrica, o
comparar contra la referencia equivocada, hace parecer ganador a algo
que no lo es. Restringiendo la comparación a las combinaciones que SÍ
usan los mismos 2239 partidos que la producción estándar (las que no
llevan `localía`), la mejor es `árbitro_v20+h2h_reciente+tabla_goles`
con -0.86s -- peor que el -0.68s de producción sola, no mejor.

**Corrección posterior (el usuario, con razón): el acierto era la
métrica equivocada para decidir.** En apuestas manda el Brier/sigma --
se apuesta comparando la probabilidad con la cuota, no eligiendo
ganador. Rehecho con la prueba correcta: Brier emparejado partido a
partido, combo contra producción, mismos 194 partidos de validación
(`scripts/comparar_combo_vs_produccion.py`):

| config | vs producción | vs mercado |
|---|---|---|
| árbitro_v20+h2h_rec+tabla_goles+localía | +0.83s | -0.68s |
| árbitro_v20+h2h_rec+tabla_goles+localía+mom5 | +0.32s | -0.79s |
| árbitro_v20+h2h_rec+localía | +0.18s | -0.84s |
| árbitro_v20+tabla_goles+localía | -0.07s | -0.92s |
| árbitro_v20+tabla_goles+localía+mom5 | -0.24s | -0.99s |
| producción (árbitro original) | -- | -0.88s |

El mejor combo SÍ mejora a producción en sigma (+0.83), pero: (1) lejos
de +2s, no se distingue del azar con 194 partidos; (2) es el mejor de
42, y entre los 5 mejores sale mezclado (3 mejoran, 2 empeoran) --
exactamente lo que se espera si el efecto real es cero y se está viendo
al que tuvo suerte en la selección. **Pista, no hallazgo.** No entra en
producción. Candidato a revisar con más partidos: si el +0.83 sube hacia
+2 al crecer la muestra, es real; si baja hacia 0, era selección (misma
regla que ya enterró la mezcla en el repo padre).

**Y con más muestra se desinfla.** Los 194 partidos eran solo los que
tienen cuota (cosecha desde el 24/08/2026). Pero comparar combo contra
producción NO necesita cuota: los dos modelos predicen todos los
partidos de validación, que son 521. El script ahora hace las dos
comparaciones, cada una con su muestra correcta:

| config | vs producción (194) | vs producción (521) |
|---|---|---|
| árbitro_v20+h2h_rec+tabla_goles+localía | +0.83s | +0.66s |
| árbitro_v20+tabla_goles+localía | -0.07s | +0.20s |
| árbitro_v20+h2h_rec+localía | +0.18s | -0.39s |
| árbitro_v20+h2h_rec+tabla_goles+localía+mom5 | +0.32s | -0.74s |
| árbitro_v20+tabla_goles+localía+mom5 | -0.24s | -1.37s |

El mejor baja de +0.83 a +0.66 al casi triplicar la muestra, y de los 5
solo quedan 2 en positivo. Regla del repo padre: si el número se mueve
hacia cero al crecer la muestra, era falso. Va en esa dirección -- la
pista se debilita. Lección extra: para comparar dos modelos entre sí no
hace falta cuota, así que no hay que limitarse a los partidos con cuota;
eso solo hace falta para comparar contra el mercado.

Lecciones de esta ronda: (1) con variables que reducen la muestra,
comparar siempre en la MISMA submuestra; (2) para decidir entre dos
modelos, comparar los dos modelos entre sí partido a partido (Brier
emparejado), no cada uno por separado contra el mercado; (3) el mejor
de N combinaciones está inflado por selección -- mirar si el patrón se
repite en los siguientes, no solo el primero.

## Todas las comparaciones de ambos_marcan, rehechas sobre la validación completa (24/09/2026)

Petición del usuario: usar la validación completa (no solo los partidos
con cuota) para TODO lo anterior. Brier emparejado modelo contra modelo,
mismos partidos para variante y referencia (`scripts/comparar_todo_vs_referencia.py`,
61 comparaciones, resultados en `data/comparar_todo_vs_referencia.csv`).
n=560 partidos de validación (523 cuando entra localía).

Solas contra base+Elo: árbitro v10 +1.96s, árbitro v20 +1.93s, h2h reciente
+1.28s, tabla goles +0.78s, btts -0.14s, Poisson -0.22s, localía -0.72s,
impacto jugador -1.06s, momentum5 -1.68s.

Contra producción: árbitro v10 sustituyendo al original +0.36s, v20 +0.30s,
h2h reciente sustituyendo a h2h profundo +0.29s; tabla goles, impacto,
localía y momentum5 añadidas, todas negativas (-0.95s a -1.93s). De las 42
combinaciones, solo 3 mejoran a producción (mejor +0.77s), ninguna llega a +2s.

Lectura: el árbitro es la señal más sólida (casi +2s solo contra base+Elo),
pero frente al árbitro original la ventana aporta poco (+0.3). Ninguna
combinación bate a producción con claridad.

**Aviso de contaminación (conversación con el usuario):** todas las pruebas
de la sesión -- 256 combinaciones del repo padre, 42 de aquí, rejilla de
hiperparámetros, 6 ideas -- se midieron contra la MISMA validación (partidos
posteriores al 24/04/2026). Elegir repetidamente "el mejor" según esos
partidos infla su resultado. Además, el conjunto de producción se eligió
por la suma de los 5 mercados: para ambos_marcan mejora mucho sobre
base+Elo (-1.96s -> -0.77s), pero para tarjetas EMPEORA (-1.40s -> -2.77s).
Pendiente: (1) conjunto de variables por mercado, no uno común; (2) juzgar
los candidatos congelados solo con partidos jugados a partir del 24/09/2026,
que ninguna prueba ha tocado.

## Selección propia de ambos_marcan + prueba limpia (24/09/2026)

Los dos arreglos del aviso de contaminación, centrados en ambos_marcan
(`scripts/seleccion_y_prueba_limpia.py`):

**Tres tramos por fecha**, 2085 partidos fijos (todos con todas las
candidatas; clima fuera -- ya cerrada y quitaba 112 partidos):
- entrenamiento: 1155 (sep 2025 - mar 2026)
- selección: 384 (mar - 23 abr 2026) -- en toda la sesión solo se usó
  para entrenar, nunca para evaluar
- prueba final: 546 (24 abr - 20 sep 2026) -- la selección no lo ve; se
  mira una vez al final, reentrenando con entrenamiento+selección

**Selección hacia delante SOLO por el Brier de ambos_marcan** (no por la
suma de 5 mercados), 15 grupos candidatos:
base+Elo -> +calidad_plantilla (+1.57s) -> +árbitro (+1.27s) -> +h2h
(+1.44s) -> nada más baja el Brier. Ninguna de las 6 ideas nuevas
(árbitro ventana, h2h reciente, tabla goles, impacto, localía, momentum5)
ni btts/Poisson/forma reciente/rotación pasa una selección limpia.

**Prueba final** (546 partidos; 194 con cuota para la columna de mercado):

| modelo | elegido vs este | vs mercado |
|---|---|---|
| elegido (base+Elo+calidad+árbitro+h2h) | -- | -0.88s |
| producción del repo padre (5 grupos) | +0.25s (empate) | -0.83s |
| base+Elo | **+3.02s** | -2.03s |

- **+3.02s sobre base+Elo: primer resultado >+2s en prueba limpia de toda
  la sesión.** Las variables añadidas (calidad, árbitro, h2h) mejoran el
  modelo de verdad; no era efecto de reutilizar la misma validación.
- El conjunto propio empata con producción con 3 grupos en vez de 5 -- se
  adopta por simple. `columnas_rasgo_default()` de ESTA carpeta pasa a
  ser base+Elo+calidad_plantilla+árbitro+h2h (87 rasgos). El repo padre no
  cambia (sigue sirviendo a los otros 4 mercados).
- Contra el mercado sigue perdiendo (-0.88s). Mejor modelo, no ventaja.

Contaminación residual: la LISTA de candidatas se construyó el 24/09
mirando resultados posteriores al 24/04; la elección entre ellas sí es
limpia. Para una prueba 100% limpia: juzgar este conjunto congelado solo
con partidos jugados desde el 25/09/2026.

## El cambio de temporada hunde el modelo (24/09/2026)

Observación del usuario: entre temporadas cambian jugadores, entrenadores
y estilo, y hay casi 2 meses de parón (su ejemplo: el Elche de este
inicio no es el del año pasado; Osasuna, con lo mismo, ha vuelto
irregular). Medido con el conjunto propio de ambos_marcan, entrenado con
todo lo anterior al 24/04/2026:

| tramo de prueba | partidos | mejora sobre predecir siempre la media |
|---|---|---|
| final 2025/26 (abr-jun) | 303 | +2.43% |
| inicio 2026/27 (ago-sep) | 261 | **-0.60%** (peor que la media) |

Al arrancar la temporada nueva el modelo pierde toda su ventaja. Dos
consecuencias:

1. **El entrenamiento no tiene NINGÚN cambio de temporada.** El histórico
   empezaba en agosto de 2025 y las medias móviles necesitan 4 partidos
   previos, así que todo lo que el modelo vio es de dentro de una misma
   temporada. Nunca aprendió a desconfiar de la forma del año pasado.
2. **La comparación contra el mercado está sesgada contra el modelo.** Las
   212 cuotas de ambos_marcan son TODAS de ago-sep 2026, el peor tramo del
   modelo, justo cuando el mercado incorpora fichajes y cambios de
   banquillo. El -0.88s contra el mercado es la foto del peor momento, no
   de la temporada. Cuotas de octubre en adelante medirían OTRO momento,
   no solo con más precisión.

Arreglo en marcha: temporadas anteriores (ver siguiente sección) para que
el entrenamiento incluya cambios de temporada reales.

## Temporadas anteriores SÍ existen en la API (24/09/2026)

`sondeo_temporadas_antiguas.md` (repo padre): /matches con season=2024,
2023 y 2022 devuelve temporadas completas (~2.224 partidos por temporada en
las 6 ligas). Profundidad, comprobada con un partido de La Liga por
temporada:

| temporada | /statistics | árbitro | alineaciones |
|---|---|---|---|
| 2024/25 | 39 estadísticas | sí | sí (22) |
| 2023/24 | 30 estadísticas | sí | sí (22) |
| 2022/23 | 29 estadísticas | no | no |

2024/25 y 2023/24 sirven para el modelo actual; triplicarían el
entrenamiento (~2.200 -> ~6.700) y darían dos cambios de temporada reales.
2022/23 no trae árbitro ni alineaciones. Coste estimado: ~15.000 llamadas
(estadísticas + árbitro + alineaciones + jugadores nuevos), 2-3 días de
cuota. Backfill de 2024/25 lanzado el 24/09 con tope 2.000 (reanudable).
Ojo: 2023/24 trae 30 estadísticas en vez de 39 -- comprobar cuáles faltan
antes de fiarse de esa temporada (si falta xG, las medias de xG saldrían
vacías).

## Entrenar con 2024/25: arregla el inicio de temporada (24/09/2026)

Backfill de 2024/25 (run del 24/09, tope 2.000 llamadas): **1.743 partidos**
de las 5 grandes (Premier 380, La Liga 380, Serie A 380, Bundesliga 308,
Ligue 1 295). Segunda salió vacía con UNA sola llamada, y 5 partidos de
Ligue 1 + la última página de Ligue 1 fallaron justo antes: todo al final
de la pasada, a las ~20:50 UTC. Casi seguro la cuota diaria agotada, no un
ID malo (el sondeo vio 468 partidos de Segunda 2024 con ese ID). Relanzar.

**Ojo, 2024/25 NO trae las 39 estadísticas.** El sondeo miró un partido de
la última jornada (mayo 2025) y eso engañó: xG solo está en el 5% de los
partidos (empieza a aparecer en marzo de 2025), centros en el 18%. Goles,
córners, faltas, amarillas, posesión, tiros y pases, al 92-100%. Tampoco
tiene aún árbitro, alineaciones ni h2h profundo. XGBoost acepta huecos, así
que las filas entran igual con lo que tienen.

`scripts/experimento_temporada_extra.py`: mismos rasgos, mismos 567
partidos de prueba (posteriores al 24/04/2026); solo cambia el
entrenamiento. A = como hasta ahora (1.703 filas de 2025/26). B = A + 1.743
filas de 2024/25. 5 semillas, Brier emparejado.

| tramo de prueba | n | base+Elo: B vs A | conjunto propio: B vs A |
|---|---|---|---|
| final 2025/26 | 303 | -0.04s | -0.65s |
| **inicio 2026/27** | 264 | **+2.67s** | **+2.79s** |
| todo | 567 | +1.86s | +1.35s |

Contra predecir la media en el inicio de 2026/27, el conjunto propio pasa
de +1.33% a +4.73%. **Era lo que decía el usuario:** el modelo nunca había
visto un cambio de temporada, y con una temporada más aprende a arrancar.
Es una hipótesis escrita ANTES de mirar (sección anterior), y la mejora
cae justo donde se predijo, no en otro sitio.

**Contra el mercado (215 partidos con cuota, todos de ago-sep 2026):**

| modelo | A | B |
|---|---|---|
| base+Elo | -1.07s | +0.56s |
| conjunto propio | -0.41s | **+1.11s** |

Primera vez que ambos_marcan sale POSITIVO contra el mercado. **No es un
hallazgo todavía:**
- +1.11s está lejos de +2s; el bootstrap da peor que el mercado en el 14%
  de remuestreos.
- Quitando los 10 partidos que más aportan cae a -0.30s (sin 5: +0.38s).
- Son 215 partidos de un mes. Misma regla de siempre: si crece hacia +2s
  con más cuotas, es real; si baja hacia 0, no.

Pendiente, por orden: (1) relanzar backfill (Segunda 2024 + resto de
2023/24); (2) árbitro, alineaciones y jugadores de 2024/25 para que esas
filas tengan también calidad_plantilla y árbitro; (3) repetir esta prueba
con todo eso y vigilar el +1.11s contra el mercado según entren cuotas.

### Repetido con 2024/25 COMPLETA (25/09/2026, madrugada)

Backfills del 25/09: 2024/25 entera (2.223 partidos, Segunda incluida) con
árbitro, alineaciones y jugadores nuevos (854). De 2023/24 hay 932 partidos
(La Liga, Premier, Serie A a medias) y casi sin árbitro ni alineaciones;
el resto de 2023/24 y el h2h profundo de pares nuevos quedan para otro día.
Tres entrenamientos, mismos 572 partidos de prueba:
A = 2025/26 (1.722), B = +2024/25 (3.945), C = B + 2023/24 parcial (4.877).

Conjunto propio (base+Elo+calidad+árbitro+h2h):

| tramo | B vs A | C vs A | A/media | B/media | C/media |
|---|---|---|---|---|---|
| final 2025/26 (303) | -0.66s | +0.00s | +3.51% | +2.70% | +3.51% |
| **inicio 2026/27 (269)** | **+3.53s** | +2.66s | -0.66% | **+4.06%** | +3.15% |
| todo (572) | **+1.97s** | +1.87s | +1.54% | +3.34% | +3.34% |

**Confirmado y más fuerte:** con 2024/25 completa el arranque de temporada
pasa de -0.66% (peor que la media) a +4.06%, a +3.53 sigmas. base+Elo da lo
mismo (+3.46s). Lo que decía el usuario del cambio de temporada era cierto,
y más temporadas lo arreglan.

**Contra el mercado (219 partidos con cuota): la pista se desinfla.**

| modelo | A | B | C |
|---|---|---|---|
| base+Elo | -1.53s | -0.07s | +0.01s |
| conjunto propio | -1.08s | **+0.42s** | +0.15s |

El +1.11s de la versión con 2024/25 a medias baja a +0.42s con 2024/25
completa (bootstrap: peor que el mercado en el 34%; sin sus 3 mejores
partidos, -0.04s). Regla de este proyecto: si al mejorar los datos el
número va hacia cero, no era real. El modelo ya EMPATA con el mercado
(antes perdía por -1 a -2 sigmas) pero no le gana. Mejor modelo, no
ventaja.

C (añadir 2023/24 a medias) no mejora a B en conjunto (-0.00s). Juzgar
2023/24 solo cuando esté completa y con árbitro/alineaciones.

## Cuota como variable, con football-data (25/09/2026)

Detalle en el CLAUDE.md del repo padre ("Cuotas históricas de
football-data.co.uk"). Para ambos_marcan: football-data NO trae ambos marcan;
se usa un ambos marcan implícito (Poisson sobre 1X2 + más/menos 2.5, 0.73
de correlación con el real) más el 1X2 y el más/menos 2.5 como variables.
Con el modelo general: +2.14s sobre el modelo sin precio (568 partidos) y
**+0.87s contra el mercado cosechado** (219 partidos). Pista, no hallazgo:
lejos de +2s, y el precio cosechado es más blando que un cierre de Pinnacle.

## Salida del modelo de más de 2.5 como variable (25/09/2026)

Idea del usuario: apilar. `scripts/apilar_mas25_en_ambos.py` (repo padre):
la probabilidad del mejor modelo de más de 2.5 (producción + precio) entra
como variable en el mejor de ambos marcan (producción + precio). En
entrenamiento, predicción fuera de muestra por 5 bloques de fecha (si no,
la variable "sabe" el resultado y el apilado sale inflado). Comprobado sin
fuga: Brier de la variable 0.4824 en entrenamiento y 0.4717 en validación
(no es menor en entrenamiento).

- Con la variable vs sin ella: **+0.52s** (568 partidos). Del tamaño del ruido.
- Contra el mercado cosechado (219): +0.87s -> **+0.98s** (bootstrap: peor
  que el mercado en el 16%, antes 19%).

Mejora poco y dentro del ruido: la salida del modelo de 2.5 sale de los
mismos datos que ya ve el de ambos marcan (mismo patrón que Poisson). No se
declara nada; si con más cuotas el +0.98 sube hacia +2, se revisa.

## Córners en el modelo de ambos marcan (25/09/2026)

`scripts/corners_en_ambos.py` (repo padre), sobre el mejor modelo (producción
+ precio, 106 rasgos). Los 6 de córners (media de los últimos 8 partidos, a
favor y en contra, loc/vis/dif):
- Importancia: 5.3% de la ganancia entre los 6 (su peso "justo" por número
  sería 5.7%). Puestos 28 a 91 de 106. Ni destacan ni sobran.
- Quitarlos: -0.43s (algo peor, dentro del ruido). Se quedan.
- Apilar la salida del modelo de más de 9.5 córners (fuera de muestra, sin
  fuga: Brier 0.4971 entreno / 0.4866 validación): -0.95s en los 568
  partidos, +0.99s contra el mercado (antes +0.87s) en los 219. Señales
  opuestas y pequeñas: ruido. No entra.
Lo que más pesa en ambos marcan es el precio (ambos marcan implícito, más
de 2.5, lambda local), los puntos del visitante y los puntos por partido
en la tabla.

## Poda de la base (25/09/2026)

`scripts/podar_base_ambos.py` (repo padre): eliminación hacia atrás por
medida entera (sus 3 columnas loc/vis/dif), decidida en el último 25% del
entrenamiento (1.266 partidos, nov 2025-abr 2026) y probada UNA vez en los
568 de validación. Salen 3 de 24 medidas: tiros fuera propios (+1.85s en
selección), días de descanso (+1.14s) y centros del rival (+0.57s). A partir
de ahí, quitar cualquier otra empeora: las otras 21 aportan.

Prueba final: podado (97) vs completo (106) **-0.14s** (empate). Contra el
mercado (219): +0.87s -> +1.11s. En la muestra grande no mejora; la subida
contra el mercado sale de 219 partidos y es del tamaño del ruido. Resultado:
la base ya estaba casi limpia; podar no compra nada claro. Se mantiene el de
106 (no se cambia el modelo por una diferencia que no se distingue de cero).

## Poda de TODOS los grupos (25/09/2026)

Mismo script con `ALCANCE=todo`: 38 unidades (24 medidas de la base; Elo,
h2h, h2h profundo y árbitro como bloque; tabla y calidad por medida; el
precio en 4 piezas). En selección salen 6: tiros fuera, descanso, posición
en la tabla, ambos marcan implícito, árbitro y h2h profundo (cada paso
+0.8 a +1.9s en selección).

**Prueba final: podado (91) vs completo (106) -1.20s -- PEOR.** Contra el
mercado (219) +0.87s -> +1.05s, pero en los 568 partidos pierde. Lo que la
selección daba por sobrante (árbitro, ambos marcan implícito...) sí aportaba
fuera de ese tramo: podar a partir de un solo tramo de 1.266 partidos
sobreajusta a ese tramo. Con la base sola (arriba) al menos empataba. Se
mantiene el modelo de 106. No repetir poda por eliminación hacia atrás
salvo con bastante más muestra.

Nota de procesos: esperar con `until ! pgrep -f script.py` no termina nunca,
porque el propio bucle lleva "script.py" en su línea de comando y pgrep lo
encuentra. Esperar por PID (`kill -0 PID`), no por nombre.

## Configuración oficial de ambos marcan (26/09/2026)

Tras la prueba mes a mes (`scripts/walk_forward_ambos.py`, repo padre), la
que mejor funcionó es el brazo "reentreno" y queda fijada en
`scripts/modelo_ambos_marcan.py` (repo padre):
- producción (99) + 7 rasgos del precio PREVIO de Pinnacle/Betfair = 106
- reentrenado cada mes con todo lo anterior, entrenamiento con huecos
- sin selección automática de variables ni recalibración (el adaptativo
  perdió dinero: -12% contra +6.2% del reentreno)
Todo lo nuevo (xG/xA por jugador incluido) se compara contra esto.

## PUNTO DE RETORNO (26/09/2026, ~15:00 UTC) -- leer al volver de un paréntesis

El usuario abrió un tema aparte, SIN relación con ambos marcan. Cuando diga
"ya está", "es lo que quería" o similar, ese tema se cierra y se vuelve AQUÍ,
al único tema abierto antes: ambos marcan. No mezclar nada del paréntesis.

Estado exacto al abrir el paréntesis:
- Modelo oficial: `scripts/modelo_ambos_marcan.py` (producción 99 + precio
  previo 7 = 106 variables, reentreno mensual, sin selección ni recalibración).
- Resultado vigente: mes a mes (walk_forward_ambos.py) reentreno +2.79s sobre
  el congelado; apostando ago-sep 2026: +6.2% (mediana de casas) / +9.9%
  (bet365), no aguanta sin los 5 mejores partidos. Pista débil, no hallazgo.
- En marcha: 27/09 02:31 UTC se lanza backfill_xg_jugador.yml (xG/xA y 35
  estadísticas por jugador desde abr-2025, ~3.036 partidos). Después: prueba
  mes a mes CONTRA el modelo oficial añadiendo xG/xA por jugador (solo
  partidos anteriores, anti-fuga), y avisar al usuario del resultado.
- Pendiente de decidir con el usuario: apuestas en papel (sin dinero) sobre
  partidos futuros, con la regla fijada de antemano.

**Paréntesis CERRADO (26/09/2026, ~19:00 UTC).** El tema aparte (pronósticos
de selecciones, Nations League) vive entero en `modelos/selecciones/` con su
propio CLAUDE.md. No se mezcla con ambos marcan: no comparte modelo ni
variables. El usuario puede pedir más pronósticos de selecciones en las
próximas 3 semanas; eso se atiende desde esa carpeta y se vuelve aquí al
terminar. El tema activo vuelve a ser ambos marcan, en el estado de arriba.
