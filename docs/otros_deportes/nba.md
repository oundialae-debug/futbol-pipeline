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

## Modelo entrenado con partidos pasados (28/09/2026)

Datos históricos sin gastar API: Kaggle `eoinamoore/historical-nba-data-and-player-box-scores`
(box-score por equipo y por jugador, con DNP/lesión, y árbitros en ~20% de los partidos),
de 2021-22 a la final de 2026, en `data/nba/kaggle/`. Cruzado con nuestra API: marcador
idéntico en el 99,97% de 6.921 partidos.

`scripts/nba/modelo_totales.py` (`MERCADO=totales|handicap`): ritmo, eficiencia ofensiva y
defensiva, tasa de triples y tiros libres (temporada y últimos 10), descanso, back-to-back,
bajas de jugadores fijos (≥20 min) y árbitros. XGBoost reentrenado cada mes, 5 semillas.
Prueba: 1.926 partidos de 2024-25 y 2025-26, contra el cierre de MGM.

| mercado | config | corr(pred, real-línea) | ROI apostando todo |
|---|---|---|---|
| totales | base | +0.002 (+0.08s) | -4.6% |
| totales | +bajas | +0.018 (+0.80s) | -7.7% |
| totales | +bajas+árbitros | +0.014 (+0.63s) | -5.3% |
| hándicap | base / +bajas / +árbitros | entre -0.017 y +0.005 | -4% a -7% |

Sin línea, el modelo tiene más error que la línea (totales: RMSE 20.3 frente a 19.4). Los
ROI positivos que salen solo en los umbrales altos (n≈250-460, <0.7s, tras probar 5 umbrales)
son ruido. **No hay hallazgo: el cierre de MGM ya lleva dentro ritmo, eficiencia, descanso y bajas.**

Pendiente:
- Árbitros: solo en el 11% de los partidos de prueba, así que aún no se han probado de verdad.
- Ganador (moneyline) con cuota ≥ 1.4: sin probar con este modelo.
- El cron de box-score de la API (`nba_boxscore.yml`) ya es redundante para el histórico
  (Kaggle lo trae entero). Decidir si se reorienta a la temporada en curso (alineaciones antes del partido).
- Lo que puede quedar: la línea de APERTURA (el histórico solo tiene el cierre).

## Segunda ronda (28/09/2026, noche): Elo, calidad de los disponibles, ganador y dinero del público

Rasgos en `scripts/nba/rasgos_nba.py` (compartido); modelos en `modelo_totales.py` y
`modelo_ganador.py`. Prueba: los mismos 1.926 partidos de 2024-25 y 2025-26, reentreno mensual.

**Dos fallos silenciosos del dataset de Kaggle, arreglados:**
- `playerteamId` está vacío en el 99,9% de 2021-22 y en el ~7% del resto. Las bajas de esos
  partidos salían a 0 sin avisar. Se recupera con (partido, local/visitante): coincide en el
  99,9% de los casos donde sí venía.
- Los lesionados de larga duración **no tienen fila** (Embiid 2024-25: 19 partidos jugados y
  solo 9 ausencias registradas). "Bajas" solo ve a los que causan baja ese mismo día.

**Fuga detectada y quitada:** la primera versión de la calidad de plantilla sumaba a "los que
JUGARON". Eso depende del propio partido: el número de jugadores que juegan correlaciona 0,63
con el margen final (19,5 en partidos igualados, 24 en palizas de más de 30). Ahora suma a los
DISPONIBLES (con fila y sin marca de baja). "DNP - Coach's Decision" cuenta como disponible.

**Ganador (moneyline), cuota ≥ 1.4:**

| modelo | Brier vs mercado | acierto eligiendo al favorito |
|---|---|---|
| mercado (cierre MGM) | -- | 68.0% |
| XGBoost, rasgos de equipo | -5.11s | 65.1% |
| + Elo + calidad de los disponibles | -4.26s | 65.3% |
| + precio como variable | -3.39s | 67.2% |
| logística simple (solo Elo) | -5.19s | 65.3% |

Apostando con VE>0 y cuota ≥ 1.4, todas las variantes pierden (-1% a -9%). El Elo solo ya
acierta lo mismo que el XGBoost entero: el techo son los datos, no el modelo.

**Totales con Elo y calidad:** Pearson +0.100 (+4.38s) con el modelo que ve la línea, pero
**Spearman 0.005** y deciles planos (del 46% al 55% de "más", sin tendencia). Lo empujan unos
pocos partidos con desvíos enormes. No es señal. `evaluar()` imprime ya las dos correlaciones.

**Dinero del público (MGM trae % de dinero y % de apuestas por lado):** unas 40 reglas a ciegas
(seguir al dinero grande o ir contra el público, en totales, hándicap y ganador). La mejor sale a
+1,02 sigmas, lo esperable por azar con tantas pruebas. Nada.

**Árbitros (solo 2025-26 trae árbitro; con línea de MGM, 626 partidos, nov-2025 a feb-2026):**
Spearman -0.057 (-1.43s). Los tríos con partidos más altos en el pasado dan totales POR DEBAJO
de la línea (42% de "más" en el cuartil alto, 50% en el bajo). Encaja con que la casa sobreajuste
por árbitro, pero con una sola temporada no significa nada. **Pista, no hallazgo.** Para medirla
de verdad harían falta árbitros de temporadas anteriores, y la API NBA no los da.

**Conclusión de la ronda:** con datos públicos (box-scores, Elo, disponibles, descanso), el
modelo NBA acierta el 65-67% de ganadores frente al 68% del cierre, y en totales y hándicap no
ve nada que la línea no sepa. Lo que puede quedar:
1. Árbitros con más temporadas (otra fuente).
2. Línea de APERTURA en vez de cierre: el modelo compite contra un precio menos informado.
3. Saber las bajas antes que la casa (noticias de última hora): es cuestión de velocidad, no de modelo.
