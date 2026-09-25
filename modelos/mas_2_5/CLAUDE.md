# Más de 2.5 goles -- carpeta propia (24/09/2026)

Mismo patrón que `modelos/ambos_marcan/`: todo lo necesario para trabajar
SOLO el mercado Más/Menos 2.5 goles. Scripts con rutas relativas: ejecutar
desde ESTA carpeta (`cd modelos/mas_2_5 && python3 scripts/...`).

- `scripts/rasgos.py`, `modelo_xgboost.py`, `evaluar_mercados.py`: copia
  del repo padre a 24/09 (Elo, tabla y las referencias salen de aquí).
- `scripts/rasgos_mas25.py`: **nuevo**, las variables diseñadas por el
  usuario (ver abajo) y su comprobación de fuga.
- `scripts/seleccion_combinaciones.py`: las 128 combinaciones + prueba final.
- `scripts/ranking_y_combo_usuario.py`: ranking por variable y combinaciones pedidas.
- `scripts/prueba_humo.py`: fuga de los dos módulos + un entrenamiento real.
- `data/`: históricos completos (4.283 partidos, incluye 2024/25) y cuotas
  filtradas SOLO a "Total Goals 2.5" (19.094 + 9.816 filas).
  Sin clave de API ni workflows: los backfills se lanzan desde el repo padre.

## Variables pedidas por el usuario (rasgos_mas25.py)

| grupo | qué es |
|---|---|
| `base_cf` | medias de los últimos 8 partidos del LOCAL SOLO EN CASA y del VISITANTE SOLO FUERA: goles a favor/contra, xG a favor/contra, tiros a puerta y fuera (propios y del rival), córners, faltas, posesión, pases, centros, puntos; partidos previos en ese escenario, descanso, liga. Sin amarillas |
| `elo`, `tabla` | iguales que en el repo padre |
| `cp_ataque` | g+a por 90 de la temporada ANTERIOR de delanteros y de medios titulares |
| `cp_defensa` | porterías a cero de medios, defensas y portero titulares |
| `cp_minutos` | minutos medios de la temporada anterior de los 11, y cuántos se conocen |
| `h2h_reciente` | enfrentamientos reales (/head-2-head) de los 2 últimos años, peso doble al último año: puntos, diferencia, **goles totales y tasa de Más 2.5** |

Detalles que no hay que redescubrir:
- **La posición sale de la formación.** `historico_lineups.csv` guarda los 11
  IDs línea a línea (portero, defensas, medios, delanteros). Verificado: g+a/90
  de 0.003 / 0.10 / 0.28 / 0.53 en ese orden.
- **Porterías a cero por jugador**: proporción de sus titularidades ANTERIORES
  en nuestro histórico sin encajar, contraída hacia la tasa global con K=5.
  `/players/{id}/statistics` trae `cleanSheets` y `goalsConceded` en
  `perCompetition`, pero `backfill_jugador_stats.py` no los guardó, y ese
  dato (estilo Transfermarkt) suele ser solo de porteros. No verificado:
  no hay clave de API en esta sesión.
- 2024/25 no tiene alineaciones, así que las porterías a cero empiezan a
  contar en 2025/26. 2024/25 casi no tiene xG (5%).
- Comprobación de fuga: se trunca el marcador de UN partido cada vez. Truncar
  varios a la vez daba una falsa alarma (el primero mueve, legítimamente,
  las porterías a cero de los posteriores).

## Bug de subcadena en la primera versión (24/09/2026) -- números anteriores INVÁLIDOS

`rasgos.grupos_rasgo()` mete en "base" todo lo que empiece por `loc_`/`vis_`/
`dif_`. Las columnas nuevas `loc_cp_*`/`vis_cp_*`/`dif_cp_*` (calidad por
posición) y `dif_cf_*` (casa/fuera) empiezan así, así que la "base clásica" y
la "producción del padre" las llevaban dentro sin querer. Se detectó porque
añadir `cp_ataque` a la base clásica daba predicciones IDÉNTICAS. Es el mismo
fallo que "duelos"/"elo" del CLAUDE.md del padre. Corregido en `grupos()`;
todo lo de abajo está rehecho. La primera tabla publicada (elegido
base_cf+elo+tabla+cp_ataque+h2h, "-0.74s contra la clásica") no vale.

