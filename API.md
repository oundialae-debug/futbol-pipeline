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

## Cosas que no hay

- **No hay desglose por tiempos** en `/statistics`: devuelve el acumulado del
  partido. Pero en un partido EN JUEGO ese acumulado va al minuto, así que
  llamándolo en el descanso se obtienen las faltas del primer tiempo.
- **No hay marca de tiempo** en las cuotas.
- El endpoint `/odds` no está disponible en el plan gratuito.
