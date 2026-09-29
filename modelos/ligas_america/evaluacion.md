# Ambos marcan y más/menos 2.5 en ARG, BRA y MEX (sin API)

Mes a mes desde 2024-01, entrenando cada mes con todo lo anterior. Brier (más bajo mejor) y sigmas del Brier emparejado partido a partido (positivo = mejor que la referencia). Fuente: football-data.co.uk (cierre del 1X2).

**No hay cuota histórica de ambos marcan ni de más/menos 2.5 en estas ligas**: aquí no se mide contra ESE mercado. 'poisson' es lo que el 1X2 del mercado implica para esos mercados, sin entrenar nada.


## ambos_marcan

| liga | n | tasa real | Brier base | Brier poisson | Brier mercado | Brier juego | Brier completo | Brier completo_sola | completo vs base | completo vs poisson | completo vs mercado | sola vs juntas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ARG | 1495 | 0.419 | 0.2438 | 0.2471 | 0.2442 | 0.2442 | 0.2425 | 0.2440 | +1.02s | +2.36s | +1.91s | -1.55s |
| BRA | 1037 | 0.527 | 0.2509 | 0.2626 | 0.2503 | 0.2522 | 0.2507 | 0.2541 | +0.07s | +4.23s | -0.44s | -2.11s |
| MEX | 934 | 0.571 | 0.2453 | 0.2533 | 0.2440 | 0.2466 | 0.2442 | 0.2473 | +0.60s | +2.95s | -0.13s | -2.03s |
| todas | 3466 | 0.492 | 0.2463 | 0.2534 | 0.2459 | 0.2473 | 0.2454 | 0.2479 | +0.97s | +5.51s | +0.83s | -3.29s |

## mas_2_5

| liga | n | tasa real | Brier base | Brier poisson | Brier mercado | Brier juego | Brier completo | Brier completo_sola | completo vs base | completo vs poisson | completo vs mercado | sola vs juntas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ARG | 1495 | 0.339 | 0.2248 | 0.2233 | 0.2224 | 0.2253 | 0.2219 | 0.2250 | +1.63s | +0.83s | +0.64s | -3.88s |
| BRA | 1037 | 0.480 | 0.2499 | 0.2575 | 0.2485 | 0.2520 | 0.2496 | 0.2513 | +0.13s | +3.52s | -1.19s | -1.11s |
| MEX | 934 | 0.547 | 0.2485 | 0.2509 | 0.2444 | 0.2484 | 0.2437 | 0.2447 | +1.82s | +2.25s | +0.61s | -0.67s |
| todas | 3466 | 0.437 | 0.2387 | 0.2410 | 0.2362 | 0.2395 | 0.2360 | 0.2382 | +2.10s | +3.72s | +0.21s | -2.98s |
