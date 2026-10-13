# Registro en papel: modelo de ambos marcan (desde el 27/09/2026)

Cada pronóstico se apunta ANTES del partido; aquí se cruza con lo que pasó (el último pronóstico antes del pitido). Es la prueba limpia del modelo.

**Reglas fijadas el 29/09/2026, antes de ver resultados:** el juez principal es el Brier y el log loss sobre TODOS los partidos, contra el ambos marcan real (mediana de casas sin margen), emparejado partido a partido. Primer punto de control a los 400 partidos. Apuesta en papel (1 unidad) solo si el VE supera el 8%. No se toca el modelo antes del control.

**Partidos jugados: 63** (pendientes 9).

## Juez principal: todos los partidos contra el ambos marcan real

| modelo | partidos | Brier modelo | Brier mercado | sigmas Brier | log loss modelo | log loss mercado | sigmas log loss |
|---|---|---|---|---|---|---|---|
| oficial | 63 | 0.2324 | 0.2411 | +1.73s | 0.6576 | 0.6758 | +1.74s |
| solo precio (comparación) | 59 | 0.2384 | 0.2411 | +0.77s | 0.6708 | 0.6758 | +0.67s |

Punto de control: 63 de 400 partidos. Hasta entonces las sigmas son orientativas (hace falta +2s en Brier Y log loss para decir que un modelo bate al mercado).

| mercado | acierto modelo | acierto mercado | Brier modelo | Brier mercado |
|---|---|---|---|---|
| ambos marcan | 63% | 62% | 0.232 | 0.241 |
| más de 2.5 | 62% | 67% | 0.237 | 0.229 |
| 1X2 | 57% | 60% | - | - |

