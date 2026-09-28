# Variables de clubes en el modelo de selecciones

Prueba hacia delante: 337 partidos desde 2025-10-01, cada fecha solo con los anteriores. Entreno desde ene-2025 (peso por recencia de 365 días). Sigmas emparejadas contra el modelo actual (+ = mejor; hace falta +2). Brier del 1X2 = suma de las tres.

Cobertura: once conocido en el 94% de los partidos de prueba; enfrentamiento previo entre las dos selecciones dentro de la ventana en 117 de 507 partidos.

| config | 1X2 | más de 2.5 | ambos marcan | sin empate | suma sigmas |
|---|---|---|---|---|---|
| actual | 0.5266 | 0.2466 | 0.2456 | 0.1440 | - |
| +fifa | 0.5089 (+2.60s) | 0.2404 (+3.21s) | 0.2441 (+0.73s) | 0.1383 (+1.26s) | +7.80 |
| +elo | 0.5112 (+2.39s) | 0.2407 (+3.06s) | 0.2446 (+0.50s) | 0.1391 (+1.16s) | +7.11 |
| +xi | 0.5244 (+0.66s) | 0.2472 (-0.35s) | 0.2456 (+0.09s) | 0.1459 (-0.85s) | -0.45 |
| +fifa+elo | 0.5094 (+2.48s) | 0.2404 (+3.09s) | 0.2444 (+0.56s) | 0.1385 (+1.20s) | +7.33 |
| +todas | 0.5055 (+2.85s) | 0.2409 (+2.26s) | 0.2443 (+0.58s) | 0.1391 (+0.99s) | +6.67 |