## Resultado corregido (seleccion_combinaciones.py)

Protocolo: 2 núcleos (`base_cf` / `base_clasica` sin amarillas) x 64
combinaciones de los 6 grupos = 128 configs, 5 semillas. Selección sobre 388
partidos (01/03-23/04/2026), entrenando con 3.264 filas (incluye 2024/25).
Prueba final UNA vez sobre 528 (24/04-20/09/2026), 186 con cuota.

En selección, las 16 mejores llevan todas `base_cf`. Presencia en esas 16:
h2h_reciente 14, cp_ataque 11, elo 10, tabla 10, cp_minutos 7, **cp_defensa 1**.
Elegido: **`base_cf+elo+cp_ataque+h2h_reciente`** (75 rasgos).

| modelo | Brier | elegido vs este | vs media | vs mercado | acierto |
|---|---|---|---|---|---|
| ELEGIDO | 0.4783 | -- | +3.24% | -0.92s | 66.1% |
| todo lo pedido (base_cf + los 6) | 0.4836 | +2.09s | +2.16% | -1.91s | 64.5% |
| base_cf+elo | 0.4801 | +0.55s | +2.88% | -1.00s | 62.4% |
| base_clasica+elo | 0.4765 | -0.25s | +3.60% | -0.97s | 63.4% |
| producción repo padre | 0.4753 | -0.42s | +3.86% | -1.07s | 64.5% |
| mercado | 0.4430 | | | | 68.3% |

- El elegido EMPATA con la base clásica (-0.25s) y con la producción del
  padre (-0.42s). Casa/fuera ganaba en selección y no se sostiene en prueba.
- Todo lo pedido junto es claramente peor (+2.09s a favor del elegido).
- Contra el mercado: -0.92s; peor que el mercado en el 82% de bootstraps;
  sin sus 10 mejores partidos, -2.74s. Inicio 2026/27: +6.21% sobre la media.

## Ranking de cada variable (ranking_y_combo_usuario.py, prueba final)

Positivo = ayuda. "Sola" = añadida al núcleo; "quitar" = cuánto empeora el
conjunto completo sin ella. Ojo: medido sobre la prueba final, informativo.

| variable | sola / quitar (base clásica) | sola / quitar (base casa/fuera) |
|---|---|---|
| cp_ataque (g/a delanteros y medios) | +0.94 / +1.24 | +1.50 / +1.70 |
| tabla | +1.04 / +0.81 | -0.46 / -0.81 |
| elo | +0.33 / -0.06 | +0.90 / -1.02 |
| cp_minutos | -1.00 / +0.44 | -0.44 / -2.29 |
| h2h_reciente | -1.80 / -1.78 | -0.96 / -1.90 |
| cp_defensa (porterías a cero) | -1.13 / -0.89 | -1.99 / -1.80 |

base_cf sola frente a base_clasica sola: -0.62s. **Solo cp_ataque ayuda en las
cuatro mediciones.** Porterías a cero y h2h restan en las cuatro.

Combinación pedida por el usuario (porterías + g/a + h2h), frente a
base_clasica+elo: sobre base clásica -1.40s (mercado -2.00s), con Elo -1.31s,
sobre base casa/fuera -0.87s (mercado -1.68s). Peor en las tres. La mejor
de las probadas: **base_clasica+elo+g/a, +1.03s sobre la referencia, -0.66s
contra el mercado** (elegida tras ver la prueba: algo inflada).

## Qué no repetir

- No hay combinación que bata al mercado. Congelados en `rasgos_mas25.py`:
  `PRODUCCION` (el elegido) y `ALTERNATIVA` (base_clasica+elo). Siguiente
  candidato a congelar: base_clasica+elo+cp_ataque. Juzgarlos SOLO con
  partidos jugados desde el 25/09/2026, sin volver a elegir.
- No reabrir "casa/fuera" como mejora sin muestra nueva: ganó en selección
  y empató en prueba limpia (en ambos_marcan, localía también empeoraba).
- Al añadir columnas con prefijo loc_/vis_/dif_, comprobar que no se cuelan
  en el grupo "base" de rasgos.grupos_rasgo() (ver bug de arriba).
- `cp_defensa` (porterías a cero) casi no aparece entre las mejores: la
  porterías a cero de un jugador es sobre todo la del equipo, que ya está en
  goles encajados de `base_cf`. Probar el `cleanSheets` de la API solo si se
  confirma que viene para no-porteros.
