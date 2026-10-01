# Estructura final de 2yellow (plantilla para todo lo siguiente)

Petición del usuario (01/10/2026): todo lo que acabemos metiendo **y él
confirme** queda aquí como estructura fija. Cualquier partido, selección o
liga nueva se monta con estas tarjetas, en este orden, con estas reglas.
Lo que aún no ha confirmado va marcado **pendiente**: no se copia a otras
pantallas hasta que diga que sí. Al confirmarlo, cambiar el estado aquí (y
apuntarlo en `BITACORA.md`).

Ejemplo vivo: lienzo de la Nations League
(https://claude.ai/artifact/PyGg13vymnA4UtaYcunLzR), generado por
`diseno_nl/nl_datos.py` + `diseno_nl/generador/nl_pantallas.py`.

## Reglas comunes

- Textos de la app en inglés. Aspecto de app publicada: nada provisional.
- Si falta un dato, **la tarjeta no sale** (o se calcula con nuestro modelo).
  Nunca se inventan cuotas ni datos de terceros.
- Sin la predicción de la propia API (petición del usuario, 01/10/2026).
- **Colores (01/10/2026, queja del usuario: España y Chequia las dos en
  rojo):** los de las equipaciones reales 2026/27 (1ª, 2ª y 3ª) sacados de
  Wikipedia (`colores/`). Nunca dos equipos con el mismo color en la misma
  vista:
  - un partido: `kits(local, visitante)`; el visitante, la primera de sus
    equipaciones que no choque;
  - varios equipos a la vez (grupo, «What's at stake»): `kgrupo(...)`, con
    los dos del partido fijos;
  - tablas largas: `klista(...)`, filas vecinas distintas.
- Muestra pequeña: el n al lado («20 games», «since 2025»).
- Ninguna llamada nueva a la API sin un sí del usuario para esa llamada.

## Previa de un partido (pantalla Partido)

| # | Tarjeta | Qué enseña | Datos | Estado |
|---|---|---|---|---|
| 0 | Cabecera | escudos, hora, ciudad, puesto FIFA (o en la liga) | calendario | en uso |
| 0b | Sede | estadio y aforo, previsión del tiempo, hora; árbitro solo si está designado | `/matches/{id}` | **pendiente** |
| 1 | Win chance | 1X2 y cuota justa (100/p) | nuestro modelo | en uso |
| 2 | Goals | más de 1.5/2.5/3.5, ambos marcan, marcador probable, quién marca primero | nuestro modelo | en uso |
| 3 | Corners & cards | córners y tarjetas esperados y líneas | nuestro modelo | en uso |
| 4 | Form | últimos 5 de cada uno, el más reciente a la derecha | histórico | en uso |
| 5 | What's at stake | puesto final de cada equipo del grupo/tabla (20.000 simulaciones) y top 2 si gana/empata/pierde | modelo + calendario | **pendiente** |
| 6 | Likely XIs | último once con nota justa | alineaciones + notas | en uso |
| 6b | Squads this season | valor de mercado de los onces, minutos y G+A con sus clubes esta temporada, 3 más en forma, lesiones actuales | `/players/{id}` y `/players/{id}/statistics` de los titulares probables | **pendiente** |
| 7 | Style clash | medias por partido de los dos (posesión, tiros a puerta, ocasiones claras, goles a favor/en contra, porterías a cero) | estadísticas de partido | **pendiente** |
| 8 | Last time out | último partido de cada uno minuto a minuto: tiros cada 5', goles con asistente | `/matches/{id}` (`events`, `shots`) | **pendiente** |
| 9 | Last meeting | último cara a cara minuto a minuto (goles con asistente), xG, tiros a puerta, ocasiones, 3 mejores notas, y los anteriores | `/head-2-head` + `/matches/{id}` + box-score | **pendiente** |

## Informe de un partido terminado (pantalla Report)

| # | Tarjeta | Qué enseña | Datos | Estado |
|---|---|---|---|---|
| 1 | Sede | estadio, árbitro, tiempo | `/matches/{id}` | **pendiente** |
| 2 | Match story | tiros cada 5' por equipo, goles, rojas, momento clave | `events` + `shots` | **pendiente** |
| 3 | Deserved? | goles frente a xG | estadísticas | en uso |
| 4 | Shots | tiros por resultado y zona de la portería | `shots` | **pendiente** |
| 5 | Our call vs the bookies | nuestro pronóstico frente al de las casas, y acierto | registro + cuotas reales | en uso |
| 6 | Key stats | estadísticas principales | estadísticas | en uso |
| 7 | Best players | mejores notas | box-score | en uso |
| 8 | From the bench | cambios con la nota del que entra | `events` + box-score | **pendiente** |
| 9 | Goalkeepers | paradas y nota de los porteros | box-score | en uso |
| 10 | In the news | titulares del partido (filtrados) | `/matches/{id}` (`news`) | **pendiente** |

## Trampas de datos ya conocidas (no redescubrir)

- La ciudad del partido sale de `venue`, no se supone: Croacia–Inglaterra se
  juega en Rijeka, no en Zagreb.
- Los eventos de la API llegan sin tildes («P. Sucic»): recuperar el nombre
  de nuestros datos.
- `/head-2-head` da como mucho 10, pero solo los que tiene: Croacia–Inglaterra,
  2.
- `/lineups` solo desde 40' antes del partido: no pedirlas antes.
- Temporada en `/players/{id}/statistics`: «26/27» en Europa, «2026» en la MLS.
- Vídeos (`/highlights`): fuera hasta aclarar si es legal ponerlos.

- En un cambio, `player` es el que **sale** y `substituted` el que **entra**.
- Un penalti marcado llega como `Penalty`, no `Goal`.
- La lista de `shots` no cuadra al 100% con las estadísticas del equipo:
  lista para la línea del partido, estadísticas para los totales.
- Nota del que entra: buscarla solo entre suplentes, desempate por inicial
  (Croacia tiene dos Pašalić).
- Noticias: filtrar por el partido; el dominio `bbc.co.ukundefined` llega roto.
- `predictions.live` reacciona tarde: no sirve como «momentum».
- Desempate de la simulación de grupo: puntos, duelos entre empatados,
  diferencia de goles, goles a favor. No se afirma qué premio da cada puesto.
