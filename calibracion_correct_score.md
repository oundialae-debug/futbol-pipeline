# Calibración de Correct Score -- 2026-09-24 18:38 UTC

9036 pares partido+marcador (251 partidos ya jugados) de data/cuotas_cosechadas.csv -- nunca antes analizado, excluido de censo_margenes.py por el problema de conjunto incompleto (no todas las casas cotizan todos los marcadores).

**Probabilidad CRUDA (1/cuota mediana), NO desmarginada** -- no se puede desmarginar sin un conjunto completo. Esto favorece encontrar sesgo: la cruda ya lleva el margen dentro, así que lo normal es que la frecuencia real quede POR DEBAJO. Si algún tramo iguala o supera lo que dice la cuota, es la señal que se busca.

Acierto global: 2.76% de 9036 filas.

| Dice (cruda) | Pasa de verdad | Casos | Sesgo | Sigmas |
|---|---|---|---|---|
| 0.9% | 0.4% | 4693 | -0.54 pts | -6.16 |
| 3.0% | 2.8% | 1328 | -0.18 pts | -0.40 |
| 5.0% | 4.1% | 778 | -0.91 pts | -1.28 |
| 7.1% | 4.5% | 618 | -2.53 pts | -3.02 |
| 9.1% | 6.1% | 609 | -3.00 pts | -3.10 |
| 11.6% | 7.4% | 608 | -4.16 pts | -3.92 |
| 14.8% | 11.6% | 346 | -3.20 pts | -1.86 |
| 17.8% | 23.2% | 56 | +5.45 pts | +0.97 |

**El tramo (0.0, 0.02] se desvía -6.16 sigmas** (-0.54 puntos, n=4693) incluso con probabilidad cruda -- esto SÍ merece mirarse con más muestra antes de nada, la dirección importa: si 'pasa' > 'dice' es al revés de lo esperado (el margen debería hacer que pase MENOS, no más).

