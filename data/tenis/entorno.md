# Desfase horario, altitud y velocidad de pista contra el mercado recalibrado

Generado por `modelos/tenis/scripts/entorno.py`. Entrena 2020-2023, juzga 2024-2026.
Se pide >= 2,5 sigmas y que aguante en los dos tramos. Log-loss negativo = mejora.

Sedes sin coordenadas: ninguna. Partidos con desfase > 0: 767; con pista conocida: 28564 de 30698; en sede >= 1.000 m: 593.

| variable | coef. entreno (sigmas) | coef. prueba (sigmas) | 2024-2025 Pinnacle | 2026 Betfair |
|---|---|---|---|---|
| desfase | +0.011 (+0.63) | -0.025 (-1.17) | +0.00004 (+0.84) | +0.00010 (+1.39) |
| altitud | -0.009 (-0.49) | +0.017 (+0.82) | +0.00003 (+0.74) | +0.00005 (+1.05) |
| pista | +0.009 (+0.49) | +0.030 (+2.05) | -0.00003 (-0.71) | -0.00018 (-1.51) |
| las tres | +0.011 (+0.64) / -0.010 (-0.57) / +0.011 (+0.58) | -0.025 (-1.15) / +0.007 (+0.31) / +0.029 (+1.88) | +0.00003 (+0.42) | -0.00006 (-0.37) |
