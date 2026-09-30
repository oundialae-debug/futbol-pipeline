# Calibración del cierre de Pinnacle (ganador del partido)

Generado por `modelos/tenis/scripts/calibracion_cierre.py`. tennis-data 2020-2026.
Partidos completos: 26467 (ATP 13787, WTA 12680). Retiradas y otros aparte: 815. Walkovers fuera.
Margen medio de Pinnacle: ATP 2.60%, WTA 2.83%.

## Pendiente favorito-marginado (1 = calibrado, >1 = el favorito gana más de lo que dice)

| grupo | partidos | pendiente | error | sigmas contra 1 |
|---|---|---|---|---|
| todo | 26467 | 1.135 | 0.028 | +4.85 |
| ATP | 13787 | 1.110 | 0.038 | +2.89 |
| WTA | 12680 | 1.164 | 0.041 | +4.01 |
| superficie Clay | 7573 | 1.103 | 0.051 | +2.00 |
| superficie Grass | 2965 | 1.118 | 0.081 | +1.44 |
| superficie Hard | 15929 | 1.155 | 0.036 | +4.28 |
| nivel ATP250 | 5664 | 1.075 | 0.068 | +1.11 |
| nivel ATP500 | 2067 | 1.212 | 0.103 | +2.05 |
| nivel Grand Slam | 5627 | 1.215 | 0.055 | +3.91 |
| nivel International | 403 | 1.106 | 0.251 | +0.42 |
| nivel Masters 1000 | 3180 | 0.979 | 0.077 | -0.27 |
| nivel Premier | 300 | 0.982 | 0.300 | -0.06 |
| nivel WTA1000 | 2953 | 1.106 | 0.084 | +1.27 |
| nivel WTA250 | 3896 | 1.171 | 0.078 | +2.20 |
| nivel WTA500 | 2176 | 1.164 | 0.104 | +1.58 |
| 1ª-2ª ronda | 19490 | 1.165 | 0.033 | +5.07 |
| 3ª ronda o más | 6977 | 1.049 | 0.054 | +0.90 |
| año 2020 | 2246 | 1.102 | 0.095 | +1.07 |
| año 2021 | 4681 | 1.132 | 0.067 | +1.97 |
| año 2022 | 4750 | 1.257 | 0.067 | +3.81 |
| año 2023 | 4981 | 1.107 | 0.063 | +1.69 |
| año 2024 | 5000 | 1.223 | 0.066 | +3.41 |
| año 2025 | 4643 | 0.982 | 0.064 | -0.28 |

## Calibración por tramos, ATP (partidos completos)

| favorito (Pinnacle sin margen) | dice | gana de verdad | partidos | sigmas |
|---|---|---|---|---|
| 50%-55% | 52.7% | 52.9% | 1814 | +0.12 |
| 55%-60% | 57.5% | 56.7% | 2331 | -0.84 |
| 60%-65% | 62.5% | 61.0% | 2299 | -1.42 |
| 65%-70% | 67.5% | 69.7% | 1913 | +2.07 |
| 70%-75% | 72.4% | 72.5% | 1613 | +0.03 |
| 75%-80% | 77.5% | 78.3% | 1346 | +0.74 |
| 80%-85% | 82.4% | 83.3% | 1071 | +0.74 |
| 85%-90% | 87.3% | 88.5% | 715 | +0.97 |
| 90%-95% | 92.4% | 95.8% | 495 | +2.84 |
| 95%-100% | 96.3% | 97.4% | 190 | +0.76 |

## Calibración por tramos, WTA (partidos completos)

