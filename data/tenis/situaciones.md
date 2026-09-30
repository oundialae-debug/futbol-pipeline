# Cinco situaciones concretas contra el mercado recalibrado

Generado por `modelos/tenis/scripts/situaciones.py`. Entrena 2020-2023, juzga 2024-2026.
Coeficiente > 0: el mercado infravalora a quien está en la situación. Log-loss: negativo =
mejora al mercado recalibrado. Se pide >= 2,5 sigmas y que aguante en los dos tramos.

Ciudades sin país en la tabla: ninguna.

| situación | partidos con ella (entreno / prueba) | coef. entreno (sigmas) | coef. en prueba (sigmas) | 2024-2025 Pinnacle | 2026 Betfair |
|---|---|---|---|---|---|
| local | 3522 / 2886 | -0.027 (-0.70) | -0.049 (-1.16) | -0.00005 (-0.86) | -0.00004 (-0.47) |
| previa | 3751 / 2896 | +0.138 (+3.61) | +0.036 (+0.84) | +0.00021 (+0.75) | +0.00018 (+0.44) |
| cansancio | 1371 / 1170 | -0.024 (-0.39) | -0.028 (-0.41) | +0.00000 (+0.03) | -0.00001 (-0.18) |
| regreso | 894 / 618 | -0.153 (-1.96) | -0.173 (-1.85) | -0.00006 (-0.43) | -0.00025 (-1.03) |
| cambio_superficie | 1314 / 1135 | -0.096 (-1.53) | -0.160 (-2.39) | -0.00023 (-1.94) | -0.00004 (-0.18) |
