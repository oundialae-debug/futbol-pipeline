# Graph Report - futbol-pipeline  (2026-10-05)

## Corpus Check
- 198 files · ~276,264 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 1449 nodes · 3222 edges · 122 communities (98 shown, 24 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9f496b83`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- csv
- json
- descanso_en_vivo.py
- diagnostico_directo.py
- contraste_directo.py
- scripts/evaluar_mercados.py
- requests
- os
- datetime
- modelo_selecciones.py
- ambos_marcan_hoy.py
- scripts/rasgos.py
- sys
- ambos_marcan/scripts/rasgos.py
- boletin.py
- numpy
- aporta_algo.py
- diagnostico_api.py
- sondeo_frescura.py
- ambos_marcan/scripts/evaluar_mercados.py
- apuesta_ambos_marcan.py
- ambos_marcan/scripts/modelo_xgboost.py
- backtest_valor.py
- monitor_directo.py
- nations_league_hoy.py
- Ambos Marcan -- offshoot enfocado de futbol-pipeline
- forma_clubes.py
- scripts/modelo_xgboost.py
- afinar_ambos.py
- Pronósticos de selecciones (05/10/2026 07:41 UTC)
- Notas para trabajar en este repositorio
- auditoria2_tabla_fuga.py
- experimentos_seis_ideas.py
- calendario_mes.py
- radiografia_ligas.py
- recalibrar_ambos.py
- pandas
- time
- La API de Highlightly, en lo que nos afecta
- casas_descolgadas.py
- censo_tarjetas.py
- sondeo_faltas.py
- casas_contra_cierre.py
- cerrar_descanso.py
- descargar_partido.py
- Estado: mercado poco competido + value bets + herramienta interna
- f
- sondeo_temporadas_antiguas.py
- collections
- calcular_calidad_plantilla
- UEFA Nations League, 2026-09-26 (hora de España)
- backfill_titulares_boxscore.py
- backfill_historico.py
- experimentos_combinaciones.py
- sondeo_live_odds.py
- Provider APIs - Setup Guides
- Selecciones (Nations League y similares)
- backfill_h2h_profundo.py
- sondeo_odds.py
- Doble Oportunidad, Sin Empate y Más/Menos goles
- censo_margenes.py
- NBA: qué mercado atacar y con qué variables (28/09/2026)
- El sesgo favorito-marginado: existe, y no se puede cobrar
- sondeo_titulares_boxscore.py
- scripts/backfill_boxscore.py
- backfill_xg_jugador.py
- ¿Hay arbitraje? Medido en la mejor condición posible, y no
- Cierre del registro del descanso -- 2026-09-23 23:19 UTC
- buscar_ligas.py
- ¿Hay algún mercado donde el precio esté MAL, o solo caro?
- backfill_arbitro_clima.py
- backfill_jugador_stats.py
- backfill_lineups.py
- ¿Se puede ganar dinero con esta API, GitHub y una IA?
- Agenda del 2026-09-26
- futbol-pipeline
- Inference Providers - Setup Guides
- Free LLM API Setup
- La pista de la mezcla murió al crecer la muestra
- Rumanía Liga II y México Liga MX: auditadas, ninguna es la respuesta hoy
- Middling: cómo funciona y cuánto se podría ganar, medido
- Qué 8 casas abrir: 9,58 puntos de diferencia en cada apuesta
- Backtest de valor -- 2026-09-20 19:37 UTC
- experimentos_rasgos.py
- sondeo_boxscore.py
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
- experimento_temporada_extra.py
- experimentos_cuota_feature.py
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

## God Nodes (most connected - your core abstractions)
1. `Ambos Marcan -- offshoot enfocado de futbol-pipeline` - 38 edges
2. `construir()` - 36 edges
3. `Notas para trabajar en este repositorio` - 36 edges
4. `Pronósticos de selecciones (05/10/2026 07:41 UTC)` - 20 edges
5. `columnas_rasgo_default()` - 19 edges
6. `construir()` - 18 edges
7. `f()` - 17 edges
8. `main()` - 16 edges
9. `analizar()` - 15 edges
10. `main()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Crons en pausa (26/09/2026)` --references--> `calendario()`  [INFERRED]
  docs/notas_proyecto.md → modelos/selecciones/nations_league.py
- `Segunda auditoría externa (29/09/2026): reproducida con XGBoost real` --references--> `preparar()`  [INFERRED]
  modelos/ambos_marcan/CLAUDE.md → scripts/modelo_ambos_marcan.py
- `Comprobaciones hechas en la revisión de código (sin cambios)` --references--> `pronosticar()`  [INFERRED]
  BITACORA.md → scripts/ambos_marcan_hoy.py
- `Auditoría externa (29/09/2026): pruebas de los puntos aceptados` --references--> `ajustar()`  [INFERRED]
  modelos/ambos_marcan/CLAUDE.md → scripts/btts_implicito.py
- `MODELO OFICIAL desde el 28/09/2026 (tarde): + 2022/23, - xG del equipo` --references--> `columnas()`  [INFERRED]
  modelos/ambos_marcan/CLAUDE.md → scripts/modelo_ambos_marcan.py

## Import Cycles
- None detected.

## Communities (122 total, 24 thin omitted)

### Community 0 - "csv"
Cohesion: 0.52
Nodes (4): desempaquetar(), main(), pedir(), ya_tengo()

### Community 1 - "json"
Cohesion: 0.06
Nodes (41): lista(), main(), leer_o_pedir(), marcador(), pedir(), terminado(), ya_en_raw(), main() (+33 more)

### Community 2 - "descanso_en_vivo.py"
Cohesion: 0.07
Nodes (33): analizar(), aplanar_cuotas(), apuntar_consumo(), buscar_en_juego(), consumo_de_hoy(), desempaquetar(), en_juego(), es_descanso() (+25 more)

### Community 3 - "diagnostico_directo.py"
Cohesion: 0.25
Nodes (13): aplanar_cuotas(), buscar_en_vivo(), describir(), descubrir_ligas(), desempaquetar(), esta_en_juego(), main(), minuto_de() (+5 more)

### Community 4 - "contraste_directo.py"
Cohesion: 0.11
Nodes (18): main(), norm(), buscar(), cargar_referencia(), desempaquetar(), en_juego(), main(), minuto_de() (+10 more)

### Community 5 - "scripts/evaluar_mercados.py"
Cohesion: 0.17
Nodes (10): main(), predecir(), sig(), brier(), cargar_cuotas_crudas(), evaluar_uno(), main(), mejor_peso() (+2 more)

### Community 6 - "requests"
Cohesion: 0.15
Nodes (8): desempaquetar(), main(), pedir(), main(), main(), main(), main(), pedir()

### Community 7 - "os"
Cohesion: 0.11
Nodes (6): desempaquetar(), main(), minuto_de_evento(), pedir(), reparto_de_tarjetas(), main()

### Community 8 - "datetime"
Cohesion: 0.06
Nodes (35): cargar(), franjas(), main(), desempaquetar(), esquema(), main(), pedir(), probar() (+27 more)

### Community 9 - "modelo_selecciones.py"
Cohesion: 0.08
Nodes (19): ajustar(), brier(), elo_previo(), fifa_antes(), main(), preparar(), prueba(), xi_club() (+11 more)

### Community 10 - "ambos_marcan_hoy.py"
Cohesion: 0.06
Nodes (33): 05/10/2026, 29/09/2026, Antes del 29/09/2026 (resumen; el detalle está en los CLAUDE.md), Bitácora del proyecto, Cambios de código y ficheros, Cambios de código y ficheros, Comprobaciones hechas en la revisión de código (sin cambios), Errores en los datos encontrados (+25 more)

### Community 11 - "scripts/rasgos.py"
Cohesion: 0.07
Nodes (24): main(), main(), main(), predecir(), sig(), main(), a_largo(), calcular_arbitro() (+16 more)

### Community 12 - "sys"
Cohesion: 0.09
Nodes (20): grupo(), main(), main(), precio_directo(), sin_margen(), comparar(), main(), main() (+12 more)

### Community 13 - "ambos_marcan/scripts/rasgos.py"
Cohesion: 0.10
Nodes (14): a_largo(), calcular_arbitro(), calcular_btts(), calcular_elo(), calcular_h2h(), calcular_rotacion(), calcular_tabla(), columnas_rasgo() (+6 more)

### Community 14 - "boletin.py"
Cohesion: 0.11
Nodes (14): consenso_de(), escribir(), linea_boletin(), main(), mejor_precio_mio(), modelo_validado(), Apuesta, comparar_sistemas() (+6 more)

### Community 15 - "numpy"
Cohesion: 0.10
Nodes (18): logit(), main(), sig(), elo(), main(), sig(), brier(), ll() (+10 more)

### Community 16 - "aporta_algo.py"
Cohesion: 0.14
Nodes (9): brier(), cargar_cuotas_1x2(), main(), mejor_peso(), probabilidades_de_mercado(), main(), probabilidad_mercado(), cuotas_por_partido() (+1 more)

### Community 17 - "diagnostico_api.py"
Cohesion: 0.28
Nodes (11): aplanar_cuotas(), arbitro_previo(), cuotas(), describir(), estados_y_en_vivo(), eventos_parciales(), limites_del_plan(), main() (+3 more)

### Community 18 - "sondeo_frescura.py"
Cohesion: 0.40
Nodes (7): desempaquetar(), en_juego(), estado_de(), foto(), main(), minuto_de(), pedir()

### Community 19 - "ambos_marcan/scripts/evaluar_mercados.py"
Cohesion: 0.24
Nodes (7): brier(), cargar_cuotas_crudas(), evaluar_uno(), main(), mejor_peso(), mercado_por_partido(), probabilidad_binaria()

### Community 20 - "apuesta_ambos_marcan.py"
Cohesion: 0.16
Nodes (9): main(), rasgos_hoy(), main(), rasgos_mercado(), resumen(), brier(), logit(), main() (+1 more)

### Community 21 - "ambos_marcan/scripts/modelo_xgboost.py"
Cohesion: 0.39
Nodes (5): brier(), cargar(), entrenar(), main(), probabilidades()

### Community 22 - "backtest_valor.py"
Cohesion: 0.20
Nodes (9): desempaquetar(), desmarginar(), familia_de(), handicap_local(), hechos_del_partido(), main(), pedir(), resolver() (+1 more)

### Community 23 - "monitor_directo.py"
Cohesion: 0.26
Nodes (13): aplanar_cuotas(), desempaquetar(), elegir_seguidos(), prioridad(), en_juego(), escanear(), huella_cuotas(), liga_de() (+5 more)

### Community 24 - "nations_league_hoy.py"
Cohesion: 0.47
Nodes (3): lista(), main(), pedir()

### Community 25 - "Ambos Marcan -- offshoot enfocado de futbol-pipeline"
Cohesion: 0.05
Nodes (41): Ajuste interno (29/09/2026): árboles de un nivel (NO CONFIRMADO, ver revisión abajo), Ambos Marcan -- offshoot enfocado de futbol-pipeline, Bajas por lesión (29/09/2026): no entran, empeoran, Configuración oficial de ambos marcan (26/09/2026), Cuota como variable, con football-data (25/09/2026), Cuota de mercado como variable: imposible con el método estándar, y por qué (24/09/2026), Córners en el modelo de ambos marcan (25/09/2026), ¿Debe pesar más la liga? (29/09/2026): no (+33 more)

### Community 26 - "forma_clubes.py"
Cohesion: 0.60
Nodes (3): lista(), main(), pedir()

### Community 27 - "scripts/modelo_xgboost.py"
Cohesion: 0.19
Nodes (6): brier(), cargar(), entrenar(), main(), partir(), probabilidades()

### Community 28 - "afinar_ambos.py"
Cohesion: 0.18
Nodes (8): correr(), entrenar(), main(), nombre(), predecir(), evaluar_config(), main(), todas_las_combinaciones()

### Community 29 - "Pronósticos de selecciones (05/10/2026 07:41 UTC)"
Cohesion: 0.10
Nodes (20): Albania - San Marino (2026-10-06 18:45 UTC), Belarus - Finland (2026-10-06 18:45 UTC), Bosnia & Herzegovina - Poland (2026-10-05 18:45 UTC), Croatia - Spain (2026-10-06 18:45 UTC), Cuánto fiarse, Cyprus - Latvia (2026-10-05 16:00 UTC), England - Czech Republic (2026-10-06 18:45 UTC), Estonia - Iceland (2026-10-06 18:45 UTC) (+12 more)

### Community 30 - "Notas para trabajar en este repositorio"
Cohesion: 0.05
Nodes (46): 2023/24 completa: mezclada, y xG por jugador solo desde abril de 2025 (26/09/2026), 2023/24: partidos y árbitro completos, alineaciones solo desde abril de 2024 (26/09/2026), 2024/25 en el histórico, y entrenar CON huecos (25/09/2026), Acierto (hit-rate) además de Brier, y barrido de las 256 combinaciones (24/09/2026), Ambos marcan mes a mes: reentrenar ayuda, adaptarse poco, y la apuesta se desinfla (26/09/2026), Antes de afirmar que algo NO existe, Antes de empujar código, Apostar a ambos marcan: primer resultado positivo en versión honesta (26/09/2026) (+38 more)

### Community 31 - "auditoria2_tabla_fuga.py"
Cohesion: 0.36
Nodes (4): main(), comp(), posiciones(), sig()

### Community 32 - "experimentos_seis_ideas.py"
Cohesion: 0.18
Nodes (8): calcular_h2h_reciente(), calcular_arbitro_ventana(), calcular_h2h_reciente(), calcular_impacto_jugador(), calcular_tabla_goles(), evaluar(), calcular_h2h_profundo(), _clave_par()

### Community 33 - "calendario_mes.py"
Cohesion: 0.21
Nodes (11): anclas_encontradas(), avisar_de_cobertura(), descubrir_ligas(), desempaquetar(), equipos_de(), main(), nombre_encaja(), partidos_de_liga() (+3 more)

### Community 34 - "radiografia_ligas.py"
Cohesion: 0.39
Nodes (7): desempaquetar(), en_juego(), main(), minuto_de(), nombre_de(), pedir(), recoger()

### Community 35 - "recalibrar_ambos.py"
Cohesion: 0.33
Nodes (5): logit(), main(), predicciones(), sigmas(), tabla()

### Community 36 - "pandas"
Cohesion: 0.11
Nodes (16): evaluar(), main(), lesiones(), main(), rasgos(), valor_antes(), valores(), main() (+8 more)

### Community 37 - "time"
Cohesion: 0.17
Nodes (9): main(), obtener_detalle_partido(), obtener_partidos_recientes(), es_derbi(), main(), obtener_detalle_completo(), obtener_pagina_partidos(), main() (+1 more)

### Community 38 - "La API de Highlightly, en lo que nos afecta"
Cohesion: 0.12
Nodes (15): `/box-score/{matchId}`: 37 estadísticas POR JUGADOR, Cada cuánto se refresca cada cosa, Cosas que no hay, Estados de partido (lista oficial), Forma de la respuesta de `/odds`, Inventario real (leído de la especificación, 20/09/2026), La API de Highlightly, en lo que nos afecta, Las cuotas de distintas casas NO son simultáneas (+7 more)

### Community 39 - "casas_descolgadas.py"
Cohesion: 0.36
Nodes (4): desmarginar(), familia_de(), main(), pedir()

### Community 40 - "censo_tarjetas.py"
Cohesion: 0.50
Nodes (6): aplanar_cuotas(), desempaquetar(), main(), pedir(), proximos_partidos(), titulo()

### Community 41 - "sondeo_faltas.py"
Cohesion: 0.46
Nodes (6): desempaquetar(), estado_de(), main(), minuto_de(), pedir(), volcar_estadisticas()

### Community 42 - "casas_contra_cierre.py"
Cohesion: 0.38
Nodes (3): analizar(), cuando_se_cosecha(), main()

### Community 43 - "cerrar_descanso.py"
Cohesion: 0.43
Nodes (4): brier(), main(), pedir(), resultado_final()

### Community 45 - "descargar_partido.py"
Cohesion: 0.48
Nodes (5): estado(), lista(), main(), marcador(), pedir()

### Community 46 - "Estado: mercado poco competido + value bets + herramienta interna"
Cohesion: 0.15
Nodes (12): Cómo se mide "poco competido", ¿El precio poco vigilado está MAL, o solo caro?, Estado: mercado poco competido + value bets + herramienta interna, La pista que murió, Las value bets, cruzadas con la vigilancia, Lo que decide, Lo que el modelo aprende de verdad, Lo que falta (actualizado 24/09/2026) (+4 more)

### Community 47 - "f"
Cohesion: 0.27
Nodes (8): ajustar(), f(), matriz(), esperados(), fecha(), main(), partidos(), pendientes_previa()

### Community 48 - "sondeo_temporadas_antiguas.py"
Cohesion: 0.53
Nodes (4): lista(), main(), pedir(), terminado()

### Community 49 - "collections"
Cohesion: 0.17
Nodes (7): main(), pedir(), main(), pedir(), desempaquetar(), main(), pedir()

### Community 51 - "UEFA Nations League, 2026-09-26 (hora de España)"
Cohesion: 0.17
Nodes (11): 15:00  Slovenia - Scotland  (Finished), 18:00  Bulgaria - Luxembourg  (Not started), 18:00  Faroe Islands - Kazakhstan  (Not started), 18:00  Iceland - Estonia  (Not started), 18:00  San Marino - Finland  (Not started), 20:45  Albania - Belarus  (Not started), 20:45  Czech Republic - Croatia  (Not started), 20:45  England - Spain  (Not started) (+3 more)

### Community 52 - "backfill_titulares_boxscore.py"
Cohesion: 0.43
Nodes (4): main(), once(), pedir(), ya_tengo()

### Community 53 - "backfill_historico.py"
Cohesion: 0.30
Nodes (8): columnas(), desempaquetar(), estadisticas_de(), goles(), main(), pedir(), terminado(), ya_guardados()

### Community 54 - "experimentos_combinaciones.py"
Cohesion: 0.33
Nodes (4): calcular_arbitro_ventana(), calcular_impacto_jugador(), calcular_tabla_goles(), evaluar()

### Community 56 - "sondeo_live_odds.py"
Cohesion: 0.33
Nodes (10): aplanar(), buscar_en_juego(), desempaquetar(), en_juego(), huella(), main(), minuto_de(), nombre_de() (+2 more)

### Community 57 - "Provider APIs - Setup Guides"
Cohesion: 0.18
Nodes (9): Environment variable, Environment variable, Get your API key, Get your API key, Mistral AI, Provider APIs - Setup Guides, Usage example, Usage example (+1 more)

### Community 58 - "Selecciones (Nations League y similares)"
Cohesion: 0.18
Nodes (10): Automático: el ciclo de la Nations League (desde el 26/09/2026), Cuánto fiarse, Fallos silenciosos ya encontrados (no repetir), Fuga de la tabla de clubes arreglada (29/09/2026): a selecciones no le afecta, Qué hace cada pieza, Receta manual para una jornada (antes del ciclo, o para partidos fuera de la Nations League), Resultado del 26/09 (para comparar cuando se jueguen), Selecciones (Nations League y similares) (+2 more)

### Community 59 - "backfill_h2h_profundo.py"
Cohesion: 0.53
Nodes (4): clave_par(), main(), pedir(), ya_tengo()

### Community 60 - "sondeo_odds.py"
Cohesion: 0.35
Nodes (7): aplanar(), desempaquetar(), elegir_partidos(), main(), pedir(), resumen(), titulo()

### Community 61 - "Doble Oportunidad, Sin Empate y Más/Menos goles"
Cohesion: 0.20
Nodes (9): Antes de dar ningún número: comprobar que el resolutor no miente, Cogiendo la mejor cuota de entre todas las casas, Con la cuota de una casa cualquiera, Conclusión, Doble Oportunidad, Sin Empate y Más/Menos goles, Dónde viven estos mercados, Filtrar por "valor contra el consenso" lo empeora, Lo único con señal, y por qué tampoco sirve (+1 more)

### Community 62 - "censo_margenes.py"
Cohesion: 0.47
Nodes (3): familia_de(), main(), pedir()

### Community 63 - "NBA: qué mercado atacar y con qué variables (28/09/2026)"
Cohesion: 0.25
Nodes (7): Aviso importante, Coste de la descarga, ¿El precio está torcido? (medido antes de montar nada), Mercado elegido: totales (más/menos puntos del partido), NBA: qué mercado atacar y con qué variables (28/09/2026), Primera prueba: modelo solo con marcadores (`scripts/nba/totales_primera_prueba.py`), Variables que harían falta (y de dónde salen)

### Community 64 - "El sesgo favorito-marginado: existe, y no se puede cobrar"
Cohesion: 0.25
Nodes (7): Cómo se encontró, El hallazgo, El sesgo favorito-marginado: existe, y no se puede cobrar, La lectura, Lo que además lo haría inviable en la práctica, Por qué no se puede cobrar, Qué queda abierto

### Community 65 - "sondeo_titulares_boxscore.py"
Cohesion: 0.47
Nodes (3): main(), pedir(), titulares()

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

### Community 70 - "buscar_ligas.py"
Cohesion: 0.60
Nodes (3): desempaquetar(), main(), pedir()

### Community 71 - "¿Hay algún mercado donde el precio esté MAL, o solo caro?"
Cohesion: 0.29
Nodes (6): El resultado, El único hueco real, y por qué tampoco sirve, ¿Hay algún mercado donde el precio esté MAL, o solo caro?, La lección de método, Lo que esto cierra, Por qué esta es la pregunta

### Community 72 - "backfill_arbitro_clima.py"
Cohesion: 0.43
Nodes (4): main(), parsear_temp(), pedir(), ya_tengo()

### Community 73 - "backfill_jugador_stats.py"
Cohesion: 0.43
Nodes (4): jugadores_unicos(), main(), pedir(), ya_tengo()

### Community 74 - "backfill_lineups.py"
Cohesion: 0.43
Nodes (4): ids_titulares(), main(), pedir(), ya_tengo()

### Community 75 - "¿Se puede ganar dinero con esta API, GitHub y una IA?"
Cohesion: 0.29
Nodes (6): La prueba definitiva, Lo que sí hemos medido bien, Por qué, estructuralmente, Qué haría falta para que esto cambiara, ¿Se puede ganar dinero con esta API, GitHub y una IA?, Veredicto

### Community 76 - "Agenda del 2026-09-26"
Cohesion: 0.33
Nodes (5): 12:45-13:02 UTC  (1 partidos), 15:00-15:17 UTC  (1 partidos), 17:15-17:32 UTC  (2 partidos), Agenda del 2026-09-26, Para el comparador

### Community 77 - "futbol-pipeline"
Cohesion: 0.33
Nodes (5): APIs gratuitas, futbol-pipeline, Grafo de conocimiento (graphify), Mapa, Notas compartidas

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

### Community 88 - "sondeo_boxscore.py"
Cohesion: 0.60
Nodes (3): desempaquetar(), main(), pedir()

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

### Community 103 - "experimentos_cuota_feature.py"
Cohesion: 0.67
Nodes (3): entrenar_ligero(), evaluar_config(), evaluar_ligero()

### Community 104 - "Sondeo: temporadas anteriores a la 2025/26"
Cohesion: 0.50
Nodes (3): Partidos por liga y temporada (/matches, hasta 100 por página), Profundidad de datos: un partido terminado de La Liga por temporada, Sondeo: temporadas anteriores a la 2025/26

## Knowledge Gaps
- **266 isolated node(s):** `Provider categories`, `Workflow`, `Quick Test Template`, `Key Notes`, `Get your API key` (+261 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 632 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ambos Marcan -- offshoot enfocado de futbol-pipeline` connect `Ambos Marcan -- offshoot enfocado de futbol-pipeline` to `ambos_marcan_hoy.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **What connects `Provider categories`, `Workflow`, `Quick Test Template` to the rest of the system?**
  _266 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `json` be split into smaller, more focused modules?**
  _Cohesion score 0.056314699792960665 - nodes in this community are weakly interconnected._
- **Why does `calendario()` connect `json` to `pandas`, `Notas para trabajar en este repositorio`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Should `descanso_en_vivo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07467532467532467 - nodes in this community are weakly interconnected._
- **Should `contraste_directo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10967741935483871 - nodes in this community are weakly interconnected._
- **Should `os` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._