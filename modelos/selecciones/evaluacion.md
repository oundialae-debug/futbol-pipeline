# Evaluación de los pronósticos de selecciones

57 partidos jugados con pronóstico previo (de 70 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 49 | 0.1971 | 0.1863 | -0.98s | 0.00 | 0.00 (aprendido) |
| X | 49 | 0.2220 | 0.2174 | -0.67s | 0.00 | 0.00 (aprendido) |
| 2 | 49 | 0.1962 | 0.1839 | -1.53s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 49 | 0.2337 | 0.2280 | -0.69s | 0.00 | 0.00 (aprendido) |
| btts | 49 | 0.2470 | 0.2411 | -0.98s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 49 | 0.1780 | 0.1766 | -0.18s | 0.25 | 0.25 (aprendido) |
| mas_3.5 | 49 | 0.1891 | 0.1813 | -1.08s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 49 | 0.2719 | 0.2561 | -0.95s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 49 | 0.2434 | 0.2288 | -0.94s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 46 | 0.2447 | 0.2455 | +0.03s | 0.50 | 0.50 (aprendido) |
| tarjetas_mas_4.5 | 45 | 0.2371 | 0.2324 | -0.24s | 0.40 | 0.40 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 28 | 0.2130 | 0.1914 | -1.96s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

