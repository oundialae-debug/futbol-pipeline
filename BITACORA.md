# Bitácora del proyecto

Pedida por el usuario el 29/09/2026: "estamos profundizando mucho en este
proyecto, es importante llevar una bitácora de ideas probadas, pero también
cambios de código y archivos".

**Cómo se usa:**
- Cada cambio de código, prueba o descarga se apunta aquí EN EL MISMO COMMIT,
  con una línea para el qué y otra para el porqué.
- El detalle largo (tablas, sigmas) va en el CLAUDE.md del modelo. Aquí va
  el resumen y dónde leerlo.
- Lo más nuevo, arriba.

## 10/10/2026 — redes: respaldo del recolector del post-partido (`post_partido_respaldo.yml`)
- Qué: segundo workflow (cron cada 10 min, grupo de concurrencia propio) que hace UNA pasada de `post_partido.py una` solo si un partido grande lleva saque+2h05 sin marca; `post_partido.py hay_respaldo` lo decide sin API ni instalar nada. Prueba sin red añadida.
- Por qué (usuario): "20 minutos = 4 pasadas del primer recolector (empieza a saque+1h45, cada 5 min); si después no hay datos actualizados, que se active el respaldo". Si el cron de GitHub falla, los datos no se quedan sin recoger. La plantilla y Buffer (Live) siguen esperando a la marca "datos_listos". Mismo tope de 30 llamadas/día.

## 10/10/2026 — post-partido: futbol-pipeline solo DATOS, Live publica; previo y post siempre 5 + 1 tarjetas
- Qué: `post_partido.py` ya no dibuja, ni monta vídeo, ni manda a Buffer: al terminar el partido añade la fila al
  histórico y escribe la marca `data/redes/post_partido/<id>.json` con estado "datos_listos" (match_id, local, visitante
  con los nombres del histórico, liga, fecha, saque_utc, resultado) en el MISMO commit. Fuera `scripts/buffer_envio.py`
  y `BUFFER_API_KEY`/`PREPARAR_RENDER` del workflow. Live (`enviar_cola.yml` → `scripts/post_partido_live.py`) lee las
  marcas, ejecuta `LIENZO=reel datos_clubes.py post`, monta el vídeo (6 × 2.8 s) y lo publica (TikTok + IG reel).
- `datos_clubes.py`: SIEMPRE 5 tarjetas + la lista tapada (usuario 10/10). Previo: pre2 = forma de los últimos 5
  (head_to_head con nuestros datos, sustituye al "upset alert" del mercado); si falta Elo o el último cara a cara, entran
  casa/fuera, tiros o marcadores más probables. Post: sin sorpresa, el hueco de post3 lo ocupa "Match stats" (xG, tiros,
  a puerta, ocasiones claras, posesión, con el marcador real en el centro); post5 (la jornada) siempre, completada con
  los 3 días anteriores si el resto del día aún no está en el histórico; la lista "next" busca el próximo día con partidos.
- `generar.py`: comprueba la zona segura al dibujar (`generar.FUERA`; `ZONA_ESTRICTA=1` en `datos_clubes.py` sale con
  error); las etiquetas de equipo de `.vs` se encogen si no caben ("Newcastle United" vs "Aston Villa" pasaba de x 880);
  leyenda del 1X2 en 3 columnas fijas; gráfico Elo a 800 px; "goals" con `.vs` pequeño. Revisado a ojo y con la
  comprobación en 8 post y 6 previos con nombres largos: 0 fuera.
- Por qué: el secreto de Buffer solo está en Live (el Real Madrid-Villarreal salió en `video_listo_sin_buffer` y se
  publicó a mano); y el usuario pide 6 imágenes siempre (el post del Madrid salió con 5).
- Real Madrid-Villarreal (1336420545): su marca sigue en `video_listo_sin_buffer` (+ `publicado_manual`), así Live
  no lo recoge; además Live lo tiene en su registro. RB Leipzig-Frankfurt: "abandonado", se ignora.
- Pruebas sin red: `scripts/prueba_post_partido.py` (antes de ventana 0 llamadas, en juego → sigue, terminado →
  "datos_listos", la marca impide repetir, >4h abandona, tope 30/día, bucle con reloj falso hasta terminar, hasta
  abandonar y hasta el tope) y en Live `scripts/prueba_post_partido_live.py`. No se llamó a la API.

## 10/10/2026 — redes: marcadores más pequeños en las plantillas (zona segura)
- Qué: `generar.py` .res de 150 a 118 px y el xG de post1 de 130 a 100 px; post-partido del Real Madrid-Villarreal rehecho (post_v2.mp4).
- Por qué: con "Villarreal" la etiqueta del visitante pasaba de x 880 en post1 y post2.

