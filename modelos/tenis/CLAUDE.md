# Tenis (ATP y WTA) -- empezado el 30/09/2026

Petición del usuario: "quiero que empecemos a pronosticar tenis", ATP y WTA.
Tema aparte: no comparte código ni datos con los modelos de fútbol. Las reglas
generales del `CLAUDE.md` raíz (sin API sin permiso, bitácora, fallos
silenciosos) valen igual aquí.

## Fuentes

- **Highlightly NO tiene tenis.** Comprobado sin llamadas en
  `docs/otros_deportes/spec_sport.json`: la All Sports API cubre fútbol, NBA,
  NFL, MLB, NHL, baloncesto, hockey, voleibol, balonmano, rugby y críquet.
- **tennis-data.co.uk** (`data/tenis/tennis_data/`): resultados con cuotas de
  cierre (Pinnacle `PSW/PSL`, Bet365, `Max`, `Avg`). ATP desde 2000, WTA desde
  2007. Es la referencia de mercado y **la única fuente independiente** para
  validar las otras dos. **Claude NO la descarga**: limita el uso a
  particulares y bloquea a los agentes de IA en `robots.txt` (y la carpeta
  de ficheros ha cambiado de ruta). El workflow que la bajaba (30/09) dio
  47/47 FALLO con la ejecución en verde; se retiró. El usuario baja los
  ficheros a mano y los sube TAL CUAL a `data/tenis/tennis_data_crudo/` (zip o
  Excel, cualquier nombre; circuito y año salen del contenido) y
  `scripts/procesar_tennis_data.py` los pasa a CSV
  (`data/tenis/resumen_tennis_data.md`). Sin ficheros, sale con error.
- **Sackmann**: los repos `JeffSackmann/tennis_atp` y `tennis_wta` **ya no
  existen en GitHub**: la API de GitHub da "Not Found" y en su cuenta solo
  queda `tennis_MatchChartingProject` (`data/tenis/sondeo_sackmann.md`). Se usa la copia de archivo
  `huggingface.co/datasets/Aneeshers/tennis-sackmann-archive`, congelada en
  junio de 2026 (ATP y WTA hasta el 25/05/2026). CC BY-NC-SA 4.0, uso no
  comercial. En `data/tenis/sackmann/`: circuito principal desde 1991,
  Challenger/previas (ATP) y previas/ITF (WTA) desde 2010, jugadores.
- **TennisMyLife** (`stats.tennismylife.org`, MIT, actualizada a diario):
  ATP desde 1991, Challenger y previas ATP desde 2010, WTA desde 1991, más
  torneos en curso. En `data/tenis/tennismylife/`. Hasta el 29/09/2026.
- Sackmann y TennisMyLife se bajan desde el contenedor con
  `scripts/descargar_tml_sackmann.py`. Resúmenes en
  `data/tenis/resumen_sackmann.md` y `resumen_tennismylife.md`.
- Descartadas (30/09): Betfair histórico (el usuario no tiene cuenta), The
  Odds API (sin Challenger, histórico de pago), OddsPortal/Tennis Explorer/
  FlashScore/SofaScore (solo raspando, lo prohíben sus condiciones), Kaggle
  "ATP daily" (sale de tennis-data, solo ATP).

## TennisMyLife NO es independiente de Sackmann (30/09/2026)

Comprobado partido a partido (clave: fecha del torneo + ganador + perdedor,
nombres normalizados; `tourney_id` y `match_num` NO sirven de clave porque
cada fuente numera distinto, y usarlos dio cientos de "diferencias" falsas):

- ATP: el MISMO número de partidos cada año (3.378 en 2000, 3.030 en 2010,
  3.076 en 2024, 2.944 en 2025). TennisMyLife partió de Sackmann y lo retocó:
  IDs de jugador cambiados por códigos ATP ("D875" frente a 105777), nombres
  corregidos, algunos marcadores y stats distintos (2024: 40 marcadores y
  5 w_svpt distintos de 2.741 emparejados).
- WTA: copia casi exacta (2024: mismos IDs, 0 marcadores ni stats distintos).
- Emparejan peor en 2025 (67%) y Challenger 2024 (14%): sin mirar aún por
  qué (¿fechas de torneo distintas?, ¿previas incluidas en uno y no en otro?).

