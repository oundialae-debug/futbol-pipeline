# Evaluación de los pronósticos de selecciones

10 partidos jugados con pronóstico previo (de 18 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 10 | 0.1924 | 0.1360 | -2.41s | 0.00 | 0.50 (inicial) |
| X | 10 | 0.1443 | 0.1331 | -0.72s | 0.00 | 0.50 (inicial) |
| 2 | 10 | 0.2481 | 0.2499 | +0.08s | 0.70 | 0.50 (inicial) |
| mas_2.5 | 10 | 0.2343 | 0.2167 | -0.78s | 0.00 | 0.00 (inicial) |
| btts | 10 | 0.2402 | 0.2276 | -0.81s | 0.00 | 0.50 (inicial) |
| mas_1.5 | 10 | 0.1660 | 0.1483 | -0.69s | 0.00 | 0.00 (inicial) |
| mas_3.5 | 10 | 0.2037 | 0.1818 | -1.44s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 10 | 0.2774 | 0.2580 | -0.42s | 0.00 | 0.00 (inicial) |
| corners_mas_9.5 | 10 | 0.2034 | 0.1933 | -0.23s | 0.20 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 10 | 0.2379 | 0.2128 | -0.41s | 0.20 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 10 | 0.2150 | 0.1930 | -0.46s | 0.05 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 3 | 0.4724 | 0.3918 | -1.07s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

