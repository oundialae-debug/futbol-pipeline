# Evaluación de los pronósticos de selecciones

3 partidos jugados con pronóstico previo (de 18 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 3 | 0.1349 | 0.1008 | -0.69s | 0.00 | 0.50 (inicial) |
| X | 3 | 0.2160 | 0.1998 | -0.40s | 0.00 | 0.50 (inicial) |
| 2 | 3 | 0.1451 | 0.2070 | +1.99s | 1.00 | 0.50 (inicial) |
| mas_2.5 | 3 | 0.1690 | 0.1795 | +0.20s | 1.00 | 0.00 (inicial) |
| btts | 3 | 0.2308 | 0.2429 | +0.52s | 1.00 | 0.50 (inicial) |
| mas_1.5 | 3 | 0.0627 | 0.0987 | +1.79s | 1.00 | 0.00 (inicial) |
| mas_3.5 | 3 | 0.2385 | 0.1851 | -2.38s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 3 | 0.3210 | 0.2698 | -1.81s | 0.00 | 0.00 (inicial) |
| corners_mas_9.5 | 3 | 0.1974 | 0.1941 | -0.09s | 0.00 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 3 | 0.1214 | 0.1982 | +0.74s | 1.00 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 3 | 0.0477 | 0.1306 | +11.59s | 1.00 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