Consecuencia: cruzarlas entre sí NO detecta errores de origen. El control
independiente es tennis-data. Sus diferencias sí marcan dónde una de las dos
corrigió algo.

## Validación interna (30/09/2026): Sackmann limpio, lo nuevo de TennisMyLife no tanto

`scripts/validar_interno.py` -> `data/tenis/validacion_interna.md`. Desde 2000:
imposibles físicos en stats de saque, texto en columnas numéricas,
duplicados, ganador = perdedor, retiradas.

- Sackmann ATP: 0 imposibles en 79.299 partidos (91% con stats). WTA: 1 en
  72.714 (66% con stats). Challenger+previas ATP: 0 en 137.088 (97%).
- Previas+ITF WTA (Sackmann): 1.354 duplicados y solo 15% con stats. Quitar
  duplicados antes de usarlo.
- TennisMyLife: los errores están en lo que ha añadido él, no en lo heredado:
  Copa Davis del 12/09/2025, previas de Roland Garros 2026 (10 partidos con
  bpSaved > bpFaced, todos del 24/05/2026) y 2026 tecleado a mano
  (`l_bpFaced='4y'`, `l_2ndWon='-35.9%'`). Poco en total (~0,01%), pero **la
  parte reciente de TennisMyLife, la que Sackmann ya no cubre (desde junio de
  2026), es la menos fiable**, y es justo la que hará falta para pronosticar.
- Retiradas/walkovers: 3-4% en todas las fuentes. Se apartan al medir precio.

## Cruce independiente con tennis-data (30/09/2026)

`scripts/cruce_fuentes.py` -> `data/tenis/cruce_fuentes.md`. 2020-2026, cada
partido de tennis-data buscado en Sackmann y TennisMyLife (apellido+inicial,
fecha dentro de [inicio del torneo -3, +20 días]).

- Emparejan 96-98%. Los que no, sobre todo por nombres escritos distinto
  ("O Connell C.", "Varillas J. P.", "Osorio M." = Camila Osorio), no por
  datos malos. Si se necesita el 100%, hace falta una tabla de alias.
- Ganador al revés: 4-8 de ~15.000 (casi todos retiradas), salvo
  TennisMyLife WTA: 24, varios de Rouen 2026 (lo que añade él, otra vez).
- Marcador distinto en partidos completos: 0,3% (TennisMyLife WTA 1%).
- **tennis-data también falla**: da ganador a De Minaur contra Fritz en el
  Masters 2024 (ganó Fritz), Sardegna Open 2021 como pista dura (era
  tierra), Acapulco 2020 WTA como tierra (era dura). Con tres fuentes decide
  la mayoría; ninguna es perfecta.

## Precio de cierre de Pinnacle: sesgo real, pero no tapa el margen (30/09/2026)

`scripts/calibracion_cierre.py` -> `data/tenis/calibracion_cierre.md`.
ATP+WTA 2020-2026, 26.467 partidos completos (walkovers fuera, retiradas
aparte). Margen medio de Pinnacle: ATP 2,60%, WTA 2,83%.

- **Sesgo favorito-marginado, sí**: pendiente logística 1,135 (±0,028),
  +4,85 sigmas contra 1. El favorito gana más de lo que dice el precio, sobre
  todo los muy favoritos (ATP 90-95%: dice 92,4%, gana 95,8%, +2,84s; WTA
  85%+: +2,2 a +2,4s).
- Dónde: 1ª-2ª ronda +5,07s (3ª ronda o más +0,90s); Grand Slam +3,91s;
  Masters 1000 nada (-0,27s). Por años, inestable: 2022 1,26, 2024 1,22,
  **2025 0,98 (sin sesgo)**. Vigilar 2026 antes de creérselo.
- **No da dinero a ciegas**: apostar siempre al favorito en Pinnacle pierde
  -2,28% (ATP) y -2,03% (WTA). El hueco con el precio perfecto es solo
  +0,43s y +1,18s. **Contando retiradas como "gana quien avanza"**, el hueco
  del favorito desaparece (-0,01s): depende de cómo liquide cada casa las
  retiradas.
