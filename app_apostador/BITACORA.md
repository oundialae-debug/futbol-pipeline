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

## 30/09/2026: ideas de datos y nombre

- **Qué:** `IDEAS.md` con las ideas de pantallas y datos que se harán a
  continuación (partido con más pestañas, equipo, jugador), qué datos hay en
  `data/` para cada una, sus límites y el estudio de nombre y dominios.
- **Por qué:** el usuario quiere una app de datos al nivel de FotMob, no solo
  de cuotas, y pidió guardar las ideas. La app será en inglés.
- **Dominios:** consultas DNS y RDAP públicas (`dns.google`, `rdap.org`), sin
  API de Highlightly. Resultado en `IDEAS.md`.
- **Ficheros:** `app_apostador/IDEAS.md`. Nada fuera de la carpeta.

## 30/09/2026: nombres inventados

- **Qué:** búsqueda de nombres al estilo Flashscore/SofaScore/FotMob y
  comprobación de dominios (unos 200 nombres). Resultado en `IDEAS.md`.
- **Por qué:** el usuario descartó los nombres evidentes.
- **Cómo:** DNS y RDAP públicos, sin API de Highlightly. Validado contra
  sitios conocidos antes de fiarse de los «libre».
- **Ficheros:** `app_apostador/IDEAS.md`.

## 30/09/2026: términos de fútbol en inglés

- **Qué:** 109 términos de fútbol en inglés comprobados en `.com`, `.app` e
  `.io`. Resultado en `IDEAS.md`. Consultas DNS y RDAP, sin API.

## 30/09/2026: combinaciones de dos palabras

- **Qué:** 870 combinaciones de término de fútbol + palabra corta, con sus
  dominios. Resultado en `IDEAS.md`. DNS y RDAP, sin API.

## 30/09/2026: diseño nuevo (mezcla propia de FotMob y Flashscore)

- **Qué:** `diseno_nuevo/`, un lienzo aparte con un solo diseño en inglés y
  datos falsos (clubes y jugadores inventados): Matches, Match y Lineups.
  Lienzo: https://claude.ai/artifact/5i65iCH12v7HmM1oSY7R8K
- **Por qué:** el usuario pidió inventar un diseño a partir de FotMob y
  Flashscore sin copiarlos, y ver solo uno. Sustituye al estilo Discord/Twitch
  (que queda en `project/` como referencia).
- **Ideas del diseño:** filas densas como las de Flashscore, pero cada una con
  una barra de probabilidad 1 · X · 2 y una etiqueta de dato (xG, tip);
  ficha de partido con tarjeta negra, línea de tiempo, momentum, estadísticas
  centradas y mejores tips con el acierto de la casa; alineaciones con notas
  por jugador. Fondo papel cálido, negro tinta, azul y amarillo ácido.
- **Datos:** todos inventados. No hay cifras del proyecto en este diseño.
- **Ficheros:** `app_apostador/diseno_nuevo/`. Nada fuera de la carpeta.

## 30/09/2026: diseño oscuro, siete pantallas

- **Qué:** `diseno_nuevo/` rehecho: más oscuro y con más contenido, solo diseño,
  datos falsos (clubes inventados). Siete pantallas: Matches, Match, Match
  stats, Lineups, Team, Player y Tips. Mismo lienzo:
  https://claude.ai/artifact/5i65iCH12v7HmM1oSY7R8K
- **Por qué:** el usuario dijo que el diseño anterior era muy pobre, que lo
  quería más oscuro y que nos centráramos solo en diseño; los datos reales
  se ajustan después.
- **Cómo:** `diseno_nuevo/generador/` (Python) genera los `.dc.html` con las
  mismas cabecera, colores y barra de navegación. Los `.dc.html` son la
  versión que vale.
- **Datos:** todos inventados. Sin API ni descargas.

## 30/09/2026: tres direcciones visuales

- **Qué:** `diseno_direcciones/`, un lienzo con tres direcciones oscuras y
  distintas, dos pantallas cada una (inicio y partido): A Night Pitch,
  B Poster, C Glass. https://claude.ai/artifact/FK9bJiMQKuhDwmGCaCnxU7
- **Por qué:** el usuario pidió solo diseño, sin ocuparse de cómo se muestran
  los datos (todo es relleno).
- **Ficheros:** `app_apostador/diseno_direcciones/`. Sin API ni descargas.

## 30/09/2026: diseño elegido

- **Qué:** el usuario elige el diseño oscuro de siete pantallas
  (`diseno_nuevo/`, https://claude.ai/artifact/5i65iCH12v7HmM1oSY7R8K) como
  base de la app. Las tres direcciones de `diseno_direcciones/` quedan
  descartadas (se conservan como referencia).

## 30/09/2026: nombre 2yellow y logotipo

- **Qué:** nombre elegido por el usuario: **2yellow**. Logotipo: dos tarjetas
  amarillas que se solapan; donde se cruzan, roja (dos amarillas = roja).
  Palabra «2yellow» con el «2» en amarillo. Hoja de logo (`Logo.dc.html`:
  versión grande, icono de app, sobre amarillo, tamaños pequeños, sobre claro,
  solo palabra y colores) y logo puesto en la cabecera de `Main.dc.html`.
- **Ficheros:** `diseno_nuevo/generador/logo.py` (el logo en un sitio),
  `s1.py`, `s4_logo.py` y los `.dc.html` generados. Nombre sin comprobar como
  marca ni dominio.

## 30/09/2026: inventario de datos e ideas de cruces

- **Qué:** inventario de lo que hay en `data/` y 12 ideas de datos nuevos
  cruzando ficheros, con qué está probado y qué no. En `IDEAS.md`.
- **Por qué:** el usuario quiere definir los datos antes de llevarlos al
  diseño y crear cosas que no tengan otras apps.
- **Cómo:** solo lectura de cabeceras y conteos. Sin API ni descargas.
