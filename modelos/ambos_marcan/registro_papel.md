# Registro en papel: modelo de ambos marcan (desde el 27/09/2026)

Cada pronóstico se apunta ANTES del partido; aquí se cruza con lo que pasó (el último pronóstico antes del pitido). Es la prueba limpia del modelo.

**Reglas fijadas el 29/09/2026, antes de ver resultados:** el juez principal es el Brier y el log loss sobre TODOS los partidos, contra el ambos marcan real (mediana de casas sin margen), emparejado partido a partido. Primer punto de control a los 400 partidos. Apuesta en papel (1 unidad) solo si el VE supera el 8%. No se toca el modelo antes del control.

**Partidos jugados: 8** (pendientes 4).

## Juez principal: todos los partidos contra el ambos marcan real

| modelo | partidos | Brier modelo | Brier mercado | sigmas Brier | log loss modelo | log loss mercado | sigmas log loss |
|---|---|---|---|---|---|---|---|
| oficial | 8 | 0.2386 | 0.2440 | +0.47s | 0.6703 | 0.6812 | +0.47s |
| solo precio (comparación) | 4 | 0.2346 | 0.2473 | +1.29s | 0.6621 | 0.6877 | +1.30s |

Punto de control: 8 de 400 partidos. Hasta entonces las sigmas son orientativas (hace falta +2s en Brier Y log loss para decir que un modelo bate al mercado).

| mercado | acierto modelo | acierto mercado | Brier modelo | Brier mercado |
|---|---|---|---|---|
| ambos marcan | 62% | 62% | 0.239 | 0.244 |
| más de 2.5 | 38% | 38% | 0.270 | 0.255 |
| 1X2 | 88% | 88% | - | - |

**Apuestas de ambos marcan (VE > 8%):** 0, ganadas 0, beneficio +0.00 unidades (+0.0% por apuesta). Solo como referencia, con VE > 0: 2 apuestas, -0.19 unidades.

| saque | partido | resultado | ambos (modelo/mercado) | apuesta | cuota | beneficio |
|---|---|---|---|---|---|---|
| 2026-09-27 16:30 | Eibar - Las Palmas | 3-2 | 54% / 54% | - | 1.73 |  |
| 2026-09-27 16:30 | Burgos - Eldense | 1-0 | 53% / 48% | - | 1.93 |  |
| 2026-09-27 19:00 | Oviedo - Sporting Gijón | 2-0 | 46% / 45% | - | 1.70 |  |
| 2026-09-28 18:30 | Leganes - Castellón | 0-2 | 55% / 56% | - | 1.65 |  |
| 2026-10-02 18:30 | Eldense - Oviedo | 4-1 | 47% / 46% | - | 1.73 |  |
| 2026-10-03 12:00 | Albacete - Eibar | 1-3 | 54% / 55% | - | 1.69 |  |
| 2026-10-03 14:15 | Almería - Burgos | 2-1 | 52% / 49% | - | 1.90 |  |
| 2026-10-03 16:30 | Cadiz - Leganes | 4-0 | 43% / 49% | - | 1.81 |  |
