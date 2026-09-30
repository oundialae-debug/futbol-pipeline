# Registro en papel: modelo de ambos marcan (desde el 27/09/2026)

Cada pronóstico se apunta ANTES del partido; aquí se cruza con lo que pasó (el último pronóstico antes del pitido). Es la prueba limpia del modelo.

**Reglas fijadas el 29/09/2026, antes de ver resultados:** el juez principal es el Brier y el log loss sobre TODOS los partidos, contra el ambos marcan real (mediana de casas sin margen), emparejado partido a partido. Primer punto de control a los 400 partidos. Apuesta en papel (1 unidad) solo si el VE supera el 8%. No se toca el modelo antes del control.

**Partidos jugados: 4** (pendientes 0).

## Juez principal: todos los partidos contra el ambos marcan real

| modelo | partidos | Brier modelo | Brier mercado | sigmas Brier | log loss modelo | log loss mercado | sigmas log loss |
|---|---|---|---|---|---|---|---|
| oficial | 4 | 0.2507 | 0.2408 | -0.63s | 0.6945 | 0.6747 | -0.62s |

Punto de control: 4 de 400 partidos. Hasta entonces las sigmas son orientativas (hace falta +2s en Brier Y log loss para decir que un modelo bate al mercado).

| mercado | acierto modelo | acierto mercado | Brier modelo | Brier mercado |
|---|---|---|---|---|
| ambos marcan | 50% | 75% | 0.251 | 0.241 |
| más de 2.5 | 75% | 75% | 0.224 | 0.207 |
| 1X2 | 100% | 100% | - | - |

**Apuestas de ambos marcan (VE > 8%):** 0, ganadas 0, beneficio +0.00 unidades (+0.0% por apuesta). Solo como referencia, con VE > 0: 1 apuestas, -1.00 unidades.

| saque | partido | resultado | ambos (modelo/mercado) | apuesta | cuota | beneficio |
|---|---|---|---|---|---|---|
| 2026-09-27 16:30 | Eibar - Las Palmas | 3-2 | 54% / 54% | - | 1.73 |  |
| 2026-09-27 16:30 | Burgos - Eldense | 1-0 | 53% / 48% | - | 1.93 |  |
| 2026-09-27 19:00 | Oviedo - Sporting Gijón | 2-0 | 46% / 45% | - | 1.70 |  |
| 2026-09-28 18:30 | Leganes - Castellón | 0-2 | 55% / 56% | - | 1.65 |  |
