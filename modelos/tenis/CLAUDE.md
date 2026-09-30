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
  validar las otras dos. Bloqueada desde el contenedor (403): se baja con
  `.github/workflows/descargar_tenis.yml` (a mano) y
  `scripts/descargar_tenis.py`. Resumen: `data/tenis/resumen_descarga.md`.
- **Sackmann**: los repos `JeffSackmann/tennis_atp` y `tennis_wta` **ya no
  existen en GitHub** (el clon falló el 30/09 y hay constancia pública de su
  retirada). Se usa la copia de archivo
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
