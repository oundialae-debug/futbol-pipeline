# Evaluación de los pronósticos de selecciones

63 partidos jugados con pronóstico previo (de 80 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 55 | 0.1954 | 0.1789 | -1.59s | 0.00 | 0.00 (aprendido) |
| X | 55 | 0.2238 | 0.2170 | -1.07s | 0.00 | 0.00 (aprendido) |
| 2 | 55 | 0.1899 | 0.1762 | -1.86s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 55 | 0.2365 | 0.2278 | -1.14s | 0.00 | 0.00 (aprendido) |
| btts | 55 | 0.2494 | 0.2436 | -1.04s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 55 | 0.1857 | 0.1834 | -0.33s | 0.05 | 0.05 (aprendido) |
| mas_3.5 | 55 | 0.1801 | 0.1771 | -0.44s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 55 | 0.2715 | 0.2546 | -1.10s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 55 | 0.2452 | 0.2299 | -1.07s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 52 | 0.2625 | 0.2457 | -0.71s | 0.20 | 0.20 (aprendido) |
| tarjetas_mas_4.5 | 51 | 0.2479 | 0.2425 | -0.30s | 0.35 | 0.35 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 32 | 0.2000 | 0.1754 | -2.43s | 0.00 | 0.00 (aprendido) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

