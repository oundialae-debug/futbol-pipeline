# Graph Report - futbol-pipeline  (2026-10-10)

## Corpus Check
- 218 files · ~384,432 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .woff2 1)

## Summary
- 1794 nodes · 4088 edges · 126 communities (106 shown, 20 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 99 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3b79e2e8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- backfill_h2h_profundo.py
- contraste_directo.py
- descanso_en_vivo.py
- apuesta_ambos_marcan.py
- datos_clubes.py
- experimento_titulares_2324.py
- requests
- datos_rankings.py
- datetime
- time
- json
- equipaciones.py
- modelo_ambos_marcan.py
- ambos_marcan/scripts/rasgos.py
- boletin.py
- diagnostico_directo.py
- aporta_algo.py
- diagnostico_api.py
- post_partido.py
- collections
- cerrar_descanso.py
- backtest_valor.py
- auditoria2_precio.py
- modelo_selecciones.py
- descargar_selecciones.py
- Ambos Marcan -- offshoot enfocado de futbol-pipeline
- generar.py
- Bitácora del proyecto
- afinar_ambos.py
- Pronósticos de selecciones (06/10/2026 17:58 UTC)
- Notas para trabajar en este repositorio
- sondeo_live_odds.py
- sondeo_odds.py
- calendario_mes.py
- datos_formatos.py
- datos_selecciones.py
- ambos_marcan/scripts/evaluar_mercados.py
- casas_descolgadas.py
- La API de Highlightly, en lo que nos afecta
- backfill_perfil_jugador.py
- censo_tarjetas.py
- ambos_marcan/scripts/modelo_xgboost.py
- comparar_entreno_con_huecos.py
- monitor_directo.py
- descargar_partido.py
- sin_empate.py
- Estado: mercado poco competido + value bets + herramienta interna
- sys
- re
- auditoria2_tabla_fuga.py
- radiografia_ligas.py
- UEFA Nations League, 2026-09-26 (hora de España)
- backfill_titulares_boxscore.py
- backfill_historico.py
- cuotas_football_data.py
- numpy
- columnas_rasgo_default
- Provider APIs - Setup Guides
- Selecciones (Nations League y similares)
- cosechar_cuotas.py
- sondeo_frescura.py
- Doble Oportunidad, Sin Empate y Más/Menos goles
- sondeo_titulares_boxscore.py
- NBA: qué mercado atacar y con qué variables (28/09/2026)
- El sesgo favorito-marginado: existe, y no se puede cobrar
- sondeo_faltas.py
- scripts/backfill_boxscore.py
- backfill_xg_jugador.py
- ¿Hay arbitraje? Medido en la mejor condición posible, y no
- Cierre del registro del descanso -- 2026-09-23 23:19 UTC
- recalibrar_ambos.py
- ¿Hay algún mercado donde el precio esté MAL, o solo caro?
- csv
- backfill_lineups.py
- ¿Se puede ganar dinero con esta API, GitHub y una IA?
- Agenda del 2026-10-10
- Inference Providers - Setup Guides
- Free LLM API Setup
- La pista de la mezcla murió al crecer la muestra
- Rumanía Liga II y México Liga MX: auditadas, ninguna es la respuesta hoy
- Middling: cómo funciona y cuánto se podría ganar, medido
- Qué 8 casas abrir: 9,58 puntos de diferencia en cada apuesta
- Backtest de valor -- 2026-09-20 19:37 UTC
- pandas
- scripts/rasgos.py
- Sondeo: Nations League -- gol de equipo en la 1ª parte
- Calendario -- próximos 30 días
- Cloudflare Workers AI
- GitHub Models
- Groq
- LLM7.io
- Kluster AI
- OpenRouter
- Hugging Face
- NVIDIA NIM
- Cohere
- Google Gemini
- El modelo
- ambos_marcan_hoy.py
- Sondeo: temporadas anteriores a la 2025/26
- Calibración del mercado -- 2026-09-20 18:37 UTC
- Casas descolgadas del consenso -- 2026-09-20 17:36 UTC
- Ambos Marcan
- Registro en papel: modelo de ambos marcan (desde el 27/09/2026)
- Sondeo: gol de equipo en la 1ª parte (5 grandes ligas)
- boletin.md
- calibracion_correct_score.md
- censo_margenes.md
- descanso_en_vivo.md
- otros_deportes/README.md
- historico_por_liga.md
- evaluacion.md
- experimento_variables.md
- sin_empate.md
- pronosticos_jornada.md
- sondeo_titulares_boxscore.md
- sondeo_xg_jugador.md
- ambos_hay_partido.py
- backfill_arbitro_clima.py
- calcular_calidad_plantilla
- experimento_temporada_extra.py
- experimentos_cuota_feature.py
- os
- sondeo_temporadas_antiguas.py
- prueba_post_partido.py
- Falso

## God Nodes (most connected - your core abstractions)
1. `e()` - 40 edges
2. `Ambos Marcan -- offshoot enfocado de futbol-pipeline` - 38 edges
3. `construir()` - 36 edges
4. `Notas para trabajar en este repositorio` - 36 edges
5. `Bitácora del proyecto` - 35 edges
6. `pagina()` - 20 edges
7. `columnas_rasgo_default()` - 19 edges
8. `construir()` - 18 edges
9. `main()` - 16 edges
10. `analizar()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `06/10/2026 — redes: nunca el mismo color para los dos equipos` --references--> `separar()`  [INFERRED]
  BITACORA.md → redes/plantillas/generar.py
- `06/10/2026 — redes: plantillas head_to_head y ranking` --references--> `head_to_head()`  [INFERRED]
  BITACORA.md → redes/plantillas/generar.py
- `Comprobaciones hechas en la revisión de código (sin cambios)` --references--> `pronosticar()`  [INFERRED]
  BITACORA.md → scripts/ambos_marcan_hoy.py
- `Auditoría externa (29/09/2026): pruebas de los puntos aceptados` --references--> `ajustar()`  [INFERRED]
  modelos/ambos_marcan/CLAUDE.md → scripts/btts_implicito.py
- `Segunda auditoría externa (29/09/2026): reproducida con XGBoost real` --references--> `preparar()`  [INFERRED]
  modelos/ambos_marcan/CLAUDE.md → scripts/modelo_ambos_marcan.py

## Import Cycles
- None detected.

## Communities (126 total, 20 thin omitted)

### Community 0 - "backfill_h2h_profundo.py"
Cohesion: 0.53
Nodes (4): clave_par(), main(), pedir(), ya_tengo()

### Community 1 - "contraste_directo.py"
Cohesion: 0.23
Nodes (9): buscar(), cargar_referencia(), desempaquetar(), en_juego(), main(), minuto_de(), normalizar(), pedir() (+1 more)

### Community 2 - "descanso_en_vivo.py"
Cohesion: 0.07
Nodes (33): analizar(), aplanar_cuotas(), apuntar_consumo(), buscar_en_juego(), consumo_de_hoy(), desempaquetar(), en_juego(), es_descanso() (+25 more)

### Community 3 - "apuesta_ambos_marcan.py"
Cohesion: 0.13
Nodes (16): Cambios de código y ficheros, pronosticar(), main(), rasgos_mercado(), resumen(), main(), precio_directo(), sin_margen() (+8 more)

### Community 4 - "datos_clubes.py"
Cohesion: 0.09
Nodes (31): 10/10/2026 — redes: post-partido AUTOMÁTICO en vídeo (`post_partido.py` + `post_partido.yml`), APIs gratuitas, futbol-pipeline, Grafo de conocimiento (graphify), Mapa, Notas compartidas, ajustar_poisson(), buscar() (+23 more)

### Community 5 - "experimento_titulares_2324.py"
Cohesion: 0.20
Nodes (10): main(), lesiones(), main(), rasgos(), valor_antes(), valores(), comparar(), main() (+2 more)

### Community 6 - "requests"
Cohesion: 0.10
Nodes (14): desempaquetar(), main(), pedir(), desempaquetar(), main(), pedir(), desempaquetar(), main() (+6 more)

### Community 7 - "datos_rankings.py"
Cohesion: 0.09
Nodes (25): 06/10/2026 — redes: índice 2yellow del Balón de Oro, dibujo(), dist(), dominantes(), hexa(), lab(), rgb(), balon_oro_indice() (+17 more)

### Community 8 - "datetime"
Cohesion: 0.06
Nodes (35): cargar(), franjas(), main(), desempaquetar(), esquema(), main(), pedir(), probar() (+27 more)

### Community 9 - "time"
Cohesion: 0.13
Nodes (12): lista(), main(), pedir(), main(), obtener_detalle_partido(), obtener_partidos_recientes(), es_derbi(), main() (+4 more)

### Community 10 - "json"
Cohesion: 0.06
Nodes (48): main(), resultados(), aplanar(), calendario(), clave(), detalles(), historial(), lista() (+40 more)

### Community 11 - "equipaciones.py"
Cohesion: 0.14
Nodes (16): choca(), colores_grupo(), colores_lista(), colores_partido(), contraste(), distancia(), kit(), _lab() (+8 more)

### Community 12 - "modelo_ambos_marcan.py"
Cohesion: 0.08
Nodes (16): main(), rasgos_hoy(), grupo(), main(), comparar(), main(), main(), preparar() (+8 more)

### Community 13 - "ambos_marcan/scripts/rasgos.py"
Cohesion: 0.12
Nodes (12): a_largo(), calcular_arbitro(), calcular_btts(), calcular_elo(), calcular_h2h(), calcular_h2h_profundo(), calcular_rotacion(), calcular_tabla() (+4 more)

### Community 14 - "boletin.py"
Cohesion: 0.11
Nodes (14): consenso_de(), escribir(), linea_boletin(), main(), mejor_precio_mio(), modelo_validado(), Apuesta, comparar_sistemas() (+6 more)

### Community 15 - "diagnostico_directo.py"
Cohesion: 0.16
Nodes (13): aplanar_cuotas(), buscar_en_vivo(), describir(), descubrir_ligas(), desempaquetar(), esta_en_juego(), main(), minuto_de() (+5 more)

### Community 16 - "aporta_algo.py"
Cohesion: 0.14
Nodes (9): brier(), cargar_cuotas_1x2(), main(), mejor_peso(), probabilidades_de_mercado(), main(), probabilidad_mercado(), cuotas_por_partido() (+1 more)

### Community 17 - "diagnostico_api.py"
Cohesion: 0.28
Nodes (11): aplanar_cuotas(), arbitro_previo(), cuotas(), describir(), estados_y_en_vivo(), eventos_parciales(), limites_del_plan(), main() (+3 more)

### Community 18 - "post_partido.py"
Cohesion: 0.13
Nodes (18): ahora(), anadir_fila(), bajar_pista(), elegir_pista(), en_historico(), fechas(), fin(), git() (+10 more)

### Community 19 - "collections"
Cohesion: 0.12
Nodes (10): familia_de(), main(), pedir(), main(), pedir(), main(), pedir(), desempaquetar() (+2 more)

### Community 20 - "cerrar_descanso.py"
Cohesion: 0.43
Nodes (4): brier(), main(), pedir(), resultado_final()

### Community 21 - "backtest_valor.py"
Cohesion: 0.20
Nodes (9): desempaquetar(), desmarginar(), familia_de(), handicap_local(), hechos_del_partido(), main(), pedir(), resolver() (+1 more)

### Community 22 - "auditoria2_precio.py"
Cohesion: 0.32
Nodes (8): brier(), ll(), logit(), main(), comp(), sig(), x_precio(), xgb()

### Community 23 - "modelo_selecciones.py"
Cohesion: 0.17
Nodes (9): ajustar(), f(), matriz(), calidad_equipos(), cargar(), esperados(), fifa_antes(), goles() (+1 more)

### Community 24 - "descargar_selecciones.py"
Cohesion: 0.22
Nodes (10): lista(), main(), leer_o_pedir(), marcador(), pedir(), terminado(), ya_en_raw(), lista() (+2 more)

### Community 25 - "Ambos Marcan -- offshoot enfocado de futbol-pipeline"
Cohesion: 0.05
Nodes (42): Ajuste interno (29/09/2026): árboles de un nivel (NO CONFIRMADO, ver revisión abajo), Ambos Marcan -- offshoot enfocado de futbol-pipeline, Auditoría externa (29/09/2026): pruebas de los puntos aceptados, Bajas por lesión (29/09/2026): no entran, empeoran, Configuración oficial de ambos marcan (26/09/2026), Cuota como variable, con football-data (25/09/2026), Cuota de mercado como variable: imposible con el método estándar, y por qué (24/09/2026), Córners en el modelo de ambos marcan (25/09/2026) (+34 more)

### Community 26 - "generar.py"
Cohesion: 0.07
Nodes (44): 10/10/2026 — redes: plantillas de CLUBES (5 grandes ligas), `datos_clubes.py`, acierto(), _alternativas(), b64(), barra3(), color(), color_viejo(), deserved() (+36 more)

### Community 27 - "Bitácora del proyecto"
Cohesion: 0.05
Nodes (44): 05/10/2026, 05/10/2026 — redes: backup sin Claude, 05/10/2026 — redes: fuera "bookies" de las imágenes, 06/10/2026 — colores de 228 equipos, curados, 06/10/2026 — colores_redes: descarga robusta, 06/10/2026 — redes: 2yellow Index POR ROL (ataque, medio, defensa, portero), 06/10/2026 — redes: 2yellow XI con posiciones reales y filtro de nivel, 06/10/2026 — redes_api: no perder descargas por conflictos (+36 more)

### Community 28 - "afinar_ambos.py"
Cohesion: 0.18
Nodes (8): correr(), entrenar(), main(), nombre(), predecir(), evaluar_config(), main(), todas_las_combinaciones()

### Community 29 - "Pronósticos de selecciones (06/10/2026 17:58 UTC)"
Cohesion: 0.17
Nodes (11): Albania - San Marino (2026-10-06 18:45 UTC), Belarus - Finland (2026-10-06 18:45 UTC), Croatia - Spain (2026-10-06 18:45 UTC), Cuánto fiarse, England - Czech Republic (2026-10-06 18:45 UTC), Estonia - Iceland (2026-10-06 18:45 UTC), Luxembourg - Bulgaria (2026-10-06 18:45 UTC), Moldova - Slovakia (2026-10-06 18:45 UTC) (+3 more)

### Community 30 - "Notas para trabajar en este repositorio"
Cohesion: 0.05
Nodes (46): 2023/24 completa: mezclada, y xG por jugador solo desde abril de 2025 (26/09/2026), 2023/24: partidos y árbitro completos, alineaciones solo desde abril de 2024 (26/09/2026), 2024/25 en el histórico, y entrenar CON huecos (25/09/2026), Acierto (hit-rate) además de Brier, y barrido de las 256 combinaciones (24/09/2026), Ambos marcan mes a mes: reentrenar ayuda, adaptarse poco, y la apuesta se desinfla (26/09/2026), Antes de afirmar que algo NO existe, Antes de empujar código, Apostar a ambos marcan: primer resultado positivo en versión honesta (26/09/2026) (+38 more)

### Community 31 - "sondeo_live_odds.py"
Cohesion: 0.33
Nodes (10): aplanar(), buscar_en_juego(), desempaquetar(), en_juego(), huella(), main(), minuto_de(), nombre_de() (+2 more)

### Community 32 - "sondeo_odds.py"
Cohesion: 0.35
Nodes (7): aplanar(), desempaquetar(), elegir_partidos(), main(), pedir(), resumen(), titulo()

### Community 33 - "calendario_mes.py"
Cohesion: 0.21
Nodes (11): anclas_encontradas(), avisar_de_cobertura(), descubrir_ligas(), desempaquetar(), equipos_de(), main(), nombre_encaja(), partidos_de_liga() (+3 more)

### Community 34 - "datos_formatos.py"
Cohesion: 0.23
Nodes (10): 07/10/2026 — redes: perfil de delantero centro y Balón de Oro en dos listas, balon_oro_doble(), corto(), desempate(), filas(), indice(), posiciones(), puntuar() (+2 more)

### Community 35 - "datos_selecciones.py"
Cohesion: 0.10
Nodes (19): hexa(), kit(), dia(), elo_series(), eq(), leer(), lista_hoy(), partido() (+11 more)

### Community 36 - "ambos_marcan/scripts/evaluar_mercados.py"
Cohesion: 0.24
Nodes (7): brier(), cargar_cuotas_crudas(), evaluar_uno(), main(), mejor_peso(), mercado_por_partido(), probabilidad_binaria()

### Community 37 - "casas_descolgadas.py"
Cohesion: 0.36
Nodes (4): desmarginar(), familia_de(), main(), pedir()

### Community 38 - "La API de Highlightly, en lo que nos afecta"
Cohesion: 0.12
Nodes (15): `/box-score/{matchId}`: 37 estadísticas POR JUGADOR, Cada cuánto se refresca cada cosa, Cosas que no hay, Estados de partido (lista oficial), Forma de la respuesta de `/odds`, Inventario real (leído de la especificación, 20/09/2026), La API de Highlightly, en lo que nos afecta, Las cuotas de distintas casas NO son simultáneas (+7 more)

### Community 39 - "backfill_perfil_jugador.py"
Cohesion: 0.33
Nodes (7): abrir(), altura(), fecha(), jugadores_unicos(), main(), pedir(), ya_tengo()

### Community 40 - "censo_tarjetas.py"
Cohesion: 0.50
Nodes (6): aplanar_cuotas(), desempaquetar(), main(), pedir(), proximos_partidos(), titulo()

### Community 41 - "ambos_marcan/scripts/modelo_xgboost.py"
Cohesion: 0.39
Nodes (5): brier(), cargar(), entrenar(), main(), probabilidades()

### Community 42 - "comparar_entreno_con_huecos.py"
Cohesion: 0.60
Nodes (3): main(), predecir(), sig()

### Community 43 - "monitor_directo.py"
Cohesion: 0.26
Nodes (13): aplanar_cuotas(), desempaquetar(), elegir_seguidos(), prioridad(), en_juego(), escanear(), huella_cuotas(), liga_de() (+5 more)

### Community 44 - "descargar_partido.py"
Cohesion: 0.48
Nodes (5): estado(), lista(), main(), marcador(), pedir()

### Community 45 - "sin_empate.py"
Cohesion: 0.29
Nodes (5): ajustar_sin_empate(), derivado_goles(), main(), prueba(), sigmas()

### Community 46 - "Estado: mercado poco competido + value bets + herramienta interna"
Cohesion: 0.15
Nodes (12): Cómo se mide "poco competido", ¿El precio poco vigilado está MAL, o solo caro?, Estado: mercado poco competido + value bets + herramienta interna, La pista que murió, Las value bets, cruzadas con la vigilancia, Lo que decide, Lo que el modelo aprende de verdad, Lo que falta (actualizado 24/09/2026) (+4 more)

### Community 47 - "sys"
Cohesion: 0.07
Nodes (19): brier(), cargar_cuotas_crudas(), evaluar_uno(), main(), mejor_peso(), mercado_por_partido(), probabilidad_binaria(), evaluar() (+11 more)

### Community 48 - "re"
Cohesion: 0.26
Nodes (5): main(), norm(), etiqueta(), montar_video(), texto()

### Community 49 - "auditoria2_tabla_fuga.py"
Cohesion: 0.36
Nodes (4): main(), comp(), posiciones(), sig()

### Community 50 - "radiografia_ligas.py"
Cohesion: 0.39
Nodes (7): desempaquetar(), en_juego(), main(), minuto_de(), nombre_de(), pedir(), recoger()

### Community 51 - "UEFA Nations League, 2026-09-26 (hora de España)"
Cohesion: 0.17
Nodes (11): 15:00  Slovenia - Scotland  (Finished), 18:00  Bulgaria - Luxembourg  (Not started), 18:00  Faroe Islands - Kazakhstan  (Not started), 18:00  Iceland - Estonia  (Not started), 18:00  San Marino - Finland  (Not started), 20:45  Albania - Belarus  (Not started), 20:45  Czech Republic - Croatia  (Not started), 20:45  England - Spain  (Not started) (+3 more)

### Community 52 - "backfill_titulares_boxscore.py"
Cohesion: 0.43
Nodes (4): main(), once(), pedir(), ya_tengo()

### Community 53 - "backfill_historico.py"
Cohesion: 0.30
Nodes (8): columnas(), desempaquetar(), estadisticas_de(), goles(), main(), pedir(), terminado(), ya_guardados()

### Community 54 - "cuotas_football_data.py"
Cohesion: 0.36
Nodes (7): cargar_fd(), elegir(), main(), norm(), parecido(), previa(), sin_margen()

### Community 55 - "numpy"
Cohesion: 0.08
Nodes (24): evaluar(), prueba_hacia_delante(), ajustar(), X(), main(), probs(), c(), logit() (+16 more)

### Community 56 - "columnas_rasgo_default"
Cohesion: 0.33
Nodes (4): columnas_rasgo(), columnas_rasgo_default(), comprobar_sin_fuga(), grupos_rasgo()

### Community 57 - "Provider APIs - Setup Guides"
Cohesion: 0.18
Nodes (9): Environment variable, Environment variable, Get your API key, Get your API key, Mistral AI, Provider APIs - Setup Guides, Usage example, Usage example (+1 more)

### Community 58 - "Selecciones (Nations League y similares)"
Cohesion: 0.17
Nodes (11): Automático: el ciclo de la Nations League (desde el 26/09/2026), Cuánto fiarse, Fallos silenciosos ya encontrados (no repetir), Fuga de la tabla de clubes arreglada (29/09/2026): a selecciones no le afecta, Listas para el usuario (05/10/2026), Qué hace cada pieza, Receta manual para una jornada (antes del ciclo, o para partidos fuera de la Nations League), Resultado del 26/09 (para comparar cuando se jueguen) (+3 more)

### Community 59 - "cosechar_cuotas.py"
Cohesion: 0.53
Nodes (4): desempaquetar(), main(), pedir(), ya_tengo()

### Community 60 - "sondeo_frescura.py"
Cohesion: 0.40
Nodes (7): desempaquetar(), en_juego(), estado_de(), foto(), main(), minuto_de(), pedir()

### Community 61 - "Doble Oportunidad, Sin Empate y Más/Menos goles"
Cohesion: 0.20
Nodes (9): Antes de dar ningún número: comprobar que el resolutor no miente, Cogiendo la mejor cuota de entre todas las casas, Con la cuota de una casa cualquiera, Conclusión, Doble Oportunidad, Sin Empate y Más/Menos goles, Dónde viven estos mercados, Filtrar por "valor contra el consenso" lo empeora, Lo único con señal, y por qué tampoco sirve (+1 more)

### Community 62 - "sondeo_titulares_boxscore.py"
Cohesion: 0.47
Nodes (3): main(), pedir(), titulares()

### Community 63 - "NBA: qué mercado atacar y con qué variables (28/09/2026)"
Cohesion: 0.25
Nodes (7): Aviso importante, Coste de la descarga, ¿El precio está torcido? (medido antes de montar nada), Mercado elegido: totales (más/menos puntos del partido), NBA: qué mercado atacar y con qué variables (28/09/2026), Primera prueba: modelo solo con marcadores (`scripts/nba/totales_primera_prueba.py`), Variables que harían falta (y de dónde salen)

### Community 64 - "El sesgo favorito-marginado: existe, y no se puede cobrar"
Cohesion: 0.25
Nodes (7): Cómo se encontró, El hallazgo, El sesgo favorito-marginado: existe, y no se puede cobrar, La lectura, Lo que además lo haría inviable en la práctica, Por qué no se puede cobrar, Qué queda abierto

### Community 65 - "sondeo_faltas.py"
Cohesion: 0.46
Nodes (6): desempaquetar(), estado_de(), main(), minuto_de(), pedir(), volcar_estadisticas()

### Community 66 - "scripts/backfill_boxscore.py"
Cohesion: 0.39
Nodes (5): agregar_equipo(), desempaquetar(), main(), pedir(), ya_tengo()

### Community 67 - "backfill_xg_jugador.py"
Cohesion: 0.39
Nodes (5): desempaquetar(), estadisticas_de(), main(), pedir(), ya_tengo()

### Community 68 - "¿Hay arbitraje? Medido en la mejor condición posible, y no"
Cohesion: 0.29
Nodes (6): ¿Hay arbitraje? Medido en la mejor condición posible, y no, La prueba, en las mejores condiciones que tenemos, Por qué esto ya lo sabíamos, con más fuerza, Por qué tampoco funcionaría con datos perfectos, Qué es el arbitraje (surebet), Veredicto

### Community 69 - "Cierre del registro del descanso -- 2026-09-23 23:19 UTC"
Cohesion: 0.29
Nodes (6): Cierre del registro del descanso -- 2026-09-23 23:19 UTC, Las faltas del primer tiempo, Movimiento del precio, Partido a partido, Quién acierta más, Si se hubiera apostado

### Community 70 - "recalibrar_ambos.py"
Cohesion: 0.33
Nodes (5): logit(), main(), predicciones(), sigmas(), tabla()

### Community 71 - "¿Hay algún mercado donde el precio esté MAL, o solo caro?"
Cohesion: 0.29
Nodes (6): El resultado, El único hueco real, y por qué tampoco sirve, ¿Hay algún mercado donde el precio esté MAL, o solo caro?, La lección de método, Lo que esto cierra, Por qué esta es la pregunta

### Community 73 - "csv"
Cohesion: 0.26
Nodes (7): jugadores_unicos(), main(), pedir(), ya_tengo(), highlightly(), temporada_us(), understat()

### Community 74 - "backfill_lineups.py"
Cohesion: 0.43
Nodes (4): ids_titulares(), main(), pedir(), ya_tengo()

### Community 75 - "¿Se puede ganar dinero con esta API, GitHub y una IA?"
Cohesion: 0.29
Nodes (6): La prueba definitiva, Lo que sí hemos medido bien, Por qué, estructuralmente, Qué haría falta para que esto cambiara, ¿Se puede ganar dinero con esta API, GitHub y una IA?, Veredicto

### Community 76 - "Agenda del 2026-10-10"
Cohesion: 0.17
Nodes (11): 12:15-12:32 UTC  (1 partidos), 12:45-13:02 UTC  (1 partidos), 13:45-14:02 UTC  (1 partidos), 14:15-14:32 UTC  (5 partidos), 14:45-15:17 UTC  (5 partidos), 16:00-16:17 UTC  (1 partidos), 16:45-17:02 UTC  (1 partidos), 17:15-17:32 UTC  (3 partidos) (+3 more)

### Community 78 - "Inference Providers - Setup Guides"
Cohesion: 0.33
Nodes (5): Cerebras, Environment variable, Get your API key, Inference Providers - Setup Guides, Usage example

### Community 79 - "Free LLM API Setup"
Cohesion: 0.33
Nodes (6): Free LLM API Setup, Key Notes, Provider categories, Provider Selection, Quick Test Template, Workflow

### Community 80 - "La pista de la mezcla murió al crecer la muestra"
Cohesion: 0.33
Nodes (5): Dónde queda el proyecto, La pista de la mezcla murió al crecer la muestra, Lo que es, Lo que hay que retener, Lo que parecía

### Community 81 - "Rumanía Liga II y México Liga MX: auditadas, ninguna es la respuesta hoy"
Cohesion: 0.33
Nodes (5): El fallo de método que casi nos lleva por mal camino, México Liga MX: ni fantasma ni hallazgo, Rumanía Liga II: cerrada, Rumanía Liga II y México Liga MX: auditadas, ninguna es la respuesta hoy, Veredicto

### Community 82 - "Middling: cómo funciona y cuánto se podría ganar, medido"
Cohesion: 0.33
Nodes (5): Cuánto se podría ganar: medido con 2.004 partidos reales, La mecánica, Middling: cómo funciona y cuánto se podría ganar, medido, Por qué pierde, estructuralmente, Veredicto

### Community 83 - "Qué 8 casas abrir: 9,58 puntos de diferencia en cada apuesta"
Cohesion: 0.33
Nodes (5): El margen del 1X2, casa por casa, Lo que esto NO arregla, Qué 8 casas abrir: 9,58 puntos de diferencia en cada apuesta, Qué cambia esto, Y lo que NO se puede hacer

### Community 84 - "Backtest de valor -- 2026-09-20 19:37 UTC"
Cohesion: 0.40
Nodes (4): Backtest de valor -- 2026-09-20 19:37 UTC, Lo que decide, Por mercado (solo apuestas con más de 2% de valor), Por nivel de valor

### Community 85 - "pandas"
Cohesion: 0.08
Nodes (24): calcular_arbitro_ventana(), calcular_h2h_reciente(), calcular_impacto_jugador(), calcular_tabla_goles(), evaluar(), calcular_arbitro_ventana(), calcular_h2h_reciente(), calcular_impacto_jugador() (+16 more)

### Community 87 - "scripts/rasgos.py"
Cohesion: 0.07
Nodes (26): main(), main(), main(), predecir(), sig(), main(), sig(), main() (+18 more)

### Community 89 - "Sondeo: Nations League -- gol de equipo en la 1ª parte"
Cohesion: 0.40
Nodes (4): 195 mercados distintos vistos (20 partidos con /odds sondeado), Coincidencias con "medio tiempo/1ª parte" + "marcar/gol", Ligas encontradas por nombre, Sondeo: Nations League -- gol de equipo en la 1ª parte

### Community 90 - "Calendario -- próximos 30 días"
Cohesion: 0.50
Nodes (3): Calendario -- próximos 30 días, Carga por día, Partidos por día

### Community 91 - "Cloudflare Workers AI"
Cohesion: 0.50
Nodes (4): Cloudflare Workers AI, Environment variable, Get your API key, Usage example

### Community 92 - "GitHub Models"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, GitHub Models, Usage example

### Community 93 - "Groq"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, Groq, Usage example

### Community 94 - "LLM7.io"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, LLM7.io, Usage example

### Community 95 - "Kluster AI"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, Kluster AI, Usage example

### Community 96 - "OpenRouter"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, OpenRouter, Usage example

### Community 97 - "Hugging Face"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, Hugging Face, Usage example

### Community 98 - "NVIDIA NIM"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, NVIDIA NIM, Usage example

### Community 99 - "Cohere"
Cohesion: 0.50
Nodes (4): Cohere, Environment variable, Get your API key, Usage example

### Community 100 - "Google Gemini"
Cohesion: 0.50
Nodes (4): Environment variable, Get your API key, Google Gemini, Usage example

### Community 101 - "El modelo"
Cohesion: 0.50
Nodes (3): Cómo leer esto, El modelo, Lo que este fichero NO dice

### Community 103 - "ambos_marcan_hoy.py"
Cohesion: 0.16
Nodes (8): descargar(), evaluar(), juez(), lista(), partidos_del_dia(), pedir(), precio(), registrar()

### Community 104 - "Sondeo: temporadas anteriores a la 2025/26"
Cohesion: 0.50
Nodes (3): Partidos por liga y temporada (/matches, hasta 100 por página), Profundidad de datos: un partido terminado de La Liga por temporada, Sondeo: temporadas anteriores a la 2025/26

### Community 123 - "ambos_hay_partido.py"
Cohesion: 0.60
Nodes (4): fecha(), main(), partidos(), pendientes_previa()

### Community 124 - "backfill_arbitro_clima.py"
Cohesion: 0.43
Nodes (4): main(), parsear_temp(), pedir(), ya_tengo()

### Community 127 - "experimentos_cuota_feature.py"
Cohesion: 0.67
Nodes (3): entrenar_ligero(), evaluar_config(), evaluar_ligero()

### Community 129 - "os"
Cohesion: 0.12
Nodes (6): desempaquetar(), main(), minuto_de_evento(), pedir(), reparto_de_tarjetas(), main()

### Community 130 - "sondeo_temporadas_antiguas.py"
Cohesion: 0.53
Nodes (4): lista(), main(), pedir(), terminado()

### Community 131 - "prueba_post_partido.py"
Cohesion: 0.43
Nodes (4): main(), partido(), pasada(), stats()

## Knowledge Gaps
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `analizar()` connect `Notas para trabajar en este repositorio` to `numpy`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Should `descanso_en_vivo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07467532467532467 - nodes in this community are weakly interconnected._
- **Should `apuesta_ambos_marcan.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12923076923076923 - nodes in this community are weakly interconnected._
- **Should `datos_clubes.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `requests` be split into smaller, more focused modules?**
  _Cohesion score 0.10344827586206896 - nodes in this community are weakly interconnected._
- **Should `datos_rankings.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08826945412311266 - nodes in this community are weakly interconnected._
- **Should `datetime` be split into smaller, more focused modules?**
  _Cohesion score 0.06174863387978142 - nodes in this community are weakly interconnected._