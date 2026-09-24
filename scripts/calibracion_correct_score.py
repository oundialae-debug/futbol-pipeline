"""
¿ESTÁ CALIBRADO EL MERCADO DE MARCADOR EXACTO (CORRECT SCORE)?

Pregunta del usuario: Correct Score tiene decenas de resultados posibles,
casi todos de probabilidad baja -- si el mercado se equivoca en algún
sitio, sería aquí. `censo_margenes.py` excluyó este mercado del cálculo
de margen a propósito (el conjunto de resultados cotizados es incompleto
-- no todas las casas ponen precio a los marcadores más raros -- y sumar
1/cuota sobre un conjunto incompleto da un margen absurdamente bajo que
parece una ganga sin serlo). Pero calibración no tiene ese problema: no
hace falta que el conjunto esté completo, solo comparar cada línea contra
lo que pasó de verdad, exactamente como calibracion_mercado.py.

192.932 filas de cuotas de Correct Score en data/cuotas_cosechadas.csv
(301 partidos), nunca antes usadas -- el clasificador de familias de
backtest_valor.py no reconoce "Correct Score" y las descarta en silencio.
251 de esos partidos ya tienen resultado conocido en historico_partidos.csv.

CÓMO SE MIDE
------------
Probabilidad CRUDA (1/cuota, mediana entre casas por partido+marcador) --
NO desmarginada, porque desmarginar exige un conjunto completo que aquí no
se tiene. Esto es conservador a nuestro favor: la probabilidad cruda ya
lleva el margen de la casa metido dentro, así que la frecuencia real
DEBERÍA salir por debajo de lo que dice la cuota. Si en algún tramo sale
igual o por encima, eso sí sería raro -- no solo "sin margen", sino con el
mercado literalmente equivocado en la dirección que nos interesa.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timezone

RUTA_CUOTAS = "data/cuotas_cosechadas.csv"
RUTA_HISTORICO = "data/historico_partidos.csv"
RUTA_INFORME = "calibracion_correct_score.md"


def main():
    cc = pd.read_csv(RUTA_CUOTAS)
    cs = cc[cc["mercado"].astype(str).str.startswith("Correct Score")].copy()
    print(f"{len(cs)} filas de Correct Score, {cs.match_id.nunique()} partidos")

    partes = cs["lado"].astype(str).str.split(" : ", expand=True)
    cs["gl_linea"] = pd.to_numeric(partes[0], errors="coerce")
    cs["gv_linea"] = pd.to_numeric(partes[1], errors="coerce")
    cs = cs.dropna(subset=["gl_linea", "gv_linea", "cuota"])
    cs = cs[cs["cuota"] > 1]

    hist = pd.read_csv(RUTA_HISTORICO)[["match_id", "liga", "goles_l", "goles_v"]].dropna()
    cs = cs.merge(hist, on="match_id", how="inner")
    print(f"{len(cs)} filas tras cruzar con resultado conocido, "
          f"{cs.match_id.nunique()} partidos")

    # mediana de cuota entre casas para cada partido+marcador -- consenso
    # crudo, sin desmarginar (ver docstring: aquí no se puede desmarginar)
    u = cs.groupby(["match_id", "liga", "gl_linea", "gv_linea"]).agg(
        cuota_mediana=("cuota", "median"), casas=("casa", "nunique"),
        goles_l=("goles_l", "first"), goles_v=("goles_v", "first"),
    ).reset_index()
    u["prob_cruda"] = 1 / u["cuota_mediana"]
    u["acierto"] = ((u["gl_linea"] == u["goles_l"]) & (u["gv_linea"] == u["goles_v"])).astype(float)

    print(f"\n{len(u)} pares partido+marcador únicos (consenso ya calculado)")
    print(f"aciertos reales: {int(u['acierto'].sum())} de {len(u)} filas "
          f"({u['acierto'].mean()*100:.2f}%)")
    print(f"rango de probabilidad cruda: {u['prob_cruda'].min()*100:.2f}% a "
          f"{u['prob_cruda'].max()*100:.2f}%, mediana {u['prob_cruda'].median()*100:.2f}%")

    # tramos ajustados al rango real -- Correct Score vive casi entero por
    # debajo del 20%, tramos anchos como calibracion_mercado.md (0-20-30...)
    # meterian todo en un solo cajón y no dirian nada.
    tramos = [0, .02, .04, .06, .08, .10, .13, .17, .22, .30, 1.0]
    u["tramo"] = pd.cut(u["prob_cruda"], tramos)
    g = u.groupby("tramo", observed=True).agg(
        n=("acierto", "size"), dice=("prob_cruda", "mean"), pasa=("acierto", "mean"))
    g = g[g["n"] >= 20]          # no dar tramos con muestra minuscula
    g["sesgo"] = (g["pasa"] - g["dice"]) * 100
    g["error"] = np.sqrt(g["pasa"] * (1 - g["pasa"]) / g["n"]) * 100
    g["sigmas"] = np.where(g["error"] > 0, g["sesgo"] / g["error"], 0)

    print("\nTramo | dice | pasa | n | sesgo | sigmas")
    for tramo, f in g.iterrows():
        print(f"  {str(tramo):15s} {f['dice']*100:5.1f}%  {f['pasa']*100:5.1f}%  "
              f"n={int(f['n']):4d}  {f['sesgo']:+.2f}pts  {f['sigmas']:+.2f}s")

    lineas = [
        f"# Calibración de Correct Score -- "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"{len(u)} pares partido+marcador ({u['match_id'].nunique()} partidos "
        "ya jugados) de data/cuotas_cosechadas.csv -- nunca antes analizado, "
        "excluido de censo_margenes.py por el problema de conjunto "
        "incompleto (no todas las casas cotizan todos los marcadores).\n",
        "**Probabilidad CRUDA (1/cuota mediana), NO desmarginada** -- no se "
        "puede desmarginar sin un conjunto completo. Esto favorece encontrar "
        "sesgo: la cruda ya lleva el margen dentro, así que lo normal es que "
        "la frecuencia real quede POR DEBAJO. Si algún tramo iguala o supera "
        "lo que dice la cuota, es la señal que se busca.\n",
        f"Acierto global: {u['acierto'].mean()*100:.2f}% de {len(u)} filas.\n",
        "| Dice (cruda) | Pasa de verdad | Casos | Sesgo | Sigmas |",
        "|---|---|---|---|---|",
    ]
    for tramo, f in g.iterrows():
        lineas.append(f"| {f['dice']*100:.1f}% | {f['pasa']*100:.1f}% | "
                      f"{int(f['n'])} | {f['sesgo']:+.2f} pts | {f['sigmas']:+.2f} |")

    peor = g["sigmas"].abs().max() if len(g) else 0
    lineas.append("")
    if peor < 2:
        lineas.append(f"**Ningún tramo se desvía más de {peor:.2f} sigmas** "
                      "incluso usando la probabilidad CRUDA (sin quitar "
                      "margen) -- si ni así hay sesgo, con la de verdad "
                      "(que es menor) hay todavía menos margen de maniobra. "
                      "Correct Score no es una grieta.\n")
    else:
        tramo = g["sigmas"].abs().idxmax()
        lineas.append(f"**El tramo {tramo} se desvía "
                      f"{g.loc[tramo, 'sigmas']:+.2f} sigmas** "
                      f"({g.loc[tramo, 'sesgo']:+.2f} puntos, n={int(g.loc[tramo, 'n'])}) "
                      "incluso con probabilidad cruda -- esto SÍ merece mirarse "
                      "con más muestra antes de nada, la dirección importa: "
                      "si 'pasa' > 'dice' es al revés de lo esperado (el "
                      "margen debería hacer que pase MENOS, no más).\n")

    with open(RUTA_INFORME, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"\nEscrito {RUTA_INFORME}")


if __name__ == "__main__":
    main()
