# Evaluación de los pronósticos de selecciones

0 partidos jugados con pronóstico previo (de 0 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 0 | - | - | - | - | 0.50 (inicial) |
| X | 0 | - | - | - | - | 0.50 (inicial) |
| 2 | 0 | - | - | - | - | 0.50 (inicial) |
| mas_2.5 | 0 | - | - | - | - | 0.00 (inicial) |
| btts | 0 | - | - | - | - | 0.50 (inicial) |
| mas_1.5 | 0 | - | - | - | - | 0.00 (inicial) |
| mas_3.5 | 0 | - | - | - | - | 0.00 (inicial) |
| corners_mas_8.5 | 0 | - | - | - | - | 0.00 (inicial) |
| corners_mas_9.5 | 0 | - | - | - | - | 0.00 (inicial) |
| tarjetas_mas_3.5 | 0 | - | - | - | - | 0.00 (inicial) |
| tarjetas_mas_4.5 | 0 | - | - | - | - | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

