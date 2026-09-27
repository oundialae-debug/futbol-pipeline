# Sin empate (Draw No Bet): modelo propio contra el derivado del modelo de goles

Prueba hacia delante: 252 partidos SIN empate desde 2025-10-01, cada uno pronosticado solo con los anteriores (los empates no cuentan: en este mercado se devuelve la apuesta). Brier: más bajo es mejor. Sigmas emparejadas por partido; hace falta +2 para creérselo.

| modelo | Brier | acierto | contra el derivado | contra la tasa base |
|---|---|---|---|---|
| derivado del modelo de goles (P1/(P1+P2)) | 0.1418 | 79% | - | +9.59s |
| propio, ridge C=0.3 (control) | 0.1505 | 78% | -1.95s | +7.49s |
| propio, ridge C=1.0 (el elegido de antemano) | 0.1490 | 79% | -1.52s | +7.18s |
| propio, ridge C=3.0 (control) | 0.1531 | 81% | -1.59s | +6.16s |
| tasa base (sin empate, gana el de casa) | 0.2459 | 55% | -9.59s | - |

Por tramos de tiempo (Brier, propio elegido contra derivado):

| tramo | n | propio | derivado |
|---|---|---|---|
| 2025Q4 | 88 | 0.1014 | 0.0983 |
| 2026Q1 | 41 | 0.2016 | 0.1866 |
| 2026Q2 | 83 | 0.1814 | 0.1616 |
| 2026Q3 | 40 | 0.1326 | 0.1502 |
