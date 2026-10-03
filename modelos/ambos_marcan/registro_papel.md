# Registro en papel: modelo de ambos marcan (desde el 27/09/2026)

Cada pronóstico se apunta ANTES del partido; aquí se cruza con lo que pasó (el último pronóstico antes del pitido). Es la prueba limpia del modelo.

**Reglas fijadas el 29/09/2026, antes de ver resultados:** el juez principal es el Brier y el log loss sobre TODOS los partidos, contra el ambos marcan real (mediana de casas sin margen), emparejado partido a partido. Primer punto de control a los 400 partidos. Apuesta en papel (1 unidad) solo si el VE supera el 8%. No se toca el modelo antes del control.

**Partidos jugados: 5** (pendientes 4).

## Juez principal: todos los partidos contra el ambos marcan real

| modelo | partidos | Brier modelo | Brier mercado | sigmas Brier | log loss modelo | log loss mercado | sigmas log loss |
|---|---|---|---|---|---|---|---|
| oficial | 5 | 0.2577 | 0.2501 | -0.61s | 0.7086 | 0.6934 | -0.60s |
| solo precio (comparación) | 1 | 0.2716 | 0.2875 | +nans | 0.7365 | 0.7683 | +nans |

Punto de control: 5 de 400 partidos. Hasta entonces las sigmas son orientativas (hace falta +2s en Brier Y log loss para decir que un modelo bate al mercado).

| mercado | acierto modelo | acierto mercado | Brier modelo | Brier mercado |
|---|---|---|---|---|
| ambos marcan | 40% | 60% | 0.258 | 0.250 |
| más de 2.5 | 60% | 60% | 0.258 | 0.241 |
| 1X2 | 100% | 100% | - | - |

**Apuestas de ambos marcan (VE > 8%):** 0, ganadas 0, beneficio +0.00 unidades (+0.0% por apuesta). Solo como referencia, con VE > 0: 1 apuestas, -1.00 unidades.

| saque | partido | resultado | ambos (modelo/mercado) | apuesta | cuota | beneficio |
|---|---|---|---|---|---|---|
| 2026-09-27 16:30 | Eibar - Las Palmas | 3-2 | 54% / 54% | - | 1.73 |  |
| 2026-09-27 16:30 | Burgos - Eldense | 1-0 | 53% / 48% | - | 1.93 |  |
| 2026-09-27 19:00 | Oviedo - Sporting Gijón | 2-0 | 46% / 45% | - | 1.70 |  |
| 2026-09-28 18:30 | Leganes - Castellón | 0-2 | 55% / 56% | - | 1.65 |  |
| 2026-10-02 18:30 | Eldense - Oviedo | 4-1 | 47% / 46% | - | 1.73 |  |
