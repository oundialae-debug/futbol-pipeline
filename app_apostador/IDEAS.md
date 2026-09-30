# Ideas para la app (guardadas el 30/09/2026)

Decisión del usuario: la app no gira solo en torno a las cuotas. Debe dar
datos de fútbol al nivel de FotMob y mejores que Flashscore, con las cuotas
como una pestaña más. La app será principalmente en inglés.

## Qué construir después del nombre

1. **Partido con más pestañas:** estadísticas, alineaciones, cara a cara y
   árbitro (además de Pronósticos, Datos y Cara a cara, que ya existen).
2. **Pantalla de equipo:** forma, xG, once habitual, calendario.
3. **Pantalla de jugador:** minutos, goles y asistencias por temporada, xG y xA.

## Datos que ya tenemos en `data/` (sin llamar a la API)

| dato | fichero | notas |
|---|---|---|
| Suerte o nivel: goles reales frente a xG | `historico_partidos.csv` (`l_/v_expected_goals`) | xG de equipo desde 2025/26; en 2024/25 casi no hay (5%) |
| ~39 estadísticas por equipo y partido | `historico_partidos.csv` | posesión, tiros, ocasiones claras, pases clave, duelos, entradas, paradas |
| Alineaciones y rotaciones | `historico_lineups.csv` | 2023/24 completado con titulares de `/box-score` |
| Jugadores: minutos, goles y asistencias | `historico_jugador_stats.csv` | por temporada |
| xG y xA por jugador | `historico_xg_jugador.csv` | solo desde abril de 2025 |
| Árbitros | `historico_arbitro_clima.csv`, `historico_tarjetas.csv` | tarjetas por partido frente a la media |
| Cara a cara profundo | `historico_h2h_profundo.csv` | últimos 10 reales, desde 2022 |
| Nivel (Elo) frente a tabla | calculado en `generar_datos.py` | único, no lo tiene nadie más |
| Pronósticos y acierto de la casa | calculado en `generar_datos.py` | ver README |
| Perfil, valor de mercado, lesiones | `jugador_perfil.csv`, `jugador_valor_mercado.csv`, `jugador_lesiones.csv` | sin revisar su calidad |

## Límites (decirlos siempre)

- Datos al día, **no en directo**. Un marcador en vivo como el de Flashscore
  exige llamar a la API cada pocos minutos: caro y necesita el sí del usuario
  para cada llamada (regla del `CLAUDE.md` de la raíz).
- **No hay mapa de tiros con coordenadas**, solo tiros dentro y fuera del área.
- xG por jugador desde abril de 2025; xG de equipo casi vacío en 2024/25.
- Antes de mostrar una cifra nueva, recalcularla y comprobarla (regla del
  proyecto: los fallos aquí no dan error, dan números con buena pinta).

## Nombre de la app

Sale del enfoque en cuotas: **Fairline**, Fair Odds, TruOdds, OddsFair,
Fair Price. Fair Play descartado como marca: es un término genérico y
difícil de registrar (los nombres descriptivos protegen poco), y sus dominios
`.com`, `.app` y `.io` están ocupados.

Como la app es de datos de fútbol, no de cuotas, candidatos nuevos:
**Pitchside, Kickoff Data, Gaffer, Pitchmap**.

### Dominios (comprobado el 30/09/2026 por DNS y RDAP)

Con servidores DNS = registrado. El RDAP de `.io` y `.co` no es fiable
(contradice al DNS), así que esos casos son solo una pista.

| nombre | .com | .app | .io | .co | .football |
|---|---|---|---|---|---|
| Pitchside | ocupado | ocupado | ocupado | ocupado | ocupado |
| Gaffer | ocupado | ocupado | ocupado | ocupado | ocupado |
| Pitchmap | ocupado | ocupado | ocupado | sin DNS (sin confirmar) | **libre** |
| Kickoff Data | ocupado | **libre** | sin DNS (sin confirmar) | sin DNS (sin confirmar) | **libre** |

«Libre» = sin DNS y el RDAP del registro dice que no existe. Falta
confirmar en un registrador (Namecheap, Cloudflare) y ver precio. Que un
dominio esté libre no dice nada de si el nombre está registrado como marca
ni de si hay una app con ese nombre: eso no se ha comprobado.

## Nombres inventados, al estilo Flashscore / SofaScore / FotMob (30/09/2026)

El usuario descartó los nombres evidentes (Pitchside, Gaffer…): quiere algo
como Flashscore, SofaScore o FotMob, donde el nombre no dice «datos de
fútbol» directamente. Fórmula: palabra con gancho + palabra de función
(score, stats, mob, data), o palabra inventada.

Comprobado por DNS y RDAP. Método validado: da «ocupado» en sofascore.com,
flashscore.com, fotmob.com, livescore.com, onefootball.com, fbref.com,
transfermarkt.com y understat.com, y «libre» en una palabra sin sentido.
El `.io` es solo pista (su RDAP no es fiable).

- Palabras sueltas de fútbol (regista, cutback, halfspace, rondo, panenka,
  rabona, nutmeg, dugout, tifo, crossbar…): todas ocupadas en `.com`, `.app`
  y `.io`.
- Con `.com`, `.app` y `.io` libres: **rondoscore, rondostats, rondodata,
  rondomob, panenkascore, panenkastats, registascore, registastats,
  tifostat, cutbackstats, halfspacedata, mezzalastats, nutmob, kopmob,
  ballmob, fotstat, kopstat**, y muchas más de la misma fórmula.
- Sin comprobar: si están registradas como marca o ya las usa alguna app.
  `nutmob` puede chocar con Nutmeg (empresa de inversión).
