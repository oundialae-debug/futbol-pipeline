# Más de 2.5 goles -- carpeta propia (24/09/2026)

Mismo patrón que `modelos/ambos_marcan/`: todo lo necesario para trabajar
SOLO el mercado Más/Menos 2.5 goles. Scripts con rutas relativas: ejecutar
desde ESTA carpeta (`cd modelos/mas_2_5 && python3 scripts/...`).

- `scripts/rasgos.py`, `modelo_xgboost.py`, `evaluar_mercados.py`: copia
  del repo padre a 24/09 (Elo, tabla y las referencias salen de aquí).
- `scripts/rasgos_mas25.py`: **nuevo**, las variables diseñadas por el
  usuario (ver abajo) y su comprobación de fuga.
- `scripts/seleccion_combinaciones.py`: las 128 combinaciones + prueba final.
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

## Resultado (seleccion_combinaciones.py, 24/09/2026)

Protocolo: 2 núcleos (`base_cf` / `base_clasica` sin amarillas) x 64
combinaciones de los 6 grupos = 128 configs, 5 semillas. Partidos fijos
1.916 (2025/26+, con alineaciones y las dos bases completas). Selección
sobre 356 (28/02-23/04/2026), entrenando con 3.258 filas (incluye 2024/25).
Prueba final UNA vez sobre 490 (24/04-20/09/2026), 169 con cuota.

**En el tramo de selección, la base casa/fuera gana claro:** las 16 mejores
combinaciones de 128 llevan todas `base_cf`. Presencia en esas 16: tabla y
h2h_reciente 13, cp_ataque 11, elo 10, cp_minutos 9, **cp_defensa solo 2**.
Elegido: `base_cf+elo+tabla+cp_ataque+h2h_reciente` (84 rasgos).

**En la prueba final limpia, NO se sostiene:**

| modelo | Brier | elegido vs este | vs media | vs mercado | acierto |
|---|---|---|---|---|---|
| ELEGIDO | 0.4787 | -- | +3.22% | -1.55s | 63.3% |
| todo lo pedido (base_cf + los 6) | 0.4816 | +1.35s | +2.65% | -1.89s | 63.9% |
| base_cf+elo | 0.4797 | +0.27s | +3.02% | -1.14s | 62.7% |
| base_clasica+elo | 0.4741 | **-0.74s** | +4.17% | -1.45s | 59.2% |
| producción repo padre (99) | 0.4737 | **-0.78s** | +4.23% | -1.62s | 62.7% |
| mercado | 0.4397 | | | | 69.8% |

- El elegido queda por DEBAJO de la base clásica y de la producción del
  padre (-0.74s / -0.78s: dentro del ruido, pero en contra). La ventaja
  de `base_cf` en selección era, sobre todo, selección entre 128.
- Meterlo todo lo pedido empeora (+1.35s a favor del elegido): mismo
  patrón de todo el proyecto, más columnas con las mismas filas = sobreajuste.
- Por tramo: final 2025/26 +1.36% sobre la media, inicio 2026/27 +5.78%
  (2024/25 en el entrenamiento ayuda al arranque, igual que en ambos_marcan).
- **Contra el mercado todos pierden** (-1.14s a -1.89s). El elegido: -1.55s,
  peor que el mercado en el 95% de los bootstraps; quitando sus 10 mejores
  partidos, -3.38s. El mercado acierta el 69.8%; el mejor modelo, el 63.9%.

**No hay combinación ganadora.** Ni contra la base clásica, ni contra el
mercado. `PRODUCCION` (el elegido) y `ALTERNATIVA` (base_clasica+elo) quedan
congelados en `rasgos_mas25.py`. Siguiente paso honesto: juzgar los dos
SOLO con partidos jugados desde el 25/09/2026, sin volver a elegir.

## Qué no repetir

- No reabrir "casa/fuera" como mejora sin muestra nueva: ya ganó en selección
  y perdió en prueba limpia (en ambos_marcan, localía también empeoraba).
- `cp_defensa` (porterías a cero) casi no aparece entre las mejores: la
  porterías a cero de un jugador es sobre todo la del equipo, que ya está en
  goles encajados de `base_cf`. Probar el `cleanSheets` de la API solo si se
  confirma que viene para no-porteros.
- Cualquier variable nueva: más columnas con ~3.600 filas de entrenamiento
  ya se sabe que resta.
