# Lo que da la API y no usamos (01/10/2026)

Revisión de las 25 rutas de `docs/openapi_highlightly.json`, campo a campo,
contra lo que guarda `data/`. Sin llamar a la API: especificación más las
respuestas crudas ya guardadas (`data/sondeo_perfil_jugador/*.json` y
`data/selecciones/raw/partido_hoy_*.json` de `main`).

## Ya lo pedimos y lo tiramos

| Ruta (ya la llamamos) | Guardamos | Viene y se tira |
|---|---|---|
| `/matches/{id}` | árbitro, tiempo, tarjetas con minuto | **goles con minuto y asistente, cambios (quién entra y sale), penaltis fallados, VAR** (`events`); **tiros con minuto, jugador, resultado y zona de la portería** (`shots`); **predicciones de la propia API** (`predictions.prematch`, varias al día; `live` durante el partido); **noticias** del partido; **estadio y aforo**; top 3 jugadores |
| `/players/{id}` | nacimiento, altura, pie, posición, valor, lesiones | **traspasos con precio** (de, a, fecha, valor en ese momento), **contrato** (fecha de llegada, fin de contrato, última renovación), **rumores de fichaje con probabilidad**, nacionalidad, lugar de nacimiento, noticias del jugador |
| `/players/{id}/statistics` | por liga: partidos, goles, asistencias, minutos, tarjetas | **todas las competiciones** (copa, Europa, selección), porterías a cero, entradas y salidas desde el banquillo, penaltis, autogoles |
| `/lineups/{id}` | dibujo e IDs del once | **dorsales, banquillo completo**, posición en el campo |
| `/box-score/{id}` | notas y estadísticas | **capitán**, dorsal |

## No la usamos nunca

| Ruta | Qué da |
|---|---|
| `/highlights` | **vídeos del partido** (resumen, goles, entrevistas), con miniatura y enlace para incrustar; verificados 1–48 h después |
| `/odds?oddsType=live` | **cuotas en directo** cada 10 minutos |
| `/teams/statistics`, `/standings` | casa/fuera ya calculado (lo sacamos nosotros; sin fecha final, no sirve para histórico) |

## Comprobado en respuestas reales

- Predicciones de la API: Inglaterra–España tiene **22 versiones** en 7 días
  (España 37% → 48%). Solo tipo 1X2 («three-way»).
- Noticias: 16 en Inglaterra–España, 0 en Chequia–Inglaterra.
- Estadio: viene en Chequia–Inglaterra (Fortuna Arena, Praga, 21.000), vacío
  en Inglaterra–España.
- Top players: viene, pero con las cifras vacías («-»).
- **Sin comprobar:** `shots`, `events` de goles y cambios, y
  `predictions.live` después del pitido (lo guardado es de antes de empezar).
  Antes de construir nada con ellos: sondear 2–3 partidos terminados.

## Qué se puede mostrar (por valor para la app)

1. **Partido minuto a minuto de verdad** (`events` + `shots`): goles con
   minuto y asistente, cambios, VAR; línea de tiros. Sustituye el «goals per
   half» del informe.
   - Cruce: cambios × nota del jugador → **«super-suplentes»**: quién cambia
     los partidos al entrar.
   - Cruce: minutos de gol → **cuándo marca y cuándo encaja cada equipo**
     (finales de partido, arranques).
   - Cruce: tarjetas por minuto × árbitro → perfil del árbitro según tramo.
2. **Probabilidad durante el partido** (`predictions.live`, si viene relleno):
   gráfico de quién iba ganando según avanzaba el partido. Es el «momentum»
   que pidió el usuario.
3. **Tres opiniones antes del partido**: 2yellow, el modelo de la API y las
   casas. Se puede medir quién acierta más (como «How we did»). Y cómo se
   movió la predicción de la API en la semana («humor del mercado»).
4. **Mercado de fichajes** (`/players/{id}`):
   - **contratos que acaban**: lista de jugadores libres el próximo verano,
     cruzada con su nota justa y su valor → «gangas a coste cero»;
   - **fichajes que salieron bien o mal**: precio pagado × nota desde que
     llegó (cruce con Moneyball);
   - **rumores** con probabilidad.
5. **Cansancio real** (`/players/{id}/statistics` con todas las
   competiciones): minutos de Champions, copa y selección. Hoy la rotación
   solo ve la liga (`rotacion` lo dice: «Champions y Copa no están»).
6. **Vídeos en el informe** (`/highlights`): resumen del partido dentro de la
   app. Ojo: algunos no se pueden incrustar por país; la ruta que lo dice no
   está en el plan gratuito.
7. **Banquillo y dorsales** (`/lineups`): alineaciones más reales y «fuerza
   del banquillo» (nota media de los suplentes).
8. **Noticias** del partido y del jugador: pestaña de noticias.
9. **Cuotas en directo**: movimiento del mercado durante el partido.

## Coste aproximado en llamadas (nada pedido)

| Idea | Llamadas | Nota |
|---|---|---|
| Sondeo previo (shots/events/live en partidos terminados) | 3 | lo primero |
| 1–3 para LaLiga 2026/27 (70 partidos) | ~70 | una por partido |
| 1–3 para LaLiga 2025/26 completa | ~380 | |
| 4 (perfiles de los jugadores de LaLiga) | ~600 | jugadores con minutos en 2026/27 |
| 5 (estadísticas por competición) | ~600 | |
| 6 (vídeos) | 1 por partido | o 1 por jornada filtrando por liga |
| Nations League (selecciones) | ~1 por partido | `/matches/{id}` ya se pide en el ciclo: basta con guardar más campos |
