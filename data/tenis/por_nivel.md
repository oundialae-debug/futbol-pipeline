# Mezcla por circuito y nivel de torneo, o una para todo

Generado por `modelos/tenis/scripts/por_nivel.py`. Juzgado 2023-2026. Log-loss: negativo = mejora
al mercado recalibrado (con la misma partición).

Partidos 2023-2026 por grupo: {'atp 250': 3406, 'wta 250': 2691, 'wta 1000': 2657, 'atp 1000': 2553, 'wta GS': 1950, 'atp GS': 1892, 'wta 500': 1666, 'atp 500': 1567}

| partición | mezcla - mercado recalibrado | apuestas valor>0: n / rendimiento (sigmas) |
|---|---|---|
| una para todo | -0.00025 (-1.72) | 7299 / -0.08% (-0.09) |
| por circuito | -0.00021 (-1.36) | 7739 / +0.93% (+0.98) |
| por circuito y nivel | +0.00012 (+0.46) | 10806 / +0.52% (+0.51) |

## Por grupo (partición circuito x nivel)

| grupo | partidos | mezcla - mercado (sigmas) | pesos medios cuota / Elo / puntos | apuestas: n / rendimiento |
|---|---|---|---|---|
| atp 1000 | 2553 | -0.00009 (-0.10) | +0.90 / -0.20 / +0.21 | 1750 / +3.74% |
| atp 250 | 3406 | -0.00015 (-0.44) | +1.08 / -0.12 / +0.06 | 949 / +2.83% |
| atp 500 | 1567 | +0.00038 (+0.34) | +1.41 / -0.08 / -0.15 | 1133 / +1.83% |
| atp GS | 1892 | +0.00004 (+0.08) | +1.01 / +0.08 / +0.03 | 1255 / +0.64% |
| wta 1000 | 2657 | +0.00073 (+0.81) | +1.21 / -0.31 / +0.12 | 1828 / -2.51% |
| wta 250 | 2691 | -0.00062 (-0.77) | +1.24 / -0.22 / +0.04 | 1340 / -0.10% |
| wta 500 | 1666 | +0.00064 (+1.06) | +1.13 / -0.07 / +0.09 | 1135 / -2.79% |
| wta GS | 1950 | +0.00048 (+1.83) | +1.06 / +0.04 / +0.02 | 1416 / +0.96% |
