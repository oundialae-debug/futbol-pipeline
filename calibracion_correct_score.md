# Calibración de Correct Score -- 2026-09-24 18:37 UTC

19645 pares partido+marcador (251 partidos ya jugados) de data/cuotas_cosechadas.csv -- nunca antes analizado, excluido de censo_margenes.py por el problema de conjunto incompleto (no todas las casas cotizan todos los marcadores).

**Probabilidad CRUDA (1/cuota mediana), NO desmarginada** -- no se puede desmarginar sin un conjunto completo. Esto favorece encontrar sesgo: la cruda ya lleva el margen dentro, así que lo normal es que la frecuencia real quede POR DEBAJO. Si algún tramo iguala o supera lo que dice la cuota, es la señal que se busca.

Acierto global: 1.28% de 19645 filas.

| Dice (cruda) | Pasa de verdad | Casos | Sesgo | Sigmas |
|---|---|---|---|---|
| 0.5% | 0.1% | 15243 | -0.41 pts | -14.90 |
| 3.0% | 2.7% | 1376 | -0.27 pts | -0.63 |
| 5.0% | 4.1% | 784 | -0.94 pts | -1.33 |
| 7.1% | 4.7% | 621 | -2.39 pts | -2.82 |
| 9.1% | 6.1% | 611 | -3.02 pts | -3.13 |
| 11.6% | 7.4% | 608 | -4.16 pts | -3.92 |
| 14.8% | 11.6% | 346 | -3.20 pts | -1.86 |
| 17.8% | 23.2% | 56 | +5.45 pts | +0.97 |

**El tramo (0.0, 0.02] se desvía -14.90 sigmas** (-0.41 puntos, n=15243) incluso con probabilidad cruda -- esto SÍ merece mirarse con más muestra antes de nada, la dirección importa: si 'pasa' > 'dice' es al revés de lo esperado (el margen debería hacer que pase MENOS, no más).

