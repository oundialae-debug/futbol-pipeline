# Evaluación de los pronósticos de selecciones

7 partidos jugados con pronóstico previo (de 18 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 7 | 0.1364 | 0.0926 | -2.01s | 0.00 | 0.50 (inicial) |
| X | 7 | 0.1866 | 0.1628 | -1.16s | 0.00 | 0.50 (inicial) |
| 2 | 7 | 0.1116 | 0.1319 | +1.03s | 1.00 | 0.50 (inicial) |
| mas_2.5 | 7 | 0.2023 | 0.1937 | -0.34s | 0.00 | 0.00 (inicial) |
| btts | 7 | 0.2367 | 0.2253 | -0.56s | 0.00 | 0.50 (inicial) |
| mas_1.5 | 7 | 0.1115 | 0.0997 | -0.35s | 0.00 | 0.00 (inicial) |
| mas_3.5 | 7 | 0.2246 | 0.1988 | -1.77s | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 7 | 0.3140 | 0.2740 | -0.61s | 0.00 | 0.00 (inicial) |
| corners_mas_9.5 | 7 | 0.2131 | 0.1800 | -0.53s | 0.00 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 7 | 0.1631 | 0.1789 | +0.25s | 0.70 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 7 | 0.0970 | 0.1167 | +0.39s | 0.85 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |
| sin_empate_local | 0 | - | - | - | - | 0.50 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

