# Modelo de puntos contra los precios de Kalshi

Generado por `modelos/tenis/scripts/kalshi_puntos.py`. Log-loss: negativo = el modelo es mejor
que el precio de Kalshi. Apuestas al precio de venta con comisión.

| mercado | partidos emparejados | acierto modelo | acierto Kalshi | log-loss modelo | log-loss Kalshi | modelo - Kalshi (sigmas) | apuestas valor>0: n / rendimiento (sigmas) | valor>5%: n / rendimiento (sigmas) |
|---|---|---|---|---|---|---|---|---|
| KXATPMATCH | 1669 de 2341 | 66.5% | 69.0% | 0.6084 | 0.5785 | +0.0299 (+4.81) | 1390 / -5.91% (-2.24) | 748 / -8.76% (-2.34) |
| KXATPCHALLENGERMATCH | 910 de 1491 | 64.9% | 66.0% | 0.6453 | 0.6059 | +0.0395 (+4.15) | 729 / -7.49% (-1.77) | 433 / -3.96% (-0.70) |
| KXWTAMATCH | 1376 de 2068 | 66.8% | 68.1% | 0.6152 | 0.5866 | +0.0286 (+4.28) | 1141 / -3.82% (-1.18) | 588 / -2.11% (-0.46) |
| KXWTACHALLENGERMATCH | 787 de 1298 | 63.0% | 65.8% | 0.6329 | 0.5983 | +0.0346 (+3.38) | 645 / -2.43% (-0.47) | 404 / -2.63% (-0.39) |
| KXATPGTOTAL | 495 de 628 | 53.1% | 56.8% | 0.6945 | 0.6806 | +0.0139 (+1.05) | 360 / -11.64% (-2.33) | 222 / -12.59% (-1.97) |
| KXWTAGTOTAL | 351 de 558 | 56.7% | 61.3% | 0.6731 | 0.6692 | +0.0038 (+0.26) | 318 / +1.66% (+0.31) | 254 / -0.61% (-0.10) |
| KXATPGSPREAD | 482 de 594 | 58.1% | 57.7% | 0.6825 | 0.6969 | -0.0144 (-0.69) | 294 / -3.75% (-0.69) | 176 / -2.43% (-0.33) |
