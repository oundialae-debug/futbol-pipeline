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

## DÓNDE ESTAMOS (26/09/2026, 20:05 UTC) -- leer al retomar ambos marcan

El paréntesis de selecciones está cerrado y vive aparte (`modelos/selecciones/`,
con su propio chat). No mezclar nada de allí aquí.

**Modelo oficial:** `scripts/modelo_ambos_marcan.py`.
- Producción (99 variables) + 7 de precio de la PREVIA de football-data
  (Pinnacle/Betfair días antes; nunca el cierre).
- Entrenamiento con huecos y reentreno mensual.
- Sin selección de variables ni recalibración: el adaptativo perdió
  apostando (-12%).

**Números vigentes:**

| prueba | resultado |
|---|---|
| Brier contra lo cosechado (cuota_como_variable.py) | +1.32s |
| Mes a mes, reentreno vs congelado (walk_forward_ambos.py) | +2.79s |
| Apuestas ago-sep 2026, regla VE>0, mediana de casas | +6.2% |
| Apuestas ago-sep 2026, regla VE>0, bet365 | +9.9% |

Las apuestas no aguantan sin los 5 mejores partidos: es una pista débil,
no un hallazgo.

**La API se quedó sin cuota el 26/09 a las 20:00 UTC.** Nada que llame a
la API antes del 27/09 a las 12:00 UTC (lo pidió el usuario: 16 horas).

**Programado:**
1. **27/09 12:30 UTC**, rutina `trig_012f6QzxhvKG21hszTPMVPr7`: lanza
   `backfill_xg_jugador.yml` (tope 3100; ya hay 330 partidos del
   31/05-20/09/2026).
   - Revisión a los ~45 min.
   - Después, prueba mes a mes de xG/xA por jugador (solo partidos
     anteriores, anti-fuga) CONTRA el modelo oficial, y avisar al usuario.
2. **Diaria 23:40 UTC**, `trig_01EMBFJxcUiL1bgg1rAJxwKi`: cosecha y
   vigilancia. Ya sabe que no debe llamar a la API antes del 27/09
   12:00 UTC.

**Pendiente de decidir con el usuario:** apuestas en papel (sin dinero)
sobre partidos jugados desde el 27/09, con la regla fijada de antemano.
Es el único juez limpio que queda: todo lo anterior está contaminado por
haber elegido variables mirando esos partidos.

**ACTUALIZACIÓN 26/09 20:10 UTC: AMBOS MARCAN EN PAUSA** (lo pide el usuario).
No se descarga nada para ambos marcan mientras dura la Nations League
(~3 semanas sin partidos de liga).
- Desactivadas (no borradas) las rutinas `trig_012f6QzxhvKG21hszTPMVPr7`
  (backfill de xG por jugador) y `trig_01EMBFJxcUiL1bgg1rAJxwKi` (vigilancia
  diaria).
- Quitado el cron de `cosechar_cuotas.yml`.

Para retomar: reactivar las dos rutinas, descomentar el schedule y seguir
el plan de arriba. Las cuotas de los partidos del 19-20/09 se pueden
cosechar hasta ~18/10.

## Registro en papel (desde el 27/09/2026): todo lo nuevo aprende

Petición del usuario: "todo lo que se haga a partir de ahora tiene que ir
aprendiendo". Pronósticos bajo demanda de una liga concreta (con el resto
de ambos marcan en pausa) con `scripts/ambos_marcan_hoy.py`:

1. **`ambos_marcan_hoy.yml`** (GitHub Actions, input `liga_id`; 120775 es
   la Segunda): baja los partidos de hoy de `data/calendario.csv` con
   árbitro, once y cuotas. Son 3 llamadas por partido. Antes conviene
   poner al día los resultados de esa liga con `backfill_historico`
   (temporadas 2026, tope bajo), `backfill_arbitro_clima` y
   `backfill_lineups`.
2. **`python3 scripts/ambos_marcan_hoy.py pronosticar`** (local):
   - Primero evalúa lo ya jugado.
   - Entrena con TODO lo jugado hasta hoy (el modelo aprende con cada
     resultado nuevo).
   - Pronostica ambos marcan, más de 2.5 y 1X2.
   - Apunta cada partido ANTES del pitido en
     `data/ambos_marcan/registro_papel.csv`, con la apuesta de ambos marcan
     si el valor esperado es positivo contra la cuota mediana.
3. **`python3 scripts/ambos_marcan_hoy.py evaluar`**: cruza el registro con
   `historico_partidos.csv` y escribe
   `modelos/ambos_marcan/registro_papel.md` (acierto, Brier y beneficio,
   modelo contra mercado).

**Regla:** no se cambia NADA del modelo por lo que salga en el registro
hasta tener 100 o más apuestas. Es el único juez limpio; tocarlo por dos
resultados lo contamina.

**27/09, primeros 3 partidos (Segunda):** Eibar 3-2 Las Palmas (sí,
acertado, sin apuesta) y Burgos 1-0 Eldense (sí a 1.93, apostado,
perdido). Oviedo-Sporting quedó pendiente.