- Favorito y marginado son la misma cosa vista desde los dos lados (mercado
  de dos resultados): no son dos hallazgos.
- "Máxima" casi empata en favoritos (ATP -0,32%, WTA +0,28%), pero su
  esperado en marginados sale +1,5%: precios de casas distintas NO
  simultáneos, la misma trampa que en fútbol ("casas contra cierre"). No es
  accesible.
- **Pinnacle desaparece de tennis-data desde febrero de 2026** (PSW vacío
  95-97% en 2026). Betfair Exchange (BFEW/BFEL) entra a finales de 2025 (75%
  vacío en 2025, 5% en 2026): desde 2026 la referencia de cierre es Betfair.

## Elo y regla del favorito, prueba limpia (30/09/2026): ninguno bate al cierre

Regla fijada antes de mirar: 2020-2023 para elegir, 2024-2026 solo para
juzgar (2024-2025 contra Pinnacle, 2026 contra Betfair Exchange).

**Elo por superficie** (`scripts/elo_tenis.py`, `scripts/evaluar_elo.py` ->
`data/tenis/evaluar_elo.md`). Historial: TennisMyLife ATP (con Challenger y
previas) y Sackmann WTA (con previas e ITF) + TennisMyLife WTA tras mayo de
2026. Orden por inicio de torneo y ronda; control de fuga (trucar un
resultado no cambia nada anterior ni de la misma ronda): pasa. Elegido
c=250 (ATP) / 350 (WTA), peso de superficie 0,25.
- Solo, pierde con claridad: log-loss +7,2 a +8,5 sigmas peor que Pinnacle
  (2024-2025) y +4,6/+5,2 peor que Betfair (2026); 2-3 puntos menos de
  acierto. Apostando con él: ATP -3,7%, WTA -6,3%.
- Mezcla mercado+Elo (ajustada en 2020-2023): mercado con peso >1 (1,12
  ATP, 1,20 WTA) y Elo con peso NEGATIVO (-0,08/-0,10). La mejora no viene
  del Elo sino de estirar el precio: es el sesgo favorito-marginado. En la
  prueba mejora al mercado 0,25-1,26 sigmas: nada.

**Regla del favorito** (`scripts/regla_favorito.py` ->
`data/tenis/regla_favorito.md`). 15 candidatas; elegida "1ª-2ª ronda,
favorito >= 90%": +1,61% (+2,10s) en la elección. En la prueba: **-0,09%
(2024-2025, Pinnacle, 345 apuestas) y -2,07% (2026, Betfair bruto, 173)**.
Al hacer la prueba limpia, el número fue a cero: era el premio de elegir la
mejor de 15. El sesgo existe en el precio pero no deja dinero.

No reabrir "Elo solo" ni "regla del favorito" con estos mismos datos.

## Modelo con saque, fatiga, perfil y cara a cara (30/09/2026): no bate al mercado

`scripts/rasgos_tenis.py` (variables antes de cada partido, control de fuga
que pasa) y `scripts/modelo_tenis.py` -> `data/tenis/modelo_tenis.md`.
Entrena 2020-2022, elige en 2023, reentrena 2020-2023 y juzga 2024-2026.
Comparador: el mercado recalibrado (ya corrige el favorito-marginado).

- Ninguna de 20 configuraciones (10 conjuntos x logística/XGBoost) mejora al
  mercado recalibrado con significación. Elegida en 2023: "perfil"
  (logística): -1,41s en 2024-2025, +1,42s en 2026. Ruido. Apostando con
  ella: +0,80% en 7.776 apuestas, +0,73s.
- XGBoost empeora SIEMPRE frente a la logística (sobreajuste con ~16.000
  partidos de entrenamiento), como en fútbol.
- Pista, no hallazgo: **fatiga** (logística) mejora en las dos pruebas
  (-1,91s en 2024-2025, -0,95s en 2026) pero empeoraba en 2023 (+0,91s).
  Solo se podría confirmar con partidos futuros.

