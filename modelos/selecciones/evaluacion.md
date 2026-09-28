# Evaluación de los pronósticos de selecciones

13 partidos jugados con pronóstico previo (de 28 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 13 | 0.1771 | 0.1318 | -2.42s | 0.00 | 0.50 (inicial) |
| X | 13 | 0.1977 | 0.1825 | -1.15s | 0.00 | 0.50 (inicial) |
| 2 | 13 | 0.2362 | 0.2393 | +0.17s | 0.90 | 0.50 (inicial) |
| mas_2.5 | 13 | 0.2277 | 0.2148 | -0.64s | 0.00 | 0.00 (inicial) |
| btts | 13 | 0.2381 | 0.2287 | -0.70s | 0.00 | 0.50 (inicial) |
| mas_1.5 | 13 | 0.2097 | 0.1874 | -1.04s | 0.00 | 0.00 (inicial) |
| mas_3.5 | 13 | 0.1998 | 0.1894 | -0.67s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 13 | 0.2712 | 0.2605 | -0.29s | 0.10 | 0.00 (inicial) |
| corners_mas_9.5 | 13 | 0.2060 | 0.2015 | -0.13s | 0.35 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 13 | 0.2578 | 0.1987 | -1.19s | 0.00 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 13 | 0.2416 | 0.2007 | -0.98s | 0.00 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 4 | 0.4014 | 0.3481 | -0.89s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

