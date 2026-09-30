# Modelo de puntos contra Elo y contra el cierre (ganador del partido)

Generado por `modelos/tenis/scripts/evaluar_puntos.py`. Ventana móvil: cada año se juzga
con una capa ajustada solo con los años anteriores. Log-loss: negativo = el primero es mejor.

| año | partidos | puntos - Elo | puntos - mercado | mezcla - mercado recalibrado | peso mercado / puntos en la mezcla |
|---|---|---|---|---|---|
| 2021 | 4571 | +0.0079 (+2.09) | +0.0276 (+7.12) | +0.0001 (+0.53) | +1.09 / -0.03 |
| 2022 | 4650 | +0.0027 (+0.75) | +0.0237 (+6.22) | -0.0000 (-0.04) | +1.09 / +0.00 |
| 2023 | 4869 | -0.0003 (-0.08) | +0.0231 (+6.56) | -0.0000 (-0.80) | +1.07 / +0.01 |
| 2024 | 4906 | +0.0025 (+0.75) | +0.0233 (+6.90) | +0.0000 (+0.40) | +1.05 / +0.02 |
| 2025 | 4697 | +0.0035 (+1.06) | +0.0264 (+7.34) | +0.0000 (+0.07) | +1.06 / +0.01 |
| 2026 | 3910 | -0.0019 (-0.50) | +0.0254 (+6.64) | +0.0000 (+0.32) | +1.05 / +0.01 |
| **2021-2026** | 27603 | +0.0025 (+1.72) | +0.0249 (+16.62) | +0.0000 (+0.52) | |

Acierto del ganador 2021-2026: puntos 67.0%, Elo 66.3%, mercado 68.2%.
