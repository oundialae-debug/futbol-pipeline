# Más/menos juegos en directo: apuestas en papel

Partidos acabados con cuota de juegos en el registro: **36**. Una apuesta por partido (se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. Con menos de 20 apuestas el número no significa nada.

| estrategia | apuestas | aciertos | beneficio medio | sigmas |
|---|---|---|---|---|
| **señal: vigilar el menos** | 12 | 75% | +28.4% | +1.16 |
| control: siempre el menos (1ª pasada) | 36 | 61% | +13.8% | +0.89 |
| control: siempre el más (1ª pasada) | 36 | 39% | -25.7% | -1.62 |

Brier del 'más' en la línea principal (1ª pasada): modelo 0.2978, mercado 0.2570 (menor es mejor). El modelo da al más +25.1% sobre lo que pasa de verdad.

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
| WTA 125 Adana (Turkey): C. Buyukakcay vs L. Stefanini | 31.5 | 2.62 | 31 | gana |
| Challenger Mouilleron-Le-Captif: L. Poullain vs R. Bertola | 31.5 | 1.83 | 30 | gana |
| Challenger Columbus: L. Staeheli vs A. Andrade | 22.5 | 1.36 | 22 | gana |

## Avisos del vigilante (lo que llega al móvil)

| lado | avisos resueltos | aciertos | beneficio medio (cuota API) | sigmas |
|---|---|---|---|---|
| menos | 12 | 83% | +21.6% | +1.30 |

## Previos (antes de empezar), línea principal de juegos y ganador

2 partidos. Juegos (más de la línea principal), Brier (menor es mejor): modelo 0.4323, modelo corregido con el historial 0.3770, casa 0.2487. Pasó el más en el 50%.
Ganador (2): acierto modelo 0%, casa 50%.

## Aprendizaje (recalibración del modelo)

Partidos resueltos: 36 (234 líneas). Activa: **sí** (hace falta 30+ partidos y que mejore al modelo en partidos que no vio).
Brier (menor es mejor): modelo 0.3017, modelo con el saque de hoy 0.2950, casa 0.2438, recalibrado (validado por partidos) 0.2386. Sesgo del modelo hacia el más: +26.3%.
