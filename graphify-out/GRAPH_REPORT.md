# Graph Report - futbol-pipeline  (2026-10-05)

## Corpus Check
- 254 files · ~275,099 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 1064 nodes · 2869 edges · 56 communities (52 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Backfills del histórico
- Selecciones y Nations League
- Descanso en vivo
- Sondeos de cuotas en directo
- Onces de prensa y calendario
- Modelo XGBoost y barridos
- Censos y sondeos de la API
- Separar fútbol y precio
- Pipeline diario
- Modelo de selecciones
- Registro en papel de ambos marcan
- Rasgos y cuota como variable
- Modelo oficial de ambos marcan
- Rasgos (copia de ambos marcan)
- Boletín y gestión de banca
- Experimentos de ambos marcan (copia)
- Mezcla modelo y mercado
- Diagnóstico de la API
- Censo de estadísticas
- Evaluación de mercados (copia)
- Apuesta y walk-forward
- XGBoost (copia de ambos marcan)
- Backtest de valor
- Monitor en directo
- Descarga de selecciones
- Actualización de datos
- Forma de clubes
- Precio implícito y directo
- Afinado de ambos marcan
- Evaluación de mercados
- Ligas candidatas
- Auditoría de fuga de tabla
- Perfil de jugadores
- Experimentos de onces
- Radiografía de ligas
- Recalibración
- Experimento de lesiones
- Backfill histórico completo
- Backfill por liga
- Casas descolgadas
- Censo de tarjetas
- Sondeo de faltas
- Casas frente al cierre
- Cierre del descanso
- Agenda de hoy
- Cosecha de cuotas
- Experimento edad y valor
- Sondeo de temporadas
- Sondeo de titulares
- Calidad de plantilla (copia)
- Censo de ligas blandas
- Entreno con huecos
- Calidad de plantilla
- Sondeo Nations League

## God Nodes (most connected - your core abstractions)
1. `construir()` - 36 edges
2. `columnas_rasgo_default()` - 19 edges
3. `construir()` - 18 edges
4. `f()` - 17 edges
5. `main()` - 16 edges
6. `analizar()` - 15 edges
7. `main()` - 13 edges
8. `rasgos_mercado()` - 13 edges
9. `cuotas()` - 13 edges
10. `main()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `evaluar()` --indirect_call--> `cuotas()`  [INFERRED]
  modelos/ambos_marcan/scripts/experimentos_combinaciones.py → scripts/diagnostico_api.py
- `evaluar()` --indirect_call--> `cuotas()`  [INFERRED]
  modelos/ambos_marcan/scripts/experimentos_poisson_btts.py → scripts/diagnostico_api.py
- `evaluar()` --indirect_call--> `cuotas()`  [INFERRED]
  modelos/ambos_marcan/scripts/experimentos_seis_ideas.py → scripts/diagnostico_api.py
- `ya_tengo()` --indirect_call--> `f()`  [INFERRED]
  scripts/cosechar_cuotas.py → modelos/selecciones/modelo_selecciones.py
- `ajustar_pesos()` --indirect_call--> `f()`  [INFERRED]
  scripts/pipeline_diario.py → modelos/selecciones/modelo_selecciones.py

## Import Cycles
- None detected.

## Communities (56 total, 4 thin omitted)

### Community 0 - "Backfills del histórico"
Cohesion: 0.05
Nodes (46): ajustar(), f(), matriz(), esperados(), fecha(), main(), partidos(), pendientes_previa() (+38 more)

### Community 1 - "Selecciones y Nations League"
Cohesion: 0.07
Nodes (35): main(), resultados(), aplanar(), calendario(), clave(), detalles(), historial(), lista() (+27 more)

### Community 2 - "Descanso en vivo"
Cohesion: 0.07
Nodes (33): analizar(), aplanar_cuotas(), apuntar_consumo(), buscar_en_juego(), consumo_de_hoy(), desempaquetar(), en_juego(), es_descanso() (+25 more)

### Community 3 - "Sondeos de cuotas en directo"
Cohesion: 0.08
Nodes (32): main(), pedir(), aplanar_cuotas(), buscar_en_vivo(), describir(), descubrir_ligas(), desempaquetar(), esta_en_juego() (+24 more)

### Community 4 - "Onces de prensa y calendario"
Cohesion: 0.07
Nodes (29): main(), norm(), anclas_encontradas(), avisar_de_cobertura(), descubrir_ligas(), desempaquetar(), equipos_de(), main() (+21 more)

### Community 5 - "Modelo XGBoost y barridos"
Cohesion: 0.09
Nodes (15): evaluar_config(), main(), main(), sig(), configuraciones(), main(), brier(), cargar() (+7 more)

### Community 6 - "Censos y sondeos de la API"
Cohesion: 0.08
Nodes (12): desempaquetar(), main(), pedir(), familia_de(), main(), pedir(), main(), main() (+4 more)

### Community 7 - "Separar fútbol y precio"
Cohesion: 0.10
Nodes (19): main(), rasgos_hoy(), logit(), main(), sig(), elo(), main(), sig() (+11 more)

### Community 8 - "Pipeline diario"
Cohesion: 0.11
Nodes (21): actualizar_historico(), ajustar_pesos(), calcular_calibracion(), cargar_pesos(), _detalle_partido(), _entradas_de(), _es_refinado(), generar_informe() (+13 more)

### Community 9 - "Modelo de selecciones"
Cohesion: 0.08
Nodes (19): ajustar(), brier(), elo_previo(), fifa_antes(), main(), preparar(), prueba(), xi_club() (+11 more)

### Community 10 - "Registro en papel de ambos marcan"
Cohesion: 0.10
Nodes (18): X(), descargar(), evaluar(), juez(), lista(), partidos_del_dia(), pedir(), precio() (+10 more)

### Community 11 - "Rasgos y cuota como variable"
Cohesion: 0.10
Nodes (15): main(), main(), main(), predecir(), sig(), main(), a_largo(), calcular_arbitro() (+7 more)

### Community 12 - "Modelo oficial de ambos marcan"
Cohesion: 0.09
Nodes (15): grupo(), main(), comparar(), main(), main(), preparar(), main(), rasgos() (+7 more)

### Community 13 - "Rasgos (copia de ambos marcan)"
Cohesion: 0.10
Nodes (15): a_largo(), calcular_arbitro(), calcular_btts(), calcular_elo(), calcular_h2h(), calcular_h2h_profundo(), calcular_rotacion(), calcular_tabla() (+7 more)

### Community 14 - "Boletín y gestión de banca"
Cohesion: 0.11
Nodes (14): consenso_de(), escribir(), linea_boletin(), main(), mejor_precio_mio(), modelo_validado(), Apuesta, comparar_sistemas() (+6 more)

### Community 15 - "Experimentos de ambos marcan (copia)"
Cohesion: 0.16
Nodes (13): calcular_arbitro_ventana(), calcular_h2h_reciente(), calcular_impacto_jugador(), calcular_tabla_goles(), evaluar(), evaluar(), calcular_arbitro_ventana(), calcular_h2h_reciente() (+5 more)

### Community 16 - "Mezcla modelo y mercado"
Cohesion: 0.14
Nodes (9): brier(), cargar_cuotas_1x2(), main(), mejor_peso(), probabilidades_de_mercado(), main(), probabilidad_mercado(), cuotas_por_partido() (+1 more)

### Community 17 - "Diagnóstico de la API"
Cohesion: 0.20
Nodes (15): aplanar_cuotas(), arbitro_previo(), cuotas(), describir(), estados_y_en_vivo(), eventos_parciales(), limites_del_plan(), main() (+7 more)

### Community 18 - "Censo de estadísticas"
Cohesion: 0.19
Nodes (13): cuenta_jugadores(), desempaquetar(), estado_de(), main(), partidos_de(), pedir(), desempaquetar(), en_juego() (+5 more)

### Community 19 - "Evaluación de mercados (copia)"
Cohesion: 0.18
Nodes (10): brier(), cargar_cuotas_crudas(), evaluar_uno(), main(), mejor_peso(), mercado_por_partido(), probabilidad_binaria(), entrenar_ligero() (+2 more)

### Community 20 - "Apuesta y walk-forward"
Cohesion: 0.19
Nodes (10): main(), rasgos_mercado(), resumen(), columnas_rasgo(), columnas_rasgo_default(), grupos_rasgo(), brier(), logit() (+2 more)

### Community 21 - "XGBoost (copia de ambos marcan)"
Cohesion: 0.16
Nodes (7): predecir(), sig(), brier(), cargar(), entrenar(), main(), probabilidades()

### Community 22 - "Backtest de valor"
Cohesion: 0.20
Nodes (9): desempaquetar(), desmarginar(), familia_de(), handicap_local(), hechos_del_partido(), main(), pedir(), resolver() (+1 more)

### Community 23 - "Monitor en directo"
Cohesion: 0.26
Nodes (13): aplanar_cuotas(), desempaquetar(), elegir_seguidos(), prioridad(), en_juego(), escanear(), huella_cuotas(), liga_de() (+5 more)

### Community 24 - "Descarga de selecciones"
Cohesion: 0.22
Nodes (10): lista(), main(), leer_o_pedir(), marcador(), pedir(), terminado(), ya_en_raw(), lista() (+2 more)

### Community 25 - "Actualización de datos"
Cohesion: 0.21
Nodes (7): main(), obtener_detalle_partido(), obtener_partidos_recientes(), main(), pedir(), main(), pedir()

### Community 26 - "Forma de clubes"
Cohesion: 0.19
Nodes (7): lista(), main(), pedir(), main(), desempaquetar(), main(), pedir()

### Community 27 - "Precio implícito y directo"
Cohesion: 0.23
Nodes (7): main(), precio_directo(), sin_margen(), ajustar(), err(), main(), probs()

### Community 28 - "Afinado de ambos marcan"
Cohesion: 0.23
Nodes (6): correr(), entrenar(), main(), nombre(), predecir(), todas_las_combinaciones()

### Community 29 - "Evaluación de mercados"
Cohesion: 0.20
Nodes (7): brier(), cargar_cuotas_crudas(), evaluar_uno(), main(), mejor_peso(), mercado_por_partido(), probabilidad_binaria()

### Community 30 - "Ligas candidatas"
Cohesion: 0.38
Nodes (7): analizar(), desempaquetar(), encontrar_liga_id(), goles(), main(), pedir(), terminado()

### Community 31 - "Auditoría de fuga de tabla"
Cohesion: 0.27
Nodes (5): main(), comp(), posiciones(), sig(), calcular_tabla()

### Community 32 - "Perfil de jugadores"
Cohesion: 0.33
Nodes (7): abrir(), altura(), fecha(), jugadores_unicos(), main(), pedir(), ya_tengo()

### Community 33 - "Experimentos de onces"
Cohesion: 0.39
Nodes (5): main(), comparar(), main(), nuevos(), preparar()

### Community 34 - "Radiografía de ligas"
Cohesion: 0.39
Nodes (7): desempaquetar(), en_juego(), main(), minuto_de(), nombre_de(), pedir(), recoger()

### Community 35 - "Recalibración"
Cohesion: 0.33
Nodes (5): logit(), main(), predicciones(), sigmas(), tabla()

### Community 36 - "Experimento de lesiones"
Cohesion: 0.43
Nodes (5): lesiones(), main(), rasgos(), valor_antes(), valores()

### Community 37 - "Backfill histórico completo"
Cohesion: 0.36
Nodes (4): es_derbi(), main(), obtener_detalle_completo(), obtener_pagina_partidos()

### Community 38 - "Backfill por liga"
Cohesion: 0.43
Nodes (5): desempaquetar(), main(), minuto_de_evento(), pedir(), reparto_de_tarjetas()

### Community 39 - "Casas descolgadas"
Cohesion: 0.36
Nodes (4): desmarginar(), familia_de(), main(), pedir()

### Community 40 - "Censo de tarjetas"
Cohesion: 0.50
Nodes (6): aplanar_cuotas(), desempaquetar(), main(), pedir(), proximos_partidos(), titulo()

### Community 41 - "Sondeo de faltas"
Cohesion: 0.46
Nodes (6): desempaquetar(), estado_de(), main(), minuto_de(), pedir(), volcar_estadisticas()

### Community 42 - "Casas frente al cierre"
Cohesion: 0.38
Nodes (3): analizar(), cuando_se_cosecha(), main()

### Community 43 - "Cierre del descanso"
Cohesion: 0.43
Nodes (4): brier(), main(), pedir(), resultado_final()

### Community 45 - "Agenda de hoy"
Cohesion: 0.47
Nodes (3): cargar(), franjas(), main()

### Community 46 - "Cosecha de cuotas"
Cohesion: 0.53
Nodes (4): desempaquetar(), main(), pedir(), ya_tengo()

### Community 47 - "Experimento edad y valor"
Cohesion: 0.47
Nodes (3): main(), once_largo(), rasgos()

### Community 48 - "Sondeo de temporadas"
Cohesion: 0.53
Nodes (4): lista(), main(), pedir(), terminado()

### Community 49 - "Sondeo de titulares"
Cohesion: 0.47
Nodes (3): main(), pedir(), titulares()

### Community 51 - "Censo de ligas blandas"
Cohesion: 0.60
Nodes (3): desempaquetar(), main(), pedir()

### Community 52 - "Entreno con huecos"
Cohesion: 0.60
Nodes (3): main(), predecir(), sig()

### Community 54 - "Sondeo Nations League"
Cohesion: 0.60
Nodes (3): desempaquetar(), main(), pedir()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Selecciones y Nations League` to `Experimentos de ambos marcan (copia)`, `Separar fútbol y precio`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `Backfills del histórico` be split into smaller, more focused modules?**
  _Cohesion score 0.05009009009009009 - nodes in this community are weakly interconnected._
- **Why does `main()` connect `Backtest de valor` to `Experimentos de ambos marcan (copia)`, `Censos y sondeos de la API`, `Separar fútbol y precio`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `Selecciones y Nations League` be split into smaller, more focused modules?**
  _Cohesion score 0.07330827067669173 - nodes in this community are weakly interconnected._
- **Why does `ajustar()` connect `Backfills del histórico` to `Modelo de selecciones`, `Experimentos de ambos marcan (copia)`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Should `Descanso en vivo` be split into smaller, more focused modules?**
  _Cohesion score 0.07467532467532467 - nodes in this community are weakly interconnected._
- **Should `Sondeos de cuotas en directo` be split into smaller, more focused modules?**
  _Cohesion score 0.08156028368794327 - nodes in this community are weakly interconnected._