- Cualquier variable nueva: más columnas con ~3.600 filas de entrenamiento
  ya se sabe que resta.

## Sin ningún bloque de base (sin_base.py, 24/09/2026)

Petición del usuario: quitar la base. 63 combinaciones de los 6 grupos
(+liga), elegida en selección: tabla+cp_ataque+cp_minutos+h2h_reciente.
Prueba final (528, 186 con cuota), frente a base_clasica+elo+g/a:

| modelo | vs mejor con base | vs mercado | acierto |
|---|---|---|---|
| base_clasica+elo+g/a | -- | -0.66s | 63.4% |
| sin base, elegido | -1.80s | -2.37s | 59.7% |
| sin base, elo+tabla+g/a | -1.81s | -2.74s | 57.5% |
| sin base, las 6 | -2.43s | -3.25s | 54.8% |
| mercado | | | 68.3% |

Quitar la base empeora en todos los casos: las medias de goles, tiros y xG
son lo que más sabe de este mercado. No repetir.

## Titulares nuevos respecto a la temporada anterior (experimento_plantilla_nueva.py, 24/09/2026)

Idea del usuario: al empezar temporada cambian jugadores, entrenador y
momento, y el modelo no lo ve. Variable `plantilla_nueva` (rasgos_mas25.py):
fracción y número de titulares cuyo club de la temporada anterior no es el
equipo de hoy (equipo = club mayoritario del once en la temporada en curso,
según historico_jugador_stats.csv; el club es identidad, no rendimiento).
Cobertura 100% de los partidos fijos. Hipótesis declarada antes de mirar:
si ayuda, debe ayudar sobre todo en ago-sep 2026.

Sorpresa en los datos: la fracción de nuevos es MENOR al empezar temporada
(22-26% en agosto) que en primavera (~40%). Los fichajes no entran de golpe
en el once: los entrenadores arrancan con el bloque del año anterior.

| positivo = la variable ayuda | selección | final 25/26 | inicio 26/27 | todo | vs mercado |
|---|---|---|---|---|---|
| base_clasica+elo+g/a (+pn) | -0.54s | +0.07s | -0.95s | -0.60s | -0.66s -> -0.75s |
| base_clasica+elo (+pn) | -0.68s | -0.62s | +0.76s | +0.14s | -0.97s -> -0.71s |

Sin dirección consistente: con g/a empeora justo donde debía ayudar (inicio
de temporada); sin g/a ayuda un poco ahí y empeora en el resto. Lectura
probable: el g/a de atacantes YA sigue a los fichajes (va con el jugador), así
que la parte útil de "quién es nuevo" ya estaba dentro. No entra en el modelo.
Entrenador nuevo sigue sin medir: `docs/openapi_highlightly.json` no tiene
ningún campo coach/manager/trainer en ninguna de sus 25 rutas (buscado el
24/09 en la especificación entera). Haría falta otra fuente de datos.

## Depuración + salto de temporada (depurar_y_temporada.py, 24/09/2026) -- MODELO ACTUAL

Petición del usuario: demasiadas variables, depurar; y que el modelo sepa
saltar de temporada y se mida también a final de temporada.

**Cuotas de final de temporada: no existen.** `/odds` solo sirve hasta 28
días después del partido (API.md); las de abr-jun 2026 se perdieron. Contra
el mercado solo se puede medir el inicio de 2026/27. El final de 2025/26 se
mide contra la media y entre modelos.

**Depuración:** eliminación hacia atrás por MEDIDA desde base_clasica+elo+g/a
(73 rasgos), eligiendo SOLO en el tramo de selección. Por orden, fuera:
córners, goles, centros, previos/descanso, posesión, xG, Elo, faltas. Quedan
**tiros a puerta, tiros fuera, pases, puntos (propios y del rival,
loc/vis/dif) y g/a de atacantes: 28 rasgos.** Que se vayan goles y xG no es
raro: los tiros ya llevan esa información con menos ruido.

**Salto de temporada:** grupo `jornada` (partidos jugados en ESTA temporada,
loc/vis/dif_tabla_pj). Entrenar con 2024/25 ya estaba hecho.

