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

Dónde está cada cosa:
- Modelos de clubes (1X2, goles, córners, tarjetas) y reglas generales: `CLAUDE.md`.
- Ambos marcan: `modelos/ambos_marcan/CLAUDE.md`.
- Selecciones: `modelos/selecciones/CLAUDE.md` (otro chat).
- NBA: `docs/otros_deportes/nba.md`.
- Tenis: `modelos/tenis/CLAUDE.md`.

---

## 30/09/2026

### Cambios de código y ficheros

| qué | por qué | ficheros | commit |
|---|---|---|---|
| Empieza el tema **tenis** (ATP y WTA), aparte del fútbol: guía y plan. | Petición del usuario: "quiero que empecemos a pronosticar tenis", los dos circuitos. | `modelos/tenis/CLAUDE.md` | este commit |
| Descarga de tennis-data.co.uk (resultados y cuotas de cierre, ATP 2000+, WTA 2007+) y Sackmann (partidos con stats de saque, 1991+ circuito principal, 2010+ Challenger/qualy/ITF). Por GitHub Actions, al empujar a esta rama. | Highlightly no tiene tenis. Las dos fuentes están bloqueadas desde el contenedor (403, y GitHub solo a los repos del usuario). **Aprobada por el usuario** antes de lanzarla. | `modelos/tenis/scripts/descargar_tenis.py`, `.github/workflows/descargar_tenis.yml` | este commit |
| El workflow de tenis ya no se para si falla Sackmann, y deja un sondeo (`data/tenis/sondeo_sackmann.md`): qué responde GitHub por `JeffSackmann/tennis_atp`/`tennis_wta` y qué copias hay. | 1ª ejecución: el clon falló con "could not read Username" (repo inexistente o privado) y por eso tennis-data no llegó a bajarse. No se da Sackmann por desaparecido sin ver la respuesta. | `.github/workflows/descargar_tenis.yml`, `modelos/tenis/scripts/descargar_tenis.py` | este commit |
| Reglas para validar Sackmann antes de usarlo (cruce con tennis-data, imposibles en stats de saque) y aviso de fuga: `tourney_date` es el inicio del torneo. | Pregunta del usuario: qué pasa si los datos de Sackmann son erróneos. | `modelos/tenis/CLAUDE.md` | este commit |
| Descarga de **TennisMyLife** (ATP, Challenger, previas y WTA; 1991/2010-29/09/2026) y de la **copia de archivo de Sackmann** en Hugging Face (junio de 2026). Desde el contenedor, sin Actions. | Los repos originales de Sackmann ya no existen en GitHub. Aprobada por el usuario. | `modelos/tenis/scripts/descargar_tml_sackmann.py`, `data/tenis/tennismylife/`, `data/tenis/sackmann/`, `data/tenis/resumen_*.md` | este commit |
| **TennisMyLife no es independiente de Sackmann**: mismo nº de partidos ATP cada año, WTA casi idéntica. Solo tennis-data sirve para validar. | Comprobado partido a partido antes de usarlas como control cruzado. Un primer cruce por `tourney_id`+`match_num` dio diferencias falsas: cada fuente numera distinto. | `modelos/tenis/CLAUDE.md` | este commit |
| El workflow de tenis baja solo tennis-data y ya no se dispara al empujar (solo a mano). | Sackmann se baja ahora desde el contenedor; así se evita relanzar la descarga en cada cambio del script. | `.github/workflows/descargar_tenis.yml`, `modelos/tenis/scripts/descargar_tenis.py` | este commit |
| Validación interna de Sackmann y TennisMyLife: imposibles en stats, texto en numéricas, duplicados. Sackmann limpio (0 imposibles en 79.299 partidos ATP); los errores de TennisMyLife están en lo que añade él (Davis 2025, previas RG 2026, 2026 tecleado a mano). | Petición del usuario: cuidado con datos erróneos. | `modelos/tenis/scripts/validar_interno.py`, `data/tenis/validacion_interna.md`, `modelos/tenis/CLAUDE.md` | este commit |
| **Se retira la descarga automática de tennis-data** (workflow y script); nuevo `procesar_tennis_data.py` que convierte los ficheros que el usuario baja a mano. | La ejecución salió en verde con 47/47 FALLO (el script se tragaba el motivo). Además tennis-data (y football-data) limitan el uso a particulares y bloquean a agentes de IA en robots.txt: no se esquiva. El nuevo script sale con error si no convierte nada. | `modelos/tenis/scripts/procesar_tennis_data.py`, `data/tenis/tennis_data_crudo/LEEME.md`; borrados `.github/workflows/descargar_tenis.yml`, `modelos/tenis/scripts/descargar_tenis.py` | este commit |
| API-Tennis funciona: 61 partidos en juego (ITF, Challenger, ATP, WTA) con saque, puntos y punto a punto; cuotas en directo con línea, suspensión y hora. Fallo arreglado en `estado()`: la corrección de ventaja se aplicaba en tie-break. | Resultado de la prueba. | `data/tenis/api_tennis/prueba.md`, `modelos/tenis/scripts/api_tennis.py` | este commit |
| Prueba de API-Tennis en GitHub Actions (2 llamadas: get_livescore y get_live_odds) con la clave guardada por el usuario como secreto del repo (se prueban varios nombres). Los errores ya no muestran la URL (llevaría la clave). | La clave está como secreto de GitHub, no en esta sesión. | `.github/workflows/prueba_api_tennis.yml`, `modelos/tenis/scripts/prueba_api_tennis.py`, `modelos/tenis/scripts/api_tennis.py` | este commit |
| Conector de API-Tennis (cuenta del usuario): marcador con saque y puntos, y cuotas en directo por mercado. Clave en `API_TENNIS_KEY` (pendiente de que el usuario la guarde en el entorno). Probado solo con una respuesta de ejemplo. Tennis Explorer descartado por sus condiciones de uso. | Petición del usuario: marcadores más rápidos y completos que ESPN. | `modelos/tenis/scripts/api_tennis.py` | este commit |
| **Calculadora en directo**: Markov desde cualquier marcador + marcadores de ESPN (gratis, sin clave; sets y juegos). Da ganador, sets, total de juegos y hándicap. Sin validar aún. Fallos arreglados: cuadros femeninos en el enlace ATP, 5 sets en todo ATP, nombres chinos al revés. | Idea del usuario: en directo puede haber valor en juegos y sets. | `modelos/tenis/scripts/markov_tenis.py` (`partido_desde`), `modelos/tenis/scripts/directo.py`, `modelos/tenis/pronosticos/directo_2026-09-30_0950.md` | este commit |
| Pronósticos de ITF femenino del 30/09-01/10/2026 (85 partidos abiertos en Kalshi): favorito según Kalshi cuando hay precio fiable, si no Elo de ITF. | Petición del usuario: partidos de hoy en ITF femenino. | `modelos/tenis/pronosticos/itf_femenino_2026-09-30.md` | este commit |
| **Entrenar en ITF**: ITF masculino de Sackmann 2010-jun 2026 (estadísticas en 2025-2026) + resultados de ITF de Kalshi jun-sep 2026 como historial. Debutantes en ITF con nota de partida baja (1100 h / 1300 m, elegida con ITF 2025). Acierto en ITF de Kalshi: Elo 68,2% (h) y 69,6% (m) contra Kalshi 74,5% y 72,2%. | Petición del usuario: entrenar en ITF. | `modelos/tenis/scripts/itf.py`, `modelos/tenis/scripts/elo_tenis.py` (`itf`, `extra`, `inicial_itf`), `modelos/tenis/scripts/descargar_tml_sackmann.py`, `data/tenis/sackmann/atp_matches_futures_*.csv`, `data/tenis/resumen_itf.md`, `data/tenis/itf.md` | este commit |
| Fallo silencioso: la clave de jugador dejaba espacios y quitaba guiones ("Bruce-Smith" -> "brucesmith" frente a "bruce smith"). Ahora solo letras. | Cruce de nombres Kalshi-Sackmann en ITF. | `modelos/tenis/scripts/elo_tenis.py` (`norm`) | este commit |
| Kalshi completo con ITF: ganador bien calibrado en ITF hombres y mujeres (pendiente 0,94/0,96), poco líquido (38-51% con precio, diferencial 4 céntimos), a ciegas pierde. Ningún nivel tiene el ganador mal puesto. | Cerrar la búsqueda del mercado más flojo. | `data/tenis/kalshi/precios_KXITF*.csv`, `data/tenis/calibracion_kalshi.md`, `modelos/tenis/CLAUDE.md` | este commit |
| Kalshi con Challenger ATP y acierto añadido al informe: Kalshi acierta más que el modelo de puntos en todos los mercados (Challenger ATP 66,0% contra 64,9%) salvo hándicap ATP (empate). | Objetivo del usuario: acertar más. | `modelos/tenis/scripts/kalshi_puntos.py`, `data/tenis/kalshi_puntos.md`, `data/tenis/kalshi/precios_KXATPCHALLENGERMATCH.csv` | este commit |
| Acierto del ganador de cada opción (objetivo del usuario: acertar más): cuota 68,3% (lo mejor; añadir modelos no sube); sin cuota, modelo de puntos 67,1% (el mejor), Elo 66,3%. Techo ~68% (GS ATP 74%, ATP 250 65%). | Aclaración del usuario: acertar más, no ganar al mercado. | `modelos/tenis/scripts/acierto.py`, `data/tenis/acierto.md` | este commit |
| Kalshi (parcial): ganador ATP/WTA bien calibrado; total y hándicap de juegos ATP con precio demasiado extremo (-3,98s y -5,62s) pero el más caro de operar (a ciegas -7% a -17%). El modelo de puntos no gana en ningún mercado de Kalshi. Fallo de lectura de nombres en juegos arreglado. | Buscar el mercado más flojo y probar el modelo de puntos donde debería servir. | `modelos/tenis/scripts/kalshi_puntos.py`, `modelos/tenis/scripts/calibracion_kalshi.py`, `data/tenis/kalshi_puntos.md`, `data/tenis/calibracion_kalshi.md` | este commit |
| Mezcla por circuito y nivel: separar no mejora la predicción (8 grupos: +0,46s, peor). Pista en ATP (gana en sus 4 niveles, 1000 +3,7% a ~1,5s; WTA pierde), elegida tras mirar: se fija como regla para seguir en papel. | Pregunta del usuario: no mezclar torneos de distinto nivel. | `modelos/tenis/scripts/por_nivel.py`, `data/tenis/por_nivel.md` | este commit |
| Ventana de ajuste de la mezcla: 3 años = todo lo anterior; 1-2 años peor (más apuestas falsas, -0,9% a -1,1%). | Pregunta del usuario: ventanas cortas de 3-4 años. | `modelos/tenis/scripts/ventanas.py`, `data/tenis/ventanas.md` | este commit |
| Cuota + Elo + puntos juntos (ventana móvil): mejor combinación del tenis (2023 -2,63s, 2025 -1,77s) con pesos estables (Elo negativo, puntos positivo), pero en dinero 2021-2026 -1,49% y 2022-2026 ~0%. No es hallazgo. | Pregunta del usuario: juntar modelos con la cuota como en fútbol. | `modelos/tenis/scripts/mezcla_tres.py`, `data/tenis/mezcla_tres.md` | este commit |
| Modelo de puntos contra los precios de Kalshi (partido): pierde en ATP (+4,81s de log-loss, apostando -5,9%), WTA (+4,28s, -3,8%) y Challenger WTA (+3,38s, -2,4%). Emparejamiento: en los mercados de partido los dos lados llevan el nombre del mismo jugador y el texto solo trae apellidos. Total de juegos, hándicap y Challenger ATP pendientes de la descarga. | Probar el modelo de puntos donde el precio podría ser flojo. | `modelos/tenis/scripts/kalshi_puntos.py`, `data/tenis/kalshi_puntos.md` | este commit |
| **Modelo de puntos con incertidumbre** (saque/resto por jugador y superficie, varianza que crece con el tiempo sin jugar, Markov puntos->partido): en el ganador empata con el Elo y no aporta al mercado (ventana móvil 2021-2026). El crecimiento de la incertidumbre por tiempo sin jugar lo eligen los datos de puntos. | Cambio estructural propuesto por otra conversación; su valor debería estar en juegos/hándicap (siguiente prueba, Kalshi). | `modelos/tenis/scripts/markov_tenis.py`, `modelos/tenis/scripts/modelo_puntos.py`, `modelos/tenis/scripts/evaluar_puntos.py`, `data/tenis/evaluar_puntos.md` | este commit |
| Desfase horario, altitud y velocidad de pista (de la propuesta de "pipeline" con GNN): nada en desfase ni altitud; velocidad de pista x saque es pista débil (+2,05s en prueba, no llega a 2,5s). Fallo silencioso: sin estandarizar, el ajuste daba coeficiente 0. | Petición del usuario: probar lo construible de esa propuesta. | `modelos/tenis/scripts/entorno.py`, `modelos/tenis/scripts/rasgos_tenis.py` (`ritmo_pista`), `data/tenis/entorno.md` | este commit |
| Kalshi limita a ~1 petición/s efectiva en mercados antiguos (Challenger WTA: 2.000 en 20 min, incluso en Actions). Se cancela y se relanza con muestra de 1.500 antiguos por serie; recientes completos. Tres series ya guardadas (ATP, WTA, Challenger WTA). | Petición del usuario: reducir tiempo. | `.github/workflows/kalshi_tenis.yml` | este commit |
| Descarga de Kalshi más rápida: una máquina de GitHub por serie en paralelo, y en ITF muestra fija (semilla 1) de 4.000 mercados antiguos por serie; el resto completo. De ~2,5 h a ~20-25 min. Se cancela la primera ejecución. | Petición del usuario: reducir el tiempo, aunque sea con menos datos. | `modelos/tenis/scripts/kalshi_precios.py` (`--max=N`), `.github/workflows/kalshi_tenis.yml` | este commit |
| Precios de Kalshi de antes del partido (foto a cierre - 4 h; ATP 6 h; control 2 h antes), en GitHub Actions para no gastar la sesión: recientes en lotes de 100, antiguos de uno en uno a 8/s (el límite da 429 con más; en local iban a 1,7/s). Script de análisis listo (`calibracion_kalshi.py`: calibración, pendiente favorito-marginado, apuestas a ciegas con comisión, referencia contra Betfair). | Petición del usuario: más rápido y sin gastar créditos. | `modelos/tenis/scripts/kalshi_precios.py`, `modelos/tenis/scripts/calibracion_kalshi.py`, `.github/workflows/kalshi_tenis.yml` | este commit |
| **Kalshi: inventario de mercados de tenis cerrados** (API pública sin clave, aprobada por el usuario): ATP 4.733 y WTA 4.700 partidos desde jun-2025, Challenger ATP 9.351 y WTA 1.962 desde ene-2026, ITF 18.585 (hombres) y 16.513 (mujeres) desde abr-2026, total de juegos ATP 1.806 / WTA 600 y hándicap de juegos ATP 1.868. Lo anterior al 01/08/2026 está en `/historical/markets` (sin él todo parecía empezar el 24/07/2026). Falta el precio de antes del partido. | Buscar mercados más blandos (Challenger/ITF) y otros mercados. | `modelos/tenis/scripts/kalshi_mercados.py`, `data/tenis/kalshi/` | este commit |
| Segunda búsqueda de fuentes (solo web): Polymarket y Kalshi (mercados de predicción, datos gratis sin clave, con Challenger/ITF y total de juegos en Polymarket), API-Tennis (14 días de prueba). Tennis API y SportsAPI365 parecen el mismo proveedor. | Petición del usuario: más opciones. | `modelos/tenis/CLAUDE.md` | este commit |
| Búsqueda (solo web, sin llamadas) de cuotas de Challenger/ITF y de juegos/hándicap: Kaggle ehallmar (2010-2018, gratis, ATP+Challenger+ITF, ganador/spread/totales), Tennis API (10-39 $/mes, sin detalles publicados), OddsPapi (gratis pero 1 partido por petición). | Petición del usuario: opciones 2 y 3. | `modelos/tenis/CLAUDE.md` | este commit |
| Cinco situaciones (local, previa, cansancio, regreso tras parón, cambio de superficie) contra el mercado recalibrado, entreno 2020-2023 y prueba 2024-2026: ninguna llega a 2,5 sigmas. "Previa" se desinfla (+3,61s -> +0,84s). Pistas a vigilar: regreso y cambio de superficie (el mercado sobrevalora al jugador sin ritmo). | Seguir buscando mejoras (petición del usuario). | `modelos/tenis/scripts/situaciones.py`, `modelos/tenis/scripts/rasgos_tenis.py`, `modelos/tenis/scripts/elo_tenis.py`, `data/tenis/situaciones.md` | este commit |
| Modelo con saque/resto, fatiga, perfil, cara a cara y Elo (logística y XGBoost, 20 configuraciones, elegida en 2023, juzgada en 2024-2026): nada mejora al mercado recalibrado con significación. Pista a vigilar: fatiga. | Petición del usuario: probar lo que el Elo no ve. | `modelos/tenis/scripts/rasgos_tenis.py`, `modelos/tenis/scripts/modelo_tenis.py`, `data/tenis/modelo_tenis.md` | este commit |
| **Fallo silencioso**: TennisMyLife WTA 2026 con columnas desplazadas (edad 3.387, altura = fecha de nacimiento) y alturas 0 en Challengers. Empeoraba 2026 sin error. Edad/altura fuera de rango pasan a vacío; `validar_interno.py` cuenta los fuera de rango. | Un número diez veces mayor que los demás en la prueba. | `modelos/tenis/scripts/rasgos_tenis.py`, `modelos/tenis/scripts/validar_interno.py`, `data/tenis/validacion_interna.md` | este commit |
| **Elo por superficie** (ATP y WTA, historial largo con niveles bajos, control de fuga que pasa) contra el cierre, elegido en 2020-2023 y juzgado en 2024-2026: pierde +4,6 a +8,5 sigmas en log-loss; la mezcla con el mercado da peso negativo al Elo y no mejora (0,25-1,26s). | Petición del usuario (opción 3: Elo y sesgo). | `modelos/tenis/scripts/elo_tenis.py`, `modelos/tenis/scripts/evaluar_elo.py`, `data/tenis/evaluar_elo.md` | este commit |
| **Regla del favorito** (15 candidatas, elegida con 2020-2023: 1ª-2ª ronda, favorito >= 90%, +1,61%): en la prueba -0,09% (2024-2025, Pinnacle) y -2,07% (2026, Betfair). Se va a cero: no es explotable. | Idem. | `modelos/tenis/scripts/regla_favorito.py`, `data/tenis/regla_favorito.md` | este commit |
| Calibración del cierre de Pinnacle en ganador, ATP+WTA 2020-2026 (26.467 partidos): sesgo favorito-marginado real (pendiente 1,135, +4,85s; fuerte en 1ª-2ª ronda y Grand Slam; 2025 sin sesgo), pero apostar a ciegas al favorito pierde -2,3%/-2,0% y con retiradas el hueco desaparece. Pinnacle sale de tennis-data desde feb-2026; entra Betfair Exchange. | Medir el precio antes de montar un modelo. | `modelos/tenis/scripts/calibracion_cierre.py`, `data/tenis/calibracion_cierre.md`, `modelos/tenis/CLAUDE.md` | este commit |
| Cruce tennis-data contra Sackmann y TennisMyLife: 96-98% emparejan, ganador al revés en 4-8 de ~15.000 (24 en TennisMyLife WTA), marcador distinto 0,3%. tennis-data también tiene errores (De Minaur-Fritz 2024, superficies). | Validar con una fuente independiente antes de usar nada. | `modelos/tenis/scripts/cruce_fuentes.py`, `data/tenis/cruce_fuentes.md`, `modelos/tenis/CLAUDE.md` | este commit |
| tennis-data 2020-2026 subido por el usuario y convertido: ATP 16.642 partidos y WTA 15.548, con Pinnacle (PSW/PSL), Bet365, máxima, media y Betfair Exchange (BFEW/BFEL). Los WTA subieron como "2024 (1).xlsx": el script los reconoció por el contenido. | Referencia de mercado y fuente independiente para validar. | `data/tenis/tennis_data_crudo/`, `data/tenis/tennis_data/`, `data/tenis/resumen_tennis_data.md` | cd3a5be y 6e52a9a (subidas), este commit |
| `procesar_tennis_data.py` acepta los ficheros tal cual salen de la web (.zip/.xlsx/.xls, cualquier nombre, ATP y WTA mezclados): circuito y año salen del contenido. | Petición del usuario: que no le toque renombrar ni descomprimir. Probado con ficheros de mentira (xlsx suelto, zip con WTA, fichero basura). | `modelos/tenis/scripts/procesar_tennis_data.py`, `data/tenis/tennis_data_crudo/LEEME.md` | este commit |
| Sondeo en Actions: `JeffSackmann/tennis_atp` y `tennis_wta` dan Not Found; en su cuenta solo queda `tennis_MatchChartingProject`. | Confirmar que Sackmann se ha ido antes de darlo por hecho. | `data/tenis/sondeo_sackmann.md` | ab526b5 |

---

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
  frente al cierre, cuota como variable. Todo en `CLAUDE.md`, con sus tablas.
- Ambos marcan: todo en `modelos/ambos_marcan/CLAUDE.md`.
