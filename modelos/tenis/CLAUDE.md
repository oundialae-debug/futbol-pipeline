# Tenis (ATP y WTA) -- empezado el 30/09/2026

Petición del usuario: "quiero que empecemos a pronosticar tenis", ATP y WTA.
Tema aparte: no comparte código ni datos con los modelos de fútbol. Las reglas
generales del `CLAUDE.md` raíz (sin API sin permiso, bitácora, fallos
silenciosos) valen igual aquí.

## Fuentes

- **Highlightly NO tiene tenis.** Comprobado sin llamadas en
  `docs/otros_deportes/spec_sport.json`: la All Sports API cubre fútbol, NBA,
  NFL, MLB, NHL, baloncesto, hockey, voleibol, balonmano, rugby y críquet.
- **tennis-data.co.uk**: resultados con cuotas de cierre (Pinnacle `PSW/PSL`,
  Bet365, `Max`, `Avg`). ATP desde 2000, WTA desde 2007. Es la referencia de
  mercado, como football-data en fútbol.
- **Jeff Sackmann** (`tennis_atp`, `tennis_wta` en GitHub): todos los
  partidos, con estadísticas de saque desde 1991. Licencia CC BY-NC-SA 4.0,
  uso no comercial.
- Desde el contenedor de Claude las dos están bloqueadas (tennis-data da 403;
  a GitHub solo se llega a los repos del usuario). Se bajan con
  `.github/workflows/descargar_tenis.yml` (script
  `modelos/tenis/scripts/descargar_tenis.py`), que guarda en `data/tenis/`.
  Qué ha llegado de verdad: `data/tenis/resumen_descarga.md`.

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
- **Sackmann se valida antes de usarlo** (pregunta del usuario, 30/09):
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