**Apuestas de ambos marcan (VE > 8%):** 1, ganadas 1, beneficio +1.02 unidades (+102.0% por apuesta). Solo como referencia, con VE > 0: 15 apuestas, +0.75 unidades.

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
| 2026-10-03 16:30 | Sabadell - FC Andorra | 0-0 | 57% / 51% | - | 1.80 |  |
| 2026-10-04 16:30 | Castellón - AD Ceuta FC | 1-1 | 58% / 55% | - | 1.68 |  |
| 2026-10-04 16:30 | Las Palmas - Valladolid | 2-2 | 61% / 53% | - | 1.75 |  |
| 2026-10-04 19:00 | Girona - Mallorca | 0-0 | 53% / 55% | - | 1.69 |  |
| 2026-10-05 18:30 | Cordoba - Tenerife | 3-2 | 55% / 56% | - | 1.68 |  |
| 2026-10-09 18:30 | Borussia Dortmund - Werder Bremen | 2-2 | 54% / 57% | - | 1.65 |  |
| 2026-10-09 18:45 | Lens - Lyon | 2-1 | 61% / 65% | - | 1.44 |  |
| 2026-10-09 19:00 | Malaga - Espanyol | 1-1 | 56% / 53% | - | 1.75 |  |
| 2026-10-10 11:30 | Arsenal - Leeds | 2-1 | 46% / 47% | - | 1.75 |  |
| 2026-10-10 13:00 | Genoa - Fiorentina | 2-1 | 54% / 52% | - | 1.79 |  |
| 2026-10-10 13:30 | FSV Mainz 05 - Bayer Leverkusen | 3-4 | 63% / 67% | - | 1.40 |  |
| 2026-10-10 13:30 | FC Augsburg - Bayern Munich | 2-2 | 62% / 65% | - | 1.45 |  |
| 2026-10-10 13:30 | Union Berlin - SV Elversberg | 1-0 | 65% / 64% | - | 1.47 |  |
| 2026-10-10 13:30 | 1899 Hoffenheim - Hamburger SV | 2-3 | 62% / 60% | - | 1.55 |  |
| 2026-10-10 13:30 | SC Paderborn 07 - VfB Stuttgart | 0-2 | 60% / 67% | - | 1.39 |  |
| 2026-10-10 14:00 | Sunderland - Brighton | 0-2 | 55% / 57% | - | 1.64 |  |
| 2026-10-10 14:00 | Ipswich - Fulham | 2-1 | 52% / 59% | - | 1.57 |  |
| 2026-10-10 14:00 | Aston Villa - Brentford | 2-2 | 67% / 61% | - | 1.53 |  |
| 2026-10-10 14:00 | Chelsea - Bournemouth | 5-1 | 65% / 61% | - | 1.53 |  |
| 2026-10-10 14:15 | Alavés - Atlético Madrid | 1-2 | 50% / 53% | - | 1.74 |  |
| 2026-10-10 14:15 | AD Ceuta FC - Sabadell | 1-2 | 45% / 52% | - | 1.92 |  |
| 2026-10-10 15:15 | Lille - LE Havre AC | 1-0 | 54% / 51% | - | 1.83 |  |
| 2026-10-10 16:00 | Inter - Parma | 3-0 | 51% / 45% | - | 2.10 |  |
| 2026-10-10 16:30 | Eldense - Cordoba | 2-1 | 66% / 61% | - | 1.51 |  |
| 2026-10-10 16:30 | Manchester United - Tottenham | 1-1 | 65% / 62% | - | 1.50 |  |
| 2026-10-10 16:30 | RB Leipzig - Eintracht Frankfurt | 6-0 | 67% / 70% | - | 1.35 |  |
| 2026-10-10 16:30 | Barcelona - Getafe | 3-0 | 44% / 42% | - | 1.62 |  |
| 2026-10-10 18:45 | Napoli - Frosinone | 3-0 | 59% / 58% | - | 1.61 |  |
| 2026-10-10 18:45 | Stade Brestois 29 - Angers | 5-1 | 59% / 58% | - | 1.62 |  |
| 2026-10-10 18:45 | Lorient - Paris FC | 1-0 | 49% / 53% | - | 2.00 |  |
| 2026-10-10 18:45 | Paris Saint Germain - Le Mans | 3-1 | 59% / 46% | si | 2.02 | +1.02 |
| 2026-10-10 18:45 | Monaco - Toulouse | 2-2 | 61% / 58% | - | 1.61 |  |
| 2026-10-10 19:00 | Celta de Vigo II - Real Sociedad B | 4-1 | 58% / 58% | - | 1.60 |  |
| 2026-10-10 19:00 | Real Madrid - Villarreal | 1-0 | 70% / 64% | - | 1.46 |  |
| 2026-10-11 10:30 | Como - AS Roma | 0-0 | 62% / 62% | - | 1.50 |  |
| 2026-10-11 12:00 | Elche - Celta de Vigo | 0-0 | 52% / 53% | - | 1.74 |  |
| 2026-10-11 12:00 | FC Andorra - Castellón | 1-0 | 53% / 62% | - | 1.50 |  |
| 2026-10-11 13:00 | Lazio - Monza | 3-1 | 53% / 50% | - | 1.87 |  |
| 2026-10-11 13:00 | Nice - Strasbourg | 2-1 | 65% / 60% | - | 1.56 |  |
| 2026-10-11 13:00 | Lecce - Bologna | 1-2 | 50% / 50% | - | 1.88 |  |
| 2026-10-11 13:00 | Crystal Palace - Nottingham Forest | 3-1 | 63% / 56% | - | 1.67 |  |
| 2026-10-11 13:00 | Hull City - Everton | 2-2 | 53% / 52% | - | 1.78 |  |
| 2026-10-11 13:30 | FC Koln - Borussia Mönchengladbach | 2-1 | 69% / 65% | - | 1.44 |  |
| 2026-10-11 14:15 | Almería - Leganes | 3-0 | 60% / 54% | - | 1.70 |  |
| 2026-10-11 14:15 | Real Sociedad - Deportivo La Coruña | 3-2 | 53% / 53% | - | 1.76 |  |
| 2026-10-11 15:15 | Rennes FC - Auxerre | 4-1 | 65% / 57% | - | 1.63 |  |
| 2026-10-11 15:30 | Liverpool - Manchester City | 0-3 | 59% / 62% | - | 1.51 |  |
| 2026-10-11 15:30 | SC Freiburg - FC Schalke 04 | 2-1 | 55% / 58% | - | 1.61 |  |
| 2026-10-11 16:00 | Sassuolo - AC Milan | 1-1 | 58% / 58% | - | 1.60 |  |
| 2026-10-11 16:30 | Mallorca - Las Palmas | 3-1 | 51% / 50% | - | 1.87 |  |
| 2026-10-11 16:30 | Real Betis - Osasuna | 5-2 | 56% / 53% | - | 1.78 |  |
| 2026-10-11 18:45 | Estac Troyes - Marseille | 0-2 | 60% / 61% | - | 1.52 |  |
| 2026-10-11 18:45 | Cagliari - Juventus | 1-1 | 49% / 46% | - | 1.73 |  |
| 2026-10-11 19:00 | Cadiz - Sporting Gijón | 0-1 | 52% / 49% | - | 1.91 |  |
| 2026-10-11 19:00 | Racing Santander - Valencia | 2-2 | 63% / 61% | - | 1.54 |  |
