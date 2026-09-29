# Bitácora de app_apostador

La bitácora general (`BITACORA.md` en la raíz) no se toca: el usuario pidió
que esta carpeta sea propia y que fuera de ella solo se copie. Lo de esta
carpeta se apunta aquí.

## 29/09/2026: maquetas explicadas para el público

- **Qué:** seis pantallas nuevas (`project/*.dc.html`) de una app de datos de
  fútbol para apostadores, publicadas en el lienzo
  https://claude.ai/artifact/FBTarsYtUpRSFEYTpVSvaG.
- **Por qué:** petición del usuario. Las maquetas del 29/09 estaban bien,
  pero alguien de fuera del proyecto no entendía los datos (Elo, Brier,
  sigmas, "fuerza real").
- **Cómo:** `generar_datos.py` lee `data/historico_partidos.csv`,
  `calendario.csv`, `historico_arbitro_clima.csv` y
  `historico_h2h_profundo.csv` y escribe `datos.json`. Sin API, sin
  descargas.
- **Diferencias con la maqueta anterior:** Sevilla 15.º por nivel (antes
  18.º), Málaga 17.º (antes 11.º), media de tarjetas 4,52 (antes 5,28).
  Detalle en `README.md`.
- **Ficheros:** `app_apostador/` entero. Nada fuera.