## 10/10/2026 — redes: post-partido AUTOMÁTICO en vídeo (`post_partido.py` + `post_partido.yml`)
- Qué: cron cada 5 min. Para los 2 partidos de `datos_clubes.elegir` (hoy y ayer en Madrid): nada antes de inicio+1h45
  (0 llamadas); después, `/matches/{id}` hasta que termine, y entonces `/statistics/{id}` (funciones de
  `backfill_historico.py`) → fila en `data/historico_partidos.csv` (mismas columnas, sin duplicar) → `datos_clubes.post`
  (LIENZO=reel) → vídeo como `Live/scripts/montar_video.py` (5 tarjetas de 2.8 s, pista menos usada de la biblioteca
  de Live) en `media/post_partido/<fecha>_<local>_<visitante>/` → push → URL raw 200 → Buffer vídeo automático a
  TikTok e Instagram (reel) a ahora+3 min (`scripts/buffer_envio.py`, copia de `Live/enviar_cola.py`). Marca en
  `data/redes/post_partido/<id>.json` (no repite), registro `data/redes/post_partido_log.csv`, consumo en
  `data/redes/post_partido_consumo.json`. Pasado inicio+4h sin terminar: "abandonado". Sin xG y antes de 3h: espera.
- Por qué: el usuario lo aprobó el 10/10 (excepción fija a la regla de la API, ≤30 llamadas/día; ~3-5 por partido).
  El post-partido tenía que esperar al backfill de la mañana siguiente.
- Prueba sin red: `scripts/prueba_post_partido.py` (antes de ventana 0 llamadas, en juego → sigue, terminado → fila +
  PNG + vídeo, la marca impide repetir, >4h abandona, tope 30/día). Durante el desarrollo no se llamó a la API.
- Arreglo (misma tarde): el workflow va con Python 3.12; con 3.11 `generar.py` no compila (f-strings de 3.12) y la
  primera pasada (lanzada a mano) falló al importar, antes de cualquier llamada.
- Sin `BUFFER_API_KEY` (el secreto solo está en Live): vídeo + PNG se suben igual y la marca queda en
  `video_listo_sin_buffer` con la URL raw del vídeo y el texto, para mandarlo a mano; no se reintenta ni se llama más a la API.
- Bucle dentro del job (misma noche): el cron */5 de GitHub dio 1 pasada en 20 min. Ahora el cron (*/10) solo arranca;
  si hay un partido en ventana sin terminar, `post_partido.py` (modo `bucle`) sondea cada 5 min en el mismo job (≤1 llamada
  por sondeo) hasta que termina, pasa inicio+4h, se agota el tope o llega a 135 min (timeout del job 150). Probado con reloj falso.
  Real Madrid 1-0 Villarreal salió así a las 21:09 UTC (4 llamadas), en `video_listo_sin_buffer`.

## 10/10/2026 — redes: goles esperados de la plantilla "goals" a 92 px
- Qué: `generar.py` goals(): marcador de goles esperados de 120 a 92 px.
- Por qué: con nombres largos ("Man City") la etiqueta del visitante pasaba de x 880 (zona segura). Revisado a ojo en Liverpool-City y Como-Roma.

## 10/10/2026 — redes: plantillas de CLUBES (5 grandes ligas), `datos_clubes.py`
- `redes/plantillas/datos_clubes.py` (sin API): `elegir <fecha>` (los 2 partidos más grandes del día en data/calendario.csv,
  solo Premier, LaLiga, Serie A, Bundesliga y Ligue 1, nunca Segunda), `pre "<Local>" "<Visitante>" <fecha>` (pre1, pre3,
  pre4, pre5, pre6) y `post ...` (post1, 2, 3 si hay sorpresa, 4, 5, 6) con generar.py, como datos_selecciones.py.
  Porque la rutina diaria no podía publicar previos ni post de clubes.
- % solo de nuestro modelo: el último pronóstico antes del pitido en data/ambos_marcan/registro_papel.csv (oficial); si
  aún no está (previo del día siguiente), un Poisson ataque/defensa por liga (2 años, semivida 180 días, encogido; recién
  ascendidos hacia -0.15). Medido en 2025/26 (1.757 partidos, sin fuga): Brier 1X2 0.598 contra 0.648 de la frecuencia
  base; más/menos 2.5 y ambos marcan 0.249-0.250, es decir SIN acierto: tomar esos % del Poisson con cautela.
  Sin pre2 "upset alert" (enseña el % del mercado).
- Tamaño de partido: puntos por partido de cada club en las 5 grandes (4 temporadas, encogidos hacia 1.0 = recién
  ascendido medio, 0.98 en 45 casos) y partido = el más débil + la mitad del más fuerte (con la suma salía PSG - Le Mans).
  11/10: Liverpool - Manchester City y Como - Roma.
- Zona segura: lista de pronósticos a 7 filas y jornada a 6 (con 8 la pregunta bajaba de y 1540). `generar.elo_chart`:
  220 px a la derecha para la etiqueta (antes "AS Roma"/"Man City" pasaban de x 880; afecta también a selecciones).
- Límite: historico_partidos.csv trae los resultados de AYER cada mañana; el post de un partido sale al día siguiente
  (Man United - Tottenham del 10/10 aún no estaba).

## 07/10/2026 — redes: perfil de delantero centro y Balón de Oro en dos listas
- `datos_formatos.py`: nuevo perfil "ST" (delanteros centro: G+A, xG+xA y tiro pesan más; regate y pase clave menos),
  puntuado solo entre 9s; siguen en la línea ATT para XI y top 5. Antes Kane salía bajo porque se le medía como extremo.
