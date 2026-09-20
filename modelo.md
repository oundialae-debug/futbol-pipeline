# El modelo

1753 partidos utilizables de 2004 en el histórico. Corte temporal: se entrena con los 1314 más viejos y se valida con los 439 más nuevos.

> El rival de este modelo no es el azar, es el mercado. Un Brier bueno no sirve de nada si el de la casa es mejor.

| Objetivo | Brier modelo | Brier base liga | Brier barajado | mejora sobre base |
|---|---|---|---|---|
| 1X2 (local / empate / visitante) | 0.6301 | 0.6485 | 0.6863 | +2.84% |
| Más de 2.5 goles | 0.4935 | 0.4931 | 0.5151 | -0.07% |
| Ambos marcan | 0.4925 | 0.4916 | 0.5068 | -0.17% |

## Cómo leer esto

**Brier** es el error medio al cuadrado de la probabilidad. Más bajo, mejor. Un modelo que dijera siempre la frecuencia de la liga saca la columna *base liga*.

**Barajado** entrena el mismo modelo con los rasgos revueltos. Conserva el formato y destruye la señal. Si el modelo no le saca ventaja clara, no ha aprendido fútbol: ha aprendido la forma del fichero.

## Lo que este fichero NO dice

No dice si hay dinero. Para eso hace falta comparar contra la probabilidad del MERCADO sobre los mismos partidos, y que la ventaja supere al margen. Eso es `evaluar_contra_mercado.py`.

