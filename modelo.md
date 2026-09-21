# El modelo

1753 partidos utilizables de 2004 en el histórico. Corte temporal: se entrena con los 1314 más viejos y se valida con los 439 más nuevos.

> El rival de este modelo no es el azar, es el mercado. Un Brier bueno no sirve de nada si el de la casa es mejor.

| Objetivo | Brier modelo | Brier base liga | Brier barajado | mejora sobre base |
|---|---|---|---|---|
| 1X2 (local / empate / visitante) | 0.6271 | 0.6485 | 0.6835 | +3.30% |
| Más de 2.5 goles | 0.4993 | 0.4931 | 0.5152 | -1.25% |
| Ambos marcan | 0.4938 | 0.4916 | 0.5130 | -0.43% |
| Más de 9.5 córners | 0.5207 | 0.5015 | 0.5310 | -3.83% |
| Más de 4.5 tarjetas | 0.4319 | 0.4306 | 0.4558 | -0.30% |

## Cómo leer esto

**Brier** es el error medio al cuadrado de la probabilidad. Más bajo, mejor. Un modelo que dijera siempre la frecuencia de la liga saca la columna *base liga*.

**Barajado** entrena el mismo modelo con los rasgos revueltos. Conserva el formato y destruye la señal. Si el modelo no le saca ventaja clara, no ha aprendido fútbol: ha aprendido la forma del fichero.

## Lo que este fichero NO dice

No dice si hay dinero. Para eso hace falta comparar contra la probabilidad del MERCADO sobre los mismos partidos, y que la ventaja supere al margen. Eso es `evaluar_contra_mercado.py`.

