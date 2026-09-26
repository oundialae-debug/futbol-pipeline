# Pronósticos Nations League, 26/09/2026

Tema aparte del proyecto de ambos marcan. Modelo: Poisson ataque/defensa con los 76 partidos de las 4 selecciones desde 2025 (goles y xG promediados), anclado con la calidad de plantilla, más ajuste de forma del once con la nota justa de cada jugador (`notas_jugadores.csv`). Mercado = mediana de casas sin margen.

## England - Spain

Goles esperados: 1.18 - 1.62 (sin ajuste de forma 1.17 - 1.69). Forma del once: England -0.02, Spain -0.10.

| | modelo | sin forma | mercado (sin margen) | cuota justa del modelo |
|---|---|---|---|---|
| gana England | 27.9% | 26.5% | 27.8% | 3.58 |
| empate | 24.6% | 24.1% | 27.5% | 4.06 |
| gana Spain | 47.4% | 49.5% | 44.7% | 2.11 |
| ambos marcan: sí | 55.6% | 56.1% | 59.0% | 1.80 |

Once probable England: J. Bellingham, H. Kane, E. Anderson, D. Rice, M. Rogers, M. Guéhi, J. Pickford, A. Gordon, E. Konsa, Djed Spence, John Stones
Once probable Spain: Lamine Yamal, Rodri, Pau Cubarsí Paredes, Álex Baena, Dani Olmo, Aymeric Laporte, Unai Simón, Fabián Ruiz, Pedro Porro, Mikel Oyarzabal, Marc Cucurella

## Czech Republic - Croatia

Goles esperados: 1.26 - 2.03 (sin ajuste de forma 1.27 - 2.07). Forma del once: Czech Republic -0.05, Croatia -0.06.

| | modelo | sin forma | mercado (sin margen) | cuota justa del modelo |
|---|---|---|---|---|
| gana Czech Republic | 23.4% | 23.2% | 26.7% | 4.27 |
| empate | 21.4% | 21.1% | 27.1% | 4.68 |
| gana Croatia | 55.2% | 55.6% | 46.2% | 1.81 |
| ambos marcan: sí | 62.2% | 62.9% | 56.3% | 1.61 |

Once probable Czech Republic: M. Kovář, L. Krejčí, P. Schick, Tomáš Souček, P. Šulc, Lukáš Červ, Michal Sadílek, Jaroslav Zelený, Štěpán Chaloupek, V. Coufal, R. Hranáč
Once probable Croatia: J. Gvardiol, Luka Modrić, Martin Baturina, Petar Sučić, I. Perišić, D. Livaković, Josip Šutalo, M. Kovačić, J. Stanišić, Marin Pongračić, Nikola Vlašić

## Cuánto fiarse

Prueba hacia delante (26/09): cada partido de las 4 selecciones desde oct-2025 (53) pronosticado solo con los anteriores.

- 1X2: Brier 0.540 contra 0.627 de las frecuencias (+1.37s), acierta el 64%. Algo sabe, pero la mayoría eran partidos fáciles contra selecciones pequeñas.
- Ambos marcan: Brier 0.514 contra 0.498 de la tasa base (-0.40s). **No bate a la tasa base**: en ambos marcan este modelo no aporta.
- No hay cuotas históricas de selecciones para medirlo contra el mercado. El ajuste de forma (B_FORMA) está puesto a mano, no calibrado.