- `balon_oro_doble()`: MERECE (rendimiento por posición 60%, títulos 35% con el Mundial a la mitad, juego limpio 5%) y
  GANARÁ (70% MERECE + 30% popularidad en Wikipedia). Top: merece Yamal 93, Olise 88, Dembélé 87, Kane 86, Mbappé 86;
  ganará Yamal 95, Olise 89, Mbappé 89, Kane 87, Dembélé 87. Sustituye al índice del 06/10 (error de Bayern y sesgo a goles).

## 07/10/2026 — redes_api: modo popularidad (Google Trends, sin Highlightly)
`redes_api.py popularidad`: interés en Google Trends (mundial, ago-25 a sep-26, pytrends) de los nominados al Balón de
Oro, relativo a Lamine Yamal (=100, ancla en cada consulta de 5) -> data/redes/popularidad_bdo.csv. Para "Who will win
it". Primero se hizo con visitas de Wikipedia; el usuario pidió Google Trends.

## 07/10/2026 — redes: índice del Balón de Oro, medias encogidas por minutos
Usuario: con pocos minutos es más fácil tener buena media. Las medias por 90 (nota, G+A, xG+xA) se encogen hacia la
media de los nominados con 1350 min de peso antes de los percentiles. Resultado: Kane 91, Olise 88, Dembélé 85
(1659 min), Yamal 85, Mbappé 76. Se descartó meter los minutos como factor aparte: subía a Rice al top 5 solo por jugar.

## 07/10/2026 — redes: índice del Balón de Oro, error de nombre de Bayern
`UCL_2526` tenía "Bayern München" y nuestros datos dicen "Bayern Munich": Kane y Olise puntuaban 0 en
Champions (semifinal = 0.6). Corregido el alias. Con el dato bueno: Kane 91, Dembélé 88, Olise 88, Yamal 86,
Mbappé 75 (el post del 06/10 ponía Dembélé 88 primero y Kane 82). Detectado por la pregunta del usuario.

## 07/10/2026 — redes: zona segura común TikTok + Instagram
Usuario (5ª-6ª vez): en TikTok los iconos de la derecha y la descripción tapaban datos. `generar.py`: `.safe`
pasa a x 80-880 (right 200) y, con `LIENZO=reel`, y 318-1540 (bottom 380); el Index pone el desglose en su
propia línea (se metía bajo la tarjeta). Comprobado con XI, Index y Upset renderizados con la caja dibujada.

## 06/10/2026 — redes: LIENZO=reel para Instagram con música
- Qué: `generar.py` con `LIENZO=reel`: 1080x1920 con todo el contenido en la franja central 4:5 (y 318-1608).
- Por qué: al ponerle música, Instagram convierte la foto en reel (9:16) y el feed solo enseña el centro: al XI de septiembre se le cortaron el logo y la pregunta.

## 06/10/2026 — colores de 228 equipos, curados
- Qué: `colores_redes.yml` bajó 226 equipos de Wikipedia; `curar.py` corrige a mano 26 con motivo (rayas donde manda el color del club: Inter, Milan, Atalanta, Leverkusen, Bournemouth, PSG, Toulouse, Palace, Brighton; lisas sin secundario: Madrid, Sevilla, Villarreal, Tottenham, Marseille...; sin ficha: Frosinone, Olympiakos).
- Por qué: revisión antes de usarlos (regla de rigor). Comprobado: Inter azul vs Milan rojo; Liverpool vs United -> United con la 2ª.

## 06/10/2026 — colores_redes: descarga robusta
- Qué: wiki_equipaciones/colores_camiseta fusionan con lo ya bajado (solo piden lo que falta), van despacio y reintentan; tabla de la app restaurada.
- Por qué: la 1ª pasada solo bajó 4 de 250 equipos (Wikipedia cortó) y dejó la tabla en 18.

## 06/10/2026 — redes: paleta de la app 2yellow
- Qué: `redes/plantillas/equipaciones.py` y `redes/plantillas/colores/` copiados de app_apostador (rama ccr-302c299f-kdpgwl): 1ª, 2ª y 3ª equipación reales de Wikipedia, regla sin choques (local 1ª, visitante la primera que no choque) y aclarado a contraste 3:1. `generar.py` usa esa paleta; equipo sin ficha = gris de la app (no blanco). `colores_redes.yml` amplía la tabla a los 172 equipos de las 5 grandes y la Champions con el mismo método (Wikipedia, sin API de fútbol).
- Por qué: usuario: en el XI solo los del Barça salían en azul y el resto en blanco; "la app ya corrigió la paleta, cógela y úsala de ahora en adelante".

## 06/10/2026 — redes: XI sin banda contraria y con desempate futbolístico
- Qué: nadie juega en la banda contraria (extremo/lateral); empate de índice en la misma posición -> dato del rol (ATT xG+xA/90, MID pases clave/90, DEF entradas+int/90, GK paradas/90), luego minutos.
- Por qué: usuario: Lamine (extremo derecho) salía de extremo izquierdo al empatar con Olise. Ahora Lamine gana el desempate (1,37 vs 1,35 xG+xA/90) y Olise queda fuera.

