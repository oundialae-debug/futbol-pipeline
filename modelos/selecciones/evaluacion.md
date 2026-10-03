# Evaluación de los pronósticos de selecciones

54 partidos jugados con pronóstico previo (de 62 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 46 | 0.1937 | 0.1857 | -0.70s | 0.00 | 0.00 (aprendido) |
| X | 46 | 0.2204 | 0.2166 | -0.52s | 0.00 | 0.00 (aprendido) |
| 2 | 46 | 0.2002 | 0.1890 | -1.32s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 46 | 0.2389 | 0.2323 | -0.76s | 0.00 | 0.00 (aprendido) |
| btts | 46 | 0.2516 | 0.2451 | -1.02s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 46 | 0.1727 | 0.1703 | -0.29s | 0.10 | 0.10 (aprendido) |
| mas_3.5 | 46 | 0.1989 | 0.1900 | -1.17s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 46 | 0.2758 | 0.2560 | -1.17s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 46 | 0.2443 | 0.2284 | -1.00s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 43 | 0.2484 | 0.2484 | -0.00s | 0.50 | 0.50 (aprendido) |
| tarjetas_mas_4.5 | 42 | 0.2346 | 0.2308 | -0.19s | 0.40 | 0.40 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 26 | 0.2164 | 0.1979 | -1.60s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

