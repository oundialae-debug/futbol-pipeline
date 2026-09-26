# Selecciones (Nations League y similares)

Tema APARTE del proyecto principal (ambos marcan de clubes). Montado el
26/09/2026 para Inglaterra-España y Chequia-Croacia. Se reutiliza para las
siguientes jornadas de la Nations League (octubre-noviembre 2026).

## Automático: el ciclo de la Nations League (desde el 26/09/2026)

`nations_league_ciclo.yml` corre solo 3 veces al día (07:20, 13:35 y 17:50
UTC). También se puede lanzar a mano, con los inputs `tope_llamadas` y
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
   - Detalles de cada partido terminado.
   - Previa de los partidos de las próximas 36 h: cuotas, árbitro y once
     si la API lo tiene. Escribe `equipos.json`, `cuotas_hoy.csv` y
     `alineaciones_hoy.csv`.
3. **Notas** de los jugadores de esos partidos.
4. **Pronósticos:** `pronostico_selecciones.py` escribe
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

**Para pedir pronósticos desde otro chat:** leer `pronosticos.md` (el
último del ciclo). Si hace falta el once real y la API no lo tiene (no lo
tuvo el 26/09), buscarlo en la web y seguir el paso 5 de la receta
manual. Después relanzar solo los scripts locales:

```
python3 modelos/selecciones/nota_jugadores_selecciones.py
python3 modelos/selecciones/pronostico_selecciones.py
```

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
- **Cuota atípica:** una casa descolgada (Casumo, España a 2.55 con
  mediana 2.12) inflaba la "mejor cuota". Ahora se ignora lo que esté un
  12% por encima de la mediana.

## Resultado del 26/09 (para comparar cuando se jueguen)

Pronóstico del modelo con los onces reales:

| partido | 1X2 | ambos marcan | goles esperados | marcador más probable |
|---|---|---|---|---|
| Inglaterra - España | España 51% | sí 54% | 1.09 - 1.68 | 1-1 |
| Chequia - Croacia | Croacia 60% (mercado 47%) | sí 62% | 1.19 - 2.18 | 1-2 |

Apuntar el resultado real aquí cuando se sepa. Con los resultados de
varias jornadas se podrá empezar a medir el modelo contra el mercado.
