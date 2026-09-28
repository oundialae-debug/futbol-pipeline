# Evaluación de los pronósticos de selecciones

18 partidos jugados con pronóstico previo (de 28 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 18 | 0.1720 | 0.1340 | -2.66s | 0.00 | 0.50 (inicial) |
| X | 18 | 0.1858 | 0.1730 | -1.28s | 0.00 | 0.50 (inicial) |
| 2 | 18 | 0.2446 | 0.2442 | -0.03s | 0.45 | 0.50 (inicial) |
| mas_2.5 | 18 | 0.2393 | 0.2196 | -1.34s | 0.00 | 0.00 (inicial) |
| btts | 18 | 0.2429 | 0.2276 | -1.53s | 0.00 | 0.50 (inicial) |
| mas_1.5 | 18 | 0.2270 | 0.2032 | -1.52s | 0.00 | 0.00 (inicial) |
| mas_3.5 | 18 | 0.2438 | 0.2227 | -1.68s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 18 | 0.2848 | 0.2721 | -0.40s | 0.05 | 0.00 (inicial) |
| corners_mas_9.5 | 18 | 0.2068 | 0.1964 | -0.35s | 0.15 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 18 | 0.2512 | 0.2286 | -0.53s | 0.20 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 18 | 0.2123 | 0.2033 | -0.27s | 0.30 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 8 | 0.3046 | 0.2700 | -1.13s | 0.00 | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

