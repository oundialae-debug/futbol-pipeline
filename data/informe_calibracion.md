# Informe de calibración -- actualizado el 2026-09-19
Partidos evaluados hasta ahora: 9

## Goles (victoria local)
- Brier score: 0.1863 (0.25 = azar, más bajo = mejor)
- Acierto: 66.7%

## Tarjetas (over/under 4.5)
- Brier score: 0.1946 (0.25 = azar, más bajo = mejor)
- Acierto: 88.9%

## Modelo contra mercado
Todavía pocos partidos con cuota registrada (0); hacen falta 5+.

## Desglose por variable (para diagnosticar qué falla)

- **Partidos de derbi**: sin casos todavía
- **Partidos normales (no derbi)** (n=9): acierto tarjetas 88.9%
- **Diferencia de nivel alta** (n=5): acierto tarjetas 80.0%
- **Diferencia de nivel baja** (n=4): acierto tarjetas 100.0%

## Aprendizaje automático de pesos
Pesos vigentes ahora mismo: peso_nivel=0.15 (factor máximo 1.30),
peso_derbi=0.15 (factor derbi 1.15)

- peso_derbi: todavía no hay casos suficientes (derbis n=0, partidos normales n=9, se necesitan 10+ de cada uno)
- peso_nivel: todavía no hay casos suficientes (diferencia de nivel alta n=5, diferencia de nivel baja n=4, se necesitan 10+ de cada uno)

*Nota: el ajuste se guarda en `data/pesos_modelo.json` y persiste entre ejecuciones
semanales. Cada peso se mueve como máximo un 5% por semana, y solo si hay
10+ partidos evaluados en cada grupo comparado, para no sobrerreaccionar a
pocos casos. El split 50/50 árbitro-equipo dentro de la media base, y los
pesos de alineación/riesgo de sanción, todavía son fijos -- no se ajustan
solos.*
