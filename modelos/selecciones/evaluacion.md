# Evaluación de los pronósticos de selecciones

71 partidos jugados con pronóstico previo (de 80 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 63 | 0.1970 | 0.1807 | -1.71s | 0.00 | 0.00 (aprendido) |
| X | 63 | 0.2252 | 0.2191 | -1.08s | 0.00 | 0.00 (aprendido) |
| 2 | 63 | 0.1838 | 0.1699 | -2.14s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 63 | 0.2394 | 0.2325 | -1.02s | 0.00 | 0.00 (aprendido) |
| btts | 63 | 0.2501 | 0.2459 | -0.83s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 63 | 0.2015 | 0.1995 | -0.32s | 0.10 | 0.10 (aprendido) |
| mas_3.5 | 63 | 0.1873 | 0.1833 | -0.65s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 63 | 0.2689 | 0.2534 | -1.13s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 63 | 0.2454 | 0.2346 | -0.84s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 60 | 0.2685 | 0.2418 | -1.24s | 0.05 | 0.05 (aprendido) |
| tarjetas_mas_4.5 | 59 | 0.2488 | 0.2419 | -0.42s | 0.30 | 0.30 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 37 | 0.1952 | 0.1704 | -2.80s | 0.00 | 0.00 (aprendido) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

