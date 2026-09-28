# NBA: qué mercado atacar y con qué variables (28/09/2026)

## Mercado elegido: totales (más/menos puntos del partido)

Criterio del usuario: acertar a menudo con cuota ≥ 1.4.

- **Lo que ofrece la API en NBA** (`/odds`, spec): Moneyline, Totals, Spread, Odd/Even.
  **No hay props de jugador**, que según la literatura son el mercado más blando. Además,
  `/odds` no está en el plan gratuito, y la API solo guarda cuotas hasta 28 días después
  del partido: no sirve para cuotas históricas.
- **Orden de eficiencia según fuentes del sector:** hándicap > ganador > totales > props.
  De los tres mercados que da la API, los totales son el menos eficiente.
- **Cuota:** los totales y el hándicap pagan unos 1.91 y se aciertan cerca del 50%. En
  ganador, cuota ≥ 1.4 deja solo a los favoritos flojos (1.4-1.8: 58-64% de acierto) y a
  los no favoritos.

## ¿El precio está torcido? (medido antes de montar nada)

Cuotas de CIERRE de MGM (Kaggle `caseydurfee/mgm-grand-nba-betting-data`, gratis, sin
cuenta): 6.069 partidos, de 2021-22 a febrero de 2026. En `data/nba/cuotas_kaggle/`.
Margen medio ≈ 4,6-4,7%. Con un precio perfecto se perdería ≈ -4,5%.

| estrategia a ciegas | n | acierto | ROI |
|---|---|---|---|
| siempre over | 6069 | 50.4% | -4.50% |
| siempre under | 6069 | 49.6% | -5.15% |
| under, primeras ~3 semanas de temporada | 661 | 50.4% | -3.66% |
| under cuando ≥ 70% del dinero va al over | 4503 | 49.3% | -5.74% |
| favorito a cuota 1.4-1.6 | 1579 | 64.0% | -5.11% |
| favorito a cuota 1.6-1.8 | 1348 | 58.2% | -2.24% |

Todo cae en torno a -margen/(1+margen). **El cierre de MGM es exacto, solo caro.** El
"sesgo al under de principio de temporada" de los artículos (2007) no aparece en 2021-2026.

## Primera prueba: modelo solo con marcadores (`scripts/nba/totales_primera_prueba.py`)

Rasgos: puntos a favor/en contra (temporada y últimos 10), descanso, back-to-back y
partidos jugados. Entrenamiento 2021-22 a 2023-24, prueba 2024-25 y 2025-26 (2.100 partidos).
Cruce API-MGM por día (hora de Nueva York) y local: 100% de coincidencia del over/under.

- RMSE del modelo 18.98, de la línea 18.11.
- Correlación (modelo - línea) con (real - línea): +0.012 (+0.56s).
- Apostando donde discrepan: ROI de -7% a -9%.

**Solo con marcadores no hay nada.** Es lo esperado: la línea ya sabe los puntos que mete
cada equipo.

## Variables que harían falta (y de dónde salen)

| variable | por qué | fuente | coste |
|---|---|---|---|
| ritmo (posesiones = FGA + 0.44·FTA - OREB + TOV) | el total es ritmo × eficiencia | `/box-score` | 1 llamada/partido |
| eficiencia ofensiva/defensiva por 100 posesiones | ídem | `/box-score` | incluido |
| quién jugó y cuántos minutos; bajas de titulares | la línea se mueve con las bajas | `/box-score` (histórico), `/lineups` (antes del partido) | incluido / 1 por partido |
| calidad de los que juegan (temporada anterior) | nuestra mejor variable en fútbol | `/players/{id}/statistics` | 1 por jugador (~600) |
| descanso, back-to-back, viajes | ya probados | gratis (calendario) | 0 |
| árbitros | afectan a los tiros libres | **no está en la spec NBA** | — |

**Fallo silencioso encontrado:** `matchStatistics` de `/matches/{id}` devuelve las
estadísticas del LOCAL repetidas en el visitante (partido 1438539: FGA 108 en los dos lados;
el box-score da 108 y 92). Se usa `/box-score`, que suma exacto al marcador.

## Coste de la descarga

6.591 partidos sin pretemporada (5 temporadas × ~1.320) = 6.591 llamadas de box-score.
Con el plan gratuito (100/día): ~70 días. Con PRO (12,49 $/mes, 7.500/día): 1 día.
`nba_boxscore.yml` va del partido más reciente hacia atrás. Su cron solo corre desde `main`.

## Aviso importante

Aunque el modelo mejore, el cierre de MGM ya es exacto. Las ventajas que quedan en la NBA
suelen estar en la línea de APERTURA o en reaccionar antes que la casa a una baja. Nuestro
histórico solo tiene cierres. Por eso la prueba honesta será siempre contra el cierre.