Los valores de 1X2 y más de 2.5 de esos 3 están redondeados a %: el
registro se creó después del pronóstico, con los números que se dieron al
usuario a las 15:39 UTC, antes de los saques.

## xG/xA por jugador de los titulares (28/09/2026): pista pequeña, no entra

Backfill completo: `data/historico_xg_jugador.csv`, con 130.685 filas de
3.046 partidos (abril de 2025 en adelante; antes la API no da xG por
jugador). Un xG vacío es casi siempre "no tiró": el 88,5% de los vacíos
tienen 0 tiros. El 7,7% de los que sí tiraron vienen sin xG (huecos de
cobertura). Se tratan como 0.

**Prueba:** `scripts/experimento_xg_jugador.py`.
- Para cada titular, su xG y su xA por 90 minutos en sus 10 apariciones
  anteriores, encogido hacia la media de su posición con 270 minutos.
- Rasgos por equipo: la suma del once (`xi_xg90`, `xi_xa90`) y cuántos
  titulares tienen dato. Todos con `loc_`/`vis_`/`dif_`.
- Se compara mes a mes contra el modelo oficial (`predecir_mes`, 5
  semillas), en los 14 meses con datos: 3.026 partidos.

| | resultado |
|---|---|
| Oficial + xG de titulares contra oficial | **+0.88s** |
| Brier | 0.2481 -> 0.2477 |
| Meses que mejoran | 10 de 14 (los que empeoran: 03/2026 y 05/2026) |

Mejora pequeña y bastante constante, pero lejos de +2s. **No entra en el
modelo oficial.** Queda como pista: vuelve a medirse cuando haya más meses
(el backfill es reanudable y añade los partidos nuevos). Si al crecer la
muestra se va hacia cero, era ruido.

No probar variantes (ventana, encogimiento, solo xA...) sobre estos mismos
partidos hasta que la muestra crezca: sería buscar el número bueno a base de
intentos.

**Revisión del 28/09 (el usuario no se creía el +0.88s): sin fallo que esconda un efecto grande.**

Comprobado:
- **IDs de equipo:** el 100% de los del box-score están en el histórico.
- **Cobertura:** el 100% de los partidos desde abril de 2025 tiene el rasgo.
- **Valores:** plausibles, 1.27 de xG por 90 sumando el once.

Lo único mal era la definición de titular. El box-score marca a veces más
de 11 "no suplentes" (hasta 25 en un partido). Ahora se usa el once
CONFIRMADO de `/lineups` y, solo si falta, el box-score. Resultado:
**+0.89s** (antes +0.88s): el fallo no movía nada.

Variante pedida por la revisión: entrenar los dos brazos solo con partidos
que tienen xG por jugador (2/3 del entrenamiento viejo no lo tiene y podría
diluir los rasgos). Resultado: **-0.83s**. Con menos partidos de
entrenamiento los rasgos nuevos sobreajustan: el mismo patrón de siempre en
este proyecto.

**Por qué aporta tan poco:** el xG del once se parece mucho (correlación
0.75) al xG medio del equipo, que el modelo YA tiene (`m_expected_goals`).
Correlación con los goles: 0.257 el del once, 0.274 el del equipo. Quién
sale de titular cambia poco la media en la mayoría de partidos, y el
precio previo ya recoge las bajas importantes conocidas días antes.

Veredicto sin cambios: pista pequeña (+0.9s), no entra. Volver a medir con
más meses.

**Segunda vuelta (28/09, pregunta del usuario: ¿y si el problema era CÓMO se le dio la variable?).**
`scripts/experimento_xg_jugador_v2.py`: tres formas fijadas ANTES de
ejecutar, misma prueba mes a mes contra el oficial (14 meses, ~3.000
partidos). Con 3 intentos, el listón honesto es ~+2.4s.

| forma | vs oficial | meses que mejoran |
|---|---|---|
| A: desviación (xG del once de hoy menos el de sus 5 partidos anteriores, que mide bajas y rotaciones) | -0.43s | 8/14 |
| **B: portero titular** (goles evitados por 90 en sus 10 partidos anteriores) | **+1.25s** | **10/14** |
| C: probabilidad combinada ya cruzada ((1-e^-λl)(1-e^-λv) con el xG del once contra el xG que concede el rival) | +0.10s | 7/14 |

C sola predice casi como el precio: correlación con ambos marcan 0.098,
frente a 0.119 del ambos marcan implícito del precio. Pero se parece al
precio en un 0.51 y no añade encima de él.

B es la mejor forma encontrada, y tiene sentido: el portero es la parte
defensiva que la primera versión no tenía. Aun así no llega al listón.

**Ninguna entra.** Quedan como pistas para volver a medir con más meses
**sin cambiarlas**: xG del once (+0.89s) y portero (+1.25s).

## MODELO OFICIAL desde el 28/09/2026: + portero titular