## 06/10/2026 — redes: XI de septiembre (ligas + Champions)
- Qué: mínimo 270' en periodos de más de 10 días (mes, torneo). Con nombres completos (redes_api nombres: 3.489) y 17/18 partidos de Champions J1: Dahmen; Mitchell, Tah, Tarkowski, Davies; Cásseres, Mainoo, Nico Paz; Olise, Raphinha, Lamine Yamal.
- Por qué: sin mínimo se colaban jugadores de AEK/Sporting con un solo partido de Champions. Comprobado fuera: Olise y Yamal son los nombres del mes; Groß (jugador del mes de la Premier) queda 21º de 113 medios.

## 06/10/2026 — redes_api: no perder descargas por conflictos
- Qué: el paso Guardar usa `pull --rebase -X theirs`.
- Por qué: la 1ª descarga de nombres (~250 llamadas) se perdió al chocar con la de Champions en `jugadores_nombres.csv`.

## 06/10/2026 — redes: XI/Index con Champions
- Qué: `datos_formatos.py` acepta fuente `ucl` y `clubes+ucl` (XI del mes) y avisa si hay jugadores sin nombre.
- Por qué: usuario: XI de la Champions en sus semanas y XI del mes juntando ligas y Champions.

## 06/10/2026 — redes: descargas de API para nombres y Champions
- Qué: `scripts/redes_api.py` + `redes_api.yml` (solo a mano): `nombres` repide /box-score de la temporada en curso de las 5 grandes para guardar el nombre de cada jugador; `ucl` busca la Champions, lista sus partidos jugados y baja su box-score (`data/redes/ucl_*.csv`).
- Por qué: para el XI de septiembre (ligas + Champions) faltaba el nombre del 40% de los mejores candidatos y no había nada de Champions. Usuario: "descarga de la API todo lo que necesites".

## 06/10/2026 — redes: 2yellow Index POR ROL (ataque, medio, defensa, portero)
- Qué: `datos_formatos.py`: cada métrica en percentil dentro de su rol y periodo, media ponderada x100. ATT: G+A, regates, pases clave, xG+xA, tiros a puerta, nota. MID: pases clave, pases, % pase, entradas+intercepciones, duelos, regates, G+A, nota. DEF: entradas+intercepciones, duelos (ganados y %), pase, tarjetas (resta), nota. GK: paradas, goles evitados, encajados. `indice <desde> <hasta> <fuente> "" ATT|MID|DEF|GK`; el XI usa el mismo índice y nadie juega fuera de su rol; mínimo de minutos común (60' por partido de su equipo, tope 360'); Mundial/Euro sin filtro de nivel.
- Por qué: usuario: "si usas G+A somos lo mismo que los demás" y Lamine fuera. Comprobado: en el Mundial hizo 1 gol y 0 asistencias (también según fuentes externas); con el índice por rol destaca en regate (4,0/90) pero queda 12º de 18 atacantes.

## 06/10/2026 — redes: 2yellow XI con posiciones reales y filtro de nivel
- Qué: el XI reparte los huecos del 4-3-3 (LW, ST, RW, CM, DM, CM, LB, CB, CB, RB, GK) según la posición de `jugador_perfil.csv` (secundaria con -3), reparto global por 2yellow Index (el mismo del top 5); sin perfil, solo hueco central; si falta un hueco, no se publica. Selecciones: solo partidos entre dos equipos del top 40 FIFA. Índice con tope 99.
- Por qué: usuario: "Harry de extremo derecho, Porro de central" y onces con jugadores de selecciones menores (Bielorrusia, Estonia) por notas altas contra rivales flojos.

## 06/10/2026 — redes: formatos propios (2yellow XI, 2yellow Index), lienzo 4:5 para IG
- Qué: plantillas `xi` (once 4-3-3 con la nota en una tarjeta amarilla) e `indice` (top 5, índice = nota x10 + 3 por G+A por partido); `redes/plantillas/datos_formatos.py xi|indice <desde> <hasta> [selecciones|clubes]`; `LIENZO=4x5` genera 1080x1350 para imágenes de Instagram; barras del ranking uniformes (solo el 1º en amarillo).
- Por qué: usuario: formatos propios para diferenciarnos; IG recortaba las 9:16; Yamal salía resaltado porque solo su club tenía colores en `kits_camiseta.json`.

## 06/10/2026 — redes: índice 2yellow del Balón de Oro
- Qué: `datos_rankings.py indice_bdo` / `balon_oro_indice`: criterios oficiales (individual 55%: nota, (G+A)/90, (xG+xA)/90 en liga + Mundial; colectivo 40%: liga, fase de Champions (tabla UCL_2526 de UEFA), fase del Mundial; juego limpio 5%). `nominados` queda como "una sola cifra".
- Por qué: usuario: el Balón de Oro no se decide por goles y asistencias (otros ponen a Yamal 2º). Resultado: Dembélé 88, Yamal 86, Kane 82, Olise 79, Mbappé 74. Límite: infravalora a mediocentros defensivos (Rodri) porque lo individual mide ataque.

