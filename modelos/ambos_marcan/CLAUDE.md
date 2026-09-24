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
