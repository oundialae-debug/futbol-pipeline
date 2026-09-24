# Tarjetas al descanso -- 2026-09-24 11:08 UTC

Modelo: nivel propio de cada liga -0.068*k por tarjeta al descanso, phi=1.23, ajustado sobre 363 partidos de 6 ligas.
Niveles: Segunda División 3.21, La Liga 3.05, Premier League 2.68, (otras) 2.67, Bundesliga 2.67, Serie A 2.33, Ligue 1 2.09.
Validación fuera de muestra (línea 4.5): Brier 0.1839 frente a 0.2404 de la tasa base (+23.5%).

> El recuento del descanso es **información pública**: las casas también lo
> ven. La hipótesis original -- que sus modelos supongan persistencia cuando
> la correlación real es negativa -- está RETIRADA: ese -0.171 salía de un
> fichero de solo La Liga, y sobre 363 partidos de seis ligas la correlación
> es -0.016, o sea nada. Lo que queda es tener bien el nivel de cada liga,
> que es calibración, no ventaja.

*Consumo de API hoy: 144 llamadas en 34 pasadas, sobre un tope de 6000 (2%). El plan da 7.500 al día.*

> ⚠ Las cuotas en vivo se refrescan **cada 10 minutos** (documentación de la API) y no traen marca de tiempo. El precio de abajo puede ser de antes de las últimas tarjetas del primer tiempo, y puede no existir ya en la casa. El valor sirve para comparar modelos, no como dinero cogible.


## Japan vs Uruguay  (Friendlies)
*Half time · minuto 45 · 1 - 1 · nivel **(otras)**  ⚠ liga fuera del ajuste: se usa el nivel medio*

**0 tarjetas** al descanso · **10 faltas**. Esperadas en la 2ª parte: **2.67**.

| Línea | Modelo | Mercado | Casas | Mejor cuota | Valor |
|---|---|---|---|---|---|
| 0.5 | 91% | 79% | 1 | 1.16 (Marathonbet) | +5.5% |
| 1.0 (push 20%) | 71% | 72% | 1 | 1.28 (Vbet Sport) | +10.9% |
| 1.5 | 71% | 51% | 2 | 1.8 (Vbet Sport) | +28.4% ⚠ revisar modelo |
| 2.0 (push 23%) | 48% | 35% | 1 | 2.62 (Vbet Sport) | +49.5% ⚠ revisar modelo |
| 2.5 | 48% | 27% | 2 | 3.42 (Marathonbet) | +64.9% ⚠ revisar modelo |
| 3.0 (push 20%) | 29% | 24% | 1 | 3.83 (Vbet Sport) | +29.2% ⚠ revisar modelo |
| 3.5 | 29% | 22% | 2 | 5.85 (Marathonbet) | +67.4% ⚠ revisar modelo |
| 4.5 | 15% | 13% | 1 | 7.0 (Marathonbet) | +6.4% |