## 06/10/2026 — redes: momentos de la temporada (Balón de Oro)
- Qué: `datos_rankings.py nominados <contribucion|xg_xa|definicion>`: top 5 de nominados al Balón de Oro 2026 con nuestros datos 2025/26; `buscar()` entiende los nombres abreviados de Highlightly ("E. Haaland"); `jugadores_propios(temporada)`.
- Por qué: usuario, publicar según el momentum de la temporada (gala del Balón de Oro 26/10, Londres).

## 06/10/2026 — redes: fuera "Data, not betting advice · 18+" de las imágenes y descripciones
- Qué: `generar.py` sin pie por defecto; `backup_redes.py` sin esa línea en el texto.
- Por qué: usuario: confunde a los algoritmos y limita las publicaciones.

## 06/10/2026 — redes: correcciones del usuario y caras en jugador vs jugador
- Qué: "Swipe" solo en carruseles (`CARRUSEL=1`), nunca en vídeo; fuera "Score" en our_calls (chocaba con el over 2.5); textos sin "swipe" en la 6ª y en follow. `datos_rankings.py jugadores`: NUESTROS datos (box-score Highlightly) primero, understat solo si no están al día o falta el jugador; caras de los jugadores (fotos libres del workflow bajar-fotos de Live) con degradado hacia el centro y crédito; alias de nombres.
- Por qué: correcciones del usuario sobre el post de Croacia-España ("tienes que ser más riguroso") y su regla: siempre nuestros datos salvo que no estén al día.

## 06/10/2026 — redes: jugador vs jugador y workflow diario de jugadores
- Qué: `scripts/jugadores_redes.py` + `jugadores_redes.yml` (09:40 UTC diario, ACTIVO con el sí del usuario): understat (sin cuota, 5 peticiones) → `data/redes/jugadores_temporada.csv`; Highlightly box-score de los partidos recientes de las 5 grandes, tope 20 llamadas/día → `historico_xg_jugador.csv` + `data/redes/jugadores_nombres.csv`. `datos_rankings.py jugadores "A" "B"` y `top_jugadores <métrica>`.
- Por qué: usuario prefiere jugador vs jugador (más conversación); límite ~100 llamadas/día de Highlightly → fuente principal sin cuota y Highlightly con tope bajo como respaldo.

## 06/10/2026 — redes: plantillas head_to_head y ranking
- Qué: `generar.py` + `head_to_head` (dos equipos, 6 cifras, la mejor en su color) y `ranking` (top 5 de una métrica); `redes/plantillas/datos_rankings.py ranking <suerte|xg|muro|tiros|posesion> [liga]` y `duelo <A> <B>` con `historico_partidos.csv` (5 grandes, temporada en curso, sin API).
- Por qué: usuario, formato que hizo crecer otras cuentas de datos (cara a cara y rankings). Ojo: los datos solo llegan al 20/09; actualizarlos a diario necesita API (pendiente del sí del usuario).

## 06/10/2026 — redes: nunca el mismo color para los dos equipos
- Qué: `generar.py` nuevo `separar()`: si los colores de los dos equipos se parecen, uno pasa a su otro color más propio (Croacia → blanco); si nada sirve, amarillo. El gráfico Elo pone valor y nombre del equipo en su color.
- Por qué: usuario, previo Croacia-España (ambos rojos): no se entendía qué Elo era de quién.

## 05/10/2026 — redes: fuera "bookies" de las imágenes
- Qué: `generar.py` (upset alert) dice "Consensus" en vez de "Bookies".
- Por qué: TikTok parece no mostrar posts con vocabulario de apuestas (las 2 últimas se quedaron en 0 vistas).

## 05/10/2026 — redes: backup sin Claude
- Qué: `scripts/backup_redes.py`, `.github/workflows/redes_backup.yml` (apagado salvo variable `BACKUP_REDES=on`), plantillas de `redes/plantillas/` llevadas a main, guía en `redes/backup/LEEME.md`.
- Por qué: el usuario pidió poder seguir publicando sin la suscripción de Claude.


Dónde está cada cosa:
- Modelos de clubes (1X2, goles, córners, tarjetas) y reglas generales: `CLAUDE.md` (corto) y `docs/notas_proyecto.md` (lecciones y resultados).
- Ambos marcan: `modelos/ambos_marcan/CLAUDE.md`.
- Selecciones: `modelos/selecciones/CLAUDE.md` (otro chat).
- NBA: `docs/otros_deportes/nba.md`.

---

## 09/10/2026

| qué | por qué | ficheros |
|---|---|---|
| Reactivados los crons `cosechar_cuotas` (diario, tope 1.200 llamadas) y `calendario` (diario + lunes), con el sí del usuario. Siguen parados descanso_en_vivo (914 llamadas/día), revision_descanso, casas_descolgadas, censo_margenes y pipeline_diario. | Vuelven las ligas tras el parón. La API solo guarda las cuotas 28 días: lo que no se cosecha se pierde. Los parados no alimentan nada de lo que se hace ahora. | `.github/workflows/cosechar_cuotas.yml`, `.github/workflows/calendario.yml`, `CLAUDE.md` |

