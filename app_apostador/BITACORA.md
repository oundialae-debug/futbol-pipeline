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

## 30/09/2026: los 12 datos, calculados, comprobados y en el diseño

- **Qué:** `analisis_app.py` calcula los 12 datos pedidos más el informe
  post-partido; `datos_app.json` con los resultados; el lienzo 2yellow pasa a
  datos reales de LaLiga en 9 pantallas (portada, previa RMA–Villarreal,
  informe Atlético 2-1 Madrid, sus estadísticas y alineaciones, Real Madrid,
  Mbappé, tabla Elo, tips). Generador en `diseno_nuevo/generador/s5*_real.py`.
- **Por qué:** petición del usuario; la distinción es el Elo; la app es tanto
  de después del partido como de antes.
- **Comprobaciones:** detalle en `IDEAS.md`. Termómetro 3,2 sigmas; Elo en J7
  solo algo mejor que la tabla; segundas partes casi todo nivel.
- **Fallos silenciosos:** tarjetas con dos IDs por jugador (unificados),
  minutos negativos, etiqueta de posición, valor 0, porteros sin nombre.
- **Datos:** solo lectura de `data/`. Sin API ni descargas.

## 30/09/2026: colores de club y segunda equipación

- **Qué:** `diseno_nuevo/generador/equipaciones.py`: dos equipaciones de dos
  colores por club. En cada partido el visitante cambia a la segunda si su
  color choca con el del local (distancia CIE76 < 30). Las barras se aclaran
  hasta contraste 3:1 sobre el fondo oscuro. Franjas de dos colores junto al
  nombre, como en los marcadores de TV. Aplicado a portada, previa, informe,
  estadísticas, alineaciones (camiseta en dos mitades) y tabla Elo. Hoja nueva
  `Kits.dc.html` con los colores de los 20 clubes y ejemplos.
- **Por qué:** petición del usuario.
- **Comprobación:** las 506 parejas de LaLiga sin choque tras la regla (88 con
  segunda equipación). Málaga tenía las dos equipaciones azules y chocaba con
  4 equipos: su segunda pasa a blanca.
- **Ojo:** colores de la primera, tradicionales; los de la segunda,
  aproximados (cambian cada temporada): revisar.

## 30/09/2026: los 19 comentarios del lienzo 2yellow, aplicados