Decisión del usuario: "lo que mejor haya funcionado será el mejor modelo a
partir de ahora". `scripts/modelo_ambos_marcan.py` pasa a tener:
- producción (99 variables);
- **portero titular** (`scripts/portero.py`: `loc_gk_gp90`, `vis_gk_gp90`,
  goles evitados por 90 en sus 10 partidos anteriores);
- precio previo (7 variables).

Son **108 variables**, con reentreno mensual y entrenamiento con huecos (el
portero solo existe desde abril de 2025).

- **En `ambos_marcan_hoy.py`** se usa el portero del once confirmado si la
  API ya lo tiene. Si no, el último portero titular del equipo.
- **Aviso honesto (lo que se sabía al adoptarlo):** +1.25s sobre el
  oficial anterior y 10 de 14 meses mejor, pero por debajo del listón de
  ~+2.4s que tocaba con 3 intentos. Se vigila en el registro en papel y al
  crecer la muestra. Si se va hacia cero, se vuelve a la versión sin
  portero.
- **Primer uso:** Leganés-Castellón (28/09), ambos marcan sí 54.8% (antes
  55.2%). Portero del Leganés -0.16 goles evitados por 90, del Castellón
  +0.09.


## MODELO OFICIAL desde el 28/09/2026 (tarde): + 2022/23, - xG del equipo

La temporada 2022/23 se descargó con cuota sobrante del día: 2.295 partidos
de las 6 ligas, con estadísticas y cuotas de football-data. No trae árbitro,
alineaciones ni xG.

Prueba en `scripts/experimento_temporada_2022.py`: mes a mes de sep-2024 a
sep-2026, 4.600 partidos, contra el oficial de ese momento (108 variables).

| cambio | sigmas | meses mejor |
|---|---|---|
| + 2022/23, mismas 108 variables | +1.89s | 12/21 |
| - xG medio del equipo (6 columnas), sin 2022/23 | +1.39s | -- |
| **+ 2022/23 y - xG del equipo (102 variables)** | **+2.55s** | **13/21** |

**Fallo silencioso de la primera pasada:** `rasgos.py` descarta una medida
con menos del 30% de cobertura (`COBERTURA_MINIMA`). Con 2022/23 el xG del
equipo baja al 29% y desaparecía solo del brazo nuevo, sin avisar. El +2.55s
salió así, por accidente. Se repitió con las mismas variables en los dos
brazos y un control sin xG.

- **Decisión, por la regla del usuario ("lo que mejor haya funcionado"):**
  2022/23 dentro y xG del equipo fuera, de forma EXPLÍCITA
  (`modelo_ambos_marcan.columnas()`), no por el umbral.
- **Por qué puede sobrar el xG del equipo:** solo existe desde 2025 (vacío
  en la mayoría de filas de entrenamiento) y el precio previo ya lo lleva
  dentro. El xG por jugador (portero) sigue.
- **Aviso honesto:** se miraron tres configuraciones, así que el listón es
  ~+2.4s. Esta lo pasa por poco. Y en los dos últimos meses (ago y sep de
  2026, el arranque de temporada) sale un poco PEOR que el oficial anterior
  (-0.26 y -0.10 puntos de Brier). Vigilar en el registro en papel.
- **Solo ambos marcan.** El resto de modelos sigue desde 2023/24
  (`modelo_xgboost.TEMPORADA_MINIMA = 2023`), sin probar con 2022/23. En
  `ambos_marcan_hoy.py`, 1X2 y más/menos 2.5 siguen con sus 99 variables y
  filas desde 2023/24.
- **Ojo:** `backfill_arbitro_clima.py` intentaría rellenar 2022/23, y la API
  no tiene árbitro de esa temporada. No lanzarlo sobre 2022.

**Arranque de 2026/27, nuevo contra anterior** (pregunta del usuario):
- **Datos:** 326 partidos de ago-sep 2026. Brier 0.2464 del nuevo contra
  0.2443 del anterior (-1.29s en contra del nuevo). Acierto 56.4% contra
  57.4%.
- **Tasa base:** en agosto ninguno de los dos bate a la tasa base del mes.
- **Decisión del usuario:** se queda el nuevo. La prueba larga es de 4.600
  partidos y dos temporadas; esta es de 326.
- **Vigilar:** si el arranque sigue peor cuando haya más jornadas de
  2026/27, reconsiderar.

## Edad media y valor de mercado del once (29/09/2026): no entran

Petición del usuario, con la edad como prioritaria.
- **Datos:** `/players/{id}` para los 4.558 jugadores de las alineaciones, una
  sola pasada (`backfill_perfil_jugador.py`). Se guardó todo lo que sirve:
  `data/jugador_perfil.csv` (nacimiento, altura, pie, posición),
  `data/jugador_valor_mercado.csv` (84.780 valoraciones CON fecha, desde
  2004) y `data/jugador_lesiones.csv` (historial de lesiones, sin usar aún).
- **Fallo silencioso pillado antes de usar nada:** la especificación da las
  fechas como "Feb 2, 1989" y la API real como "16/12/1986". Con el formato
  de la especificación se leían 0 fechas y no había ningún error. Arreglado y
  reprocesado sin volver a llamar a la API: 4.057 de 4.067 fechas leídas.
