# Más/menos juegos en directo: apuestas en papel

Partidos acabados con cuota de juegos en el registro: **20**. Una apuesta por partido (se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. Con menos de 20 apuestas el número no significa nada.

| estrategia | apuestas | aciertos | beneficio medio | sigmas |
|---|---|---|---|---|
| **señal: vigilar el menos** | 6 | 83% | +37.0% | +1.30 |
| control: siempre el menos (1ª pasada) | 20 | 70% | +29.1% | +1.49 |
| control: siempre el más (1ª pasada) | 20 | 30% | -41.6% | -2.00 |

Brier del 'más' en la línea principal (1ª pasada): modelo 0.2913, mercado 0.2537 (menor es mejor). El modelo da al más +29.5% sobre lo que pasa de verdad.

## Señales

| partido | línea | cuota menos | juegos | resultado |
|---|---|---|---|---|
| Challenger Mouilleron-Le-Captif: L. Broady vs D. Stricker | 26.5 | 1.53 | 26 | gana |
| ATP 500 Beijing: N. Borges vs N. Djokovic | 22.5 | 1.80 | 22 | gana |
| WTA 1000 Beijing: T. Preston vs T. Korpatsch | 21.5 | 1.53 | 21 | gana |
| WTA 125 Adana (Turkey): A. Ruzic vs J. Riera | 19.5 | 1.44 | 19 | gana |
| WTA 1000 Beijing: M. Hontama vs K. Boulter | 21.5 | 1.91 | 19 | gana |
| ITF M M15 Telavi 2 (Georgia): N. Rispoli vs S. Purtseladze | 25.5 | 1.80 | 26 | pierde |

## Avisos del vigilante (lo que llega al móvil)

| lado | avisos resueltos | aciertos | beneficio medio (cuota API) | sigmas |
|---|---|---|---|---|
| menos | 2 | 100% | +53.5% | +15.08 |

## Aprendizaje (recalibración del modelo)

Partidos resueltos: 20 (105 líneas). Activa: **no** (hace falta 30+ partidos y que mejore al modelo en partidos que no vio).
Brier (menor es mejor): modelo 0.2755, modelo con el saque de hoy 0.2729, casa 0.2356, recalibrado (validado por partidos) 0.2094. Sesgo del modelo hacia el más: +29.3%.
