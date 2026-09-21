# Rumanía Liga II y México Liga MX: auditadas, ninguna es la respuesta hoy

## El fallo de método que casi nos lleva por mal camino

El censo de anoche marcó Rumanía Liga II (3 casas) y México Liga MX (6 casas)
como "poco vigiladas", mirando un único partido futuro. Al analizar 42 y 31
partidos YA JUGADOS de esas mismas ligas, la cobertura real es **41,6 y 30,4
casas de media** -- casi diez veces más.

La causa, documentada en la propia API: las cuotas previas se rellenan
**progresivamente durante varios días** antes del partido. Un partido a 3-5
días vista puede tener 3 casas puestas y llegar a 40 el día del pitido. El
censo de una sola foto sobre un partido lejano subestima casi siempre.

**Lección para el método:** la vigilancia de una liga no se mide en un
partido futuro. Se mide en la media de partidos ya cerrados, donde las cuotas
tuvieron tiempo de completarse. Corregido para la próxima ronda de búsqueda.

## Rumanía Liga II: cerrada

42 partidos, 41,6 casas de media -- tan vigilada como cualquiera de las seis
de siempre. Margen 10,51%, retorno a ciegas -6,84% (±7,39 pts, **-0,93
sigmas**). Sin anomalías en los datos. No hay nada aquí, y además ya no
califica como "liga blanda": nunca lo fue.

## México Liga MX: ni fantasma ni hallazgo

30,4 casas de media -- también muy vigilada, lo que ya hace sospechoso
cualquier resultado demasiado bueno (la doctrina de este proyecto: "un
resultado demasiado bueno es un síntoma, no un hallazgo").

El retorno a ciegas salió **+20,41%** (±15,34 pts, +1,33 sigmas). Auditado
partido a partido:

    CON el partido 1319878807 (2-3, ganó el equipo visitante a cuota 12.50):
      +20,41%  (±15,34 pts, +1,33 sigmas)  -- n=31
    SIN ese partido:
      +9,34%   (±11,40 pts, +0,82 sigmas)  -- n=30

**Un solo partido aporta 6,76 de los 24,0 puntos** de la media. Es una
sorpresa real -- el marcador está bien, la cuota está bien, no hay error de
datos -- pero es exactamente el tipo de resultado que una muestra de 31
partidos no puede sostener: un único resultado inesperado mueve el número
entero casi siete puntos.

Quitando ese partido, la significación cae de 1,33 a 0,82 sigmas -- muy por
debajo del umbral para creerse nada. El punto central sigue siendo positivo,
pero no hay forma honesta de distinguirlo del ruido con 30-31 partidos.

## Veredicto

Ninguna de las dos es la respuesta hoy. Rumanía está cerrada con números
limpios. México no está descartada -- es la única señal del día que no murió
al mirarla de cerca -- pero tampoco es un hallazgo: necesita más partidos
antes de que el número signifique algo, exactamente como la pista de la
mezcla de esta madrugada, que se murió al crecer de 89 a 168 partidos. Puede
pasarle lo mismo a esta, o puede sostenerse. No se sabe con 31.

La cosecha diaria de cuotas puede apuntarse a México Liga MX específicamente
para acumular semana a semana, igual que se hizo con las seis ligas
originales. Es la única línea de las dos que merece seguir viva.
