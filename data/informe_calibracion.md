# Informe de calibración -- actualizado el 2026-09-16
Partidos evaluados hasta ahora: 3

## Goles (victoria local)
- Brier score: 0.2021 (0.25 = azar, más bajo = mejor)
- Acierto: 66.7%

## Tarjetas (over/under 4.5)
- Brier score: 0.1958 (0.25 = azar, más bajo = mejor)
- Acierto: 100.0%

## Desglose por variable (para diagnosticar qué falla)
- **Partidos de derbi**: sin casos todavía- **Partidos normales (no derbi)** (n=3): acierto tarjetas 100.0%

*Nota: este desglose es para diagnóstico manual -- los pesos del modelo
(50/50 árbitro-equipo, factor derbi 1.15) todavía NO se ajustan solos
según estos resultados. Eso es un paso pendiente, no implementado todavía.*
