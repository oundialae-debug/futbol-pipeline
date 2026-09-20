# La API de Highlightly, en lo que nos afecta

Apuntes sacados de la especificación OpenAPI y de lo que ha ido fallando.
Están aquí porque varias cosas de esta lista las dedujimos mal primero y
costaron trabajo tirado.

## Plan contratado

- **7.500 peticiones al día**, 720 por minuto.
- El comparador del descanso lleva su propio contador en `data/consumo_api.json`
  y se para solo al llegar a 6.000, dejando margen para el resto.

## Cada cuánto se refresca cada cosa

| Endpoint | Refresco |
|---|---|
| `/matches` | 1 minuto |
| `/events/{id}` | 1 minuto |
| `/statistics/{matchId}` | 5 minutos |
| `/lineups/{matchId}` | 15 minutos |
| `/odds` **prematch** | varias veces al día |
| `/odds` **live** | **10 minutos** |

**Los 10 minutos de las cuotas en vivo son el dato más importante de esta
tabla.** La respuesta no trae marca de tiempo, así que de un precio solo
sabemos que tiene diez minutos o menos. Consecuencias:

- El precio que leemos en el descanso pudo fijarse en el minuto 40, antes de
  las últimas tarjetas del primer tiempo. Parte de la discrepancia que mide
  el modelo puede ser eso y no un error del mercado.
- La casa sí tiene el precio bueno en su web: una cuota que aquí parece
  regalada puede no existir ya.
- Dos fotos del precio separadas por menos de 10 minutos pueden caer en el
  mismo ciclo y salir idénticas **sin que el mercado esté quieto**. Nos pasó:
  14 líneas iguales hasta el último decimal. Por eso la segunda foto se toma
  ahora entre los 20 y los 45 minutos.
- Pedir `/odds` más de una vez cada 10 minutos por partido es tirar llamadas.

## Paginación: `/odds` no es como los demás

| Endpoint | `limit` máximo | por defecto |
|---|---|---|
| `/teams` | 500 | 500 |
| `/players` | 1000 | 1000 |
| `/matches` | 100 | 100 |
| `/leagues` | 100 | 100 |
| `/highlights` | 40 | 40 |
| **`/odds`** | **5** | **5** |

La unidad que pagina `/odds` es el PARTIDO (`{matchId, odds[]}`), no la
cuota: un solo partido trae cientos de cuotas en una respuesta. Con
`matchId` no hay problema, pero pedir por `date` o `leagueId` devuelve
**5 partidos por página**. Aun así sale a cuenta: una llamada por cada 5
partidos en vez de una por partido.

## Estados de partido (lista oficial)

`Not started`, `First half`, `Second half`, `Half time`, `Extra time`,
`Break time`, `Penalties`, `Finished`, `Finished after penalties`,
`Finished after extra time`, `Postponed`, `Suspended`, `Cancelled`,
`Awarded`, `Interrupted`, `Abandoned`, `In progress`, `Unknown`,
`To be announced`.

El descanso es exactamente **`Half time`**. Ojo con `Break time`: **no** es
el descanso, es la pausa antes de la prórroga. El modelo no vale ahí, porque
quedan 15 minutos y está ajustado sobre segundas partes enteras.

`In progress` significa partido en juego con cobertura mínima, y `Finished`
llega con retraso: hemos visto partidos terminados que seguían apareciendo
en el minuto 90 durante un rato. De ahí el tope de 87 minutos.

## Mercados que cotizan

`Full Time Result`, `Asian Handicap`, `Odd or Even`, `Total Goals`,
`Both Teams to Score`, `Correct Score`, `First Team to Score`,
**`Total Cards`**, `Clean Sheet`, **`Total Corners`**.

`Total Cards` y `Total Corners` son mercados "complejos": el nombre lleva la
línea dentro (`"Total Cards 4.5"`), y cada variante se resuelve `Over` o
`Under`. Por eso hay que parsear la línea del nombre del mercado.

## Forma de la respuesta de `/odds`

```
{ data: [ { matchId, odds: [ { bookmakerId, bookmakerName, type, market,
                                values: [ { odd, value } ] } ] } ],
  pagination, plan }
```

Los mercados van anidados bajo `odds`, y la clave del mercado es **`market`**,
no `name`. Esto costó una semana de "1 mercado encontrado": el parser leía
`.get("data")` y se quedaba en el objeto del partido.

Las cuotas son **decimales** (la suma de 1/cuota da 1.05-1.08, que es el
margen de la casa).

## Inventario real (leído de la especificación, 20/09/2026)

La especificación está guardada en `docs/openapi_highlightly.json`. **Son 25
rutas.** El proyecto entero había usado seis. Esta sección existe porque di
por cerrado el inventario sin abrirlo, y la conclusión "no tenemos
información que el mercado no tenga" se apoyaba en eso.

### Las dos ventanas temporales que mandan

- **`/lineups/{matchId}`: desde 40 MINUTOS antes del saque hasta 120 después.**
  No una hora: cuarenta minutos. Refresco cada 15 minutos, así que la
  alineación se ve entre 40 y 25 minutos antes, según caiga el ciclo.
