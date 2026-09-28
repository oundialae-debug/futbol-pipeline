# Otros deportes de Highlightly (28/09/2026)

Especificaciones OpenAPI descargadas de `https://highlightly.net/<deporte>-api/documentation/docs.json`
(la web de documentación, CERO llamadas a la API). `spec_sport.json` es la "All Sports API"
(`sports.highlightly.net`, 211 rutas con prefijo `/<deporte>/`).

**Sin comprobar:** si nuestra clave (producto Football, `soccer.highlightly.net`) sirve para
los otros deportes. La web vende la "All Sports API" como producto aparte con una sola clave
para todos. Comprobarlo cuesta 1 llamada.

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
