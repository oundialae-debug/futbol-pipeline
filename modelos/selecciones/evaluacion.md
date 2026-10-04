# Evaluación de los pronósticos de selecciones

62 partidos jugados con pronóstico previo (de 70 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 54 | 0.1936 | 0.1792 | -1.38s | 0.00 | 0.00 (aprendido) |
| X | 54 | 0.2264 | 0.2199 | -1.01s | 0.00 | 0.00 (aprendido) |
| 2 | 54 | 0.1923 | 0.1791 | -1.77s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 54 | 0.2331 | 0.2261 | -0.92s | 0.00 | 0.00 (aprendido) |
| btts | 54 | 0.2475 | 0.2420 | -0.97s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 54 | 0.1864 | 0.1848 | -0.23s | 0.20 | 0.20 (aprendido) |
| mas_3.5 | 54 | 0.1830 | 0.1793 | -0.52s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 54 | 0.2747 | 0.2559 | -1.21s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 54 | 0.2463 | 0.2287 | -1.23s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 51 | 0.2624 | 0.2457 | -0.69s | 0.25 | 0.25 (aprendido) |
| tarjetas_mas_4.5 | 50 | 0.2440 | 0.2386 | -0.30s | 0.35 | 0.35 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 31 | 0.2024 | 0.1795 | -2.23s | 0.00 | 0.00 (aprendido) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