## 05/10/2026

### Cambios de código y ficheros

| qué | por qué | ficheros |
|---|---|---|
| Selecciones: al dar listas de "lo más probable", solo mercados con historial medido (1X2, sin empate, goles, ambos marcan, córners, tarjetas); nunca "marca primero" (la API no da quién marca primero, no se puede evaluar). | Petición del usuario (05/10): "siempre mete mercados ya probados". | `modelos/selecciones/CLAUDE.md` |
| Skill `free-llm-apis` copiada de mnfst/awesome-free-llm-apis (revisada: solo documentación, sin scripts). Sin claves ni proveedores configurados. | Petición del usuario: tener a mano proveedores LLM gratuitos para ahorrar tokens. | `.claude/skills/free-llm-apis/` |
| Grafo de conocimiento con graphify (paquete `graphifyy` 0.9.76): pipeline completo, solo código, sin `data/`. 1.064 nodos, 2.869 aristas, 56 comunidades con nombre. Cero tokens (análisis estático). | Responder preguntas que cruzan varios archivos sin leerlos todos. | `graphify-out/`, `.graphifyignore` |
| Workflow que actualiza el grafo en cada push a `main` con cambios en `.py` o workflows (`graphify update .`). | Que el grafo no se quede viejo. Ojo: `update` renombra las comunidades por su nodo principal (pierde los nombres puestos a mano) e indexa también la estructura de los `.md`. | `.github/workflows/actualizar-grafo.yml` |
| Hook de arranque de sesión que instala graphify si falta. NO se instalaron `graphify claude install` ni `graphify hook install`. | Que cualquier chat nuevo pueda consultar el grafo. | `.claude/settings.json`, `.gitignore` |
| Mistral también funciona: el 429 no era el plan (activo, 10 US$/mes) sino el modelo. En el plan gratuito, mistral-small/medium/magistral tienen límite 0 pet./min y ministral-14b/8b/3b, codestral y nemo sí van. `llm_gratis.py` usa ministral-14b. | Comprobado con las cabeceras X-Ratelimit de la API. | `scripts/llm_gratis.py`, `CLAUDE.md` |
| `scripts/llm_gratis.py`: `preguntar(prompt)` con Groq y, si falla, Cerebras (y Mistral). Sin claves en el código: son credenciales del entorno que añade el proxy. User-Agent propio (con el de Python, 403). Probado: Groq y Cerebras responden; Mistral 429 (plan de la API sin activar). | Tareas mecánicas con LLM gratuito para ahorrar tokens de Claude. Solo datos públicos. | `scripts/llm_gratis.py`, `CLAUDE.md` |
| `CLAUDE.md` reducido a ~30 líneas (reglas clave, mapa, grafo, APIs gratuitas, notas compartidas). El texto anterior, entero y sin cambios, pasa a `docs/notas_proyecto.md`; referencias actualizadas. | Se carga en cada chat: menos tokens por conversación. | `CLAUDE.md`, `docs/notas_proyecto.md` |

## 29/09/2026

### Cambios de código y ficheros

