# Más/menos juegos en directo: apuestas en papel

Partidos acabados con cuota de juegos en el registro: **28**. Una apuesta por partido (se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. Con menos de 20 apuestas el número no significa nada.

| estrategia | apuestas | aciertos | beneficio medio | sigmas |
|---|---|---|---|---|
| **señal: vigilar el menos** | 8 | 75% | +19.8% | +0.74 |
| control: siempre el menos (1ª pasada) | 28 | 68% | +26.6% | +1.57 |
| control: siempre el más (1ª pasada) | 28 | 32% | -37.7% | -2.15 |

Brier del 'más' en la línea principal (1ª pasada): modelo 0.3250, mercado 0.2580 (menor es mejor). El modelo da al más +31.1% sobre lo que pasa de verdad.

## Señales

| partido | línea | cuota menos | juegos | resultado |
|---|---|---|---|---|
| Challenger Mouilleron-Le-Captif: L. Broady vs D. Stricker | 26.5 | 1.53 | 26 | gana |
| ATP 500 Beijing: N. Borges vs N. Djokovic | 22.5 | 1.80 | 22 | gana |
| WTA 1000 Beijing: T. Preston vs T. Korpatsch | 21.5 | 1.53 | 21 | gana |
| WTA 125 Adana (Turkey): A. Ruzic vs J. Riera | 19.5 | 1.44 | 19 | gana |
| Challenger Porto: L. Potenza vs I. Montes-De La Torre | 17.5 | 1.36 | 17 | gana |
| WTA 1000 Beijing: M. Hontama vs K. Boulter | 21.5 | 1.91 | 19 | gana |
| WTA 1000 Beijing: E. Jacquemot vs M. Frech | 21.5 | 1.91 | 31 | pierde |
| ITF M M15 Telavi 2 (Georgia): N. Rispoli vs S. Purtseladze | 25.5 | 1.80 | 26 | pierde |

## Avisos del vigilante (lo que llega al móvil)

| lado | avisos resueltos | aciertos | beneficio medio (cuota API) | sigmas |
|---|---|---|---|---|
| menos | 7 | 71% | +8.4% | +0.30 |

## Aprendizaje (recalibración del modelo)

Partidos resueltos: 28 (155 líneas). Activa: **no** (hace falta 30+ partidos y que mejore al modelo en partidos que no vio).
Brier (menor es mejor): modelo 0.3142, modelo con el saque de hoy 0.3019, casa 0.2408, recalibrado (validado por partidos) 0.2301. Sesgo del modelo hacia el más: +30.9%.