**Fallo silencioso encontrado y arreglado:** TennisMyLife WTA 2026 trae
columnas desplazadas (edad 3.387, altura 20011008 = fecha de nacimiento de
Peyton Stearns) y hay alturas 0 sueltas en sus Challengers. Metidas en el
modelo, empeoraban 2026 en +0,0116 de log-loss (diez veces cualquier otra
diferencia) sin ningún error. Ahora edad fuera de 14-50 y altura fuera de
150-215 quedan vacías, y `validar_interno.py` cuenta los fuera de rango.

## Cinco situaciones concretas (30/09/2026): dos pistas de "óxido", nada confirmado

`scripts/situaciones.py` -> `data/tenis/situaciones.md`. Hipótesis fijadas
antes de mirar; logística mercado + indicador, entrena 2020-2023, juzga
2024-2026 contra el mercado recalibrado. Exigencia fijada: >= 2,5 sigmas y
que aguante en los dos tramos de prueba.

| situación | coef. entreno | coef. prueba | log-loss 2024-25 | log-loss 2026 |
|---|---|---|---|---|
| local (juega en su país) | -0,70s | -1,16s | -0,86s | -0,47s |
| previa (Q/LL) | **+3,61s** | +0,84s | +0,75s | +0,44s |
| cansancio (anterior >= 180 min) | -0,39s | -0,41s | +0,03s | -0,18s |
| regreso (>= 60 días sin torneo) | -1,96s | -1,85s | -0,43s | -1,03s |
| cambio de superficie (>= 120 días) | -1,53s | -2,39s | -1,94s | -0,18s |

- "previa" parecía fuerte y en la prueba fue hacia cero: descartada.
- **Pistas, no hallazgos**: "regreso" y "cambio de superficie" van en la
  misma dirección en entreno y prueba. El mercado sobrevalora al jugador
  "oxidado" (vuelve de parón o no ha pisado esa superficie en 4 meses). No
  llegan a 2,5 sigmas y mejoran el log-loss muy poco. Juntarlas en un solo
  indicador ahora sería elegir después de mirar: se confirma solo con
  partidos futuros, con la regla escrita antes.

## Plan (en este orden)

1. Ganador del partido, único mercado con cierre de Pinnacle.
2. **Medir primero el precio**: calibración del cierre de Pinnacle y sesgo
   favorito-marginado, por circuito, nivel de torneo y superficie. Si el
   precio no está torcido, un modelo no tiene nada que corregir.
3. Modelo base: Elo por superficie, evaluado contra el cierre con corte
   temporal y errores en sigmas.
4. Solo si queda hueco: saque/resto, fatiga, cara a cara.

Lo esperable: el ganador de ATP/WTA es muy líquido y el Elo solo no bate al
cierre. Buscar rincones blandos (Challenger, WTA pequeña, primeras rondas)
se mide en partidos YA jugados, nunca con una foto de un partido futuro.

## Ojo, antes de unir las dos fuentes

- Los nombres no coinciden: tennis-data usa "Nadal R.", Sackmann "Rafael
  Nadal". El emparejamiento se comprueba a mano en una muestra, igual que los
  alias de football-data.
- **Sackmann/TennisMyLife se validan antes de usarlos** (pregunta del usuario, 30/09):
  cruce partido a partido con tennis-data (ganador, marcador, superficie,
  ranking; lo que no cuadre se aparta y se cuenta), e imposibles físicos en
  las estadísticas de saque (aces/dobles faltas <= puntos de saque,
  1stWon <= 1stIn <= svpt, bpSaved <= bpFaced, juegos al saque coherentes con
  el marcador, duplicados). Cobertura de stats medida por año y nivel, no con
  un partido.
- **Fuga: `tourney_date` de Sackmann es el INICIO del torneo**, igual para
  todas las rondas. Ordenar por fecha sin más deja que la 1ª ronda vea la
  semifinal (misma forma que la tabla de fútbol del 29/09). Ordenar por ronda
  dentro del torneo o usar la fecha real de tennis-data, y control de fuga:
  trucar un resultado y que nada anterior ni de la misma ronda cambie.
- Si Sackmann no está disponible, el Elo sale solo de tennis-data (ganador,
  marcador, superficie, ronda, ranking, fecha); se pierden las stats de saque.
- Retiradas y walkovers (`Comment` en tennis-data, `score` con "RET"/"W/O" en
  Sackmann): cada casa liquida distinto. Se apartan antes de medir nada.