| qué | por qué | ficheros | commit |
|---|---|---|---|
| La posición en la tabla se calcula **por días**: todos los partidos de un día leen la tabla del final del día anterior. | **Fuga:** con dos partidos de la misma liga a la misma hora, el segundo veía el resultado del primero (8,6% de los partidos, hasta 8 puestos). Además iguala entrenamiento y directo, donde el histórico solo llega hasta ayer. | `scripts/rasgos.py`, copia en `modelos/ambos_marcan/scripts/rasgos.py` | 2115bfb |
| La media de tarjetas de relleno (partidos sin árbitro conocido) se actualiza **por días**. | La misma fuga en pequeño: esa media incluía partidos a la misma hora. Cambio medio de 0,004 tarjetas desde sep-2022. | los dos `rasgos.py` | 6c596cc |
| Se corrige el texto de `calcular_arbitro`: la media es de todas las ligas, no "de liga". | El texto no coincidía con el código. Se cambia el texto, no el código: cambiar el código sería otra variable y habría que probarla. | los dos `rasgos.py` | 6c596cc |
| `comprobar_sin_fuga` tiene un segundo control: se truca un partido y ningún otro partido del mismo día (de cualquier liga) puede cambiar. | El control antiguo solo miraba el propio partido, así que la fuga de la tabla pasó sin avisar. Comprobado: con la tabla o el árbitro viejos falla, con el código nuevo pasa. | los dos `rasgos.py` | 2115bfb, 6c596cc |
| Registro en papel: columna `mod_ambos_precio`, el modelo de solo precio (logística "C"). | Resolver con partidos limpios la contradicción de la auditoría 2: C gana al oficial frente al resultado, pero pierde frente al mercado real. | `scripts/ambos_marcan_hoy.py` | 00727aa |
| Registro en papel: juez principal = Brier y log loss sobre TODOS los partidos contra el mercado real; control a los 400 partidos; apuesta solo con VE > 8%. | Reglas fijadas antes de ver resultados (auditoría 2, paso 4). Con VE > 0 el "valor" puede ser solo ruido de la fuente de precio. | `scripts/ambos_marcan_hoy.py` | 00727aa |
| Desempate fijo en la tabla: puntos, diferencia, goles a favor y el ID del equipo. | Con empate, el orden dependía de cómo vinieran las filas: la posición cambiaba en el 1,1% de los partidos con solo desordenar el histórico, y quedaban diferencias de 1 puesto con el directo. Ahora da igual el orden (0,00% en 3 desordenados). | los dos `rasgos.py` | este commit |
| El flujo automático ejecuta `evaluar` cada mañana (sin API). | Fallo silencioso: ningún paso lo llamaba, así que `registro_papel.md` (resultados y juez) nunca se actualizaba solo. | `.github/workflows/ambos_marcan_diario.yml` | este commit |
| En directo, la temporada de los partidos de hoy sale de la fecha (julio en adelante = año; si no, año − 1). | Antes se copiaba de la última fila de la liga. El primer día de una temporada nueva, el partido caía en la tabla de la anterior y la calidad de plantilla usaba la temporada de jugadores equivocada. La regla coincide en el 100% del histórico (9.292 partidos). | `scripts/ambos_marcan_hoy.py` | este commit |
| Limpieza: importaciones repetidas en `pronosticar`. | Sobraban, no cambian nada. | `scripts/ambos_marcan_hoy.py` | este commit |
| Fechas de hoy corregidas de 30/09 a 29/09 en textos y comentarios. | Las escribí mal; el día era el 29. | 11 ficheros | este commit |
| Scripts nuevos de la auditoría 2 (sin API): `auditoria2_precio.py`, `auditoria2_paridad.py`, `auditoria2_elo.py`, `auditoria2_tabla_fuga.py`. | Cada prueba en un script nuevo, con las reglas fijadas antes (regla del usuario). | `scripts/` | ccd5688, 7f598e9, f476f8f, e10e95c |
| `btts_implicito.ajustar` prueba varios puntos de partida y se queda con el de menor error. | Con favoritos claros, un solo arranque caía en mínimos absurdos (goles esperados 3,2 y 8,2). | `scripts/btts_implicito.py` | 0b46697 |
| Registro en papel automático: `ambos_marcan_diario.yml` + `ambos_hay_partido.py` (comprueba sin API si hay partido antes de gastar llamadas). | Petición del usuario. Activado con su sí a ~30 llamadas/día (Segunda) y ~80/día (6 ligas). | `.github/workflows/`, `scripts/` | b3fd0d9, ca6cb7e, c69fac5 |
| Árboles de 1 nivel adoptados y revertidos el mismo día. | La revisión a fondo no lo confirmó (ver ideas). | `scripts/modelo_ambos_marcan.py` | a6c321c, 8d46dda |

### Ideas probadas

| idea | resultado | veredicto | detalle |
|---|---|---|---|
| Fuga de la tabla: ¿inflaba los resultados? | Ambos marcan: sin fuga -0.37s y por días +0.31s frente a la tabla vieja, dentro del ruido. 5 mercados (`evaluar_mercados.py`), vieja frente a nueva: resultado -2.00s/-2.01s, 2.5 -2.51s/-2.57s, ambos marcan +0.18s/+0.18s, córners -1.28s/-1.28s, tarjetas -2.42s/-2.46s. | No infló nada; las conclusiones anteriores siguen en pie. Arreglado igual, por principio. | `modelos/ambos_marcan/CLAUDE.md`, `CLAUDE.md` |
| Auditoría 2, puntos 1-3: el precio solo frente al oficial | Frente al resultado, precio ampliado +3.01s (17/21 meses). Frente al mercado real: oficial -0.06s, precio -0.73s. Fútbol encima del precio empeora. La liga no aporta. | El oficial se queda. El de precio pasa al registro como comparación. | `modelos/ambos_marcan/CLAUDE.md` |
| Auditoría 2, paso 2: paridad entrenamiento/directo | Calidad y portero coinciden. El precio es otra fuente (100% distinto, 1,7 puntos de media en la predicción). La tabla difería en el 26-35% (causa: la fuga y los partidos del mismo día). | Tabla arreglada. El precio queda como diferencia conocida. | ídem |
| Auditoría 2, paso 3: Elo con regresión a la media y ancla entre ligas | +0.62s y -0.46s, 12/21 meses. | No cambia nada. | ídem |
| Auditoría 2, paso 4: cómo juzgar el registro | ~370 partidos para ver 0,005 de Brier; ~1.500 apuestas para ver un +5%; ruido del VE por la fuente de precio ~5% (p90 8%). | Reglas del registro fijadas (arriba). | ídem |
| Auditoría 1: separar fútbol y precio, precio de entreno frente a directo, semillas | El precio solo recalibrado empata con el modelo; 64 de 125 apuestas cambian según la fuente de precio; el portero no se confirma con otras semillas y 2022/23 sí. | El portero se queda por decisión del usuario; 2022/23 dentro. | ídem |
| Árboles de 1 nivel | +1.54s en 2.387 partidos, pero la apuesta sale peor en el 95% de remuestreos y peor en LaLiga y esta temporada. | Revertido a 2 niveles. | ídem |
| Ajuste por liga (desplazar o Platt por liga) | Desplazar -1.43s; Platt por liga +0.88s, mezclado. | No. La liga ya pesa lo que tiene que pesar. | ídem |

