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
