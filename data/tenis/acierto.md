# Acierto del ganador: qué opción acierta más (ventana móvil 2021-2026)

Generado por `modelos/tenis/scripts/acierto.py`. Acierto = el lado con prob. > 50% gana.
Log-loss y Brier: más bajo es mejor.

| opción | acierto | log-loss | Brier |
|---|---|---|---|
| mercado (cuota sin margen) | 68.34% | 0.5834 | 0.2004 |
| mercado recalibrado | 68.34% | 0.5831 | 0.2003 |
| cuota + Elo + puntos | 68.31% | 0.5834 | 0.2005 |
| Elo solo | 66.27% | 0.6058 | 0.2096 |
| puntos solo | 67.14% | 0.6082 | 0.2096 |
| Elo + puntos (sin cuota) | 66.83% | 0.5987 | 0.2068 |

## Acierto por circuito y nivel

| grupo | partidos | mercado (cuota sin margen) | mercado recalibrado | cuota + Elo + puntos | Elo solo | puntos solo | Elo + puntos (sin cuota) |
|---|---|---|---|---|---|---|---|
| ATP 1000 | 3583 | 66.8% | 66.8% | 66.5% | 64.9% | 65.8% | 65.2% |
| ATP 250 | 5632 | 65.2% | 65.2% | 65.1% | 62.3% | 63.7% | 63.3% |
| ATP 500 | 2236 | 70.1% | 70.0% | 70.3% | 68.2% | 68.4% | 67.9% |
| ATP GS | 2855 | 74.4% | 74.4% | 74.5% | 72.1% | 73.9% | 73.5% |
| WTA 1000 | 3533 | 67.5% | 67.6% | 67.4% | 66.0% | 66.9% | 66.7% |
| WTA 250 | 4310 | 67.1% | 66.9% | 67.2% | 65.3% | 65.5% | 65.2% |
| WTA 500 | 2551 | 67.9% | 68.1% | 67.9% | 65.0% | 66.0% | 66.1% |
| WTA GS | 2903 | 72.2% | 72.3% | 72.1% | 71.2% | 71.6% | 71.7% |

Acierto cuota+Elo+puntos - mercado: -0.04% (-0.51 sigmas; partidos donde discrepan: 382).
