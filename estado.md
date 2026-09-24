# Estado: mercado poco competido + value bets + herramienta interna

Lo que se pidió, en dos partes, y dónde está cada una. Todo con números
medidos, ninguno prestado de fuera.

---

## PARTE 1 — Mercado poco competido y value bets

### Cómo se mide "poco competido"

Por el número de casas que cotizan ese mercado. Menos casas, menos ojos, menos
dinero listo corrigiendo el precio.

| Mercado | Casas | Margen (1 cuenta) | Margen (10 cuentas) |
|---|---|---|---|
| **Total Cards** | **1,2** | 9,64% | ~8,9% (no baja: nadie más cotiza) |
| **First Team To Score** | **4,5** | 11,15% | — |
| **Total Corners** | **6,5** | 8,54% | 6,11% |
| Asian Handicap | 17,7 | 6,46% | 2,85% |
| Total Goals | 24,7 | 6,05% | 2,62% |
| Odd or Even | 27,3 | 6,87% | 4,10% |
| Both Teams To Score | 28,4 | 6,84% | 3,16% |
| Full Time Result | 47,8 | 6,23% | 2,27% |

**La trampa estructural:** vigilancia y margen van juntos, y las cuentas extra
solo ayudan donde YA hay vigilancia. En córners, pasar de 10 a 50 cuentas
ahorra 0,03 puntos, porque solo cotizan 6,5 casas. "Mercado no vigilado +
muchas cuentas" no es una combinación que exista aquí.

### ¿El precio poco vigilado está MAL, o solo caro?

Esta era la pregunta buena, y se contesta comparando lo que perderías contra
un precio PERFECTO (`-margen/(1+margen)`) con lo que se perdió de verdad:

    mercado                casas  margen  esperado   medido   hueco  sigmas
    Total Corners            6.5   8.72%    -8.02%   -7.30%  +0.72%   +0.70
    Asian Handicap          17.7   6.26%    -5.89%  -10.22%  -4.33%   -2.86
    Total Goals             24.7   5.88%    -5.55%   -6.45%  -0.90%   -0.51
    Both Teams To Score     28.4   6.99%    -6.53%   -7.17%  -0.63%   -0.43
    Odd or Even             27.3   6.90%    -6.45%   -6.26%  +0.19%   +1.00
    Full Time Result        47.8   6.01%    -5.67%   -1.98%  +3.69%   +1.24

**Córners: hueco +0,72% a 0,70 sigmas.** El precio del mercado menos vigilado
con consenso medible es exacto. Es caro, no malo. Un modelo mejor no tiene
nada que corregir ahí.

El único hueco real es el hándicap asiático (-4,33%, -2,86 sigmas), y ya está
identificado: líneas hondas, sesgo favorito-marginado. El lado cobrable está
en -1,38% (±4,10).

### Las value bets, cruzadas con la vigilancia

Apostar solo donde la cuota paga más que el consenso de las demás casas:

    mercado               casas  umbral  apuestas  partidos   retorno  sigmas
    Total Corners           6.5   todas      1928        91    -7.30%   -7.10
                                    >0%        47        13    +2.32%   +0.09
                                    >2%        15          (muestra corta)
    Asian Handicap         17.7     >0%      1044       129   -15.08%   -1.63
                                    >2%       506       112    -9.84%   -0.83
                                    >5%       218        77    -6.65%   -0.46
    Total Goals            24.7     >0%      4511       145    -9.21%   -1.14
                                    >2%      1965       140    -6.93%   -0.66
    Both Teams To Score    28.4     >0%       118        50   -20.93%   -1.33
    Full Time Result       47.8     >0%       449       104   +30.18%   +1.38
                                    >2%       147        59    -7.62%   -0.34

**Ni una sola combinación sobrevive.** Los negativos son mayoría y los
positivos son ruido: el +30,18% del 1X2 está a 1,38 sigmas y se da la vuelta
al subir el umbral, que es lo contrario de lo que haría una ventaja real. El
+2,32% de córners son 47 apuestas en 13 partidos.

