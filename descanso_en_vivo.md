# Tarjetas al descanso -- 2026-09-23 14:57 UTC

Modelo: nivel propio de cada liga -0.068*k por tarjeta al descanso, phi=1.23, ajustado sobre 363 partidos de 6 ligas.
Niveles: Segunda División 3.21, La Liga 3.05, Premier League 2.68, (otras) 2.67, Bundesliga 2.67, Serie A 2.33, Ligue 1 2.09.
Validación fuera de muestra (línea 4.5): Brier 0.1839 frente a 0.2404 de la tasa base (+23.5%).

> El recuento del descanso es **información pública**: las casas también lo
> ven. La hipótesis original -- que sus modelos supongan persistencia cuando
> la correlación real es negativa -- está RETIRADA: ese -0.171 salía de un
> fichero de solo La Liga, y sobre 363 partidos de seis ligas la correlación
> es -0.016, o sea nada. Lo que queda es tener bien el nivel de cada liga,
> que es calibración, no ventaja.

*Consumo de API hoy: 302 llamadas en 48 pasadas, sobre un tope de 6000 (5%). El plan da 7.500 al día.*

> ⚠ Las cuotas en vivo se refrescan **cada 10 minutos** (documentación de la API) y no traen marca de tiempo. El precio de abajo puede ser de antes de las últimas tarjetas del primer tiempo, y puede no existir ya en la casa. El valor sirve para comparar modelos, no como dinero cogible.


## Hapoel Azor vs Hapoel Mahane Yehuda  (Liga Alef)
*Half time · minuto 45 · 1 - 0 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**0 tarjetas** al descanso. Esperadas en la 2ª parte: **2.67**.

*Sin mercado de tarjetas en vivo para este partido.*

## Kladno vs Baník Ostrava  (Cup)
*Half time · minuto 45 · 0 - 1 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**1 tarjetas** al descanso (minutos ['45']). Esperadas en la 2ª parte: **2.6**.

| Línea | Modelo | Mercado | Casas | Mejor cuota | Valor |
|---|---|---|---|---|---|
| 1.5 | 90% | 69% | 1 | 1.34 (Vbet Sport) | +21.1% ⚠ revisar modelo |
| 2.0 (push 20%) | 70% | 59% | 1 | 1.56 (Vbet Sport) | +29.6% ⚠ revisar modelo |
| 2.5 | 70% | 45% | 1 | 2.05 (Vbet Sport) | +43.6% ⚠ revisar modelo |
| 3.0 (push 23%) | 47% | 31% | 1 | 2.95 (Vbet Sport) | +61.1% ⚠ revisar modelo |
| 3.5 | 47% | 28% | 1 | 3.25 (Vbet Sport) | +51.7% ⚠ revisar modelo |
| 4.0 (push 19%) | 27% | 27% | 1 | 3.4 (Vbet Sport) | +12.1% |
| 4.5 | 27% | 27% | 1 | 3.47 (Vbet Sport) | -5.4% |