- **Portero:** el primer id del once es el portero (9.453 de 9.453 con perfil).

Prueba fijada antes (`scripts/experimento_edad_valor.py`): mes a mes contra el
oficial de 102 variables, 24 meses (abr-2024 a sep-2026). Cobertura 52% de
los partidos, porque solo hay alineaciones desde abril de 2024.

| variante | sigmas | meses mejor | arranque 2026/27 (327 partidos) |
|---|---|---|---|
| A edad media de los 10 de campo | -0.20s | 11/24 | -0.11 pts |
| B valor medio del once (última valoración antes del partido) | +0.31s | 10/24 | +0.04 pts |
| C las dos | +0.69s | 14/24 | -0.09 pts |

Ninguna llega al listón (+2s para A; ~+2.4s para B y C). El modelo oficial
no cambia. Lectura probable: la calidad de plantilla, el Elo y el precio
previo ya llevan lo que dicen la edad y el valor. No reabrir estas dos
variables con los mismos partidos. Las lesiones quedan descargadas por si
se prueban "bajas importantes" más adelante.

## Bajas por lesión (29/09/2026): no entran, empeoran

Petición del usuario. Un lesionado no sale en el once, y el once real ya lo
ve el modelo, así que se midió QUIÉN FALTA: titulares habituales (titular en
3 de sus 5 onces anteriores) de baja el día del partido. La lesión tiene que
haber empezado ANTES de ese día. `scripts/experimento_lesiones.py`, fijado
antes de mirar; datos de `data/jugador_lesiones.csv`.

- **Comprobación con un caso real:** Real Madrid-Getafe, 01/12/2024: 4
  habituales de baja por valor de 460 M, que coincide con la plaga de
  lesiones del Madrid de esas fechas.
- **Qué mide:** media de 0,53 bajas por equipo y partido; el 39% de los
  equipos tiene al menos una.

| variante | sigmas | meses mejor | arranque 2026/27 |
|---|---|---|---|
| A bajas de habituales (número) | -1.53s | 10/23 | +0.03 pts |
| B valor de esas bajas (M€) | -1.80s | 10/23 | +0.01 pts |

Las dos empeoran. Lectura: el once real (calidad de plantilla, portero) y el
precio previo ya recogen las bajas. No reabrir las lesiones como variable
con estos datos.

## Recalibración (29/09/2026): el fallo es real, el arreglo no llega al listón

**Hallazgo:** en 4.601 partidos (sep-2024 a sep-2026), el modelo oficial es
honesto hasta el 65%. Cuando da 65-70% pasa el 60%, y cuando da 70% o más, el
56%. Exagera justo los partidos "claros". Por eso la idea de "apostar solo
en los de probabilidad alta" pierde: con cuotas reales, las reglas de
prob >= 55-65% salen entre -1% y -18% (solo una en positivo, 24 apuestas,
+0.29s).

**Prueba** (`scripts/recalibrar_ambos.py`, fijada antes): cada mes, un
calibrador ajustado solo con las predicciones de los meses anteriores (al
menos 6 meses detrás). 3.247 partidos, mar-2025 a sep-2026.

| forma | vs sin recalibrar | meses mejor | vs mercado (262 con cuota) |
|---|---|---|---|
| sin recalibrar | -- | -- | -0.44s |
| A Platt | +1.20s | 8/15 | -0.98s |
| B isotónica | +0.90s | 9/15 | -0.39s |

- **Calibración:** Platt quita la zona inflada (casi nada pasa ya del 65%).
- **Por qué no llega al listón:** pocos partidos caen en esa zona (unos 300
  de 3.247), así que el Brier casi no se mueve. Ninguna llega a ~+2.2s, ni
  mejora frente al mercado.
- **Decisión:** el modelo oficial NO se cambia.
- **Regla práctica:** un "ambos marcan sí/no" del modelo por encima del 65%
  hay que leerlo como ~60%.
- **Isotónica, ojo:** da algún 100% absurdo en los extremos (2 partidos). Si
  algún día se usa, recortarla.

## Titulares de 2023/24 (29/09/2026): datos buenos, el modelo casi no cambia

El otro chat sacó de /box-score los onces de ago-2023 a mar-2024: 1.734
partidos, 11 titulares por equipo, portero primero. Se descargaron los 385
jugadores nuevos (perfil y estadísticas, unas 770 llamadas). Cobertura de
onces: del 52% al ~70% de los partidos. Siguen sin once los 184 partidos de
abr-jun 2024 (ni /lineups ni el backfill del otro chat) y toda 2022/23.

`scripts/experimento_titulares_2324.py`, fijado antes, mes a mes sep-2024 a
sep-2026:

| prueba | sigmas | meses mejor |
|---|---|---|
| 1. oficial CON onces 23/24 vs SIN | +0.31s | 10/21 |
| 2a. + edad media (ahora 69% cobertura) | +0.30s | 12/21 |
| 2b. + valor medio | -0.22s | 10/21 |
| 2c. + bajas por lesión (71% cobertura) | -0.61s | 10/21 |

