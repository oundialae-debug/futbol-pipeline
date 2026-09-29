# app_apostador: maquetas de app explicadas para cualquier apostador

Carpeta propia. No modifica nada fuera de ella: solo **lee** `data/`.

Lienzo con las pantallas: https://claude.ai/artifact/FBTarsYtUpRSFEYTpVSvaG
(privado hasta que se comparta desde su menú Compartir).

## El problema que resuelve

Las maquetas del 29/09 ("Veredicto" LaLiga y registro) tenían buenos datos,
pero hablaban el idioma del proyecto: "fuerza real", "Elo", "Brier", "σ",
"valor > 8%", "goles + asistencias medios por titular: 15,6". Quien solo
busca datos para su pronóstico no sabe qué hacer con eso.

## Reglas que siguen estas pantallas

1. **Todo % se lee como "de cada 100 partidos".** Nunca un % suelto.
2. **Cada probabilidad lleva su cuota justa** (100 ÷ %). El apostador piensa
   en cuotas, no en probabilidades.
3. **Una calculadora "¿Te pagan bien?"** compara la cuota de su casa con la
   justa y lo dice en euros: "a la larga perderías unos 7 € de cada 100".
4. **Etiqueta de fiabilidad en cada dato**: "Dato sólido" (cientos de
   partidos) o "Puede ser azar" (10-20 partidos).
5. **Sin jerga**: "Elo" pasa a "nivel", explicado en una frase; "1X2", "más
   de 2,5" y "ambos marcan" se explican con un ejemplo de esta jornada.
6. **Honestidad**: se dice lo que los números NO saben (bajas, alineaciones)
   y que las casas suelen afinar más. Es lo que el proyecto ha medido.

## Pantallas (`project/`)

| fichero | pantalla |
|---|---|
| `Main.dc.html` | Cómo leer los datos: las cuatro ideas básicas |
| `Jornada.dc.html` | Jornada 8 de LaLiga: 1-X-2 con % y cuota justa, y una frase por partido |
| `Partido.dc.html` | Real Madrid – Villarreal: calculadora, nivel, forma, goles, cara a cara |
| `Nivel.dc.html` | ¿Suerte o nivel?: tabla frente a nivel, con veredicto por equipo |
| `Arbitros.dc.html` | Árbitros y tarjetas, con % de partidos con 5 o más |
| `Glosario.dc.html` | Palabras explicadas, con ejemplos |

## Datos

`generar_datos.py` los calcula en local, sin API, y escribe `datos.json`.
Las pantallas copian esos números.

- Nivel = el Elo de `scripts/rasgos.py` (K=20, local +60), sobre los
  1.589 partidos de LaLiga del histórico.
- Probabilidad 1-X-2: logística ordenada sobre la diferencia de nivel,
  ajustada con 1.209 partidos (sin la primera temporada, en la que el Elo
  arranca de cero). Calibración del local: dice 20% → pasa 22%; 38% → 35%;
  52% → 49%; 67% → 73%; 82% → 85%.
- Árbitros: temporadas 2025/26 y 2026/27, 395 partidos, mínimo 15 por
  árbitro. "Diferencia clara" = 2 sigmas o más frente a la media de LaLiga.

**Cambian respecto a la maqueta anterior**: allí el Sevilla salía 18.º por
nivel y el Málaga 11.º; con el Elo del proyecto salen 15.º y 17.º. La media
de tarjetas era 5,28 y aquí sale 4,52 (395 partidos con árbitro y
tarjetas de `historico_partidos.csv`). No se ha averiguado de dónde salían las
cifras anteriores. Se usan las recalculadas porque se pueden reproducir.

**Fuera**: "nivel del once" (goles + asistencias de los titulares la
temporada pasada). No se ha recalculado, así que no se muestra.
