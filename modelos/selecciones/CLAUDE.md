# Selecciones (Nations League y similares)

Tema APARTE del proyecto principal (ambos marcan de clubes). Montado el
26/09/2026 para Inglaterra-España y Chequia-Croacia. Se reutiliza para las
siguientes jornadas de la Nations League (octubre-noviembre 2026).

## Automático: el ciclo de la Nations League (desde el 26/09/2026)

`nations_league_ciclo.yml` corre 4 veces al día (07:20, 13:35, 15:10 y
17:50 UTC; la de las 15:10 es para los partidos de las 16:00 UTC). También se puede lanzar a mano, con los inputs `tope_llamadas` y
`forma_clubes`. En cada pasada:

1. **Forma de clubes** (solo la pasada de las 07:20): `forma_clubes.py`.
   Guarda el box-score de los partidos de las 6 ligas de los últimos 3 días
   en `data/selecciones/club_reciente.csv`. No toca los CSV del proyecto
   principal.
2. **Datos** (`nations_league.py`):
   - Calendario y resultados de la liga 5039, **día a día**: de 3 días
     atrás a 7 por delante. La consulta por temporada
     (leagueId+season=2026) devolvió 0 partidos el 26/09.
   - Historial desde 2025 **solo de las selecciones que juegan en los
     próximos 7 días**. Petición del usuario: no descargar las ~55 de
     golpe; cada ventana internacional entra sola cuando se acerca.
   - Es reanudable y tiene un tope de 400 llamadas por pasada. Los lunes
     vuelve a pedir la temporada en curso para recoger amistosos.
   - Las selecciones ya descargadas quedan en `selecciones_seguidas.json`,
     y solo se piden detalles de SUS partidos.
   - Detalles de cada partido terminado. **Por orden de pitido** (desde el
     26/09): historial Y detalles de una selección antes de pasar a la
     siguiente. Antes se bajaba el historial de todas y luego los detalles,
     y con el tope las del día siguiente se quedaban sin estadísticas.
   - Previa de los partidos de las próximas 36 h: cuotas, árbitro y once
     si la API lo tiene. Escribe `equipos.json`, `cuotas_hoy.csv` y
     `alineaciones_hoy.csv`.
3. **Notas** de los jugadores de esos partidos.
4. **Pronósticos:** una selección con menos de 8 partidos en el modelo
   (`MIN_PARTIDOS`) se queda sin pronóstico y lo dice: con datos a medias
   el ajuste la deja en la media y saldría un número con buena pinta y sin
   base. `pronostico_selecciones.py` escribe
   `modelos/selecciones/pronosticos.md` y añade una fila por partido a
   `data/selecciones/registro_pronosticos.csv`.
5. **Aprendizaje:** `evaluar_selecciones.py`.
   - Cruza el último pronóstico ANTES del pitido con el resultado.
   - Mide modelo contra mercado por mercado.
   - Aprende el peso de la mezcla modelo/mercado en
     `data/selecciones/pesos_mezcla.json` en cuanto hay 30 partidos
     evaluados; antes usa los pesos iniciales.
   - Informe en `modelos/selecciones/evaluacion.md`.

Además el modelo se reajusta en cada pasada con todos los partidos
jugados: los resultados nuevos entran solos.

**Qué NO aprende todavía:** el peso de la forma del once (B_FORMA = 0.5),
el 60/40 club/selección de la nota y la dispersión de córners y tarjetas.
Están puestos a mano. Cuando haya 50 o más partidos evaluados, lo
siguiente es probarlos contra el registro.

