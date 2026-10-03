# Evaluación de los pronósticos de selecciones

46 partidos jugados con pronóstico previo (de 62 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 38 | 0.2028 | 0.1945 | -0.60s | 0.00 | 0.00 (aprendido) |
| X | 38 | 0.2566 | 0.2515 | -0.58s | 0.00 | 0.00 (aprendido) |
| 2 | 38 | 0.2249 | 0.2104 | -1.43s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 38 | 0.2477 | 0.2408 | -0.68s | 0.00 | 0.00 (aprendido) |
| btts | 38 | 0.2468 | 0.2402 | -0.90s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 38 | 0.1883 | 0.1835 | -0.50s | 0.00 | 0.00 (aprendido) |
| mas_3.5 | 38 | 0.2087 | 0.1966 | -1.36s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 38 | 0.2612 | 0.2555 | -0.31s | 0.25 | 0.25 (aprendido) |
| corners_mas_9.5 | 38 | 0.2152 | 0.2142 | -0.05s | 0.45 | 0.45 (aprendido) |
| tarjetas_mas_3.5 | 38 | 0.2411 | 0.2503 | +0.34s | 0.65 | 0.65 (aprendido) |
| tarjetas_mas_4.5 | 38 | 0.2067 | 0.2201 | +0.70s | 0.85 | 0.85 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 18 | 0.2724 | 0.2455 | -1.65s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