Y hay una razón de fondo, medida: **las cuotas de distintas casas no son
simultáneas** en esta API (29% de partidos de 1X2 con arbitraje imposible).
El "valor contra el consenso" mide en parte CUÁNDO se capturó el precio, no lo
que piensa la casa. Y engaña en la peor dirección: una cuota vieja parece
generosa justo cuando el mercado se movió en su contra.

### Veredicto de la parte 1

Los mercados poco competidos son **caros pero bien pintados**. Las value bets
contra el consenso **no funcionan en ninguno**, vigilado o no. Las dos mitades
de la idea están medidas y las dos fallan por separado.

---

## PARTE 2 — La herramienta interna

Montada y funcionando de punta a punta. Seis piezas:

    backfill_historico.py    2.004 partidos con 39 estadísticas por equipo
    rasgos.py                70 rasgos sin fuga, con control positivo
    modelo_xgboost.py        gradient boosting, corte TEMPORAL
    evaluar_contra_mercado.py  la puerta: ¿batimos al mercado?
    aporta_algo.py           ¿aporta algo que el precio no lleve?
    gestion_banca.py         Kelly/4 con tope y puerta de error
    boletin.py               la salida: apuesta + casa + cuota + STAKE

### Lo que el modelo aprende de verdad

    objetivo            modelo   base liga   barajado   mejora
    1X2                 0.6301     0.6485     0.6863    +2.84%
    Más de 2.5 goles    0.4935     0.4931     0.5151    -0.07%
    Ambos marcan        0.4925     0.4916     0.5068    -0.17%

Hay señal real en el 1X2: bate claramente al control con los rasgos barajados.
En goles y ambos marcan no hay nada, y el modelo no se lo inventa.

### Lo que decide

168 partidos fuera de muestra con cuotas de 54 casas:

    Brier del mercado : 0.5762
    Brier nuestro     : 0.6166
    diferencia        : -0.0404  (±0.0205)  ->  -1.97 sigmas

El mercado es mejor, y ya casi a dos sigmas. El boletín se niega a emitir
apuestas.

### La pista que murió

Con 89 partidos, mezclar mercado y modelo daba peso óptimo 0,43 y una mejora
del 1,5%. Con 168: peso 0,10, mejora 0,01%, y el cero aparece en el 35% de los
remuestreos en vez del 9%. **El número se movió hacia cero al crecer la
muestra**, que es la firma de un hallazgo falso.

---

## Lo que sigue corriendo, y por qué

- **Cosecha diaria de cuotas.** Caducan a los 28 días; lo que no se guarda se
  pierde. Ya hay 233 partidos con 1X2 frente a los 120 de ayer. Cuesta ~200
  llamadas de 7.500.
- **El backfill grita** cuando una liga vuelve vacía, y guarda igual.

## Lo que falta (actualizado 24/09/2026)

- ~~La Segunda: cero filas.~~ **Resuelto.** El ID bueno es 120775 (ya en
  `LIGAS` de `backfill_historico.py`) y trae 532 partidos -- la liga con
  más datos de las seis. Esta sección se quedó sin actualizar cuando se
  arregló; `buscar_ligas.py` ya no hace falta pero se deja por si aparece
  otro ID roto.
- ~~Alineación, árbitro y tiempo: no se pueden traer hacia atrás.~~ **Era
  falso, nunca se comprobó con datos reales.** Comprobado el 23/09
  (`sondeo_matches.py`, `sondeo_lineups.py`) contra partidos de hace 13
  meses: los tres SÍ están disponibles retroactivamente. Backfill completo
  de los tres. Árbitro es la mejor variable nueva probada en todo el
  proyecto (ver CLAUDE.md, "Árbitro, clima y rotación"); ya es parte del
  modelo de producción.
