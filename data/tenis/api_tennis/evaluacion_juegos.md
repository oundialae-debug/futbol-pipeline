# Más/menos juegos en directo: apuestas en papel

Partidos acabados con cuota de juegos en el registro: **17**. Una apuesta por partido (se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. Con menos de 20 apuestas el número no significa nada.

| estrategia | apuestas | aciertos | beneficio medio | sigmas |
|---|---|---|---|---|
| **señal: vigilar el menos** | 5 | 100% | +64.4% | +7.22 |
| control: siempre el menos (1ª pasada) | 17 | 76% | +41.8% | +2.10 |
| control: siempre el más (1ª pasada) | 17 | 24% | -52.8% | -2.44 |

Brier del 'más' en la línea principal (1ª pasada): modelo 0.2973, mercado 0.2564 (menor es mejor). El modelo da al más +35.7% sobre lo que pasa de verdad.

## Señales

| partido | línea | cuota menos | juegos | resultado |
|---|---|---|---|---|
| Challenger Mouilleron-Le-Captif: L. Broady vs D. Stricker | 26.5 | 1.53 | 26 | gana |
| WTA 1000 Beijing: T. Preston vs T. Korpatsch | 21.5 | 1.53 | 21 | gana |
| WTA 125 Adana (Turkey): A. Ruzic vs J. Riera | 19.5 | 1.44 | 19 | gana |
| WTA 1000 Beijing: M. Hontama vs K. Boulter | 21.5 | 1.91 | 19 | gana |
| ITF M M15 Telavi 2 (Georgia): N. Rispoli vs S. Purtseladze | 25.5 | 1.80 | 16 | gana |

## Avisos del vigilante (lo que llega al móvil)

| lado | avisos resueltos | aciertos | beneficio medio (cuota API) | sigmas |
|---|---|---|---|---|
| (ninguno resuelto aún) | 0 | | | |

## Aprendizaje (recalibración del modelo)

Partidos resueltos: 17 (80 líneas). Activa: **no** (hace falta 30+ partidos y que mejore al modelo en partidos que no vio).
Brier (menor es mejor): modelo 0.2755, modelo con el saque de hoy 0.2755, casa 0.2375, recalibrado (validado por partidos) 0.1813. Sesgo del modelo hacia el más: +34.8%.
