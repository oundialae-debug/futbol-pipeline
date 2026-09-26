# Pronósticos Nations League, 26/09/2026

Tema aparte del proyecto de ambos marcan. **Pronóstico = lo más probable según el mercado** (mediana de casas sin margen), que es lo único que nada ha batido en este proyecto. Al lado, nuestro modelo de selecciones con la nota justa de los jugadores y el árbitro. **Cuota mínima** = 1/probabilidad: por debajo no compensa.

Datos: 71 partidos de las 4 selecciones desde 2025 (descartados 5 contra rivales sin jugadores en la API y 1 xG roto).

## England - Spain

Modelo: goles esperados 1.09 - 1.68, marcador más probable 1-1. Córners esperados 8.7. Tarjetas amarillas esperadas 2.1; árbitro Massa, Davide (37 partidos en nuestras ligas, x1.17) -> 2.4. Forma del once: England -0.05, Spain -0.10.

| mercado | pronóstico | prob. mercado | prob. modelo | cuota mínima | cuota mediana | mejor cuota (sin atípicos) | casas |
|---|---|---|---|---|---|---|---|
| 1X2 | **gana Spain** | 48% | 51% | 2.08 | 1.96 | 2.05 | 50 |
| Más/menos 2.5 | **más de 2.5 goles** | 55% | 52% | 1.82 | 1.73 | 1.87 | 35 |
| Ambos marcan | **ambos marcan: sí** | 58% | 54% | 1.73 | 1.61 | 1.67 | 29 |
| Tarjetas | **más de 3.5 tarjetas** | 50% | 25% | 2.00 | 1.85 | 1.85 | 1 |
| Tarjetas | **menos de 4.5 tarjetas** | 68% | 85% | 1.47 | 1.34 | 1.34 | 1 |
| Córners | **más de 8.5 córners** | 55% | 50% | 1.81 | 1.67 | 1.70 | 10 |
| Córners | **menos de 9.5 córners** | 56% | 62% | 1.78 | 1.63 | 1.70 | 11 |
| Goles | **más de 1.5 goles** | 77% | 76% | 1.30 | 1.22 | 1.26 | 35 |
| Goles | **Spain marca primero** | 58% | 61% | 1.71 | 1.67 | 1.87 | 4 |

Once real England: J. Bellingham, B. Saka, H. Kane, E. Anderson, M. Guéhi, J. Trafford, A. Gordon, E. Konsa, M. Lewis-Skelly, O'Reilly, J. Quansah
Once real Spain: Lamine Yamal, Rodri, Pau Cubarsí Paredes, Dani Olmo, Nico Williams, Aymeric Laporte, Ferran Torres, Unai Simón, Fabián Ruiz, Eric García, Marc Cucurella

## Czech Republic - Croatia

Modelo: goles esperados 1.19 - 2.18, marcador más probable 1-2. Córners esperados 9.5. Tarjetas amarillas esperadas 2.2; árbitro Sozza, Simone (37 partidos en nuestras ligas, x0.94) -> 2.0. Forma del once: Czech Republic -0.04, Croatia +0.01.

| mercado | pronóstico | prob. mercado | prob. modelo | cuota mínima | cuota mediana | mejor cuota (sin atípicos) | casas |
|---|---|---|---|---|---|---|---|
| 1X2 | **gana Croatia** | 47% | 60% | 2.14 | 2.02 | 2.12 | 50 |
| Más/menos 2.5 | **más de 2.5 goles** | 52% | 65% | 1.92 | 1.81 | 1.88 | 36 |
| Ambos marcan | **ambos marcan: sí** | 56% | 62% | 1.79 | 1.66 | 1.70 | 28 |
| Tarjetas | **menos de 3.5 tarjetas** | 54% | 82% | 1.84 | 1.70 | 1.70 | 1 |
| Tarjetas | **menos de 4.5 tarjetas** | 72% | 90% | 1.40 | 1.27 | 1.27 | 1 |
| Córners | **más de 8.5 córners** | 59% | 59% | 1.70 | 1.56 | 1.63 | 10 |
| Córners | **menos de 9.5 córners** | 52% | 53% | 1.92 | 1.77 | 1.81 | 11 |
| Goles | **más de 1.5 goles** | 75% | 85% | 1.33 | 1.25 | 1.28 | 35 |
| Goles | **Croatia marca primero** | 57% | 65% | 1.74 | 1.71 | 1.74 | 4 |

Once real Czech Republic: L. Horníček, Adam Karabec, A. Hložek, P. Šulc, Michal Sadílek, Ambros, Macek, Kricfalusi, Štěpán Chaloupek, V. Coufal, R. Hranáč
Once real Croatia: A. Budimir, J. Gvardiol, Luka Modrić, L. Vušković, Martin Baturina, Petar Sučić, I. Perišić, D. Livaković, M. Kovačić, J. Stanišić, Nikola Vlašić

## Cuánto fiarse

Prueba hacia delante del modelo de selecciones: 48 partidos desde oct-2025, cada uno pronosticado solo con los anteriores, contra la tasa de los partidos previos:

- 1X2: +1.91s (acierta el 65%). Ambos marcan: +1.28s. Algo saben, pero no se pueden medir contra el mercado (no hay cuotas históricas de selecciones).
- Más/menos goles (-0.7 a -1.2s), córners (-0.3 a -1.5s; se queda corto, 8.9 predichos contra 9.9 reales) y tarjetas (+0.1 a -2.6s): **peor que la tasa previa**. En totales, el modelo no aporta.
- Tarjetas: solo 1 casa cotiza cada línea (precio poco fiable). El árbitro, en el proyecto de clubes, no mejoró el mercado de tarjetas.
- Ajuste de forma (nota justa) puesto a mano. Las cuotas se cogieron a las 16:54 UTC; pueden moverse con las alineaciones.

