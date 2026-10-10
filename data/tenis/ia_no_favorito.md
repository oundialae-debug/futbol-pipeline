# IA para el no favorito contra bet365 (tennis-data, por años: aprende con los anteriores)

24,859 partidos de prueba (2021-2025, ATP+WTA). Una apuesta por partido al no favorito, cuota de bet365 al cierre.

| regla | apuestas | aciertos | hace falta | beneficio | sigmas |
|---|---|---|---|---|---|
| siempre al no favorito (control) | 24859 | 30.9% | 34.2% | -11.2% | -11.93 |
| Pinnacle dice que bet365 paga de más (sin IA) | 3328 | 31.8% | 32.3% | -4.0% | -1.48 |
| IA: valor > 0% | 6294 | 35.7% | 36.0% | -1.6% | -0.90 |
| IA: valor > 3% | 4313 | 35.1% | 35.0% | -1.0% | -0.45 |
| IA: valor > 8% | 2455 | 33.3% | 33.3% | -3.4% | -1.12 |

IA con valor > 3%, año a año:

| año | apuestas | aciertos | hace falta | beneficio | sigmas |
|---|---|---|---|---|---|
| 2021 | 1303 | 31.3% | 33.9% | -10.5% | -2.68 |
| 2022 | 876 | 37.2% | 35.3% | +1.9% | +0.41 |
| 2023 | 661 | 33.6% | 35.2% | -1.7% | -0.26 |
| 2024 | 814 | 36.4% | 34.9% | +4.3% | +0.81 |
| 2025 | 659 | 39.5% | 36.7% | +7.9% | +1.40 |

Calibración de la IA en prueba (no favorito):

| la IA dice | pasa | bet365 dice | partidos |
|---|---|---|---|
| (0.0, 0.15] | 8.4% | 18.9% | 3679 |
| (0.15, 0.25] | 22.2% | 23.4% | 3932 |
| (0.25, 0.35] | 30.6% | 31.8% | 6991 |
| (0.35, 0.45] | 40.4% | 39.7% | 6694 |
| (0.45, 0.55] | 46.6% | 44.3% | 3330 |
