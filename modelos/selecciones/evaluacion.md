# Evaluación de los pronósticos de selecciones

2 partidos jugados con pronóstico previo (de 18 pronosticados). Se toma el último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso se aprende con 30 partidos o más.

| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |
|---|---|---|---|---|---|---|
| 1 | 2 | 0.0504 | 0.0654 | +nans | 1.00 | 0.50 (inicial) |
| X | 2 | 0.0494 | 0.0732 | +nans | 1.00 | 0.50 (inicial) |
| 2 | 2 | 0.1996 | 0.2770 | +nans | 1.00 | 0.50 (inicial) |
| mas_2.5 | 2 | 0.1724 | 0.2173 | +nans | 1.00 | 0.00 (inicial) |
| btts | 2 | 0.1784 | 0.1868 | +nans | 1.00 | 0.50 (inicial) |
| mas_1.5 | 2 | 0.0389 | 0.0586 | +nans | 1.00 | 0.00 (inicial) |
| mas_3.5 | 2 | 0.3379 | 0.2651 | +nans | 0.00 | 0.00 (inicial) |
| corners_mas_8.5 | 2 | 0.3008 | 0.2735 | +nans | 0.00 | 0.00 (inicial) |
| corners_mas_9.5 | 2 | 0.1804 | 0.2105 | +nans | 1.00 | 0.00 (inicial) |
| tarjetas_mas_3.5 | 2 | 0.0484 | 0.2289 | +nans | 1.00 | 0.00 (inicial) |
| tarjetas_mas_4.5 | 2 | 0.0155 | 0.0920 | +nans | 1.00 | 0.00 (inicial) |
| primero_local | 0 | - | - | - | - | 0.00 (inicial) |

Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta 30. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.

