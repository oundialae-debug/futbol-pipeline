# Más/menos juegos en directo: apuestas en papel

Partidos acabados con cuota de juegos en el registro: **33**. Una apuesta por partido (se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. Con menos de 20 apuestas el número no significa nada.

| estrategia | apuestas | aciertos | beneficio medio | sigmas |
|---|---|---|---|---|
| **señal: vigilar el menos** | 9 | 67% | +6.5% | +0.24 |
| control: siempre el menos (1ª pasada) | 33 | 67% | +24.1% | +1.54 |
| control: siempre el más (1ª pasada) | 33 | 33% | -35.8% | -2.21 |

Brier del 'más' en la línea principal (1ª pasada): modelo 0.3163, mercado 0.2572 (menor es mejor). El modelo da al más +30.1% sobre lo que pasa de verdad.

## Señales

| partido | línea | cuota menos | juegos | resultado |
|---|---|---|---|---|
| Challenger Mouilleron-Le-Captif: L. Broady vs D. Stricker | 26.5 | 1.53 | 26 | gana |
| ATP 500 Beijing: N. Borges vs N. Djokovic | 22.5 | 1.80 | 22 | gana |
| WTA 1000 Beijing: T. Preston vs T. Korpatsch | 21.5 | 1.53 | 21 | gana |
| WTA 125 Adana (Turkey): A. Ruzic vs J. Riera | 19.5 | 1.44 | 19 | gana |
| Challenger Porto: L. Potenza vs I. Montes-De La Torre | 17.5 | 1.36 | 17 | gana |
| Challenger Columbus: B. Shick vs M. Rottgering | 16.5 | 1.57 | 17 | pierde |
| WTA 1000 Beijing: M. Hontama vs K. Boulter | 21.5 | 1.91 | 19 | gana |
| WTA 1000 Beijing: E. Jacquemot vs M. Frech | 21.5 | 1.91 | 31 | pierde |
| ITF M M15 Telavi 2 (Georgia): N. Rispoli vs S. Purtseladze | 25.5 | 1.80 | 26 | pierde |

## Avisos del vigilante (lo que llega al móvil)

| lado | avisos resueltos | aciertos | beneficio medio (cuota API) | sigmas |
|---|---|---|---|---|
| menos | 9 | 78% | +15.1% | +0.69 |

## Previos (antes de empezar), línea principal de juegos y ganador

Ningún partido con previo ha terminado todavía.

## Aprendizaje (recalibración del modelo)

Partidos resueltos: 33 (198 líneas). Activa: **sí** (hace falta 30+ partidos y que mejore al modelo en partidos que no vio).
Brier (menor es mejor): modelo 0.3135, modelo con el saque de hoy 0.3037, casa 0.2432, recalibrado (validado por partidos) 0.2241. Sesgo del modelo hacia el más: +29.6%.
