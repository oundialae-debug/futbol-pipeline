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

## Términos de fútbol en inglés (30/09/2026)

Probados 109 (corner, throw-in, bench, shot, cross, save, goal kick, free
kick, penalty, offside, header, tackle, dribble, assist, clean sheet, volley,
tap-in, own goal, kickoff, whistle, top bins, backheel…), solos y con
stats/data/hub.

- **Solos: todos ocupados en `.com`.** Con `.app` y `.io` libres: **throwin,
  backheel**. El resto, ocupados en `.com` y `.app`.
- **Compuestos con `.com`, `.app` y `.io` libres:** throwinstats, throwinhub,
  headerstats, tacklestats, offsidestats, freekickstats/data/hub, tapinhub,
  topbinsstats/data/hub, cleansheetstats, cleansheethub.
- Sin comprobar: marca registrada y apps con ese nombre.

## Dos palabras en inglés (30/09/2026)

Probados 126 términos de fútbol solos: ninguno con `.com` libre. Probadas
870 combinaciones de un término de fútbol con una palabra corta (lens, edge,
deck, lab, base, pulse, radar, view, wire, map, book, log, room, zone, side,
line, post, box, hub, wall, club): unas 340 con `.com`, `.app` e `.io`
libres.

Las mejores por longitud y pronunciación mundial: **rondolens, rondoedge,
rondopulse, rondoradar, rondowire, rondomap, pannalens, pannaview,
nutmegview, backheellens, strikerlens, keeperwire, wingerlens**.

Sin comprobar: marca registrada y apps con ese nombre. `.io` solo es pista.

## Qué datos tenemos y qué podemos crear cruzándolos (30/09/2026)

Revisado fichero a fichero. Todo en `data/`, sin llamar a la API.

| dato | fichero | alcance |
|---|---|---|
| Partidos + 39 estadísticas por equipo | `historico_partidos.csv` | 6 ligas, 2022/23→hoy; xG de equipo desde 2025/26 |
| Descanso (marcador al HT, tiros, córners, tarjetas) | `football_data/*.csv` | 6 ligas, 2022/23→hoy |
| Alineaciones (once por ID) | `historico_lineups.csv` | desde abr-2024 (+ 2023/24 vía box-score) |
| Jugador por partido: nota, xG, xA, tiros, pases clave, regates, duelos, faltas, xG evitado (porteros) | `historico_xg_jugador.csv` | 3.046 partidos, desde abr-2025 |
| Jugador por temporada: partidos, minutos, goles, asist., tarjetas | `historico_jugador_stats.csv` | 148.833 filas |
| Tarjetas con jugador y minuto | `eventos_tarjetas_jugadores_2025_26.csv` | solo 2025/26 |
| Perfil: edad, altura, pie, posición | `jugador_perfil.csv` | 4.953 jugadores |
| Valor de mercado (histórico) | `jugador_valor_mercado.csv` | 4.306 jugadores, 2004→hoy |
| Lesiones (motivo, desde-hasta, partidos perdidos) | `jugador_lesiones.csv` | 2022→hoy |
| Árbitro y clima | `historico_arbitro_clima.csv` | ~91% / 95% de partidos |
| Cara a cara real | `historico_h2h_profundo.csv` | últimos 10 por par, desde antes de 2022 |
| Cuotas de 50+ casas con hora de captura | `cuotas_cosechadas.csv` | ago-sep 2026 |
| Cierre de Pinnacle/Betfair | `cuotas_historicas_fd.csv` | 2022/23→hoy |

### Ideas nuevas (cruces que otras apps no dan)

Marcadas: **[probado]** ya medido en el proyecto; **[por comprobar]** hay que
medirlo antes de enseñarlo (regla del proyecto: nada sin comprobar).

1. **Peso de las bajas.** Lesiones × valor de mercado × minutos/nota ×
   alineaciones: «Hoy le faltan jugadores que suman el 28% de sus goles y
   asistencias» y «con él / sin él». [por comprobar el efecto; como dato
   descriptivo sirve ya]
2. **Con él / sin él.** Alineaciones × resultados × xG: puntos por partido y xG
   del equipo con y sin cada titular. [por comprobar muestra: n pequeño, dar el n]
3. **Ciclo de amarillas.** Tarjetas por jugador y minuto: «a una amarilla de
   la sanción», «ve la amarilla sobre el minuto 60». [datos de 2025/26; falta
   la regla de sanción de cada liga]
4. **Termómetro de tarjetas del partido.** Árbitro (tarjetas y minuto medio)
   × faltas de los dos equipos × jugadores al límite. [árbitro probado como
   la mejor variable de tarjetas; el resto por comprobar]
5. **Tabla merecida.** Puntos esperados según el xG de cada partido frente a
   los puntos reales: quién va por encima y quién por debajo. Complementa
   «¿Suerte o nivel?» (Elo). [por comprobar si predice]
