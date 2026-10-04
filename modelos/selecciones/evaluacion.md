# Evaluación de los pronósticos de selecciones

61 partidos jugados con pronóstico previo (de 70 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 53 | 0.1914 | 0.1792 | -1.18s | 0.00 | 0.00 (aprendido) |
| X | 53 | 0.2296 | 0.2231 | -0.99s | 0.00 | 0.00 (aprendido) |
| 2 | 53 | 0.1940 | 0.1816 | -1.64s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 53 | 0.2344 | 0.2284 | -0.79s | 0.00 | 0.00 (aprendido) |
| btts | 53 | 0.2494 | 0.2442 | -0.89s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 53 | 0.1893 | 0.1879 | -0.19s | 0.25 | 0.25 (aprendido) |
| mas_3.5 | 53 | 0.1838 | 0.1785 | -0.77s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 53 | 0.2759 | 0.2576 | -1.16s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 53 | 0.2445 | 0.2276 | -1.16s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 50 | 0.2566 | 0.2469 | -0.41s | 0.35 | 0.35 (aprendido) |
| tarjetas_mas_4.5 | 49 | 0.2486 | 0.2404 | -0.44s | 0.30 | 0.30 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 30 | 0.2033 | 0.1830 | -1.97s | 0.00 | 0.00 (aprendido) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

