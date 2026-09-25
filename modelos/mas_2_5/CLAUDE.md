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
número se fue lejos de cero, pero en contra. Cerrada la vía "más variables
de equipo"; el mercado NO se da por cerrado: ver siguiente sección (cuota de
la casa como variable, posible ahora que hay cuotas de temporadas enteras).

## Cuota de la casa como variable (cuota_como_variable.py, 25/09/2026)

Con cuotas de football-data para 2024/25-2026/27 el entrenamiento ya las
tiene. Dos versiones fijadas antes de mirar: A = 28 + p_mercado (media de
casas) como columna; B = XGBoost que ARRANCA en el mercado (base_margin =
logit p_mercado) y solo aprende correcciones con los 28. Mes a mes, 2.527
partidos (ago 2025 - sep 2026):

| modelo | vs media casas | vs Pinnacle cierre (1.087) | acierto |
|---|---|---|---|
| 28 sin cuota | -2.65s | -3.20s | 56.2% |
| A | -2.06s | -2.62s | 57.6% |
| B | -2.13s | -2.61s | 57.5% |
| media de casas | -- | -0.95s | 58.6% |

Apostando con la cuota media: -2.8% a -4.0% en las dos versiones.

Lectura: B se separa del mercado 5.7 puntos de media (hasta 27) y cada
separación empeora. Es decir, **lo que los 28 rasgos "corrigen" al mercado
es ruido**: no llevan información que la cuota no tenga ya. Más
regularización solo acercaría B al mercado (0s), nunca por encima. Para batir
al mercado hace falta información que el mercado no use bien, no más
estadística de equipo. Siguientes vías: movimiento de cuota (apertura ->
cierre) y diferencias entre casas (blanda frente a Pinnacle).

## Casas blandas contra Pinnacle (pinnacle_vs_blandas.py, 25/09/2026)

Sin modelo: Pinnacle sin margen = probabilidad justa; apostar donde otra
cuota pague más. football-data trae Pinnacle antes del partido en 3.283
partidos (2024/25: 2.195, 2025/26: 1.088; 2026/27 todavía no). Margen de
Pinnacle: 3.76%. Resultados completos en data/pinnacle_vs_blandas.log.

- **Bet365 y la media de casas casi nunca pagan más que Pinnacle:** 39 y 17
  apuestas en dos temporadas. En Más/Menos 2.5 de estas ligas, las casas
  blandas copian a Pinnacle y le suman margen.
- **La cuota máxima de ~40 casas sí:** 456 apuestas, +3.57% (±5.57, +0.64s),
  pero +5.36% en 2024/25 y -4.99% en 2025/26: no se repite. Con umbral 2%,
  +23.6% y -15.4%. Ruido, y la máxima mezcla momentos distintos.
- El 61-87% de esas apuestas bate el cierre de Pinnacle: señal de precio
  bueno, pero con esta muestra no se convierte en beneficio medible.
- Las cuotas de la API (38 casas) NO incluyen Pinnacle: no se puede repetir
  con cuotas simultáneas.

Conclusión: con cuotas de una foto al día no hay valor medible contra
Pinnacle. Esta estrategia en la vida real depende de ver las cuotas de muchas
casas EN TIEMPO REAL y cazar la que se queda atrás minutos u horas; eso no
se puede medir con estos datos.

## Movimiento de la cuota previa -> cierre (movimiento_cuota.py, 25/09/2026)

football-data da una foto "previa" (días antes) y el cierre. 4.744 partidos
con media de casas, 3.280 con Pinnacle (2 filas con cuotas imposibles
descartadas). Movimiento medio: 2 puntos de probabilidad.

- Control: el cierre predice mejor que la previa en las tres temporadas
  (+2.93s, +1.58s, +0.60s). Los datos son coherentes.
- ¿El movimiento predice MÁS ALLÁ del cierre? Coeficiente positivo (la
  cuota sigue un poco en la dirección en que se movía) pero no significativo:
  z=+1.68, +0.42, -0.91 por temporada con la media; +1.45, +0.42 con
  Pinnacle. No se repite con fuerza.
- Apostar al cierre en la dirección del movimiento: con la cuota media de
  cierre, -3.95% (3.204 apuestas, -2.46s); con la máxima, -0.17% (ruido;
  +3.8% en 2024/25, -4.0% en 2025/26).

El cierre ya incorpora el movimiento: no queda nada que cobrar. Con fotos de
dos momentos no se puede probar "apostar pronto antes de que se mueva" (haría
falta saber hacia dónde se moverá, que es otra vez predecir mejor que el
mercado).

## Otra arquitectura: modelo de goles Poisson (modelo_goles_poisson.py, 25/09/2026)

Goles de cada equipo = liga + ventaja local + ataque + defensa rival
(regresión de Poisson, vida media 365 días, alpha 0.01); P(Más 2.5) del
total. Todo fijado antes de mirar, incluida la mezcla 50/50 con el XGBoost
de 28. Mes a mes, mismos 2.527 partidos con cuota:

