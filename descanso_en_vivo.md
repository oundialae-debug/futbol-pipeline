# Tarjetas al descanso -- 2026-09-22 15:27 UTC

Modelo: nivel propio de cada liga -0.068*k por tarjeta al descanso, phi=1.23, ajustado sobre 363 partidos de 6 ligas.
Niveles: Segunda División 3.21, La Liga 3.05, Premier League 2.68, (otras) 2.67, Bundesliga 2.67, Serie A 2.33, Ligue 1 2.09.
Validación fuera de muestra (línea 4.5): Brier 0.1839 frente a 0.2404 de la tasa base (+23.5%).

> El recuento del descanso es **información pública**: las casas también lo
> ven. La hipótesis original -- que sus modelos supongan persistencia cuando
> la correlación real es negativa -- está RETIRADA: ese -0.171 salía de un
> fichero de solo La Liga, y sobre 363 partidos de seis ligas la correlación
> es -0.016, o sea nada. Lo que queda es tener bien el nivel de cada liga,
> que es calibración, no ventaja.

*Consumo de API hoy: 280 llamadas en 50 pasadas, sobre un tope de 6000 (5%). El plan da 7.500 al día.*

> ⚠ Las cuotas en vivo se refrescan **cada 10 minutos** (documentación de la API) y no traen marca de tiempo. El precio de abajo puede ser de antes de las últimas tarjetas del primer tiempo, y puede no existir ya en la casa. El valor sirve para comparar modelos, no como dinero cogible.

**En juego, esperando al descanso:** Dibba Al-Fujairah vs Ittifaq (min 44), Al Hamriyah vs Al Thaid (min 45), Al Urooba vs City (min 43)


## Dumbrăviţa vs CSM Reşiţa  (Liga II)
*Half time · minuto 45 · 0 - 1 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**4 tarjetas** al descanso (minutos ['18', '31', '40', '45']). Esperadas en la 2ª parte: **2.4**.

| Línea | Modelo | Mercado | Casas | Mejor cuota | Valor |
|---|---|---|---|---|---|
| 1.5 | — | — | 1 | — | ya resuelto |
| 2.5 | — | — | 2 | — | ya resuelto |
| 3.0 | — | — | 1 | — | ya resuelto |
| 3.5 | — | — | 2 | — | ya resuelto |
| 4.0 (push 12%) | 88% | 72% | 1 | 1.29 (Vbet Sport) | +25.7% ⚠ revisar modelo |
| 4.5 | 88% | 65% | 2 | 1.63 (Vbet Sport) | +44.2% ⚠ revisar modelo |
| 5.0 (push 22%) | 66% | 45% | 1 | 2.04 (Vbet Sport) | +57.0% ⚠ revisar modelo |
| 5.5 | 66% | 72% | 2 | 1.27 (Vbet Sport) | -16.2% |
| 6.0 (push 24%) | 42% | 65% | 1 | 1.42 (Vbet Sport) | -16.4% |
| 6.5 | 42% | 49% | 2 | 1.87 (Marathonbet) | -21.6% |
| 7.0 (push 19%) | 23% | 37% | 1 | 2.5 (Vbet Sport) | -23.1% |
| 7.5 | 23% | 29% | 2 | 3.2 (Marathonbet) | -25.4% |
| 8.5 | 12% | 15% | 1 | 5.95 (Marathonbet) | -31.0% |