Nada llega al listón. Los onces se quedan en el histórico: son datos
correctos y el modelo oficial ya los lee solo. Edad, valor y bajas siguen
fuera, ahora probadas también con más cobertura: no reabrir.

**Depuración: calidad de plantilla sin once vale 0, no hueco.** Parecía un
fallo (un partido sin once llega como "equipo de calidad 0"; el 27% de los
partidos). Probado ponerlo vacío (`scripts/experimento_calidad_vacia.py`):
**-1.92s, peor**. Con el 0 y "titulares conocidos = 0", el árbol ya sabe
separar "no hay once" de "equipo malo". Se queda como está. Ojo al medir
cobertura de esta variable: `notna()` da 100% siempre; hay que mirar
`calidad_conocidos > 0`.

## Ajuste interno (29/09/2026): árboles de un nivel (NO CONFIRMADO, ver revisión abajo)

`scripts/afinar_ambos.py`. Selección en sep-2024..ago-2025 (2 semillas),
confirmación en sep-2025..sep-2026 (5 semillas, meses que la selección no vio).

- **Ronda 1** (12 combinaciones: profundidad 2/3/4, hoja 5/20, lambda 1/5):
  gana la actual (profundidad 2, hoja 20, lambda 5). Cuanto más complejo,
  peor, sin excepción.
- **Ronda 2** (la actual estaba en el borde; más simple: profundidad 1/2,
  hoja 20/50, lambda 5/20): gana profundidad 1, hoja 20, lambda 5.
- **Confirmación:** +1.54s sobre la actual en 2.387 partidos no vistos,
  mejor en 9 de 11 meses.
- **Contra el mercado (262 partidos con cuota):** igual (-0.26s frente a
  -0.11s de la actual). Apostando con VE>0 en esos 262: -5.4% frente a
  +1.9%; con tan pocas apuestas es ruido.

**Decisión, por la regla del usuario ("lo que mejor funcione"):** entra.
- Por debajo de +2s, pero es la prueba más limpia hecha hasta ahora (selección
  y confirmación separadas) y el modelo es más simple.
- **Qué cambia:** `modelo_ambos_marcan.PARAMS` y `entrenar()`, usados por
  `predecir_mes` y por `ambos_marcan_hoy.py` SOLO para ambos marcan. 1X2 y
  más/menos 2.5 siguen con `modelo_xgboost.entrenar` (profundidad 2).
- **Lectura:** con árboles de un nivel no hay interacciones entre variables;
  cada una suma por su cuenta. Con estos datos, las interacciones eran ruido.
- **Vigilar:** si en el registro en papel o con más meses el efecto se va a
  cero, se vuelve a profundidad 2.

## Revisión de 1 contra 2 niveles (29/09/2026): no se confirma, vuelve a 2

Petición del usuario: "que salga mejor pero apostando no me gusta".
`scripts/revision_profundidad.py`, fijado antes, 21 meses (4.601 partidos),
dos juegos de semillas.

| prueba | 1 nivel frente a 2 |
|---|---|
| semillas 0-4 / 10-14 / las 10 | +2.55s / +3.17s / +2.86s, 16 de 21 meses |
| ruido de semillas | la mejora (0.106 pts de Brier) es 4 veces el ruido (0.027) |
| por liga | Bundesliga +2.50, Ligue 1 +2.50, Premier +2.30, Serie A +0.94, Segunda +0.33, **LaLiga -1.17** |
| por temporada | 2024/25 +2.06, 2025/26 +2.02, **2026/27 +0.22** |
| contra el mercado (262 con cuota) | -0.29s (2 niveles: -0.10s) |
| apostando VE>0 | **-6.6%** en 84 apuestas (2 niveles: +5.5% en 113); 1 nivel peor en el 95% de los remuestreos |

- **Lectura:** en probabilidad media, 1 nivel es algo mejor y no es ruido.
  Pero en esta temporada no mejora, empeora en LaLiga, y apuesta peor en la
  única prueba con cuotas reales. Sin interacciones pierde los matices por
  liga, justo donde se separa del mercado.
- **Decisión:** vuelve a 2 niveles. `modelo_ambos_marcan.PARAMS` queda igual
  que `modelo_xgboost.entrenar`.
- **Pendiente:** repetir cuando haya más meses de 2026/27 con cuota real.
- **Lección para el resto de pruebas:** dos juegos de semillas del MISMO
  modelo dan +2.12s entre sí. El sigma emparejado mide "mejor en estos
  partidos", no el azar del entrenamiento. Un +2s suelto puede ser en parte
  ruido de semillas: repetir con otras semillas antes de creérselo.

## ¿Debe pesar más la liga? (29/09/2026): no

Pregunta del usuario tras la revisión de 1 contra 2 niveles.
`scripts/ajuste_por_liga.py`, sobre las predicciones guardadas del oficial (2
niveles, 10 semillas). Cada mes, un ajuste por liga con solo sus meses
anteriores. 3.247 partidos, mar-2025 a sep-2026.