| favorito (Pinnacle sin margen) | dice | gana de verdad | partidos | sigmas |
|---|---|---|---|---|
| 50%-55% | 52.7% | 51.0% | 1771 | -1.38 |
| 55%-60% | 57.5% | 57.8% | 2084 | +0.29 |
| 60%-65% | 62.4% | 62.6% | 2090 | +0.14 |
| 65%-70% | 67.4% | 68.6% | 1782 | +1.02 |
| 70%-75% | 72.5% | 73.9% | 1474 | +1.21 |
| 75%-80% | 77.3% | 77.8% | 1341 | +0.39 |
| 80%-85% | 82.4% | 84.7% | 986 | +1.90 |
| 85%-90% | 87.4% | 90.4% | 698 | +2.42 |
| 90%-95% | 92.2% | 95.3% | 379 | +2.22 |
| 95%-100% | 95.9% | 100.0% | 75 | +1.78 |

## Apostar a ciegas: ¿precio torcido o solo caro?

Hueco = rendimiento real - esperado. Cerca de 0 sigmas: el precio es exacto y solo cobra margen.

### ATP, partidos completos

| casa | lado | partidos | rendimiento real | esperado si Pinnacle es la verdad | hueco (sigmas) |
|---|---|---|---|---|---|
| Pinnacle | favorito | 13787 | -2.28% | -2.54% | +0.43 |
| Pinnacle | marginado | 13787 | -5.90% | -2.54% | -2.43 |
| Bet365 | favorito | 13753 | -4.39% | -4.64% | +0.43 |
| Bet365 | marginado | 13753 | -9.99% | -6.87% | -2.43 |
| Media | favorito | 13785 | -2.94% | -3.65% | +0.97 |
| Media | marginado | 13785 | -10.94% | -8.05% | -2.31 |
| Máxima | favorito | 13786 | -0.32% | -0.54% | +0.35 |
| Máxima | marginado | 13786 | -2.11% | +1.63% | -2.56 |
| Betfair Exch. (sin comisión) | favorito | 609 | +0.32% | -1.39% | +0.58 |
| Betfair Exch. (sin comisión) | marginado | 609 | -6.27% | +2.73% | -1.51 |

### WTA, partidos completos

| casa | lado | partidos | rendimiento real | esperado si Pinnacle es la verdad | hueco (sigmas) |
|---|---|---|---|---|---|
| Pinnacle | favorito | 12680 | -2.03% | -2.75% | +1.18 |
| Pinnacle | marginado | 12680 | -7.95% | -2.75% | -3.86 |
| Bet365 | favorito | 12655 | -3.85% | -4.58% | +1.22 |
| Bet365 | marginado | 12655 | -11.45% | -6.70% | -3.73 |
| Media | favorito | 12678 | -3.75% | -4.47% | +1.18 |
| Media | marginado | 12678 | -12.29% | -7.77% | -3.60 |
| Máxima | favorito | 12679 | +0.28% | -0.44% | +1.13 |
| Máxima | marginado | 12679 | -4.37% | +1.50% | -4.17 |
| Betfair Exch. (sin comisión) | favorito | 612 | +5.89% | -1.46% | +2.60 |
| Betfair Exch. (sin comisión) | marginado | 612 | -11.09% | +1.96% | -1.98 |

### ATP+WTA, incluidas retiradas (liquidadas como en tennis-data: gana quien avanza)

| casa | lado | partidos | rendimiento real | esperado si Pinnacle es la verdad | hueco (sigmas) |
|---|---|---|---|---|---|
| Pinnacle | favorito | 27282 | -2.64% | -2.63% | -0.01 |
| Pinnacle | marginado | 27282 | -5.24% | -2.63% | -2.67 |
| Bet365 | favorito | 27220 | -4.60% | -4.61% | +0.02 |
| Bet365 | marginado | 27220 | -9.29% | -6.77% | -2.80 |
| Media | favorito | 27278 | -3.82% | -4.05% | +0.49 |
| Media | marginado | 27278 | -10.23% | -7.91% | -2.63 |
| Máxima | favorito | 27280 | -0.53% | -0.49% | -0.09 |
| Máxima | marginado | 27280 | -1.67% | +1.55% | -3.18 |
| Betfair Exch. (sin comisión) | favorito | 1266 | +2.03% | -1.41% | +1.71 |
| Betfair Exch. (sin comisión) | marginado | 1266 | -5.54% | +2.29% | -1.76 |
