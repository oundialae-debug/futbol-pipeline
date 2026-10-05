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
- Modelos de clubes (1X2, goles, córners, tarjetas) y reglas generales: `CLAUDE.md` (corto) y `docs/notas_proyecto.md` (lecciones y resultados).
- Ambos marcan: `modelos/ambos_marcan/CLAUDE.md`.
- Selecciones: `modelos/selecciones/CLAUDE.md` (otro chat).
- NBA: `docs/otros_deportes/nba.md`.

---

## 05/10/2026

### Cambios de código y ficheros

| qué | por qué | ficheros |
|---|---|---|
| Skill `free-llm-apis` copiada de mnfst/awesome-free-llm-apis (revisada: solo documentación, sin scripts). Sin claves ni proveedores configurados. | Petición del usuario: tener a mano proveedores LLM gratuitos para ahorrar tokens. | `.claude/skills/free-llm-apis/` |
| Grafo de conocimiento con graphify (paquete `graphifyy` 0.9.76): pipeline completo, solo código, sin `data/`. 1.064 nodos, 2.869 aristas, 56 comunidades con nombre. Cero tokens (análisis estático). | Responder preguntas que cruzan varios archivos sin leerlos todos. | `graphify-out/`, `.graphifyignore` |
| Workflow que actualiza el grafo en cada push a `main` con cambios en `.py` o workflows (`graphify update .`). | Que el grafo no se quede viejo. Ojo: `update` renombra las comunidades por su nodo principal (pierde los nombres puestos a mano) e indexa también la estructura de los `.md`. | `.github/workflows/actualizar-grafo.yml` |
| Hook de arranque de sesión que instala graphify si falta. NO se instalaron `graphify claude install` ni `graphify hook install`. | Que cualquier chat nuevo pueda consultar el grafo. | `.claude/settings.json`, `.gitignore` |
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