- **`/odds`: desde 7 días antes hasta 28 días después.** Los 28 de después ya
  los usábamos para el backtest; los 7 de antes no los habíamos mirado.

Esas dos ventanas juntas definen la única jugada posible: el precio existe
desde siete días antes, y la alineación llega cuarenta minutos antes de
empezar. Lo que se pueda ganar está en ese hueco o no está en ningún sitio.

### `/matches/{id}` trae mucho más de lo que pide su nombre

Pedí `/referees` y dio 404, y lo apunté como "no hay árbitro". **Sí hay.** Va
dentro del detalle del partido, no en una ruta propia:

    referee      -> name, nationality
    venue        -> city, name, country, capacity
    forecast     -> status, temperature          (el tiempo que hará)
    predictions  -> prematch[{type, modelType, generatedAt, probabilities}]
    events       -> tipo, minuto, jugador, asistente
    statistics   -> las mismas que /statistics
    homeTeam/awayTeam.shots -> por jugador: minuto, outcome, goalTarget
    homeTeam/awayTeam.topPlayers

El árbitro importa: es el factor que más manda en las tarjetas, y las
tarjetas son el mercado con menos casas (1,2).

Ojo con `predictions`: es el modelo de la propia API. Sirve como rival contra
el que medirse, no como fuente de ventaja. Si su modelo fuera bueno, el
precio ya lo llevaría dentro.

### `/box-score/{matchId}`: 37 estadísticas POR JUGADOR

Nunca la habíamos pedido. Refresco cada 5 minutos, o sea que en un partido en
juego va al minuto.

    goalsScored goalsSaved goalsConceded assists
    dribblesTotal dribblesSuccessful dribblesFailed dribbleSuccessRate
    fouledByOthers fouledOthers tacklesTotal interceptionsTotal
    duelsTotal duelsWon duelsLost duelSuccessRate
    cardsRed cardsYellow cardsSecondYellow
    passesAccuracy passesSuccessful passesFailed passesTotal passesKey
    penaltiesScored penaltiesMissed penaltiesTotal penaltiesAccuracy
    shotsOnTarget shotsOffTarget shotsTotal shotsAccuracy
    expectedGoals expectedAssists expectedGoalsOnTarget
    expectedGoalsOnTargetConceded expectedGoalsPrevented

`fouledOthers` y `cardsYellow` por jugador son justo lo que pedía la
intuición de las faltas: no "este partido lleva 11 faltas", sino "este
jugador concreto lleva 3 faltas y una amarilla".

### Lo demás que existe y no usábamos

    /teams/statistics/{id}      total / home / away por liga y temporada
    /players/{id}/statistics    por club y por competición: amarillas, rojas,
                                segundas amarillas, minutos, partidos
    /standings                  clasificación
    /last-five-games            forma reciente (pide teamId)
    /head-2-head                los diez últimos entre dos equipos

### Lo que NO existe

No hay rutas de lesiones, entrenadores ni traspasos. La baja por lesión solo
se deduce de la alineación cuando sale, a 40 minutos.

## Cosas que no hay

- **No hay desglose por tiempos** en `/statistics`: devuelve el acumulado del
  partido. Pero en un partido EN JUEGO ese acumulado va al minuto, así que
  llamándolo en el descanso se obtienen las faltas del primer tiempo.
- **No hay marca de tiempo** en las cuotas.
- El endpoint `/odds` no está disponible en el plan gratuito.

## Las cuotas de distintas casas NO son simultáneas

Esto sale de intentar comparar casas entre sí, y cierra esa vía entera.

El censo de márgenes encontró 124 casos de margen combinado negativo: coger
la mejor cuota de cada lado daría beneficio garantizado. Entre ellos, **9 de
31 partidos de 1X2 -- un 29% -- con cuarenta y nueve casas cotizando**, con
beneficios de hasta el 9.7%.

Eso no puede ser cierto. El 1X2 es el mercado más líquido y vigilado que
existe; si un 29% de los partidos ofreciera beneficio seguro, se arbitraría
en segundos. No hace falta más prueba: el dato no es simultáneo.

La causa está en la propia documentación. Las cuotas previas se refrescan
"varias veces al día", y la respuesta **no trae marca de tiempo**. Así que en
una misma llamada conviven precios capturados en momentos distintos. Si el
mercado se movió entre medias -- una lesión, una alineación -- coger la mejor
de cada lado compara un precio de ayer con uno de hoy e inventa un arbitraje
que no existió nunca.

CONSECUENCIA PARA CUALQUIER COMPARACIÓN ENTRE CASAS
---------------------------------------------------
La "desviación del consenso" mide, en parte, CUÁNDO se capturó el precio y no
lo que piensa la casa. Y engaña en la peor dirección posible: una cuota vieja
parece generosa justo cuando el mercado se ha movido en su contra, que es
exactamente cuando perdería.

Eso explica el resultado del backtest. Las apuestas marcadas con más de un 5%
de valor rindieron un -7.54%, peor que las que no tenían ninguno. No era que
la ventaja fuera pequeña: es que el indicador apuntaba al revés.

Con esta fuente, comparar casas entre sí no es viable. No es un problema de
modelo, es de datos.
