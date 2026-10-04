# Evaluación de los pronósticos de selecciones

55 partidos jugados con pronóstico previo (de 70 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 47 | 0.1986 | 0.1893 | -0.82s | 0.00 | 0.00 (aprendido) |
| X | 47 | 0.2178 | 0.2140 | -0.53s | 0.00 | 0.00 (aprendido) |
| 2 | 47 | 0.1983 | 0.1867 | -1.39s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 47 | 0.2357 | 0.2301 | -0.65s | 0.00 | 0.00 (aprendido) |
| btts | 47 | 0.2492 | 0.2439 | -0.84s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 47 | 0.1758 | 0.1747 | -0.14s | 0.30 | 0.30 (aprendido) |
| mas_3.5 | 47 | 0.1950 | 0.1867 | -1.11s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 47 | 0.2731 | 0.2552 | -1.07s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 47 | 0.2407 | 0.2262 | -0.93s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 44 | 0.2482 | 0.2466 | -0.06s | 0.45 | 0.45 (aprendido) |
| tarjetas_mas_4.5 | 43 | 0.2387 | 0.2336 | -0.26s | 0.35 | 0.35 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 27 | 0.2172 | 0.1971 | -1.78s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