6. **Rachas que no aguantan.** Goles frente a xG, de equipo y de jugador:
   «marca el doble de lo que le toca». [por comprobar; la forma reciente ya
   se vio que no añade al modelo, así que no venderlo como predicción]
7. **Segundas partes.** Marcador al descanso × final (football-data, 4
   temporadas): quién remonta, quién se cae, puntos ganados/perdidos tras el
   descanso. [por comprobar estabilidad año a año]
8. **Cansancio y rotación.** Días desde el último partido × titulares que
   cambia cada equipo: «suele rotar 4 jugadores tras jugar entre semana».
   [rotación medida; efecto por comprobar]
9. **Portero que salva.** xG evitado: «su portero le ha ahorrado 4 goles; la
   defensa es peor de lo que parece». [desde abr-2025]
10. **Moneyball.** Valor de mercado × xG/xA/nota por 90: jugadores que rinden
    muy por encima de lo que valen, y plantillas que rinden por debajo de su
    valor. [descriptivo]
11. **Duelo de estilos.** Posesión, pases, duelos y centros frente a la media
    de la liga: «equipo de posesión contra equipo que presiona», y cómo le
    fue a cada uno contra ese estilo. [por comprobar muestra]
12. **Cuota justa y acierto de la casa.** Ya hecho: nuestro %, cuota justa,
    acierto de la casa en ese mercado y «tu cuota». Añadible: cómo se movió
    la cuota antes del partido (tenemos hora de captura). [probado]

### Lo que NO aporta (ya lo tienen otras o no sirve)

- Mapa de tiros: lo da FotMob y además no tenemos coordenadas.
- Momentum en directo: no tenemos datos en vivo.
- Clima como predictor: probado, no ayuda (se puede mostrar como contexto).

### Recomendación de orden

1 Peso de las bajas · 3-4 Tarjetas (ciclo + termómetro) · 5 Tabla merecida ·
7 Segundas partes · 12 Cuotas (ya hecho). Son las más únicas y las que
mejor responden a «¿qué va a pasar en este partido?».

## Resultado: los 12 datos calculados y comprobados (30/09/2026)

`analisis_app.py` → `datos_app.json`. LaLiga, ejemplo Real Madrid. Sin API.

| # | dato | comprobación | veredicto |
|---|---|---|---|
| 1 | Peso de las bajas | descriptivo | RMA: le faltan jugadores con el 13% de sus G+A (Valverde, Militão, Rodrygo) |
| 2 | Con él / sin él (sobre lo esperado por Elo) | n por cada lado | ruidoso: con menos de ~20 partidos por lado puede ser azar; se enseña el n |
| 3 | Ciclo de amarillas | datos limpiados | la API da el mismo jugador con 2 IDs; unificados 20; sin eso nadie llegaba al límite |
| 4 | Termómetro de tarjetas | 820 partidos, Brier emparejado | equipos + árbitro bate a la media de liga por **3,2 sigmas** |
| 5 | Tabla por Elo (puntos esperados) | J7 → tabla final, 3 temporadas | Elo 0,87/0,72/0,68 vs tabla 0,79/0,83/0,65: gana 2 de 3, por poco. Valor = contexto, no «predice mucho mejor» |
| 6 | Segundas partes | estabilidad año a año | 0,59-0,73, pero controlando por nivel 0,11-0,49: casi todo es calidad. Se enseña como dato, no como rasgo |
| 7 | Rotación y descanso | descriptivo | solo liga: Champions y Copa no están |
| 8 | Portero (goles evitados) | mitad vs mitad 2025/26 | 0,31: pista, no ley |
| 9 | Rachas (goles vs xG) | 1ª vuelta → 2ª 2025/26 | persiste 0,34; el xG predice tan bien como los goles (0,81 vs 0,80) |
| 10 | Moneyball | por posición, sin valor 0 | descriptivo |
| 11 | Duelo de estilos | z-scores vs liga | RMA contra equipos de posesión: −0,22 pts/partido vs Elo (11 partidos, poca muestra) |
| 12 | Cuotas | apertura → cierre (football-data) | las cosechadas se capturaron todas a la vez (20/09): sin movimiento desde ahí |
| + | Informe post-partido | — | historia por mitades + tarjetas por minuto, merecido por xG (Poisson), sorpresa previa, Elo antes/después |

**Momentum a posteriori:** sin minutos de goles ni cambios guardados. La API
los da en `/matches/{id}` (eventos: goles, tarjetas, cambios, VAR) y el script
de 2025/26 solo guardó las tarjetas. Hace falta un backfill con permiso.

**Fallos silenciosos encontrados:** tarjetas del mismo jugador con dos IDs
(20 casos), minutos de tarjeta negativos (8 filas), posición «Forward» (no
«Attacker»), valor de mercado 0 = sin dato, porteros sin nombre.
