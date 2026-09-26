# Tarjetas al descanso -- 2026-09-26 11:24 UTC

Modelo: nivel propio de cada liga -0.068*k por tarjeta al descanso, phi=1.23, ajustado sobre 363 partidos de 6 ligas.
Niveles: Segunda División 3.21, La Liga 3.05, Premier League 2.68, (otras) 2.67, Bundesliga 2.67, Serie A 2.33, Ligue 1 2.09.
Validación fuera de muestra (línea 4.5): Brier 0.1839 frente a 0.2404 de la tasa base (+23.5%).

> El recuento del descanso es **información pública**: las casas también lo
> ven. La hipótesis original -- que sus modelos supongan persistencia cuando
> la correlación real es negativa -- está RETIRADA: ese -0.171 salía de un
> fichero de solo La Liga, y sobre 363 partidos de seis ligas la correlación
> es -0.016, o sea nada. Lo que queda es tener bien el nivel de cada liga,
> que es calibración, no ventaja.

*Consumo de API hoy: 454 llamadas en 35 pasadas, sobre un tope de 6000 (8%). El plan da 7.500 al día.*

> ⚠ Las cuotas en vivo se refrescan **cada 10 minutos** (documentación de la API) y no traen marca de tiempo. El precio de abajo puede ser de antes de las últimas tarjetas del primer tiempo, y puede no existir ya en la casa. El valor sirve para comparar modelos, no como dinero cogible.


## Juventus Women vs Napoli Women  (Serie A Women)
*Half time · minuto 45 · 1 - 1 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**0 tarjetas** al descanso · **8 faltas**. Esperadas en la 2ª parte: **2.67**.

*Sin mercado de tarjetas en vivo para este partido.*

## Japan U23 vs Korea DPR U23  (Asian Games)
*Half time · minuto 45 · 1 - 0 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**1 tarjetas** al descanso (minutos ['26']). Esperadas en la 2ª parte: **2.6**.

| Línea | Modelo | Mercado | Casas | Mejor cuota | Valor |
|---|---|---|---|---|---|
| 1.5 | 90% | 86% | 1 | 1.05 (Marathonbet) | -5.1% |
| 2.5 | 70% | 71% | 2 | 1.3 (Vbet Sport) | -8.9% |
| 3.0 (push 23%) | 47% | 62% | 1 | 1.48 (Vbet Sport) | -7.5% |
| 3.5 | 47% | 48% | 2 | 1.93 (Vbet Sport) | -9.9% |
| 4.0 (push 19%) | 27% | 34% | 1 | 2.68 (Vbet Sport) | -7.5% |
| 4.5 | 27% | 28% | 2 | 3.42 (Marathonbet) | -6.8% |
| 5.0 (push 13%) | 14% | 27% | 1 | 3.47 (Vbet Sport) | -37.5% |
| 5.5 | 14% | 21% | 2 | 6.35 (Marathonbet) | -9.4% |
| 6.5 | 7% | 13% | 1 | 6.85 (Marathonbet) | -53.4% |
