# Modelo con saque, fatiga, perfil y cara a cara, contra el cierre

Generado por `modelos/tenis/scripts/modelo_tenis.py`. Entrena 2020-2022, elige en 2023,
reentrena 2020-2023 y juzga en 2024-2026. Log-loss: más bajo es mejor; diferencias
negativas = el modelo es mejor. Sigmas del error emparejado partido a partido.

Partidos completos: entrenamiento 2020-2022 11429, elección 2023 4869, prueba 2024-2026 13513.

## Elección (2023)

| configuración | modelo | log-loss 2023 | contra mercado recalibrado (sigmas) |
|---|---|---|---|
| solo mercado | logistica | 0.5854 | +0.0000 (+nan) |
| solo mercado | xgboost | 0.5871 | +0.0017 (+2.05) |
| elo | logistica | 0.5854 | -0.0001 (-0.49) |
| elo | xgboost | 0.5877 | +0.0023 (+2.28) |
| saque | logistica | 0.5854 | -0.0000 (-0.08) |
| saque | xgboost | 0.5876 | +0.0021 (+1.88) |
| fatiga | logistica | 0.5859 | +0.0005 (+0.91) |
| fatiga | xgboost | 0.5874 | +0.0020 (+1.85) |
| perfil | logistica | 0.5848 | -0.0007 (-1.40) |
| perfil | xgboost | 0.5877 | +0.0022 (+2.05) |
| h2h | logistica | 0.5855 | +0.0000 (+0.17) |
| h2h | xgboost | 0.5875 | +0.0020 (+2.12) |
| elo+saque | logistica | 0.5853 | -0.0001 (-0.22) |
| elo+saque | xgboost | 0.5883 | +0.0028 (+2.40) |
| saque+fatiga | logistica | 0.5860 | +0.0006 (+0.77) |
| saque+fatiga | xgboost | 0.5871 | +0.0017 (+1.42) |
| elo+saque+fatiga | logistica | 0.5860 | +0.0005 (+0.72) |
| elo+saque+fatiga | xgboost | 0.5880 | +0.0026 (+2.10) |
| elo+saque+fatiga+perfil+h2h | logistica | 0.5861 | +0.0007 (+0.78) |
| elo+saque+fatiga+perfil+h2h | xgboost | 0.5876 | +0.0022 (+1.71) |

**Elegida: perfil (logistica).**

## Prueba (2024-2026)

