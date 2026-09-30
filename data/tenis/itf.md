# Entrenar en ITF: Elo y modelo de puntos contra el precio de Kalshi

Generado por `modelos/tenis/scripts/itf.py`. Partidos de ITF de Kalshi posteriores al final de Sackmann,
con precio a cierre - 4 h. Acierto = el lado con prob. > 50% gana. Log-loss: más bajo es mejor.

| serie | partidos de Kalshi añadidos al historial | con superficie conocida | evaluados | acierto Kalshi | acierto Elo | acierto puntos | log-loss Kalshi | log-loss Elo | log-loss puntos |
|---|---|---|---|---|---|---|---|---|---|
| KXITFMATCH | 11551 | 78% | 3413 | 74.5% | 68.2% | 62.6% | 0.5191 | 0.5974 | 0.6530 |
| KXITFWMATCH | 9745 | 72% | 1977 | 72.2% | 69.6% | 62.0% | 0.5351 | 0.5818 | 0.6675 |
