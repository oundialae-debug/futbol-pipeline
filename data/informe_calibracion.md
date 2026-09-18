# Informe de calibración -- actualizado el 2026-09-18
Partidos evaluados hasta ahora: 8

## Goles (victoria local)
- Brier score: 0.1902 (0.25 = azar, más bajo = mejor)
- Acierto: 62.5%

## Tarjetas (over/under 4.5)
- Brier score: 0.1939 (0.25 = azar, más bajo = mejor)
- Acierto: 87.5%

## Desglose por variable (para diagnosticar qué falla)
- **Partidos de derbi**: sin casos todavía- **Partidos normales (no derbi)** (n=8): acierto tarjetas 87.5%

*Nota: este desglose es para diagnóstico manual -- los pesos del modelo
(50/50 árbitro-equipo, factor derbi 1.15) todavía NO se ajustan solos
según estos resultados. Eso es un paso pendiente, no implementado todavía.*
