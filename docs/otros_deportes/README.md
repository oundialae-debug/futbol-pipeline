# Otros deportes de Highlightly (28/09/2026)

Especificaciones OpenAPI descargadas de `https://highlightly.net/<deporte>-api/documentation/docs.json`
(la web de documentación, CERO llamadas a la API). `spec_sport.json` es la "All Sports API"
(`sports.highlightly.net`, 211 rutas con prefijo `/<deporte>/`).

**Comprobado el 28/09/2026 con 1 llamada** (`scripts/sondeo_otros_deportes.py`): nuestra clave
SÍ entra en `nba.highlightly.net`, pero con el plan **BASIC gratuito: 100 llamadas/día**, cuota
aparte de la de fútbol (7.500, que no se toca). Datos históricos sí (15/03/2026: 18 partidos NBA,
terminados). Según la spec, `/odds` **no está disponible en el plan Basic/Free**. Para tener cuotas
de otro deporte habría que pagar ese deporte o la All Sports API.

| deporte | host | rutas | box-score jugador | alineaciones | stats partido | stats jugador temporada |
|---|---|---|---|---|---|---|
| NBA/NCAAB | nba. | 19 | sí | sí | en /matches/{id} | sí |
| MLB/NCAA | baseball. | 20 | sí (bateo+pitcheo) | sí (isStarter) | sí | sí |
| NFL/NCAA | american-football. | 19 | sí | sí (+lesiones en /matches/{id}) | en /matches/{id} | sí |
| NHL/NCAAH | nhl. | 18 | no | sí | en /matches/{id} | sí |
| Basket (340+ ligas) | basketball. | 19 | no | no | sí | no |
| Hockey (170+ ligas) | hockey. | 18 | no | no | no | no |
| Voleibol | volleyball. | 18 | no | no | no | no |
| Balonmano | handball. | 18 | no | no | no | no |
| Rugby | rugby. | 18 | no | en /matches/{id} | no | no |
| Críquet | cricket. | 19 | en /matches/{id} | plantilla | en /matches/{id} | no |

Todos tienen `/odds` (previas y en vivo), `/bookmakers`, `/head-2-head`, `/last-five-games`,
`/standings` y predicciones de la propia API en `/matches/{id}`. La spec no trae ejemplos de
nombres de mercado de cuotas: hay que verlos con datos reales antes de dar nada por hecho.
