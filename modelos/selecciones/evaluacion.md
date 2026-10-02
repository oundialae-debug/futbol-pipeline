# Evaluación de los pronósticos de selecciones

39 partidos jugados con pronóstico previo (de 54 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 31 | 0.1976 | 0.1915 | -0.38s | 0.05 | 0.05 (aprendido) |
| X | 31 | 0.2482 | 0.2425 | -0.53s | 0.00 | 0.00 (aprendido) |
| 2 | 31 | 0.2370 | 0.2154 | -1.83s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 31 | 0.2429 | 0.2366 | -0.55s | 0.00 | 0.00 (aprendido) |
| btts | 31 | 0.2479 | 0.2367 | -1.38s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 31 | 0.2024 | 0.1972 | -0.44s | 0.00 | 0.00 (aprendido) |
| mas_3.5 | 31 | 0.2186 | 0.2075 | -1.25s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 31 | 0.2633 | 0.2590 | -0.20s | 0.35 | 0.35 (aprendido) |
| corners_mas_9.5 | 31 | 0.2099 | 0.2112 | +0.07s | 0.55 | 0.55 (aprendido) |
| tarjetas_mas_3.5 | 31 | 0.2400 | 0.2551 | +0.48s | 0.75 | 0.75 (aprendido) |
| tarjetas_mas_4.5 | 31 | 0.1904 | 0.2077 | +0.78s | 0.95 | 0.95 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 14 | 0.2980 | 0.2621 | -1.85s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

