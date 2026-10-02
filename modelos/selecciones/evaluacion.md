# Evaluación de los pronósticos de selecciones

36 partidos jugados con pronóstico previo (de 54 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 28 | 0.1925 | 0.1903 | -0.13s | 0.35 | 0.50 (inicial) |
| X | 28 | 0.2678 | 0.2601 | -0.66s | 0.00 | 0.50 (inicial) |
| 2 | 28 | 0.2247 | 0.2058 | -1.47s | 0.00 | 0.50 (inicial) |
| mas_2.5 | 28 | 0.2386 | 0.2305 | -0.68s | 0.00 | 0.00 (inicial) |
| btts | 28 | 0.2437 | 0.2311 | -1.42s | 0.00 | 0.50 (inicial) |
| mas_1.5 | 28 | 0.2149 | 0.2073 | -0.60s | 0.00 | 0.00 (inicial) |
| mas_3.5 | 28 | 0.2359 | 0.2233 | -1.31s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 28 | 0.2707 | 0.2606 | -0.43s | 0.10 | 0.00 (inicial) |
| corners_mas_9.5 | 28 | 0.2085 | 0.2027 | -0.28s | 0.25 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 28 | 0.2438 | 0.2433 | -0.01s | 0.50 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 28 | 0.2007 | 0.2101 | +0.39s | 0.75 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 11 | 0.2981 | 0.2682 | -1.33s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

