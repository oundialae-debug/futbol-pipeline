# Modelo de puntos contra los precios de Kalshi

Generado por `modelos/tenis/scripts/kalshi_puntos.py`. Log-loss: negativo = el modelo es mejor
que el precio de Kalshi. Apuestas al precio de venta con comisión.

| mercado | partidos emparejados | log-loss modelo | log-loss Kalshi | modelo - Kalshi (sigmas) | apuestas valor>0: n / rendimiento (sigmas) | valor>5%: n / rendimiento (sigmas) |
|---|---|---|---|---|---|---|
| KXATPMATCH | 1669 de 2341 | 0.6084 | 0.5785 | +0.0299 (+4.81) | 1390 / -5.91% (-2.24) | 748 / -8.76% (-2.34) |
| KXATPCHALLENGERMATCH | sin precios | | | | | |
| KXWTAMATCH | 1376 de 2068 | 0.6152 | 0.5866 | +0.0286 (+4.28) | 1141 / -3.82% (-1.18) | 588 / -2.11% (-0.46) |
| KXWTACHALLENGERMATCH | 787 de 1298 | 0.6329 | 0.5983 | +0.0346 (+3.38) | 645 / -2.43% (-0.47) | 404 / -2.63% (-0.39) |
| KXATPGTOTAL | sin precios | | | | | |
| KXWTAGTOTAL | 13 | | | | | |
| KXATPGSPREAD | sin precios | | | | | |
