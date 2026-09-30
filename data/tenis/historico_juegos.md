# Juegos totales antes del partido: ¿exagera el modelo? (historial 2021-2026)

225,349 partidos completos (al mejor de 3: 222,278). Modelo de puntos con la fuerza de cada jugador ANTES del partido.

## Juegos esperados por el modelo frente a los reales (al mejor de 3)

| circuito | nivel | partidos | modelo espera | reales | diferencia |
|---|---|---|---|---|---|
| ATP | 250 | 8,104 | 24.69 | 23.34 | +1.35 |
| ATP | 500 | 3,421 | 24.63 | 23.29 | +1.34 |
| ATP | ATP/WTA 250-500 | 337 | 24.64 | 22.42 | +2.22 |
| ATP | Challenger/125 | 32,284 | 24.41 | 22.82 | +1.59 |
| ATP | Copa Davis/BJK | 1,235 | 24.03 | 21.97 | +2.05 |
| ATP | Grand Slam | 2,539 | 24.91 | 23.33 | +1.57 |
| ATP | Masters/1000 | 5,108 | 24.59 | 23.50 | +1.09 |
| WTA | 100 | 4,422 | 23.60 | 20.78 | +2.82 |
| WTA | 250 | 301 | 23.79 | 22.42 | +1.37 |
| WTA | 35 | 16,873 | 23.77 | 19.75 | +4.02 |
| WTA | 40 | 2,627 | 23.88 | 20.23 | +3.65 |
| WTA | 50 | 5,784 | 23.74 | 20.50 | +3.24 |
| WTA | 60 | 9,485 | 23.81 | 20.11 | +3.69 |
| WTA | 75 | 6,278 | 23.69 | 20.77 | +2.92 |
| WTA | 80 | 1,148 | 23.62 | 20.27 | +3.35 |
| WTA | Challenger/125 | 6,314 | 23.52 | 21.43 | +2.09 |
| WTA | Copa Davis/BJK | 706 | 23.05 | 20.84 | +2.21 |
| WTA | Grand Slam | 5,312 | 23.45 | 21.80 | +1.65 |
| WTA | ITF | 93,819 | 24.07 | 19.05 | +5.02 |
| WTA | W | 398 | 23.36 | 22.39 | +0.97 |
| WTA | WTA 250 | 6,240 | 23.49 | 21.67 | +1.83 |
| WTA | WTA 500-1000 | 8,562 | 23.45 | 21.82 | +1.63 |

## Por año (al mejor de 3, todos los niveles)

| año | partidos | modelo espera | reales | diferencia |
|---|---|---|---|---|
| 2021 | 33,294 | 24.08 | 20.25 | +3.83 |
| 2022 | 43,014 | 24.08 | 20.10 | +3.98 |
| 2023 | 44,854 | 24.09 | 20.42 | +3.67 |
| 2024 | 48,976 | 24.09 | 20.32 | +3.77 |
| 2025 | 32,695 | 23.79 | 21.33 | +2.46 |
| 2026 | 19,445 | 23.91 | 21.88 | +2.02 |

## P(más de la línea): dice el modelo / pasa de verdad (al mejor de 3)

| línea | modelo | real | sesgo |
|---|---|---|---|
| 19.5 | 71.3% | 47.0% | +24.2% |
| 21.5 | 59.5% | 35.1% | +24.4% |
| 23.5 | 48.1% | 25.9% | +22.2% |

## Recalibración aprendida con 2021-2023, juzgada en 2024-2026 (partidos que no vio)

| línea | Brier modelo | Brier recalibrado | mejora |
|---|---|---|---|
| 19.5 | 0.2921 | 0.2497 | +14.5% |
| 21.5 | 0.2794 | 0.2365 | +15.3% |
| 23.5 | 0.2424 | 0.2056 | +15.2% |

Corrección guardada en `data/tenis/correccion_juegos_historica.json` (por circuito): {'atp': [-0.2544956125644019, 0.640043660701941, -0.08453649520089654], 'wta': [-0.7829866767218939, -0.10418642246424356, -0.2586039218267377]}
