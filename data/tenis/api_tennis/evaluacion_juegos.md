# Más/menos juegos en directo: apuestas en papel

Partidos acabados con cuota de juegos en el registro: **133**. Una apuesta por partido (se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. Con menos de 20 apuestas el número no significa nada.

| estrategia | apuestas | aciertos | beneficio medio | sigmas |
|---|---|---|---|---|
| **señal: vigilar el menos** | 36 | 64% | +7.7% | +0.54 |
| control: siempre el menos (1ª pasada) | 133 | 58% | +5.7% | +0.73 |
| control: siempre el más (1ª pasada) | 133 | 42% | -20.8% | -2.57 |

Brier del 'más' en la línea principal (1ª pasada): modelo 0.2921, mercado 0.2496 (menor es mejor). El modelo da al más +21.5% sobre lo que pasa de verdad.

## Señales

| partido | línea | cuota menos | juegos | resultado |
|---|---|---|---|---|
| Challenger Mouilleron-Le-Captif: L. Broady vs D. Stricker | 26.5 | 1.53 | 26 | gana |
| ATP 500 Tokyo: L. Darderi vs C. Ruud | 25.5 | 2.00 | 22 | gana |
| ATP 500 Tokyo: J. Lehecka vs Z. Bergs | 31.5 | 1.80 | 31 | gana |
| ATP 500 Beijing: N. Borges vs N. Djokovic | 22.5 | 1.80 | 22 | gana |
| ATP 500 Beijing: I. Buse vs Q. Halys | 20.5 | 1.83 | 20 | gana |
| ATP 500 Beijing: A. De Minaur vs M. Navone | 22.5 | 1.73 | 21 | gana |
| ATP 500 Beijing: T. Griekspoor vs A. Rublev | 23.5 | 1.57 | 35 | pierde |
| WTA 1000 Beijing: A. Parks vs L. Zhu | 21.5 | 1.83 | 18 | gana |
| WTA 1000 Beijing: T. Preston vs T. Korpatsch | 21.5 | 1.53 | 21 | gana |
| WTA 125 Adana (Turkey): A. Ruzic vs J. Riera | 19.5 | 1.44 | 19 | gana |
| Challenger Porto: L. Potenza vs I. Montes-De La Torre | 17.5 | 1.36 | 17 | gana |
| Challenger Columbus: B. Shick vs M. Rottgering | 16.5 | 1.57 | 17 | pierde |
| WTA 125 Jingshan: A. Falei vs K. Sidorova | 22.5 | 1.91 | 33 | pierde |
| ATP 500 Tokyo: T. Fritz vs J. Munar | 33.5 | 1.61 | 32 | gana |
| WTA 1000 Beijing: H. Dart vs Y. Qu | 23.5 | 1.91 | 33 | pierde |
| WTA 1000 Beijing: Q. Zheng vs H. Shi | 25.5 | 1.83 | 31 | pierde |
| WTA 1000 Beijing: M. Hontama vs K. Boulter | 21.5 | 1.91 | 19 | gana |
| WTA 1000 Beijing: E. Jacquemot vs M. Frech | 21.5 | 1.91 | 31 | pierde |
| WTA 125 Jingshan: S. Lansere vs S. Costoulas | 16.5 | 2.62 | 19 | pierde |
| WTA 125 Jingshan: J. Bouzas Maneiro vs Y. Wang | 14.5 | 1.44 | 14 | gana |
| Challenger Porto: T. Samuel vs J. Kym | 27.5 | 1.44 | 26 | gana |
| ITF M M15 Telavi 2 (Georgia): N. Rispoli vs S. Purtseladze | 25.5 | 1.80 | 26 | pierde |
| ITF M M25 Slobozia (Romania): F. C. Jianu vs M. Todoran | 18.5 | 1.17 | 19 | pierde |
| Challenger Bari (Italy): L. Lokoli vs S. Pieri | 28.5 | 1.83 | 26 | gana |
| WTA 125 Adana (Turkey): C. Buyukakcay vs L. Stefanini | 31.5 | 2.62 | 31 | gana |
| Challenger Mouilleron-Le-Captif: L. Poullain vs R. Bertola | 31.5 | 1.83 | 30 | gana |
| Challenger Columbus: L. Staeheli vs A. Andrade | 22.5 | 1.36 | 22 | gana |
| ITF M M25 Darwin: J. Beale vs D. Pham | 16.5 | 1.57 | 24 | pierde |
| ATP 500 Tokyo: J. Faria vs A. Fery | 29.5 | 1.33 | 29 | gana |
| ITF M M25 Kigali: C. Denolly vs M. Plunger | 21.5 | 1.83 | 16 | gana |
| ITF M M25 Slobozia (Romania): F. J. Planinsek vs B. Zgola | 26.5 | 1.73 | 32 | pierde |
| ITF M M15 Luan 4: K. Ogura vs D. J. Kim | 26.5 | 2.75 | 31 | pierde |
| ITF M M15 Luan 4: Y. Taka vs I. Becroft | 22.5 | 1.83 | 17 | gana |
| ITF M M15 Baku 2 (Azerbaijan): J. Connel vs N. Jadoun | 21.5 | 1.01 | 21 | gana |
| ITF M M15 Sharm ElSheikh 11: F. Zakaria vs G. El Feky | 25.5 | 1.80 | 27 | pierde |
| ITF M M15 Sibenik: J. Nicod vs S. Seghetti | 22.5 | 1.83 | 15 | gana |

## Avisos del vigilante (lo que llega al móvil)

| lado | avisos resueltos | aciertos | beneficio medio (cuota API) | sigmas |
|---|---|---|---|---|
| menos | 103 | 65% | -0.5% | -0.07 |

## Previos (antes de empezar), línea principal de juegos y ganador

117 partidos. Juegos (más de la línea principal), Brier (menor es mejor): modelo 0.3013, modelo corregido con el historial 0.2630, casa 0.2510. Pasó el más en el 44%.
Ganador (117): acierto modelo 64%, casa 74%.

## Aprendizaje (recalibración del modelo)

Partidos resueltos: 133 (1013 líneas). Activa: **sí** (hace falta 30+ partidos y que mejore al modelo en partidos que no vio).
Brier (menor es mejor): modelo 0.2925, modelo con el saque de hoy 0.2803, casa 0.2416, recalibrado (validado por partidos) 0.2278. Sesgo del modelo hacia el más: +22.9%.
