# app_apostador: maquetas de app explicadas para cualquier apostador

Carpeta propia. No modifica nada fuera de ella: solo **lee** `data/`.

Lienzo con las pantallas: https://claude.ai/artifact/FBTarsYtUpRSFEYTpVSvaG
(privado hasta que se comparta desde su menú Compartir).

## Idea

Datos para apostar que se entienden de un vistazo, como FotMob o
Flashscore: cuotas, colores y puntos en vez de párrafos. Lo que haga falta
explicar, en 3-4 palabras.

- El número principal es la **cuota justa** (100 ÷ %). El % va debajo, pequeño.
- El favorito, relleno de color.
- Una etiqueta corta por partido cuando hay algo que ver: «Tabla engaña»,
  «Mejor de lo que va», «Igualado», «Goles».
- En el partido, escribes la cuota de tu casa y sale «Buena cuota +6%»,
  «Cuota justa» o «Cuota baja −7%».
- Forma, goles y cara a cara como casillas de colores, no como frases.

## Pantallas (`project/`)

| fichero | pantalla |
|---|---|
| `Main.dc.html` | Partidos de la jornada 8 con cuota justa 1-X-2 |
| `Partido.dc.html` | Real Madrid – Villarreal: tu cuota contra la justa, nivel, forma, goles, cara a cara |
| `Nivel.dc.html` | ¿Suerte o nivel?: tabla frente a nivel (se mantiene de la versión 1) |
| `Arbitros.dc.html` | Árbitros y tarjetas (se mantiene de la versión 1) |

## Datos

`generar_datos.py` los calcula en local, sin API, y escribe `datos.json`.
Las pantallas copian esos números.

- Nivel = el Elo de `scripts/rasgos.py` (K=20, local +60), sobre los
  1.589 partidos de LaLiga del histórico.
- Probabilidad 1-X-2: logística ordenada sobre la diferencia de nivel,
  ajustada con 1.209 partidos (sin la primera temporada, en la que el Elo
  arranca de cero). Calibración del local: dice 20% → pasa 22%; 38% → 35%;
  52% → 49%; 67% → 73%; 82% → 85%.
- Árbitros: temporadas 2025/26 y 2026/27, 395 partidos, mínimo 15 por
  árbitro. "Diferencia clara" = 2 sigmas o más frente a la media de LaLiga.

**Cambian respecto a la maqueta anterior**: allí el Sevilla salía 18.º por
nivel y el Málaga 11.º; con el Elo del proyecto salen 15.º y 17.º. La media
de tarjetas era 5,28 y aquí sale 4,52 (395 partidos con árbitro y
tarjetas de `historico_partidos.csv`). No se ha averiguado de dónde salían las
cifras anteriores. Se usan las recalculadas porque se pueden reproducir.

**Fuera**: "nivel del once" (goles + asistencias de los titulares la
temporada pasada). No se ha recalculado, así que no se muestra.
