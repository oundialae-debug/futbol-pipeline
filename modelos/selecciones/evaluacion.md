# Evaluación de los pronósticos de selecciones

29 partidos jugados con pronóstico previo (de 46 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 21 | 0.1856 | 0.1736 | -0.54s | 0.00 | 0.50 (inicial) |
| X | 21 | 0.2412 | 0.2359 | -0.36s | 0.00 | 0.50 (inicial) |
| 2 | 21 | 0.2262 | 0.2162 | -0.68s | 0.00 | 0.50 (inicial) |
| mas_2.5 | 21 | 0.2309 | 0.2192 | -0.76s | 0.00 | 0.00 (inicial) |
| btts | 21 | 0.2403 | 0.2212 | -2.12s | 0.00 | 0.50 (inicial) |
| mas_1.5 | 21 | 0.2452 | 0.2329 | -0.73s | 0.00 | 0.00 (inicial) |
| mas_3.5 | 21 | 0.2159 | 0.2014 | -1.23s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 21 | 0.2812 | 0.2689 | -0.44s | 0.00 | 0.00 (inicial) |
| corners_mas_9.5 | 21 | 0.2085 | 0.1979 | -0.41s | 0.10 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 21 | 0.2567 | 0.2406 | -0.41s | 0.25 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 21 | 0.2166 | 0.2135 | -0.11s | 0.45 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 8 | 0.3046 | 0.2700 | -1.13s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