**Onces de prensa (la API no los tuvo ni el 26 ni el 27/09):** hacia 1 h antes
del pitido, buscar el once CONFIRMADO en la web. Los "predicted/projected" no
valen, y si dos fuentes no coinciden, no se usa ninguno; las páginas de
alineación del partido (p. ej. ysscores.com/en/lineup/...) fueron las fiables.
Después:
```
python3 modelos/selecciones/onces_prensa.py "Germany: Nübel, Brown, ..." "Greece: ..."
python3 modelos/selecciones/nota_jugadores_selecciones.py
python3 modelos/selecciones/pronostico_selecciones.py      # SIN "| head": se corta y no escribe
```
- En `onces_prensa.py` el primero de cada lista es el portero. Resuelve los
  homónimos ya vistos (A. Schlager portero / X. Schlager; "Peretz" / "Eliel
  Peretz") y el `&apos;` de O'Brien.
- Sin id en la API: `Nombre@Posicion`. Para forzar un id: `Nombre=12345`.
- **No subir onces a la vez que corre el ciclo** (17:50, 13:35...): el 27/09
  chocaron al guardar y la pasada no subió nada (el paso ahora falla en rojo).

**Para pedir pronósticos desde otro chat:** leer `pronosticos.md` (el
último del ciclo). Si hace falta el once real y la API no lo tiene (no lo
tuvo el 26/09), buscarlo en la web y seguir el paso 5 de la receta
manual. Después relanzar solo los scripts locales:

```
python3 modelos/selecciones/nota_jugadores_selecciones.py
python3 modelos/selecciones/pronostico_selecciones.py
```

**Arranque del 27/09 a las 12:00:** tope de 3.000 llamadas en esa pasada
(no 400). Faltan ~50 selecciones (~60 llamadas cada una) y hay 10 partidos
ese mismo día. Calendario de la ventana, sacado de Wikipedia el 26/09 (hora
UTC = CET de Wikipedia menos 2 h, horario de verano):

| día | Liga A | Liga B |
|---|---|---|
| dom 27/09 | Serbia-Países Bajos 16:00, Dinamarca-Gales 16:00, Alemania-Grecia 18:45, Noruega-Portugal 18:45 | Austria-Kosovo 16:00, Israel-Irlanda 18:45 |
| lun 28/09 | Bélgica-Francia 18:45, Turquía-Italia 18:45 | Georgia-Ucrania 16:00, Irlanda del Norte-Hungría, Rumanía-Bosnia, Suecia-Polonia 18:45 |
| mar 29/09 | Chequia-Inglaterra 18:45, España-Croacia 18:45 | Escocia-Suiza, Eslovenia-Macedonia del Norte 18:45 |
| jue 01/10 | Alemania-Serbia, Grecia-Países Bajos, Dinamarca-Portugal, Gales-Noruega 18:45 | Israel-Kosovo, Irlanda-Austria 18:45 |
| vie 02/10 | Bélgica-Turquía, Francia-Italia 18:45 | Hungría-Georgia, Ucrania-Irlanda del Norte, Bosnia-Suecia, Polonia-Rumanía 18:45 |
| sáb 03/10 | Croacia-Inglaterra 16:00, España-Chequia 18:45 | Macedonia del Norte-Escocia, Suiza-Eslovenia 18:45 |

Ligas C y D también juegan (la API las mete en la misma liga 5039). Kosovo
no tiene jugadores en la API: sus partidos saldrán "sin pronóstico".

**Pausa del 26/09:** la cuota de la API se agotó a las 20:00 UTC. Las
pasadas programadas antes del 27/09 a las 11:55 UTC no hacen nada (paso
"Esperar a que vuelva la cuota"). La primera pasada real es el 27/09 a las
12:00 UTC, con forma de clubes incluida. Después sigue el horario normal.

## Receta manual para una jornada (antes del ciclo, o para partidos fuera de la Nations League)

Todo con GitHub Actions (la clave de Highlightly solo vive en los secrets).
Rama main.

1. **Partidos y cuotas del día:** `nations_league_hoy.yml` (input `fecha`
   opcional). Lista todos los partidos de la liga 5039 de ese día y deja
   las cuotas básicas en `nations_league_hoy.md`.
2. **Datos de las selecciones:** `descargar_selecciones.yml` con
   `cruces = "Local|Visitante;Local2|Visitante2"`. Los nombres tienen que
   ser los EXACTOS de la API (sácalos del paso 1: "Czech Republic", no
   "Czechia"). El input `fecha` va vacío si es hoy.
   - Baja todos los partidos desde 2025, las estadísticas, los onces, el
     box-score por jugador y el H2H. Las temporadas son 2024, 2025 y 2026:
     la API mete la clasificación del Mundial en la temporada 2024.
   - Es reanudable: lo que ya está en `data/selecciones/raw/` no se vuelve
     a pedir. Unas 150-250 llamadas por selección nueva.
   - Reescribe `data/selecciones/equipos.json`, que manda en todo lo demás.
3. **Previa:** `previa_hoy.yml`. Baja TODAS las cuotas (1X2, goles,
   córners, tarjetas, marcador, primer gol...) a
   `data/selecciones/cuotas_hoy.csv`, más `/matches/{id}` con el árbitro.
4. **Local, sin API:**
   ```
   python3 modelos/selecciones/nota_jugadores_selecciones.py
   python3 modelos/selecciones/pronostico_selecciones.py
   ```
   La salida está en `modelos/selecciones/pronosticos.md`.
5. **Onces reales** (~1 h antes): `alineaciones_hoy.yml` y repetir el
   paso 4. **El 26/09 la API NO los tuvo ni a 20 minutos del pitido**,
   cuando llevaban 30 minutos confirmados en prensa.
   - Plan B: buscarlos en la web (WebSearch) y escribir a mano
     `data/selecciones/alineaciones_hoy.csv` con las columnas match_id,
     equipo, equipo_id, formacion, jugador_id, jugador, posicion.
   - Los ids se sacan por nombre de `jugadores_partido.csv`.
   - Un jugador sin id va con un id negativo inventado y su posición:
     recibe la media de su posición.

## Qué hace cada pieza

- **`nota_jugadores_selecciones.py`: nota justa por jugador.** Usa la
  matchRating de la API, que tiene la misma escala en club y en selección.
  - **Club (60%):** la nota de su club en el inicio de temporada (desde
    el 01/07), encogida hacia la media de su posición con 270 minutos.
  - **Selección (40%):** su nota con la selección desde 2025, con vida
    media de 180 días, encogida hacia su nota de club con 180 minutos.
  - **Club:** sale de `data/historico_xg_jugador.csv`. Solo cubre nuestras
    6 ligas: la liga checa no está, y 6-7 de los 11 checos van sin dato.
- **`modelo_selecciones.py`: modelo de conteos.** Poisson de ataque y
  defensa con encogimiento ridge, peso por recencia (365 días), factor de
  campo, variable de amistoso y calidad de plantilla.
  - **Calidad de plantilla:** parte de los minutos jugados por futbolistas
    con 900 o más minutos en 2025/26 en las 5 grandes ligas. Ancla a los
    rivales pequeños.
  - Sirve para goles (con goles y xG promediados), córners y amarillas.
- **`pronostico_selecciones.py`: junta todo.** Da el mercado sin margen,
  el modelo, el ajuste de forma del once (nota justa de hoy contra el nivel
  con la selección del once habitual, B_FORMA = 0.5, puesto a mano), el
  árbitro (sus tarjetas en nuestras ligas frente a la media de su liga,
  encogido con 10 partidos) y la cuota mínima.
- **`segunda_opinion_ambos_selecciones.py`:** la IA de ambos marcan de
  clubes, variante "solo precio". Da casi lo mismo que el mercado. No
  merece la pena repetirla.

## Listas para el usuario (05/10/2026)

Cuando pida "lo más probable" (una por partido, cuota mínima...), usar SOLO mercados
con historial medido en `evaluacion.md`: 1X2, sin empate, goles (1.5/2.5/3.5), ambos
marcan, córners y tarjetas. Nunca "marca primero": la API no da quién marca primero
y no tiene historial de aciertos. Petición del usuario: "siempre mete mercados ya probados".

## Cuánto fiarse

Resultado de la prueba hacia delante del 26/09: 48 partidos desde
octubre de 2025, cada uno pronosticado solo con los anteriores, contra la
tasa de los partidos previos.

| mercado | resultado | lectura |
|---|---|---|
| 1X2 | **+1.91s**, acierta el 65% | Algo sabe |
| Ambos marcan | **+1.28s** | Algo sabe |
| Más/menos goles | -0.7 a -1.2s | No aporta |
| Córners | -0.3 a -1.5s | No aporta; se queda corto: 8.9 predichos contra 9.9 reales |
| Tarjetas | +0.1 a -2.6s | No aporta |

No hay cuotas históricas de selecciones, así que **nada de esto está
medido contra el mercado**. En totales, córners y tarjetas manda el
mercado.

Tarjetas: cada línea la cotiza 1 sola casa. El modelo espera unas 2
amarillas y el mercado unas 4: seguramente cuentan distinto (la roja como
dos, puntos de tarjeta...). No fiarse del precio.

## Variables de clubes en selecciones (28/09/2026): el ranking FIFA entra

Pregunta del usuario: ¿por qué no tiene selecciones las variables del modelo
de clubes? `experimento_variables.py` (resultado en `experimento_variables.md`).
Prueba hacia delante: 337 partidos desde oct-2025, entreno desde ene-2025 (el
usuario pidió no ir muy atrás), sigmas contra el modelo de entonces:

| variable | 1X2 | más de 2.5 | ambos marcan | sin empate |
|---|---|---|---|---|
| **ranking FIFA** (idea del usuario, en lugar de la clasificación) | **+2.60s** | **+3.21s** | +0.73s | +1.26s |
| Elo desde ene-2025 (arranca del FIFA de dic-2024) | +2.39s | +3.06s | +0.50s | +1.16s |
| xG/xA de club de los titulares | +0.66s | -0.35s | +0.09s | -0.85s |
| todas juntas | +2.85s | +2.26s | +0.58s | +0.99s |

- **Comprobado antes de creérselo.** 1X2: positivo en los 4 trimestres y
  +1.85s sin los 5 partidos que más aportan. Más de 2.5: positivo en 3 de 4
  trimestres y +2.43s sin los 5 mejores.
- **Por qué funciona:** con ~15 partidos por selección el modelo sabía poco
  de cada una. El ranking resume años de resultados.
- **Elo:** correlación 1.00 con el FIFA (el FIFA ya es un Elo; en 20 meses el
  nuestro apenas se aparta de su arranque). No aporta nada encima.
- **xG de los titulares:** no aporta, igual que en clubes.
- **Enfrentamientos directos:** 117 de 507 partidos tienen uno previo en la
  ventana. Sin probar todavía.

**Entra en producción:**
- Ranking FIFA en el modelo de goles (`modelo_selecciones.ajustar(...,
  extras=("fifa",))`). De ahí salen 1X2, goles, ambos marcan, sin empate y
  primer gol.
- Córners y tarjetas, sin él.
- Cada partido usa el último ranking publicado ANTES de jugarse
  (`fifa_antes`). Nombres de la API -> FIFA en `ALIAS_FIFA`.

**Mantenerlo al día:**
- Ranking en `data/selecciones/ranking_fifa.csv` (11 publicaciones, dic-2024 a
  jul-2026). **Próximo: 07/10/2026.**
- Se baja de `https://inside.fifa.com/api/ranking-overview?locale=en&dateId=idNNNNN`.
  Los ids no se listan en la web: hay que probarlos a partir del último (15175).
- Si no se actualiza, el modelo sigue usando el último publicado (no falla,
  pero envejece).

## Sin empate (27/09/2026): el modelo propio no mejora, se deriva del de goles

Petición del usuario: reentrenar solo para "gana o pierde sin empate" (Asian
Handicap 0 en la API) sin tocar los demás mercados. `sin_empate.py` hace la
prueba hacia delante (252 partidos sin empate desde oct-2025, cada uno solo
con los anteriores; resultados en `sin_empate.md`):

| modelo | Brier | acierto | contra el derivado |
|---|---|---|---|
| derivado del de goles, P1/(P1+P2) | 0.1418 | 79% | - |
| propio (Bradley-Terry solo con partidos sin empate, ridge C=1 fijado antes) | 0.1490 | 79% | -1.52s |
| propio, C=0.3 / C=3 (control) | 0.1505 / 0.1531 | 78% / 81% | -1.95s / -1.59s |
| derivado recalibrado con los resultados anteriores | | | -1.5s |
| tasa base | 0.2459 | 55% | -9.59s |

El propio tira el 21% de partidos (los empates) y la diferencia de goles;
el derivado ya está bien calibrado (dice 70% -> pasa 71%, dice 91% -> pasa
97%). **Se usa el derivado**, como mercado aparte `sin_empate_local` en
`pronostico_selecciones.py` (peso inicial 0.5 como el 1X2, se aprende en
`evaluacion.md`; los empates no cuentan al evaluar). Comprobado que el resto
de mercados sale idéntico con y sin el cambio. No reabrir "modelo propio sin
empate" con estos mismos datos: solo con más partidos o datos nuevos.

## Fallos silenciosos ya encontrados (no repetir)

- **xG roto:** Francia-Inglaterra del 18/07/2026 trae el mismo xG (2.88)
  para los dos equipos. Si una estadística sale idéntica en los dos
  lados, se descarta.
- **Rivales sin jugadores en la API** (Brasil, Kosovo, Perú, San Marino,
  Guatemala): recibían la calidad media y San Marino pasaba por un equipo
  normal. Esos partidos se descartan.
- **"Calidad" mal contada:** contaba minutos en copas y en ligas de
  fuera. Ahora solo cuenta las 5 grandes.
- **Workflows vacíos:** un `sed` dejó los workflows sin `jobs` y pasaban
  `yaml.safe_load`. Comprueba siempre que tienen `jobs`.
- **CSV de alineaciones vacío:** cuando la API aún no tiene onces, el csv
  queda vacío y rompía la lectura. Ya se aguanta.
- **Once de una jornada anterior:** un `alineaciones_hoy.csv` viejo
  colaría el once del partido anterior de la misma selección. Ahora se
  filtra por los match_id de `equipos.json`.
- **Forma inventada en selecciones pequeñas (27/09):** un jugador sin
  datos de club recibía como "nota de club" la media de su posición en las
  grandes ligas. La forma resta su nota con la selección, así que en los
  equipos débiles salía positiva para todo el once: Gibraltar +0.32 (~+17%
  de goles), Armenia +0.24, Andorra +0.23. Ahora, sin club, cuenta su nota
  con la selección encogida hacia el nivel de su selección (180 minutos), y
  la base de la forma para ellos es esa misma nota: solo mueve la forma
  QUIÉN juega, no un valor por defecto. (Sin encoger, un debutante con un
  8.15 en su único partido subía a Lituania a +0.17.) Comprobado: entre club y
  selección no hay desfase de escala (club - selección = +0.04 ± 0.04 en
  163 jugadores con los dos datos).
- **Cuota atípica:** una casa descolgada (Casumo, España a 2.55 con
  mediana 2.12) inflaba la "mejor cuota". Ahora se ignora lo que esté un
  12% por encima de la mediana.

## Resultado del 26/09 (para comparar cuando se jueguen)

Pronóstico del modelo con los onces reales:

| partido | 1X2 | ambos marcan | goles esperados | marcador más probable |
|---|---|---|---|---|
| Inglaterra - España | España 51% | sí 54% | 1.09 - 1.68 | 1-1 |
| Chequia - Croacia | Croacia 60% (mercado 47%) | sí 62% | 1.19 - 2.18 | 1-2 |

**Resultado real** (sacado de prensa el 26/09 a las 21:50 UTC, con la
API sin cuota; la pasada del ciclo del 27/09 lo trae con estadísticas):

| partido | final | goles | 1X2 | más 2.5 | ambos marcan | primer gol |
|---|---|---|---|---|---|---|
| Inglaterra - España | **2-3** | Lamine Yamal 3', Gordon 37', Kane 41', Baena 61', Oyarzabal 75' (Kane falla un penalti en la 2ª parte) | acierta (España) | acierta | acierta | acierta (España) |
| Chequia - Croacia | **1-2** | Modrić 48', Karabec 55', Pašalić 78' | acierta (Croacia; mercado 47%, modelo 60%) | acierta | acierta | acierta (Croacia) |

El 1-2 de Chequia-Croacia era el marcador más probable del modelo.
Córners y amarillas (API, pasada del 27/09): Inglaterra-España 9 córners
(6-3) y 3 amarillas (3-0); Chequia-Croacia 7 córners (1-6) y 3 amarillas
(2-1). Aciertos: córners 3 de 4 líneas (falla "más de 8.5" en
Chequia-Croacia) y tarjetas 3 de 4 (falla "más de 3.5" en Inglaterra-España). **Son 2 partidos: no dicen nada del modelo.**
Cada lado pronosticado tenía un 50-60%: acertarlos con dos partidos
se parece mucho a acertar lanzamientos de moneda. La medida de verdad es el Brier
contra el mercado en `evaluacion.md`, a partir de 30 partidos.

Fuentes: TNT Sports (Inglaterra-España) y VAVEL (Chequia-Croacia).

## Fuga de la tabla de clubes arreglada (29/09/2026): a selecciones no le afecta

En `rasgos.py` de clubes, la posición en la tabla y la media de tarjetas de
relleno del árbitro dejaban ver el resultado de otro partido jugado a la
misma hora. Desde el 29/09 se calculan por días. Selecciones solo toca
`rasgos.py` en `segunda_opinion_ambos_selecciones.py`, que usa la variante
"solo precio" (sin tabla ni árbitro), así que sus números no cambian. Si algún
día usa variables de clubes, ya van sin la fuga. Detalle en `docs/notas_proyecto.md`
y en `BITACORA.md`.
