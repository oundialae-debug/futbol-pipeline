# Bitácora de app_apostador

La bitácora general (`BITACORA.md` en la raíz) no se toca: el usuario pidió
que esta carpeta sea propia y que fuera de ella solo se copie. Lo de esta
carpeta se apunta aquí.

## 29/09/2026: maquetas explicadas para el público

- **Qué:** seis pantallas nuevas (`project/*.dc.html`) de una app de datos de
  fútbol para apostadores, publicadas en el lienzo
  https://claude.ai/artifact/FBTarsYtUpRSFEYTpVSvaG.
- **Por qué:** petición del usuario. Las maquetas del 29/09 estaban bien,
  pero alguien de fuera del proyecto no entendía los datos (Elo, Brier,
  sigmas, "fuerza real").
- **Cómo:** `generar_datos.py` lee `data/historico_partidos.csv`,
  `calendario.csv`, `historico_arbitro_clima.csv` y
  `historico_h2h_profundo.csv` y escribe `datos.json`. Sin API, sin
  descargas.
- **Diferencias con la maqueta anterior:** Sevilla 15.º por nivel (antes
  18.º), Málaga 17.º (antes 11.º), media de tarjetas 4,52 (antes 5,28).
  Detalle en `README.md`.
- **Ficheros:** `app_apostador/` entero. Nada fuera.

## 29/09/2026: versión 2, visual y con poco texto

- **Qué:** la lista de partidos (`Main.dc.html`) y la ficha del partido
  (`Partido.dc.html`) rehechas al estilo FotMob/Flashscore: cuota justa como
  número principal, etiquetas de 2-3 palabras, forma/goles/cara a cara en
  casillas de colores. Fuera la portada explicativa y el glosario
  (`Jornada.dc.html` y `Glosario.dc.html` borrados; la lista pasa a `Main`).
  Nivel y Árbitros se quedan igual (solo cambia la barra de navegación).
- **Por qué:** al usuario no le gustó la versión 1, salvo Nivel y Árbitros:
  no se trata de explicarlo todo, sino de que sea intuitivo o se explique
  con pocas palabras.
- **Datos:** los mismos de `datos.json`, sin llamadas ni descargas.

## 29/09/2026: versión 3, estilo Discord/Twitch y pestaña Pronósticos

- **Qué:** las cuatro pantallas con aspecto Discord/Twitch. La ficha del
  partido tiene pestañas; la primera, Pronósticos: los 5 más probables con
  nuestro %, cuota justa y cuánto acierta la casa en ese mercado, y tu cuota
  contra la justa del pronóstico elegido. Nivel y Árbitros: mismo contenido,
  nuevo aspecto.
- **Por qué:** el usuario pidió los pronósticos con el acierto de la casa, y
  un diseño que no se parezca a FotMob.
- **Datos:** `generar_datos.py` añade `pronosticos` a `datos.json` (Poisson de
  goles comprobado en 829 partidos y acierto de la casa por mercado). Lee
  además `cuotas_historicas_fd.csv` y `cuotas_cosechadas.csv`. Sin API ni
  descargas.
