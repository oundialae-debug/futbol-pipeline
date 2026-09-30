# app_apostador (2yellow)

## Idioma (petición del usuario, 30/09/2026)

- **Con el usuario, siempre en español**: mensajes, respuestas en los
  comentarios del lienzo, preguntas y resúmenes.
- **El proyecto, en inglés**: textos de la app, pantallas, etiquetas y todo
  lo que ve el usuario final de 2yellow.

## Forma de trabajar

- Esta carpeta es propia: fuera de ella solo se lee o se copia, no se modifica.
- Cada cambio se apunta en `BITACORA.md` (de esta carpeta), en el mismo commit.
- Ninguna llamada a la API de Highlightly sin un sí explícito del usuario para
  esa llamada (regla del `CLAUDE.md` de la raíz).
- Cuando el usuario dice «no empieces hasta que diga empieza ya», solo se
  contestan y apuntan sus comentarios. Cada cambio pedido se aplica en todas
  las pantallas donde encaje.
- **Aspecto de app ya publicada (30/09/2026):** nada de textos provisionales en
  pantallas, vídeos o imágenes («[odds from API]», «Forecast soon», «Referee
  not named»...). Lo que falta se quita o se calcula con nuestro modelo; nunca
  se inventan cuotas ni datos de terceros.
- Dónde lo dejamos y cómo regenerar: final de `BITACORA.md`.
