# Evaluación de los pronósticos de selecciones

70 partidos jugados con pronóstico previo (de 80 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 62 | 0.1979 | 0.1814 | -1.70s | 0.00 | 0.00 (aprendido) |
| X | 62 | 0.2210 | 0.2152 | -1.02s | 0.00 | 0.00 (aprendido) |
| 2 | 62 | 0.1851 | 0.1711 | -2.13s | 0.00 | 0.00 (aprendido) |
| mas_2.5 | 62 | 0.2363 | 0.2297 | -0.95s | 0.00 | 0.00 (aprendido) |
| btts | 62 | 0.2485 | 0.2449 | -0.71s | 0.00 | 0.00 (aprendido) |
| mas_1.5 | 62 | 0.2023 | 0.2004 | -0.30s | 0.10 | 0.10 (aprendido) |
| mas_3.5 | 62 | 0.1788 | 0.1756 | -0.51s | 0.00 | 0.00 (aprendido) |
| corners_mas_8.5 | 62 | 0.2714 | 0.2541 | -1.26s | 0.00 | 0.00 (aprendido) |
| corners_mas_9.5 | 62 | 0.2462 | 0.2330 | -1.02s | 0.00 | 0.00 (aprendido) |
| tarjetas_mas_3.5 | 59 | 0.2658 | 0.2432 | -1.05s | 0.10 | 0.10 (aprendido) |
| tarjetas_mas_4.5 | 58 | 0.2426 | 0.2403 | -0.14s | 0.45 | 0.45 (aprendido) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 37 | 0.1952 | 0.1704 | -2.80s | 0.00 | 0.00 (aprendido) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

