# Evaluación de los pronósticos de selecciones

80 partidos jugados con pronóstico previo (de 114 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 72 | 0.1873 | 0.1738 | -1.60s | 0.00 | 0.00 (aprendido) |
| X | 72 | 0.2094 | 0.2046 | -0.96s | 0.00 | 0.00 (aprendido) |
| 2 | 72 | 0.1855 | 0.1753 | -1.73s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 72 | 0.2298 | 0.2245 | -0.88s | 0.00 | 0.00 (aprendido) |
| btts | 72 | 0.2483 | 0.2465 | -0.37s | 0.05 | 0.05 (aprendido) |
| mas_1.5 | 72 | 0.1942 | 0.1935 | -0.13s | 0.35 | 0.35 (aprendido) |
| mas_3.5 | 72 | 0.1840 | 0.1830 | -0.19s | 0.30 | 0.30 (aprendido) |
| corners_mas_8.5 | 72 | 0.2718 | 0.2512 | -1.65s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 72 | 0.2467 | 0.2352 | -0.97s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 69 | 0.2655 | 0.2398 | -1.32s | 0.05 | 0.05 (aprendido) |
| tarjetas_mas_4.5 | 68 | 0.2541 | 0.2478 | -0.41s | 0.30 | 0.30 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 45 | 0.1882 | 0.1704 | -2.30s | 0.00 | 0.00 (aprendido) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

