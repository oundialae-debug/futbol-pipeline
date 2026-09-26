# Pronósticos de selecciones (26/09/2026 19:47 UTC)

Tema aparte del proyecto de ambos marcan. Por mercado: **modelo** (selecciones + nota justa de los jugadores + árbitro), **mercado** (mediana de casas sin margen) y **final** (mezcla con el peso que se aprende de los partidos ya jugados, ver `evaluacion.md`). Pronóstico = el lado más probable según final. **Cuota mínima** = 1/probabilidad final: por debajo no compensa.

Datos del modelo: 71 partidos de selecciones desde 2025 (descartados 5 contra rivales sin jugadores en la API y 1 xG roto).

## England - Spain (2026-09-26 18:45 UTC)

Goles esperados 1.09 - 1.68, marcador más probable 1-1. Córners esperados 8.7. Amarillas esperadas 2.4 (árbitro Massa, Davide, 37 partidos en nuestras ligas, x1.17). Forma del once: England -0.05, Spain -0.10.

| mercado | pronóstico | final | modelo | mercado | cuota mínima | cuota mediana | mejor cuota | casas |
|---|---|---|---|---|---|---|---|---|
| 1X2 | **gana Spain** | 50% | 51% | 48% | 2.02 | 1.96 | 2.05 | 50 |
| Más/menos 2.5 | **más de 2.5 goles** | 55% | 52% | 55% | 1.82 | 1.73 | 1.87 | 35 |
| Ambos marcan | **ambos marcan: sí** | 56% | 54% | 58% | 1.79 | 1.61 | 1.67 | 29 |
| Tarjetas | **más de 3.5 tarjetas** | 50% | 25% | 50% | 2.00 | 1.85 | 1.85 | 1 |
| Tarjetas | **menos de 4.5 tarjetas** | 68% | 85% | 68% | 1.47 | 1.34 | 1.34 | 1 |
| Córners | **más de 8.5 córners** | 55% | 50% | 55% | 1.81 | 1.67 | 1.70 | 10 |
| Córners | **menos de 9.5 córners** | 56% | 62% | 56% | 1.78 | 1.63 | 1.70 | 11 |
| Goles | **más de 1.5 goles** | 77% | 76% | 77% | 1.30 | 1.22 | 1.26 | 35 |
| Goles | **Spain marca primero** | 58% | 61% | 58% | 1.71 | 1.67 | 1.87 | 4 |

Once real England: J. Bellingham, B. Saka, H. Kane, E. Anderson, M. Guéhi, J. Trafford, A. Gordon, E. Konsa, M. Lewis-Skelly, O'Reilly, J. Quansah
Once real Spain: Lamine Yamal, Rodri, Pau Cubarsí Paredes, Dani Olmo, Nico Williams, Aymeric Laporte, Ferran Torres, Unai Simón, Fabián Ruiz, Eric García, Marc Cucurella

## Czech Republic - Croatia (2026-09-26 18:45 UTC)

Goles esperados 1.19 - 2.18, marcador más probable 1-2. Córners esperados 9.5. Amarillas esperadas 2.0 (árbitro Sozza, Simone, 37 partidos en nuestras ligas, x0.94). Forma del once: Czech Republic -0.04, Croatia +0.01.

| mercado | pronóstico | final | modelo | mercado | cuota mínima | cuota mediana | mejor cuota | casas |
|---|---|---|---|---|---|---|---|---|
| 1X2 | **gana Croatia** | 53% | 60% | 47% | 1.88 | 2.02 | 2.12 | 50 |
| Más/menos 2.5 | **más de 2.5 goles** | 52% | 65% | 52% | 1.92 | 1.81 | 1.88 | 36 |
| Ambos marcan | **ambos marcan: sí** | 59% | 62% | 56% | 1.70 | 1.66 | 1.70 | 28 |
| Tarjetas | **menos de 3.5 tarjetas** | 54% | 82% | 54% | 1.84 | 1.70 | 1.70 | 1 |
| Tarjetas | **menos de 4.5 tarjetas** | 72% | 90% | 72% | 1.40 | 1.27 | 1.27 | 1 |
| Córners | **más de 8.5 córners** | 59% | 59% | 59% | 1.70 | 1.56 | 1.63 | 10 |
| Córners | **menos de 9.5 córners** | 52% | 53% | 52% | 1.92 | 1.77 | 1.81 | 11 |
| Goles | **más de 1.5 goles** | 75% | 85% | 75% | 1.33 | 1.25 | 1.28 | 35 |
| Goles | **Croatia marca primero** | 57% | 65% | 57% | 1.74 | 1.71 | 1.74 | 4 |

Once real Czech Republic: L. Horníček, Adam Karabec, A. Hložek, P. Šulc, Michal Sadílek, Ambros, Macek, Kricfalusi, Štěpán Chaloupek, V. Coufal, R. Hranáč
Once real Croatia: A. Budimir, J. Gvardiol, Luka Modrić, L. Vušković, Martin Baturina, Petar Sučić, I. Perišić, D. Livaković, M. Kovačić, J. Stanišić, Nikola Vlašić

## Cuánto fiarse

- Pesos de la mezcla modelo/mercado: 1 0.50, X 0.50, 2 0.50, btts 0.50 (el resto 0 = manda el mercado). Se reaprenden en `evaluacion.md` con los partidos jugados.
- Tarjetas: pocas casas y probablemente cuentan distinto (roja = 2); el modelo cuenta amarillas.
- El ajuste de forma (nota justa) está puesto a mano (B_FORMA = 0.5).