| modelo | vs media casas | vs Pinnacle cierre | acierto | vs XGBoost 28 |
|---|---|---|---|---|
| XGBoost 28 | -2.65s | -3.20s | 56.2% | -- |
| Poisson de goles | -4.53s | -3.15s | 56.1% | -0.10s |
| **mezcla 50/50** | **-2.26s** | **-2.65s** | **57.7%** | **+2.27s** |
| media de casas | -- | -0.95s | 58.6% | |

- **La mezcla mejora al XGBoost de 28 por +2.27s**, con el peso fijado de
  antemano: primera mejora clara del modelo en esta carpeta desde la
  depuración. Los dos modelos se equivocan en sitios distintos.
- Poisson solo empata con el XGBoost (-0.10s); contra la media de casas
  queda peor (-4.53s). (Se atribuyó a los marcadores bajos; la sección
  siguiente lo desmiente: ρ de Dixon-Coles sale ~0.)
- **Contra el mercado todos siguen perdiendo.** Apostando con la cuota
  media: Poisson -10% a -13%, mezcla -7% a -11%.

Siguientes pasos razonables: corrección Dixon-Coles de marcadores bajos
(rho) y Poisson con xG en vez de goles. Fijar parámetros antes de mirar.

## Dixon-Coles y Poisson con xG (poisson_dc_xg.py, 25/09/2026)

Fijado antes de mirar: ρ de Dixon-Coles estimado cada mes por máxima
verosimilitud solo con entrenamiento; Poisson con xG (61% de partidos tienen
xG; el resto, goles). Mismos 2.527 partidos, mes a mes.

| modelo | vs XGB 28 | vs media casas | vs Pinnacle | acierto | apostando (cuota media) |
|---|---|---|---|---|---|
| XGBoost 28 | -- | -2.65s | -3.20s | 56.2% | -2.6% |
| Poisson goles (con o sin DC) | -0.10s | -4.53s | -3.15s | 56.1% | -11.9% |
| Poisson xG (con o sin DC) | +0.37s | -4.00s | -2.40s | 56.1% | -10.0% |
| mezcla goles + XGB | +2.27s | -2.26s | -2.65s | 57.7% | -7.1% |
| **mezcla xG + XGB** | **+2.61s** | **-2.08s** | **-2.35s** | 57.1% | -7.6% |

- **Dixon-Coles no cambia nada:** ρ sale entre -0.03 y 0.00 todos los meses;
  en estas ligas los marcadores bajos ya salen bien con Poisson normal.
- **xG ayuda un poco:** mezcla xG + XGBoost es el mejor modelo de la carpeta
  (+2.61s sobre el XGBoost de 28), aún lejos del mercado.
- Apostar con los modelos de Poisson pierde MÁS que con el XGBoost pese a
  Brier parecido: donde Poisson discrepa de la casa, se equivoca más.

## Peso de la mezcla Poisson-xG / XGBoost (peso_mezcla.py, 25/09/2026)

Peso elegido en ago 2025-ene 2026 (1.282 partidos), comprobado en feb-sep
2026 (1.245). Elegido: 70% Poisson-xG. En la comprobación ese peso da -2.07s
contra la casa; el mejor allí habría sido 20% (-1.09s). **El peso óptimo no
se mantiene de una mitad a otra**: no hay un peso fiable. Apostando, cuanto
más Poisson peor (0%: -1.4%, 70%: -9.0%, 100%: -14.5%). Para apostar, el
XGBoost de 28 solo sigue siendo lo menos malo.

## Con los datos nuevos de main (25/09/2026)

Copiados de main: histórico 5.694 partidos (2023/24 parcial 932, 2024/25
completa 2.223 con Segunda), alineaciones 4.760, árbitro 4.789, jugadores
4.332, h2h 1.558 pares. Cuotas 2023/24 de football-data; cruce 5.671
(99.6%). Prueba de humo OK. MISMOS 2.527 partidos de evaluación que antes
(ago 2025 - sep 2026, mes a mes); solo cambia el entrenamiento.

| modelo | vs media casas antes -> ahora | vs Pinnacle antes -> ahora | apostando (cuota media) ahora |
|---|---|---|---|
| XGBoost 28 | -2.65s -> **-1.09s** | -3.20s -> -1.76s | -1.0% / -0.2% |
| A: 28 + cuota | -2.06s -> -1.01s | -2.62s -> -1.78s | -1.4% a -4.1% |
| B: parte de la cuota | -2.13s -> -0.77s | -2.61s -> -1.77s | -1.7% a -3.4% |
| mezcla xG + XGB | -2.08s -> -1.02s | -2.35s -> **-1.15s** | -2.4% |
| media de casas | | -0.95s | |

