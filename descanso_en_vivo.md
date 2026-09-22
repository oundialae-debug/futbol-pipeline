# Tarjetas al descanso -- 2026-09-22 17:50 UTC

Modelo: nivel propio de cada liga -0.068*k por tarjeta al descanso, phi=1.23, ajustado sobre 363 partidos de 6 ligas.
Niveles: Segunda División 3.21, La Liga 3.05, Premier League 2.68, (otras) 2.67, Bundesliga 2.67, Serie A 2.33, Ligue 1 2.09.
Validación fuera de muestra (línea 4.5): Brier 0.1839 frente a 0.2404 de la tasa base (+23.5%).

> El recuento del descanso es **información pública**: las casas también lo
> ven. La hipótesis original -- que sus modelos supongan persistencia cuando
> la correlación real es negativa -- está RETIRADA: ese -0.171 salía de un
> fichero de solo La Liga, y sobre 363 partidos de seis ligas la correlación
> es -0.016, o sea nada. Lo que queda es tener bien el nivel de cada liga,
> que es calibración, no ventaja.

*Consumo de API hoy: 365 llamadas en 60 pasadas, sobre un tope de 6000 (6%). El plan da 7.500 al día.*

> ⚠ Las cuotas en vivo se refrescan **cada 10 minutos** (documentación de la API) y no traen marca de tiempo. El precio de abajo puede ser de antes de las últimas tarjetas del primer tiempo, y puede no existir ya en la casa. El valor sirve para comparar modelos, no como dinero cogible.

**En juego, esperando al descanso:** AGF vs Nordsjælland (min 45), Bristol City U21 vs Hull City U21 (min 45), Inter Milan Women vs Häcken (min 47)


## ASA Targu Mures vs CS Dinamo Bucuresti  (Liga II)
*Half time · minuto 45 · 0 - 1 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**1 tarjetas** al descanso (minutos ['28']). Esperadas en la 2ª parte: **2.6**.

*Sin mercado de tarjetas en vivo para este partido.*

## FC Tallinn vs Harju Jk Laagri U21  (Cup)
*Half time · minuto 45 · 1 - 0 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**0 tarjetas** al descanso. Esperadas en la 2ª parte: **2.67**.

*Sin mercado de tarjetas en vivo para este partido.*

## Bayern Munich Women vs Manchester City Women  (UEFA Champions League Women)
*Second half · minuto 45 · 2 - 1 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**0 tarjetas** al descanso · **13 faltas**. Esperadas en la 2ª parte: **2.67**.

| Línea | Modelo | Mercado | Casas | Mejor cuota | Valor |
|---|---|---|---|---|---|
| 0.5 | 91% | 81% | 1 | 1.13 (Marathonbet) | +2.8% |
| 1.0 (push 20%) | 71% | 72% | 1 | 1.29 (Vbet Sport) | +11.6% |
| 1.5 | 71% | 55% | 2 | 1.68 (Marathonbet) | +19.9% |
| 2.0 (push 23%) | 48% | 41% | 1 | 2.25 (Vbet Sport) | +31.6% ⚠ revisar modelo |
| 2.5 | 48% | 31% | 2 | 3.08 (Marathonbet) | +48.5% ⚠ revisar modelo |
| 3.0 (push 20%) | 29% | 27% | 1 | 3.4 (Vbet Sport) | +16.9% |
| 3.5 | 29% | 20% | 2 | 6.3 (Marathonbet) | +80.2% ⚠ revisar modelo |
| 4.5 | 15% | 13% | 1 | 7.0 (Marathonbet) | +6.4% |
