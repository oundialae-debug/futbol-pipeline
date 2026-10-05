# Registro en papel: modelo de ambos marcan (desde el 27/09/2026)

Cada pronóstico se apunta ANTES del partido; aquí se cruza con lo que pasó (el último pronóstico antes del pitido). Es la prueba limpia del modelo.

**Reglas fijadas el 29/09/2026, antes de ver resultados:** el juez principal es el Brier y el log loss sobre TODOS los partidos, contra el ambos marcan real (mediana de casas sin margen), emparejado partido a partido. Primer punto de control a los 400 partidos. Apuesta en papel (1 unidad) solo si el VE supera el 8%. No se toca el modelo antes del control.

**Partidos jugados: 12** (pendientes 1).

## Juez principal: todos los partidos contra el ambos marcan real

| modelo | partidos | Brier modelo | Brier mercado | sigmas Brier | log loss modelo | log loss mercado | sigmas log loss |
|---|---|---|---|---|---|---|---|
| oficial | 12 | 0.2367 | 0.2454 | +0.78s | 0.6663 | 0.6840 | +0.79s |
| solo precio (comparación) | 8 | 0.2396 | 0.2478 | +0.94s | 0.6721 | 0.6887 | +0.94s |

Punto de control: 12 de 400 partidos. Hasta entonces las sigmas son orientativas (hace falta +2s en Brier Y log loss para decir que un modelo bate al mercado).

| mercado | acierto modelo | acierto mercado | Brier modelo | Brier mercado |
|---|---|---|---|---|
| ambos marcan | 58% | 58% | 0.237 | 0.245 |
| más de 2.5 | 42% | 42% | 0.282 | 0.272 |
| 1X2 | 58% | 58% | - | - |

**Apuestas de ambos marcan (VE > 8%):** 0, ganadas 0, beneficio +0.00 unidades (+0.0% por apuesta). Solo como referencia, con VE > 0: 4 apuestas, -0.44 unidades.

| saque | partido | resultado | ambos (modelo/mercado) | apuesta | cuota | beneficio |
|---|---|---|---|---|---|---|
| 2026-09-27 16:30 | Eibar - Las Palmas | 3-2 | 54% / 54% | - | 1.73 |  |
| 2026-09-27 16:30 | Burgos - Eldense | 1-0 | 53% / 48% | - | 1.93 |  |
| 2026-09-27 19:00 | Oviedo - Sporting Gijón | 2-0 | 46% / 45% | - | 1.70 |  |
| 2026-09-28 18:30 | Leganes - Castellón | 0-2 | 55% / 56% | - | 1.65 |  |
| 2026-10-02 18:30 | Eldense - Oviedo | 4-1 | 47% / 46% | - | 1.73 |  |
| 2026-10-03 12:00 | Albacete - Eibar | 1-3 | 54% / 55% | - | 1.69 |  |
| 2026-10-03 14:15 | Almería - Burgos | 2-1 | 52% / 49% | - | 1.90 |  |
| 2026-10-03 16:30 | Sabadell - FC Andorra | 0-0 | 57% / 51% | - | 1.80 |  |
| 2026-10-03 16:30 | Cadiz - Leganes | 4-0 | 43% / 49% | - | 1.81 |  |
| 2026-10-04 16:30 | Castellón - AD Ceuta FC | 1-1 | 58% / 55% | - | 1.68 |  |
| 2026-10-04 16:30 | Las Palmas - Valladolid | 2-2 | 61% / 53% | - | 1.75 |  |
| 2026-10-04 19:00 | Girona - Mallorca | 0-0 | 53% / 55% | - | 1.69 |  |