- **Más temporadas de entrenamiento mejoran todo con claridad**: el XGBoost de
  28 pasa de -2.65s a -1.09s contra la media de casas (en 2025/26 sola,
  -0.67s). Es el entrenamiento el que cambia, no la muestra de prueba.
- Mezcla xG + XGB contra Pinnacle (-1.15s) ya casi igual que la media de
  casas contra Pinnacle (-0.95s).
- Apostando con cuota media, XGBoost 28 ~0% (-1.0% sin umbral, -0.4% con
  5%). Con la cuota máxima +4.2% (±2.4, +1.77s), pero la máxima es optimista
  (no simultánea): no se toma como ventaja.
- Poisson solo empeora con más datos frente a XGB (-1.16 a -1.45s); la mezcla
  ya solo aporta +0.55/+0.78s. La mejora grande viene del XGBoost.
- Pendiente: 2023/24 está a medias (932 de ~2.200). Repetir cuando termine.

## Historia larga solo con football-data (historia_larga.py, 25/09/2026)

22.873 partidos 2016/17-2026/27 (6 ligas) de football-data: goles, tiros, a
puerta, córners, cuotas (BbAv antes de 2019/20, Avg después). Variables solo
de esa fuente (medias de 8, Elo, liga; sin pases ni g/a). Fuga comprobada
(trucar un partido no mueve sus rasgos; sí 770 posteriores). Mismos meses de
evaluación (2.530 partidos, ago 2025 - sep 2026), fijado antes de mirar:

| entrenamiento | vs media casas | vs Pinnacle | acierto | apostando |
|---|---|---|---|---|
| 1 temporada | -2.59s | -1.80s | 56.1% | -3.6% |
| 3 temporadas | -4.13s | -3.68s | 56.0% | -9.4% |
| 10 temporadas | -3.68s | -2.81s | 55.5% | -8.7% |
| parte de la cuota, 10 temporadas | -1.05s | -1.78s | 58.6% | -5.3% (458 ap.) |
| media de casas | | -0.92s | 58.6% | |

**Más temporadas de estadística simple NO ayudan; empeoran.** El fútbol de
2016-2022 enseña relaciones que ya no valen (deriva de época), y sin pases ni
g/a el modelo es más pobre. Lectura de la mejora de la sección anterior
(-2.65s -> -1.09s): probablemente no fue "más partidos" sino más partidos CON
alineaciones y g/a de jugadores (2024/25 ganó alineaciones al copiar de main).
Hipótesis a comprobar; si se confirma, lo que hay que ampliar es la cobertura
de jugadores, no los años.

## Confirmado: la mejora vino del g/a de jugadores (efecto_ga.py, 25/09/2026)

Mismo modelo de 28, mismos datos nuevos, mismos 2.527 partidos mes a mes:
con g/a -1.09s contra la media de casas, sin g/a -1.99s; con frente a sin,
**+1.51s**. Cobertura de g/a de delanteros: 2023/24 2%, 2024/25 95% (antes de
copiar de main: 0%, no tenía alineaciones), 2025/26 96%. Lo que acerca el
modelo al mercado son los DATOS DE JUGADORES, no los años de historia.
Siguiente palanca: alineaciones y estadísticas de jugadores de 2023/24 (hoy
2%), y más estadísticas por jugador de la temporada anterior.

## Impacto de jugador (xG y goles) y lesiones (variables_jugador.py, 25/09/2026)

Copiado del repo 1x2 a data/de_1x2/: lesiones por jugador con fechas (La Liga
y Segunda, 727 jugadores) y su índice. **El índice de 1x2 NO se usa: pondera
por minutos de la temporada ENTERA (información futura).** Se recalcula:
peso = titularidades ANTERIORES con el equipo. Impacto xG / goles: xG o goles
a favor y en contra del equipo en las titularidades anteriores de cada
titular (K=5), media del once. Fuga comprobada (trucar un partido: el suyo
igual, 1.534 posteriores cambian). Mes a mes, 2.527 partidos:

| modelo | vs 28 (todas) | vs casas (todas) | vs 28 (España, 975) | vs casas (España) |
|---|---|---|---|---|
| 28 | -- | -1.09s | -- | -0.44s |
| + impacto xG | -1.42s | -1.45s | +0.05s | -0.42s |
| + impacto goles | -1.39s | -1.53s | -0.76s | -0.67s |
| + impacto xG y goles | -2.07s | -1.86s | -0.85s | -0.76s |
| + lesiones | -- | -- | -0.74s | -0.70s |

Ninguna mejora al 28; todas empeoran salvo impacto xG en España (empate).
El g/a individual de la temporada anterior sí sirve (+1.51s); el "impacto
de equipo cuando juega" no: mezcla al jugador con sus compañeros, y lo que
dice del equipo ya lo dicen las medias de tiros y puntos. Las lesiones: la
lista de 1x2 solo cubre ~20 jugadores por equipo y el mercado ya descuenta
las bajas.
