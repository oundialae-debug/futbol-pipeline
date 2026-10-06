# Separar a los jugadores: corrección del modelo de puntos (elegida en 2021-23, juzgada en 2024-26)

Al mejor de 3. k separa a los jugadores, c mueve el nivel de saque. Muestra de 3000 partidos por grupo y periodo.

| grupo | k | c | juegos de más (antes → después) | Brier 21,5 (antes → después) | acierto ganador (antes → después) | log-loss ganador |
|---|---|---|---|---|---|---|
| ATP challenger | 1.0 | -0.06 | +1.65 → +0.83 | 0.2614 → 0.2530 | 62.8% → 62.8% | 0.6514 → 0.6540 |
| ATP circuito | 1.0 | -0.04 | +1.38 → +0.64 | 0.2510 → 0.2451 | 63.3% → 63.3% | 0.6395 → 0.6419 |
| ATP itf | 1.0 | -0.04 | +1.33 → +0.56 | 0.2499 → 0.2439 | 64.7% → 64.7% | 0.6191 → 0.6206 |
| WTA challenger | 1.5 | -0.04 | +2.19 → +1.26 | 0.2587 → 0.2477 | 62.7% → 63.3% | 0.6250 → 0.6729 |
| WTA circuito | 1.25 | -0.04 | +1.73 → +1.00 | 0.2544 → 0.2476 | 66.3% → 66.6% | 0.5921 → 0.6097 |
| WTA itf | 2.0 | -0.06 | +3.95 → +2.72 | 0.2922 → 0.2745 | 41.9% → 42.1% | 0.6930 → 0.8387 |