### Comprobaciones hechas en la revisión de código (sin cambios)

- **Paridad final** (`auditoria2_paridad.py`, 197 partidos de sep-2026, con el
  código definitivo): las 84 variables que no son de precio, tabla incluida,
  coinciden al **100%** entre entrenamiento y directo (antes, la tabla difería
  en el 26-35%). Portero 1,3%, casi nada. Solo queda la diferencia conocida
  del precio.
- **Prueba completa de `pronosticar`** con dos partidos de la Segunda ya
  jugados, marcados como "por empezar": entrena con 102 variables, la
  temporada sale de la fecha, la columna de solo precio se rellena y el
  registro real queda intacto.

- Directo y entrenamiento usan exactamente las mismas 102 variables de ambos
  marcan, pese a los distintos umbrales de cobertura (0,2 y 0,3).
- H2H profundo filtra bien: solo usa enfrentamientos de fecha estrictamente
  anterior.
- Elo, medias móviles, H2H propio, rotación, calidad y portero son de cada
  equipo o jugador: los partidos a la misma hora no se cruzan.

### Fuera del código: maquetas de app (sin cambios en el repositorio)

- Dos diseños de app al estilo FotMob, publicados como artefactos privados
  del usuario, con datos reales calculados en local y sin API:
  1. **"Veredicto" registro:** el registro en papel de ambos marcan.
  2. **"Veredicto" LaLiga, para el público:** la jornada 8 con probabilidades
     por Elo, Real Madrid–Villarreal, "La tabla miente" (tabla frente a fuerza
     Elo) y el ranking de árbitros por tarjetas.
- Las probabilidades por Elo salen de una logística sobre la diferencia de Elo
  en 1.589 partidos de LaLiga: dice 44,8% y pasa 44,8%; dice 64,4% y pasa 62,3%.

### Errores en los datos encontrados

- **API, árbitros:** el mismo árbitro aparece en dos partidos a la misma
  hora: Real Sociedad-Espanyol y Villarreal-Girona, 24/08/2025, 17:30 UTC.
  Es imposible. Afecta a 1 partido y no se corrige a mano.
- **Árbitros en dos ligas:** 7 de 202 aparecen en LaLiga y en Segunda. Es
  legítimo (los árbitros españoles pitan en las dos) y no es una colisión de
  nombres.

### Pendiente / ideas sin probar

- Relleno del árbitro con la media de SU liga en vez de todas: hay que
  probarlo como variable nueva.
- La fuente de precio sigue siendo distinta en entrenamiento (football-data)
  y en directo (Highlightly). La decidirá el registro.

---

## Antes del 29/09/2026 (resumen; el detalle está en los CLAUDE.md)

Fallos de código ya arreglados. Todos fueron silenciosos: sin error y con
números con buena pinta.

| fecha | fallo | arreglo |
|---|---|---|
| 20/09 | `"First Team To Score"` con T mayúscula: el código buscaba `"to"` y el mercado no apareció nunca. | Comparar con el nombre exacto de los datos reales. |
| 20/09 | Filtro de ligas con `if not pais: return True`: colaba ligas de otros países. | Ante la duda, descartar. Ligas por ID, nunca por nombre. |
| 24/09 | `grupos_rasgo()` usaba `"elo" in c`: "du**elo**s" metía 12 columnas de box-score en el grupo elo. | `c.endswith("_elo")`. |
| 25/09 | Los scripts de evaluación exigían todos los rasgos para ENTRENAR: se tiraban 2.221 partidos de 2024/25 sin xG. | `M.partir()`: entrenar con huecos, validar solo con partidos completos. |
| 26/09 | `/lineups` no tiene nada antes de abril de 2024: 1.500 llamadas para 274 alineaciones. | `INICIO_COBERTURA`; titulares de 2023/24 sacados de `/box-score`. |
| ~27/09 | `COBERTURA_MINIMA` quitaba en silencio el xG de equipo al meter 2022/23. | Repetir la prueba con las mismas columnas y un brazo de control. |
| ~28/09 | Fechas de perfiles de jugador en dd/mm/yyyy, no en el formato de la especificación: cero fechas leídas. | Leer el formato real; reprocesado sin API. |

Ideas probadas antes del 29/09:
- Modelos de clubes: variables (box-score, árbitro, clima, rotación, H2H,
  H2H profundo, tabla, calidad de plantilla, forma reciente, momentum,
  btts_tasa), hiperparámetros, peso por recencia, poda, Correct Score, casas
  frente al cierre, cuota como variable. Todo en `docs/notas_proyecto.md`, con sus tablas.
- Ambos marcan: todo en `modelos/ambos_marcan/CLAUDE.md`.
