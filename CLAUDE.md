# futbol-pipeline

**Regla del usuario: NUNCA llamar a la API de Highlightly sin su sí explícito para ESA llamada** (sondeos, backfills o lanzar un workflow que la use; un sí anterior no vale). Única excepción aprobada: `ambos_marcan_diario.yml` y `post_partido.yml` (aprobado el 10/10: post-partido automático, sondeo cada 5 min desde inicio+1h45, ≤30 llamadas/día). Antes de empujar código: `python3 scripts/prueba_humo.py`. Todo cambio va en `BITACORA.md` en el mismo commit. Lecciones y resultados completos: `docs/notas_proyecto.md`; ambos marcan: `modelos/ambos_marcan/CLAUDE.md`.

## Mapa
| entrada | pieza (cómo se ejecuta) | salida |
|---|---|---|
| API Highlightly | `scripts/backfill_*.py` (workflows `backfill_*.yml`, a mano) | `data/historico_*.csv` |
| football-data.co.uk | `descargar_football_data.py` (workflow) → `cuotas_football_data.py` | `data/cuotas_historicas_fd.csv` |
| `data/historico_*.csv` | `modelo_xgboost.cargar()` → `rasgos.construir()` | variables sin fuga, una fila por partido |
| variables | `modelo_ambos_marcan.py` (oficial, 102 vars) · `evaluar_mercados.py` (5 mercados) | `data/validacion_mercados.json` |
| API, partidos de hoy | `ambos_marcan_hoy.py descargar/pronosticar/evaluar` (`ambos_marcan_diario.yml`, ACTIVO) | `data/ambos_marcan/registro_papel.csv`, `modelos/ambos_marcan/registro_papel.md` |
| API, selecciones | `modelos/selecciones/*.py` (`nations_league_ciclo.yml`, activo) | `data/selecciones/` |
| API, 2 partidos grandes del día (5 ligas) | `post_partido.py` (`post_partido.yml`, cron */5, ACTIVO; sin API hasta inicio+1h45) → `datos_clubes.post` + vídeo + Buffer | `media/post_partido/`, `data/redes/post_partido/`, fila en `data/historico_partidos.csv` |
| API NBA (cuota aparte) | `scripts/nba/*.py` (`nba_boxscore.yml`, activo) | `data/nba/` |
| datos ya en disco | `experimento_*`, `auditoria*`, `sondeo_*`, `censo_*` (sueltos) | resultados en los `.md` |

- Activos de nuevo desde el 09/10: cosechar_cuotas (≤1.200 llamadas/día) y calendario. En pausa (cron comentado): descanso_en_vivo, revision_descanso, casas_descolgadas, censo_margenes, pipeline_diario. `tenis_directo.yml` corre en la rama `ccr-3c3cfe57-etcioo`.
- Obsoletos o duplicados: `modelos/ambos_marcan/scripts/` (copia congelada del 24/09; lo vigente está en `scripts/`); `scripts/actualizar_datos.py` y `scripts/backfill_historico_completo.py` (sin workflow; los sustituye `backfill_historico.py`).

## Grafo de conocimiento (graphify)
- Úsalo solo para preguntas que crucen varios archivos; para leer un archivo concreto, ábrelo directamente.
- `graphify explain "<nodo>"`, `graphify path "<A>" "<B>"` o `graphify query "<pregunta>" --budget 800` (siempre con presupuesto).
- Solo código (sin `data/`, ver `.graphifyignore`). Se actualiza solo con el workflow `actualizar-grafo.yml`; los cambios en documentos necesitan `/graphify --update`.

## APIs gratuitas
La skill .claude/skills/free-llm-apis guía para usar proveedores LLM gratuitos. El nivel gratuito de Gemini está bloqueado en el EEE, Reino Unido y Suiza.
- Configurados (credenciales del entorno, el proxy pone la clave; nunca en el código): Groq, Cerebras y Mistral funcionan (Mistral gratis: solo ministral/codestral/nemo; small y medium dan 429). Usar `scripts/llm_gratis.py` → `preguntar(prompt)` (Groq → Cerebras → Mistral). Solo tareas mecánicas y datos públicos; avisar al usuario antes de usarlo.

## Notas compartidas
Apunta aquí, en una línea, las decisiones y lo aprendido para los próximos chats.
- 05/10/2026: el CLAUDE.md largo pasa a `docs/notas_proyecto.md`; grafo graphify solo de código (sin `data/`); skill free-llm-apis instalada sin claves.
- 05/10/2026: LLM gratuitos listos (Groq, Cerebras) vía `scripts/llm_gratis.py`; Python necesita User-Agent propio o da 403.
- 09/10/2026: reactivados cosechar_cuotas y calendario (las cuotas caducan a los 28 días); descanso_en_vivo (914/día) y los semanales siguen parados.