| modelo | rasgos | final 25/26 vs media | vs A | inicio 26/27 vs media | vs A | vs mercado | acierto |
|---|---|---|---|---|---|---|---|
| A: base_clasica+elo+g/a | 73 | +1.25% | -- | +7.64% | -- | -0.71s | 60.8% |
| A + jornada | 76 | +1.80% | +2.24s | +7.45% | -0.73s | -0.91s | 61.8% |
| **DEPURADO** | **28** | **+2.26%** | **+1.01s** | **+8.59%** | **+0.84s** | **+0.10s** | **68.8%** |
| DEPURADO + jornada | 31 | +2.40% | +1.13s | +8.04% | +0.35s | -0.33s | 66.7% |
| mercado | | | | +9.48% | | | 68.3% |

Réplica independiente (entrenar SOLO con 2024/25, probar el arranque de
2025/26, ago-oct 2025, n=564, sin g/a): DEPURADO +1.40s sobre A,
A+jornada +1.62s, DEPURADO+jornada +1.00s.

- **El depurado mejora a los 73 rasgos en los TRES tramos** (final de
  temporada, arranque 2026/27 y arranque 2025/26). Menos columnas, mejor
  modelo: el patrón de todo el proyecto.
- **Contra el mercado: EMPATE, no ventaja.** +0.10s; sin su mejor partido
  -0.13s; bootstrap peor que el mercado en el 47%; con otras semillas -0.07s
  y +0.03s. Primera vez que mas_2_5 no pierde contra el mercado.
- **`jornada` no es consistente:** ayuda a A a final de temporada y en la
  réplica, pero empeora en el inicio de 2026/27 y casi no añade al depurado.
  Fuera.

`PRODUCCION` = base_depurada + cp_ataque. Siguiente paso: juzgarlo con
partidos desde el 25/09/2026 sin volver a elegir, y ver si con más cuotas se
separa de cero hacia +2s o no.

## Acierto honesto en 2025/26 (temporada_fuera.py, 24/09/2026)

Modelo de producción (28 rasgos), 2.223 partidos de 2025/26, sin cuotas (la
API las borra a los 28 días), así que solo acierto:

| forma de medirlo | acierto |
|---|---|
| mes a mes (cada mes, entrenado solo con lo anterior) | 56.0% |
| temporada fuera (entrenado con 2024/25 + inicio 2026/27, nada de 2025/26) | 56.3% |
| siempre lo más frecuente | 52.5% |
| con trampa (entrenado incluyendo 2025/26) | 66.3% -- NO VALE |

Las dos formas honestas coinciden (56%). Cuando el modelo da más del 60% a un
lado (774 partidos) acierta el 59.2%; más del 70% (160), el 63.7%. El 68.8%
del inicio de 2026/27 no es comparable: son otros partidos, y ahí el mercado
también acertó el 68.3%.

## 18 variables añadidas una a una sobre las 28 (anadir_una_a_una.py, 24/09/2026)

Petición del usuario: probar cada variable disponible en disco, en su orden;
si mejora se queda, si no se quita. Criterio: Brier del tramo de selección
(388 partidos, mar-abr 2026). Nuevas construidas aquí: formación (defensas/
medios/delanteros), árbitro goles ventana 20, impacto de jugador, goles de
temporada, forma de 3 partidos + momentum (sin goles en contra: rasgos.py no
calcula r_goles_contra). Box-score leído del repo padre, no copiado.

| variable | vs actual (selección) | decisión |
|---|---|---|
| formación | +0.19s | se queda |
| árbitro goles v20 | -0.41s | fuera |
| impacto jugador | -0.11s | fuera |
| goles | -1.99s | fuera |
| xG | -0.53s | fuera |
| posesión | -0.19s | fuera |
| centros | -0.67s | fuera |
| previos/descanso | -1.03s | fuera |
| forma 3 + momentum | -0.74s | fuera |
| Elo | -0.49s | fuera |
| goles de temporada | -0.79s | fuera |
| calidad vieja (minutos, g/a del once) | +1.26s | se queda |
| porterías a cero | -0.85s | fuera |
| minutos/conocidos | -0.27s | fuera |
| rotación | -1.95s | fuera |
| H2H 2 años | +0.18s | se queda |
| clima | -1.50s | fuera |
| box-score (54 columnas) | +1.08s | se queda |