| configuración | modelo | tramo | partidos | contra mercado recalibrado | contra mercado en bruto | elegida |
|---|---|---|---|---|---|---|
| solo mercado | logistica | 2024-2025 Pinnacle | 9606 | +0.0000 (+nan) | -0.0001 (-0.34) |  |
| solo mercado | logistica | 2026 Betfair | 3749 | +0.0000 (+nan) | -0.0003 (-0.61) |  |
| solo mercado | xgboost | 2024-2025 Pinnacle | 9606 | +0.0011 (+2.20) | +0.0010 (+1.66) |  |
| solo mercado | xgboost | 2026 Betfair | 3749 | +0.0004 (+0.44) | +0.0000 (+0.03) |  |
| elo | logistica | 2024-2025 Pinnacle | 9606 | -0.0002 (-1.34) | -0.0003 (-0.87) |  |
| elo | logistica | 2026 Betfair | 3749 | -0.0001 (-0.24) | -0.0004 (-0.64) |  |
| elo | xgboost | 2024-2025 Pinnacle | 9606 | +0.0013 (+2.06) | +0.0012 (+1.70) |  |
| elo | xgboost | 2026 Betfair | 3749 | +0.0003 (+0.26) | -0.0001 (-0.07) |  |
| saque | logistica | 2024-2025 Pinnacle | 9606 | +0.0000 (+0.09) | -0.0001 (-0.16) |  |
| saque | logistica | 2026 Betfair | 3749 | +0.0002 (+0.26) | -0.0002 (-0.22) |  |
| saque | xgboost | 2024-2025 Pinnacle | 9606 | +0.0011 (+1.58) | +0.0010 (+1.32) |  |
| saque | xgboost | 2026 Betfair | 3749 | +0.0011 (+0.97) | +0.0008 (+0.68) |  |
| fatiga | logistica | 2024-2025 Pinnacle | 9606 | -0.0005 (-1.91) | -0.0007 (-1.54) |  |
| fatiga | logistica | 2026 Betfair | 3749 | -0.0004 (-0.95) | -0.0008 (-1.05) |  |
| fatiga | xgboost | 2024-2025 Pinnacle | 9606 | +0.0004 (+0.64) | +0.0003 (+0.43) |  |
| fatiga | xgboost | 2026 Betfair | 3749 | +0.0003 (+0.23) | -0.0001 (-0.08) |  |
| perfil | logistica | 2024-2025 Pinnacle | 9606 | -0.0005 (-1.41) | -0.0006 (-1.30) | **sí** |
| perfil | logistica | 2026 Betfair | 3749 | +0.0008 (+1.42) | +0.0005 (+0.60) | **sí** |
| perfil | xgboost | 2024-2025 Pinnacle | 9606 | +0.0009 (+1.33) | +0.0008 (+1.08) |  |
| perfil | xgboost | 2026 Betfair | 3749 | +0.0010 (+0.89) | +0.0006 (+0.55) |  |
| h2h | logistica | 2024-2025 Pinnacle | 9606 | +0.0002 (+2.24) | +0.0000 (+0.12) |  |
| h2h | logistica | 2026 Betfair | 3749 | -0.0001 (-0.69) | -0.0004 (-0.75) |  |
| h2h | xgboost | 2024-2025 Pinnacle | 9606 | +0.0017 (+2.90) | +0.0016 (+2.38) |  |
| h2h | xgboost | 2026 Betfair | 3749 | +0.0004 (+0.41) | +0.0001 (+0.05) |  |
| elo+saque | logistica | 2024-2025 Pinnacle | 9606 | -0.0002 (-0.37) | -0.0003 (-0.51) |  |
| elo+saque | logistica | 2026 Betfair | 3749 | +0.0001 (+0.11) | -0.0003 (-0.31) |  |
| elo+saque | xgboost | 2024-2025 Pinnacle | 9606 | +0.0016 (+2.17) | +0.0014 (+1.92) |  |
| elo+saque | xgboost | 2026 Betfair | 3749 | +0.0013 (+1.06) | +0.0010 (+0.80) |  |
| saque+fatiga | logistica | 2024-2025 Pinnacle | 9606 | -0.0004 (-0.82) | -0.0005 (-0.89) |  |
| saque+fatiga | logistica | 2026 Betfair | 3749 | -0.0003 (-0.40) | -0.0006 (-0.73) |  |
| saque+fatiga | xgboost | 2024-2025 Pinnacle | 9606 | +0.0007 (+0.91) | +0.0006 (+0.73) |  |
| saque+fatiga | xgboost | 2026 Betfair | 3749 | +0.0005 (+0.45) | +0.0002 (+0.17) |  |
| elo+saque+fatiga | logistica | 2024-2025 Pinnacle | 9606 | -0.0004 (-0.87) | -0.0005 (-0.93) |  |
| elo+saque+fatiga | logistica | 2026 Betfair | 3749 | -0.0002 (-0.29) | -0.0006 (-0.63) |  |
| elo+saque+fatiga | xgboost | 2024-2025 Pinnacle | 9606 | +0.0009 (+1.14) | +0.0008 (+0.97) |  |
| elo+saque+fatiga | xgboost | 2026 Betfair | 3749 | +0.0006 (+0.43) | +0.0002 (+0.17) |  |
| elo+saque+fatiga+perfil+h2h | logistica | 2024-2025 Pinnacle | 9606 | -0.0005 (-0.96) | -0.0006 (-1.03) |  |
| elo+saque+fatiga+perfil+h2h | logistica | 2026 Betfair | 3749 | +0.0006 (+0.64) | +0.0002 (+0.23) |  |
| elo+saque+fatiga+perfil+h2h | xgboost | 2024-2025 Pinnacle | 9606 | +0.0007 (+0.93) | +0.0006 (+0.76) |  |
| elo+saque+fatiga+perfil+h2h | xgboost | 2026 Betfair | 3749 | +0.0009 (+0.71) | +0.0006 (+0.45) |  |

## Apuestas de la elegida en la prueba (retiradas incluidas; Betfair sin comisión)

| umbral de valor | apuestas | rendimiento | sigmas |
|---|---|---|---|
| > 0% | 7776 | +0.80% | +0.73 |
| > 2% | 3548 | +0.62% | +0.37 |
| > 5% | 828 | -2.73% | -0.67 |
