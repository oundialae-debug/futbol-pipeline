# Elo contra el cierre del mercado (ganador del partido)

Generado por `modelos/tenis/scripts/evaluar_elo.py`. Parámetros y mezcla elegidos SOLO con
2020-2023; 2024-2026 no se tocó para elegir nada. Log-loss: más bajo es mejor.
Diferencia = Elo - mercado; negativa = Elo mejor. Sigmas del error emparejado.

## ATP

tennis-data sin walkovers: 16533. Emparejados con el historial: 15966 con mercado (ganador al revés, fuera: 5; sin encontrar: 392).
Elegido con 2020-2023: c=250, peso superficie w=0.25. Mezcla: 1.121·logit(mercado) + -0.076·logit(Elo) (constante -0.010).

| tramo | referencia | partidos | log-loss Elo | log-loss mercado | Elo - mercado (sigmas) | mezcla - mercado (sigmas) | acierto Elo | acierto mercado |
|---|---|---|---|---|---|---|---|---|
| 2020-2023 (elección) | Pinnacle | 8648 | 0.6116 | 0.5826 | +0.0290 (+11.92) | -0.0003 (-1.21) | 65.8% | 68.1% |
| 2024-2025 (prueba) | Betfair | 75 | 0.4725 | 0.4573 | +0.0152 (+0.91) | -0.0024 (-0.94) | 81.3% | 78.7% |
| 2024-2025 (prueba) | Pinnacle | 4856 | 0.6133 | 0.5874 | +0.0259 (+8.50) | -0.0004 (-1.26) | 65.2% | 68.1% |
| 2026 (prueba) | Betfair | 1884 | 0.6150 | 0.5929 | +0.0221 (+4.59) | +0.0003 (+0.51) | 66.5% | 68.1% |
| 2026 (prueba) | Pinnacle | 65 | 0.6383 | 0.5915 | +0.0468 (+1.28) | -0.0035 (-1.44) | 66.2% | 70.8% |

Apuestas en la PRUEBA (2024-2026, retiradas incluidas), al lado con valor según el Elo, a la cuota de cierre de la referencia (Betfair sin comisión):

| regla | modelo | apuestas | rendimiento | sigmas |
|---|---|---|---|---|
| valor > 0% | Elo | 6394 | -3.72% | -1.94 |
| valor > 5% | Elo | 4875 | -3.89% | -1.64 |
| valor > 0% | mezcla | 1877 | +2.05% | +1.07 |
| valor > 5% | mezcla | 5 | -68.00% | -2.12 |

## WTA

tennis-data sin walkovers: 15411. Emparejados con el historial: 14732 con mercado (ganador al revés, fuera: 8; sin encontrar: 447).
Elegido con 2020-2023: c=350, peso superficie w=0.25. Mezcla: 1.205·logit(mercado) + -0.102·logit(Elo) (constante +0.004).

| tramo | referencia | partidos | log-loss Elo | log-loss mercado | Elo - mercado (sigmas) | mezcla - mercado (sigmas) | acierto Elo | acierto mercado |
|---|---|---|---|---|---|---|---|---|
| 2020-2023 (elección) | Pinnacle | 7650 | 0.6007 | 0.5828 | +0.0179 (+9.08) | -0.0009 (-1.91) | 67.2% | 68.5% |
| 2024-2025 (prueba) | Betfair | 83 | 0.5361 | 0.5314 | +0.0048 (+0.35) | +0.0027 (+0.44) | 75.9% | 73.5% |
| 2024-2025 (prueba) | Pinnacle | 4589 | 0.6082 | 0.5905 | +0.0178 (+7.19) | -0.0002 (-0.25) | 65.8% | 67.2% |
| 2026 (prueba) | Betfair | 1865 | 0.5939 | 0.5622 | +0.0317 (+5.16) | -0.0013 (-1.24) | 66.5% | 69.5% |
| 2026 (prueba) | Pinnacle | 96 | 0.6048 | 0.5740 | +0.0308 (+1.67) | -0.0045 (-1.08) | 69.8% | 72.9% |

Apuestas en la PRUEBA (2024-2026, retiradas incluidas), al lado con valor según el Elo, a la cuota de cierre de la referencia (Betfair sin comisión):

| regla | modelo | apuestas | rendimiento | sigmas |
|---|---|---|---|---|
| valor > 0% | Elo | 6003 | -6.27% | -3.45 |
| valor > 5% | Elo | 4333 | -7.72% | -3.37 |
| valor > 0% | mezcla | 3234 | +0.21% | +0.17 |
| valor > 5% | mezcla | 46 | +11.11% | +0.72 |

