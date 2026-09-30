# Evaluación de los pronósticos de selecciones

28 partidos jugados con pronóstico previo (de 36 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 20 | 0.1744 | 0.1448 | -2.09s | 0.00 | 0.50 (inicial) |
| X | 20 | 0.2244 | 0.2079 | -1.69s | 0.00 | 0.50 (inicial) |
| 2 | 20 | 0.2368 | 0.2270 | -0.63s | 0.00 | 0.50 (inicial) |
| mas_2.5 | 20 | 0.2357 | 0.2153 | -1.55s | 0.00 | 0.00 (inicial) |
| btts | 20 | 0.2468 | 0.2304 | -1.82s | 0.00 | 0.50 (inicial) |
| mas_1.5 | 20 | 0.2373 | 0.2154 | -1.51s | 0.00 | 0.00 (inicial) |
| mas_3.5 | 20 | 0.2252 | 0.2058 | -1.70s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 20 | 0.2741 | 0.2677 | -0.22s | 0.25 | 0.00 (inicial) |
| corners_mas_9.5 | 20 | 0.2047 | 0.1986 | -0.23s | 0.25 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 20 | 0.2481 | 0.2371 | -0.27s | 0.35 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 20 | 0.1967 | 0.1977 | +0.03s | 0.50 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 8 | 0.3046 | 0.2700 | -1.13s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