- **Qué:** cambios pedidos en los comentarios del lienzo
  (https://claude.ai/artifact/5i65iCH12v7HmM1oSY7R8K), aplicados también en
  las demás pantallas donde encajan (petición del usuario):
  - Porcentajes con «%» y cabecera «Win chance · 1 X 2»; etiquetas «X better /
    worse than table: Elo Nth»; «Books hit» sustituido por «Very likely /
    Likely / Toss-up» (portada y Tips).
  - Colores: una franja para clubes de un color (Madrid, Villarreal, Getafe,
    Celta, Valencia, Sevilla, Osasuna, Mallorca, Oviedo), dos para rayas; los
    números de cada equipo en su color en todas las pantallas.
  - Previa: bajas en «Out» (lesión que pasa del partido + sancionados: Huijsen,
    roja) y «Doubtful» (vuelven ±2-3 días del partido: Valverde, Etta Eyong);
    choque de estilos con etiquetas y 4 datos en unidades con la media de LaLiga.
  - Informe: «Deserved?» con tiros, ocasiones, pases al último tercio, paradas
    y goles evitados; «Our call vs the bookies» (nuestro % previo frente a la
    mediana de 49 casas cosechadas antes del pitido, sin margen): 3/4 cada uno.
  - Estadísticas: zona contra zona y 8 duelos por puesto en la alineación.
  - Alineaciones con posiciones reales por dibujo (4-4-2, 4-2-3-1).
  - Equipo: «Second halves» (70 pts al descanso contra 86 reales, +16, 2.º de
    LaLiga 2025/26); selector Last 5 / Last 10 / Season en goles vs xG y
    portero.
  - Jugador: rival y minutos en cada nota; percentiles con selector de tramo.
  - «2yellow Ranking» (ordenado por Elo) y pestaña «LaLiga table» con P/G/E/P,
    DG, puntos merecidos, suerte y flecha si el ranking lo pone más arriba o
    abajo; selectores de tramo en rachas y porteros.
  - Tips: sin campo para escribir la cuota; hueco [odds from API] para mejor
    cuota, media y veredicto.
  - Menos texto explicativo en todas las pantallas; etiqueta «few games».
- **Datos:** `datos_extra.py` (nuevo) escribe `datos_extra.json`. Solo lee
  `data/`. Sin API ni descargas.
- **Comprobaciones:** las líneas de la alineación vienen de izquierda a derecha
  (Hancko, Romero, Pubill, Llorente), comprobado con los nombres; percentiles
  solo contra delanteros con la mitad de los minutos posibles del tramo; las
  cuotas de la casa del informe son previas al partido.
- **Ficheros:** `datos_extra.py`, `datos_extra.json`,
  `diseno_nuevo/generador/*.py`, `diseno_nuevo/project/*`.

## 30/09/2026: duelos con cada equipo en su lado

- **Qué:** en «Head to head» (estadísticas) el Atlético va siempre a la
  izquierda y el Madrid a la derecha, en dos apartados (ataque de cada uno);
  antes el atacante iba siempre a la izquierda y el Madrid cambiaba de lado.
  Nombres con inicial («M. Cucurella», «Vinícius J.»).
- **Por qué:** comentario del usuario en el lienzo.
- **Ficheros:** `diseno_nuevo/generador/s5b_real.py`, `project/Stats.dc.html`,
  `project/canvas.json`. Sin API.

## 30/09/2026: nota media de cada once contra sus últimos 10

- **Qué:** en alineaciones, nota media del once de cada equipo y diferencia
  con la media de sus 10 partidos de liga anteriores (Atlético 6,91 frente a
  7,06; Madrid 6,95 frente a 7,13). Cada jugador lleva ▲/▼ si su nota se aleja
  0,3 o más de su media de los 10 anteriores (solo con 5+ partidos previos).
- **Por qué:** comentario del usuario en el lienzo.
- **Datos:** `datos_extra.py` añade `notas_once` (solo partidos anteriores al
  del informe; media del once solo con 9+ notas). Sin API.
- **Ficheros:** `datos_extra.py`, `datos_extra.json`,
  `diseno_nuevo/generador/s5b_real.py`, `project/Alineacion.dc.html`,
  `project/canvas.json`.

## 30/09/2026: dónde lo dejamos (para retomar otro día)

- **Lienzo vigente:** https://claude.ai/artifact/5i65iCH12v7HmM1oSY7R8K
  (versión 11). Todos los comentarios del usuario resueltos; le gusta como está.
- **Cómo regenerar:** `python3 analisis_app.py` y `python3 datos_extra.py`
  (datos), luego en `diseno_nuevo/generador/`: `s5a_real.py`, `s5b_real.py`,
  `s5c_real.py`, `s6_kits.py`. Publicar `diseno_nuevo/project/canvas.json`
  con `root` = `diseno_nuevo` y los `.dc.html` en `files`. Si cambia el alto
  de una pantalla, cambiarlo también en `canvas.json`.
- **Forma de trabajar pedida:** el usuario manda comentarios en el lienzo;
  cuando dice «no empieces hasta que diga empieza ya», solo se contesta y se
  apunta. Cada cambio se aplica en todas las pantallas donde encaje.
- **Pendiente, necesita su permiso (llamadas a la API):**
  1. Minutos de goles y cambios (`/matches/{id}`, ~450 llamadas) para un
     momentum real en «Match story».
  2. Cuotas previas de los partidos próximos para rellenar los huecos
     [odds from API] de Tips (mejor cuota, media y veredicto).
- **Sin decidir:** nombres con inicial también en el campo de alineaciones
  (ahora solo apellido, por espacio); opción (b) «Bookies agree/disagree»
  cuando haya cuotas del partido.

## 30/09/2026: idioma

- **Qué:** `app_apostador/CLAUDE.md` (nuevo) con la regla del usuario: a él,
  siempre en español; el proyecto (la app), en inglés. Más las normas de
  trabajo de esta carpeta.

## 30/09/2026: 2yellow · Nations League, con Inglaterra de ejemplo

- **Qué:** lienzo nuevo, aparte del de LaLiga:
  https://claude.ai/artifact/PyGg13vymnA4UtaYcunLzR. Siete pantallas:
  - Partidos: últimos resultados con nuestro pronóstico ✓/✗ y la jornada 3.
  - Previa Croacia–Inglaterra (3/10).
  - Informe Chequia 0-2 Inglaterra y sus alineaciones.
  - Ficha de Inglaterra.
  - Clasificación de la Liga A y ranking FIFA.
  - Tips con «cuánto acertamos».
- **Datos:** `diseno_nl/nl_datos.py` → `diseno_nl/datos_nl.json`. Lee
  `diseno_nl/datos_main/`, copias de `data/selecciones` y
  `modelos/selecciones` tomadas de `main` el 30/09 (de main solo se copia).
  `notas_2909.csv` son las notas del ciclo del 29/09 18:17 (onces reales de
  Inglaterra y Croacia). Sin API.
- **Previa Croacia–Inglaterra:** aún no está en el registro (las cuotas llegan
  ~36 h antes). Se calcula en local con el modelo de selecciones
  (`modelo_selecciones.py` sin tocarlo, apuntado a la copia): Inglaterra 56%,
  1,12–1,92 goles, más de 2,5 59%, ambos marcan 58%. Sin árbitro ni cuotas.
- **Fallo silencioso encontrado en el registro de `main` (no tocado):** las
  pasadas de las últimas ~3 h antes del pitido del 29/09 guardan `mkt_*`
  vacío (desde las 15:31 UTC en todos los partidos de ese día). La casa
  desaparece justo del pronóstico que cuenta. Aquí se usa la última pasada
  con cuotas (3,5 h antes) y se dice en pantalla.
- **Otros arreglados aquí:** notas del once cruzadas por ID (por nombre no
  casaban); la columna `eq` volvía a chocar con `DataFrame.eq` y ponía a
  todos los jugadores en Inglaterra; los nombres de grupo (A1…A4) no los da
  la API: no se inventan («Group 1…4»).
- **Ficheros:** `app_apostador/diseno_nl/` entero.

## 30/09/2026: vídeo corto para redes, Croacia–Inglaterra

- **Qué:** `diseno_nl/video/2yellow_croatia_england.mp4`, vertical 1080×1920,
  30 fps, 23 s, sin sonido. Siete escenas: partido, 1X2 (22/22/56), goles
  esperados (1,12–1,92, 1-1), más de 1,5/2,5 y ambos marcan, forma de los
  últimos 5, jugadores clave con nota justa y cierre «Croatia or England?
  1 · X · 2». Pie: «probabilities, not betting advice · 18+».
- **Por qué:** petición del usuario, para probar opiniones en redes.
- **Cómo:** `diseno_nl/video/video_cro_eng.py` dibuja cada fotograma con
  Chromium y lo monta con ffmpeg (imageio-ffmpeg). Fuentes Archivo e
  Instrument Sans descargadas de Google Fonts para el render. Datos de
  `datos_nl.json`, sin API.
