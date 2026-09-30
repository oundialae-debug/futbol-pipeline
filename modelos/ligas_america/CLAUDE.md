# Ligas de América: ambos marcan y más/menos 2.5 (desde el 29/09/2026)

Chat propio, aislado de los modelos oficiales. Petición del usuario: modelos
de ambos marcan y más/menos 2.5 para ligas de América SIN meter ruido en el
modelo oficial de ambos marcan ni en `modelos/ambos_marcan/`, que usan otros
chats. Aquí nada escribe en `data/` de la raíz ni toca scripts del repo padre
(se importan, no se modifican).

## REGLAS DEL USUARIO PARA ESTE CHAT

- **API de Highlightly:** lo que dan fuentes externas NO se baja con la API
  (30/09: "no gastemos para lo mismo"). Solo se usa para algo que ninguna
  fuente externa tenga, y preguntando antes (regla general del CLAUDE.md
  raíz: sí explícito para cada llamada). El único hueco conocido: cuotas
  reales de ambos marcan y más/menos 2.5 (la API guarda ~28 días).
- Ligas pedidas: Liga Profesional Argentina, Brasileirão, Liga MX, Colombia
  Primera B. Añadidas para partidos del día: Colombia Primera A, Uruguay, MLS.

## Fuentes (todas sin API)

| fuente | qué da | cómo |
|---|---|---|
| football-data.co.uk `new/{ARG,BRA,MEX,USA}.csv` | resultados + cuota de CIERRE 1X2 desde 2012 (sin más/menos 2.5 ni ambos marcan) | curl directo, `data/football_data/` |
| FotMob `api/data/leagues?id=` y `matchDetails?matchId=` | ARG 112, BRA 268, MEX 230 desde 2023: xG, xGOT, ocasiones, remates, toques en área, nota, once con edad/valor, jugadores (xG, xA, minutos, nota), árbitro, tiempo | `scripts/fotmob.py` (1 petición/s, reanudable) -> `data/fotmob_partidos.csv`, `data/fotmob_jugadores.csv` |
| FotMob solo resultados | Colombia A (274), Colombia B (9125), Uruguay (161): sin estadísticas en FotMob | `scripts/fotmob_resultados.py` -> `data/football_data/{COLA,COLB,URU}.csv` |
| Promiedos (api.promiedos.com.ar, `?country_id=ba` = hora argentina) | calendario, 1X2 de UNA casa ahora, estadísticas, árbitro, votos | `pronostico.py`, `pronostico_hoy.py` |

Bloqueadas desde el contenedor (403): FootyStats, FBref, SofaScore, ESPN,
WhoScored. football-data NO tiene Colombia (`COL.csv` redirige a Polonia).

**Fuga en FotMob:** las medias del árbitro del infoBox y el valor de mercado
del once son de HOY, no de la fecha del partido. Se guardan, no se usan.

## Modelo (`scripts/modelo_goles.py`)

- Precio: 1X2 sin margen (media de cierre) -> lambdas Poisson que lo
  reproducen -> p implícitas de ambos marcan y más de 2.5 (variables `m_*`).
  Un 1X2 fija mal el total de goles: la p implícita sale baja (40% vs 49% real).
- Juego: Elo, forma (8 partidos, shift antes de rolling), condición
  local/visitante (6), nivel de la liga en la temporada, descanso.
- XGBoost de siempre (depth 2, mcw 20, lambda 5, 400 árboles), 3 semillas.

## Resultados (no redescubrir)

`evaluacion.md` (mes a mes 2024-01 a 2026-09, 3.466 partidos ARG/BRA/MEX):
- Modelo completo vs tasa de la liga: ambos marcan +0.97s, más de 2.5 +2.10s.
  Mejora de Brier minúscula (0.2463 -> 0.2454). Casi toda la señal es el 1X2.
- Juego encima del precio: ambos marcan +0.83s, más de 2.5 +0.21s (ruido).
- Brasil: no bate a la tasa de la liga en ninguno de los dos.
- **Entrenar las ligas JUNTAS es mejor que cada una sola** (-3.3s / -3.0s sola).

`evaluacion_colb.md` (Colombia Primera B, sin cuotas, 841 partidos): el
modelo NO bate a la tasa de la liga (-0.90s y +0.01s). Sin precio ni
estadísticas, lo mejor es la media de la liga.

**Cuota de una sola casa (Promiedos) en ligas sin cuota histórica:** el
modelo completo extrapola mal cuando el empate está muy largo (dio 72-77% de
ambos marcan/más de 2.5 el 30/09). En la historia, con empate <= 23%
implícito, ambos marcan salió 55% y más de 2.5 58% (MLS 59%/63%). Corregir
hacia esas frecuencias antes de dar números.

`evaluacion_fotmob.md`: con y sin variables de FotMob en ARG (pendiente al
escribir esto; ver el fichero).

## Registro en papel

`data/registro_papel.csv` (ARG/BRA), `data/registro_papel_colb.csv`,
`data/resultados_papel.csv` (resultados que se conocen). No cambiar el modelo
por lo que salga ahí hasta tener 100+ partidos.

- 29/09 Unión Magdalena 1-1 Real Cartagena (Colombia B): modelo 48% ambos
  marcan, 57% menos de 2.5, marcador más probable 1-1 (13%). Un partido no
  dice nada del modelo.