Resultado en selección: 28 + formación + calidad vieja + H2H + box-score =
105 rasgos. **En la prueba final limpia es PEOR que las 28:** -1.30s contra
el de 28; contra el mercado -1.07s (el de 28: +0.03s); acierto 61.8% frente
a 67.7% (mercado 68.3%). Final 2025/26: +0.74% sobre la media frente a
+2.13%; inicio 2026/27: +7.24% frente a +8.61%.

Lo que se "ganó" en selección era ajustarse a esos 388 partidos: 18 pruebas
seguidas sobre el mismo tramo, quedándose con lo que sale positivo por azar
(tres de las cuatro, por debajo de +1.3s). **El modelo de 28 rasgos se queda
como está.** No reabrir estas 18 con la misma muestra.

## Quitar puntos y pases + "quién gana" (ganar_y_goles.py, 24/09/2026)

Dato de partida: gana el local -> 63% Más 2.5, gana el visitante -> 60%,
empate -> 27%. Variables del usuario: V1 = % de Más 2.5 en las últimas 10
victorias del local en casa / visitante fuera; V2 = minimodelo 1X2 (logística
con Elo y % de victorias en casa/fuera, ajustada solo con entrenamiento;
acierta el ganador el 50.4%); combinada = P(gana)·V1 + P(empate)·tasa en
empates. Sin fuga (comprobado).

| modelo | selección vs 28 | prueba vs 28 | vs mercado | acierto |
|---|---|---|---|---|
| 28 (actual) | -- | -- | +0.03s | 67.7% |
| 19 (sin puntos ni pases) | -1.07s | -1.28s | -1.13s | 64.0% |
| 19 + V1 / V2 / combinada / todo | -0.87 a -1.35s | -1.23 a -1.50s | -1.06 a -1.36s | 60-65% |
| 28 + V1 | +0.05s | +0.03s | +0.22s | 69.4% |
| 28 + V2 | +0.01s | -1.29s | -0.18s | 68.8% |
| 28 + combinada | +0.36s | +0.00s | -0.11s | 68.8% |

Puntos y pases hacen falta: quitarlos cuesta ~1.3s y nada lo recupera. Sobre
las 28, las tres variables nuevas se mueven dentro del ruido (±0.4s). El
minimodelo no añade: quién gana ya lo saben los tiros, los puntos y el g/a.
El modelo de 28 no cambia.

## Contra el mercado en TODA la temporada, con cuotas de football-data.co.uk (25/09/2026)

La API borra las cuotas a los 28 días. football-data.co.uk (gratis, sin
clave, NO gasta llamadas de Highlightly) guarda las de temporadas enteras:
media de casas (Avg), máxima (Max), Bet365, Pinnacle y cierre.
`data/football_data/*.csv` (6 ligas x 2024/25-2026/27), cruzadas con nuestros
partidos en `scripts/cruzar_football_data.py` (liga + fecha ±1 día + marcador
+ nombre; alias para Athletic, Gladbach, PSG, Celta B): 4.265 de 4.282
(99.6%). Comprobación contra las cuotas de la API en 251 partidos comunes:
correlación 0.964, diferencia media 2.2 puntos. La fuente es fiable.

`scripts/contra_mercado_temporada.py`, modelo de 28 prediciendo mes a mes
(cada mes entrenado solo con lo anterior):

| tramo | partidos | vs media de casas | vs Pinnacle cierre | acierto modelo | acierto casas |
|---|---|---|---|---|---|
| 2025/26 | 2.211 | **-2.27s** | **-3.11s** (1.087) | 56.0% | 57.6% |
| 2026/27 | 316 | -1.31s | -- | 61.1% | 65.5% |

Apostando 1 unidad al lado con valor: con la cuota media, -2.4% a -2.9%
según umbral (1.744 a 814 apuestas). Con la cuota MÁXIMA de ~40 casas,
+1.41% sin umbral (±2.27, +0.62s) y negativo con umbral: ruido, y además
optimista (cuotas máximas no simultáneas, ver que_casas_abrir.md).

**Con la temporada entera, el modelo PIERDE contra el mercado con claridad**
(-2.27s, -3.11s contra Pinnacle). El "empate" de ago-sep 2026 (+0.03s en 186
partidos) era muestra pequeña. Regla del proyecto: al crecer la muestra el
número se fue lejos de cero, pero en contra. Cerrado para mas_2_5 con estas
variables.