| ajuste | sigmas | por liga |
|---|---|---|
| A desplazar el nivel de cada liga | -1.43s | peor en las 6 |
| B Platt por liga (nivel y confianza) | +0.88s | 3 mejor, 3 peor |

- **A:** el oficial ya acierta el nivel de ambos marcan de cada liga; los
  desplazamientos aprendidos son pequeños (±0.15 en logit) y empeoran.
- **B:** mezclado liga a liga, y por debajo del Platt global (+1.20s, ver
  "Recalibración"). Separar por liga no añade nada.
- **Conclusión:** la liga ya pesa lo que tiene que pesar. Lo que perdía el
  modelo de 1 nivel eran reglas que cambian por liga, y el de 2 niveles ya
  las tiene. No reabrir "más peso a la liga".

## Registro en papel automático (29/09/2026) -- ACTIVO (aprobado por el usuario el 29/09)

`.github/workflows/ambos_marcan_diario.yml`. Con la regla del 29/09 ("nunca
llamar a la API sin su sí explícito", ver CLAUDE.md raíz), el usuario aprobó
expresamente estas llamadas automáticas. Ampliarlas necesita otro sí.

**Horario ajustado a los calendarios.**
- **Datos de partida:** en 2025/26 y 2026/27, todos los partidos de las 6
  ligas empezaron entre las 12:00 y las 21:30 hora española, y el 93% de
  viernes a lunes.
- **Parones FIFA 2026:** 21/09-06/10 y 09-17/11; la Segunda sigue jugando.
- **Bundesliga:** para tras el 18-20/12.
- **Premier:** 5 jornadas entre semana en toda la temporada.

**Qué hace cada pasada.**
- **08:07 UTC, todos los días:** partidos del día (`/matches` por liga y día,
  6 llamadas), resultados de ayer SOLO si ayer hubo partidos
  (`backfill_historico`), y primer pronóstico de todos (3 llamadas por
  partido).
- **Viernes a lunes, 09:07-20:37 UTC cada media hora:**
  - Primero `scripts/ambos_hay_partido.py`: segundos, sin API y sin instalar
    nada.
  - Solo si un partido empieza en 45 minutos o menos y no tiene pronóstico
    en los 90 minutos antes de su pitido, se descarga (3 llamadas, con el
    once) y se pronostica.
  - Una sola pasada por partido, aunque GitHub se retrase.
- **Martes a jueves (~7% de los partidos):** solo el pronóstico de la mañana.

**Gasto estimado.**
- **Con solo la Segunda:** ~30 llamadas al día.
- **Con las 6 ligas:** ~80 al día (~1% de la cuota).

**Otros detalles.**
- `ambos_marcan_hoy.py` acepta `LIGAS` (lista de IDs; por defecto las 6) y
  `VENTANA_MIN`.
- La evaluación toma el ÚLTIMO pronóstico antes del pitido.
- **Regla:** no tocar el modelo por el registro hasta 100+ apuestas.

## Auditoría externa (29-30/09/2026): pruebas de los puntos aceptados

Contraste completo con la auditoría en el chat. Se aceptaron los puntos 1, 6
y 7 (y el log loss del 8). Todo sin API, fijado antes de mirar.

**Punto 1, separar fútbol y precio** (`scripts/auditoria_separar.py`, 3.096
partidos, mar-2025 a sep-2026):

| probabilidad | Brier | log loss | frente al oficial |
|---|---|---|---|
| oficial (fútbol + precio) | 0.2467 | 0.6868 | -- |
| solo fútbol | 0.2476 | 0.6885 | -1.25s |
| solo precio (implícito recalibrado) | 0.2459 | 0.6875 | +0.89s Brier / -0.21s log loss |
| mezcla aprendida mes a mes | 0.2458 | 0.6872 | +0.98s / -0.13s |

- **Peso del fútbol en la mezcla:** 0.16, intervalo [-0.13, 0.47], cero o
  menos en el 16% de los remuestreos.
- **Frente al ambos marcan REAL (257 partidos):** oficial -0.08s, solo fútbol
  -0.19s, mezcla -1.13s, solo precio -1.32s.
- **Lectura:** en 18 meses, el precio solo, bien recalibrado, empata o supera
  al modelo entero. El fútbol añade muy poco encima del precio. En el
  arranque de 2026/27, contra el mercado real, el oficial es el mejor de los
  cuatro, pero ninguno bate al mercado.

**Punto 7, precio de entrenamiento frente al de directo**
(`scripts/auditoria_precio_directo.py`, 255 partidos):
- Correlación entre las dos fuentes: 1X2 0.99, más de 2.5 0.96, goles
  esperados 0.88, ambos marcan implícito 0.84.
- La probabilidad del modelo cambia 1.7 puntos de media (más de 3 puntos en
  el 23% de los partidos). El Brier casi no cambia.
- **Apuestas con VE>0: cambian 64 de unas 125 según la fuente.** La decisión
  de apostar es muy frágil al precio que se use.
- **Fallo silencioso encontrado:** `btts_implicito.ajustar()` partía de un
  solo punto y, con favoritos muy claros, daba goles esperados absurdos (3.2
  y 8.2 en vez de 0.9 y 2.9; implícito 96% en vez de 53%). Pasaba en 7 de 301
  partidos de Highlightly y 30 de 9.107 de football-data.
- **Arreglo:** varios puntos de partida. Efecto en el oficial: -0.31s (ruido),
  12 partidos cambian el implícito más de 5 puntos. Se queda por ser correcto.

**Punto 6, cambios aceptados repetidos con semillas nuevas (10-14)**
(`scripts/auditoria_semillas.py`):

| cambio | semillas 0-4 (cuando se aceptó) | semillas 10-14 |
|---|---|---|
| A portero titular | +1.25s, 10/14 meses | **-0.78s, 8/14 meses** |
| B 2022/23 sin xG del equipo | +2.55s, 13/21 meses | **+2.37s, 13/21 meses** (log loss +2.34s) |

- **B se confirma.**
- **A no se confirma:** el signo se da la vuelta. Winner's curse de libro.
  **Decisión del usuario (30/09): el portero SE QUEDA**, por lógica de
  fútbol ("es una pieza fundamental en el ambos marcan"). Coste bajo: son 2
  variables y, sumando las dos pruebas, su efecto neto es ~0 (+1.25s y
  -0.78s), así que ni ayuda ni daña de forma medible. No volver a proponer
  quitarlo salvo que una prueba nueva lo muestre dañando con claridad.

## Segunda auditoría externa (30/09/2026): reproducida con XGBoost real

Todo sin API, en scripts nuevos, con las reglas fijadas antes.

**Paso 1, precio frente a modelo** (`scripts/auditoria2_precio.py`, 4.422
partidos con precio previo, sep-2024 a sep-2026, 21 meses):

| comparación | Brier | log loss | meses mejor |
|---|---|---|---|
| ruido: oficial semillas 10-14 frente a 0-4 | -1.52s | -1.58s | 7/21 |
| P1: solo precio (B) frente al oficial | **+2.58s** | +2.68s | 14/21 |
| P1: precio ampliado (C) frente al oficial | **+3.01s** | +3.05s | 17/21 |
| XGBoost con solo el precio (D) frente al oficial | +0.95s | +1.00s | 10/21 |
| P2: partir del precio + árboles de fútbol (120) frente a B | -1.64s | -1.73s | 8/21 |
| P2: lo mismo con 300 árboles frente a B | -2.56s | -2.70s | 5/21 |
| P3: precio ampliado (C) frente a solo precio (B) | +1.06s | +0.92s | 12/21 |
| P3: C + liga frente a C | -0.85s | -0.88s | 9/21 |

- **Calibración (lado elegido, >65%):** oficial dice 68.3% y pasa 61.2%;
  B 67.6/64.1; C 68.1/64.8. El precio está mejor calibrado.
- **Contra el ambos marcan REAL (255 partidos, ago-sep 2026):** oficial -0.06s,
  B -0.91s, C -0.73s, C+liga -0.69s, D -0.63s, E120 -0.22s, E300 +0.14s.
  Ninguno bate al mercado; el oficial empata y los de solo precio quedan
  algo por debajo.
- **Veredicto:** puntos 1 y 2 CONFIRMADOS: frente al resultado, en 21 meses,
  el precio solo gana al oficial por encima del ruido de semillas, y el
  fútbol encima del precio empeora. Punto 3 NO confirmado (+1.06s, la liga
  tampoco aporta).
- **Pero** en los únicos partidos con ambos marcan real, el oficial está
  más cerca del mercado que los modelos de solo precio. La muestra es
  pequeña y solo cubre el arranque de temporada.

**Paso 2, paridad entrenamiento/directo** (`scripts/auditoria2_paridad.py`,
197 partidos de sep-2026 reconstruidos día a día):

| grupo | variables | partidos que difieren | notas |
|---|---|---|---|
| calidad de plantilla | 9 | 0.0% | paridad exacta |
| portero | 2 | 1.3% | diferencias pequeñas (máx. 0.37) |
| precio | 7 | 100% | otra fuente (Highlightly frente a football-data) |
| resto | 84 | 1.2% | solo la posición en la tabla difiere (26-35% de los partidos, hasta 4 puestos: el entrenamiento cuenta los partidos del mismo día jugados antes, el directo no) |

- **Efecto en la predicción:** 1.71 puntos de media, más de 3 puntos en el
  21% de los partidos.
- **Todo viene del precio:** con el mismo precio en los dos caminos, el
  cambio es de 0.03 puntos de media (máx. 0.5).
- **El precio de directo acierta más:** Brier +1.08s, log loss +1.09s. Es
  más reciente.
- **Conclusión:** portero, calidad y resto tienen paridad en la práctica. La
  única diferencia material es la fuente del precio.

**Paso 3, Elo** (`scripts/auditoria2_elo.py`, 4.601 partidos, 21 meses):

| variante | Brier | log loss | meses mejor | contra el real |
|---|---|---|---|---|
| V1: regresión 1/3 a la media de la liga cada temporada | +0.62s | +0.59s | 12/21 | +0.05s |
| V2: V1 + ancla (percentil 20 al subir, 80 al bajar de LaLiga) | -0.46s | -0.54s | 12/21 | -0.05s |

- Como predictor del resultado por sí solo, el Elo queda igual en las tres
  versiones (Brier 0.2201 / 0.2205 / 0.2200).
- **No se confirma:** los problemas del Elo que señala la auditoría existen,
  pero no mueven nada, porque el precio ya lo lleva dentro.

**Paso 4, cómo juzgar el registro en papel** (números con los 257 partidos
con cuota real):
- **Métrica principal:** Brier y log loss del modelo frente al ambos marcan
  real (mediana sin margen), sobre TODOS los partidos pronosticados y
  emparejados partido a partido. No solo sobre los apostados.
- **La desviación por partido de la diferencia de Brier es 0.048.** Partidos
  necesarios para ver una mejora a 2 sigmas:
  - 0.005 de Brier (~2% del Brier del mercado): ~370
  - 0.002: ~2.300
  - 0.001: ~9.200
- **Apuestas:** con cuota media 1.92, la desviación del beneficio por
  apuesta es ~0.96. Para ver a 2 sigmas una ventaja del +5% hacen falta
  ~1.500 apuestas; del +10%, ~370. Con 100 apuestas solo se vería una
  ventaja de más del +19%.
- **Margen mínimo de valor esperado:** cambiar de fuente de precio mueve el
  valor esperado con una desviación del 4.9% (percentil 90 de |diferencia|:
  7.8%). Propuesta: apostar solo si el valor esperado supera el 8%. Por
  debajo, el "valor" puede ser solo ruido del precio.

**Cambios en el registro en papel (30/09/2026), aprobados por el usuario tras la auditoría.**
El modelo oficial NO cambia. En `ambos_marcan_hoy.py`:
- **Columna nueva `mod_ambos_precio`:** el modelo de solo precio ampliado (la
  logística "C" de `auditoria2_precio.py`, reentrenada en cada pasada). Solo se
  apunta; no se apuesta con él. Sirve para que el registro resuelva la
  contradicción de la auditoría: C gana al oficial frente al resultado, pero
  pierde frente al mercado real.
- **Juez principal en `evaluar`:** Brier y log loss sobre TODOS los partidos,
  contra el ambos marcan real, con sigmas emparejadas. Se calcula para el oficial
  y para el de solo precio.
- **Punto de control a los 400 partidos.** Hasta entonces no se toca el modelo.
- **Apuesta en papel solo con VE > 8%** (`UMBRAL_VE`). Se aplica también a las
  filas anteriores al cambio. VE > 0 se sigue enseñando, pero solo como
  referencia.
- **Pendiente, sin prisa:** la posición en la tabla en directo no cuenta los
  partidos acabados ese mismo día. Arreglarlo costaría llamadas a la API o
  cambiar `rasgos.py`.

**Fuga en la posición de la tabla (30/09/2026, `scripts/auditoria2_tabla_fuga.py`, sin API).**
`rasgos.calcular_tabla` va partido a partido por orden de hora. Con dos partidos
de la misma liga a la MISMA hora, el que cae segundo en el orden ya ve el
resultado del otro en la tabla. Es información que no existía al empezar.
La reimplementación reproduce la tabla actual en los 9.292 partidos.

Cuánto afecta:
- El 38% de los partidos empiezan a la misma hora que otro de su liga.
- La fuga cambia la posición en el **8,6%** de los partidos: 1,3 puestos de
  media, hasta 8.
- Los partidos jugados antes ese mismo día (que en directo no se ven y al
  entrenar sí; no es fuga) cambian otro **18%**.
- Entre las dos cosas, un 25% de partidos difiere de lo que se ve en directo.

Efecto en el modelo oficial (21 meses, 5 semillas):

| versión de la tabla | frente a la actual | meses mejor | contra el ambos marcan real |
|---|---|---|---|
| actual | - | - | -0.02s |
| estricta (sin fuga) | Brier -0.37s, log loss -0.35s | 7/21 | -0.04s |
| inicio del día (= directo) | Brier +0.31s, log loss +0.24s | 11/21 | +0.11s |

- Inicio del día frente a estricta: Brier +0.65s, log loss +0.56s, mejor en
  12/21 meses.
- La probabilidad cambia 0,25-0,29 puntos de media.

Lectura:
- La fuga es real pero no infló nada: quitarla no cambia el modelo más allá del
  ruido de semillas. Las conclusiones anteriores siguen en pie.
- Con las reglas fijadas antes, la versión recomendada es **inicio del día**:
  quita la fuga, no es peor que la estricta e iguala entrenamiento y directo.
- No se ha aplicado todavía: cambiarla es decisión del usuario.
- `rasgos.py` NO se toca (lo usan los otros modelos). El cambio iría dentro de
  `modelo_ambos_marcan.preparar()`.
- La misma fuga existe en los modelos de 1X2 y goles, que usan
  `calcular_tabla`. Sin arreglar allí.
