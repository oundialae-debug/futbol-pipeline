"""
Evaluación y aprendizaje de los pronósticos de selecciones (26/09/2026).
Tema aparte del proyecto de ambos marcan.

Para cada partido del registro (registro_pronosticos.csv) ya jugado, toma el
ÚLTIMO pronóstico hecho ANTES del inicio (nada de mirar al futuro) y lo cruza
con el resultado real (partidos.csv y estadisticas_partido.csv). Por mercado:

  - Brier del modelo, del mercado y de la mezcla final, y el modelo contra el
    mercado en sigmas, emparejado partido a partido (+2s haría falta para
    decir que el modelo sabe más que las casas).
  - APRENDE el peso de la mezcla: w entre 0 y 1 que minimiza el Brier de
    w*modelo + (1-w)*mercado en los partidos evaluados. Solo se usa (y se
    guarda como aprendido) con MIN_PARTIDOS o más; con menos, un número así
    se mueve con un solo resultado (ver CLAUDE.md principal: "Si al crecer la
    muestra el número se mueve hacia cero, era falso").
Escribe data/selecciones/pesos_mezcla.json (lo lee pronostico_selecciones.py)
y modelos/selecciones/evaluacion.md.

Tarjetas: el resultado se cuenta como amarillas + rojas; las casas pueden
contar distinto (roja = 2). Tomarlo con cautela.
"""
import json
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/selecciones")
from pronostico_selecciones import MERCADOS, PESOS_INICIALES, RUTA_PESOS, RUTA_REGISTRO

MIN_PARTIDOS = 30
CARPETA = "data/selecciones"
SALIDA = "modelos/selecciones/evaluacion.md"


def resultados():
    p = pd.read_csv(f"{CARPETA}/partidos.csv")
    p = p[p.terminado & p.goles_l.notna()].copy()
    e = pd.read_csv(f"{CARPETA}/estadisticas_partido.csv")
    e["valor"] = pd.to_numeric(e.valor, errors="coerce")
    tot = lambda nombre: e[e.estadistica == nombre].groupby("match_id").valor.sum(min_count=2)
    p["corners"] = p.match_id.map(tot("Corners"))
    p["tarjetas"] = p.match_id.map(tot("Yellow cards")) + p.match_id.map(tot("Red cards")).fillna(0)
    gl, gv, g = p.goles_l, p.goles_v, p.goles_l + p.goles_v
    y = pd.DataFrame({"match_id": p.match_id,
                      "1": (gl > gv).astype(float), "X": (gl == gv).astype(float), "2": (gl < gv).astype(float),
                      "mas_2.5": (g > 2.5).astype(float), "btts": ((gl > 0) & (gv > 0)).astype(float),
                      "mas_1.5": (g > 1.5).astype(float), "mas_3.5": (g > 3.5).astype(float),
                      "corners_mas_8.5": np.where(p.corners.notna(), p.corners > 8.5, np.nan),
                      "corners_mas_9.5": np.where(p.corners.notna(), p.corners > 9.5, np.nan),
                      "tarjetas_mas_3.5": np.where(p.tarjetas.notna(), p.tarjetas > 3.5, np.nan),
                      "tarjetas_mas_4.5": np.where(p.tarjetas.notna(), p.tarjetas > 4.5, np.nan),
                      # quién marca primero no está en /statistics: sin evaluar por ahora
                      "primero_local": np.nan})
    return y.set_index("match_id")


def main():
    if not os.path.exists(RUTA_REGISTRO):
        print("Sin registro de pronósticos todavía.")
        return
    r = pd.read_csv(RUTA_REGISTRO)
    r["generado"] = pd.to_datetime(r.generado, utc=True)
    r["inicio"] = pd.to_datetime(r.fecha_partido, utc=True, errors="coerce")
    r = r[r.inicio.isna() | (r.generado < r.inicio)]
    ultimo = r.sort_values("generado").groupby("match_id").tail(1).set_index("match_id")
    y = resultados()
    ev = ultimo.join(y, how="inner", rsuffix="_real")
    L = ["# Evaluación de los pronósticos de selecciones", "",
         f"{len(ev)} partidos jugados con pronóstico previo (de {len(ultimo)} pronosticados). Se toma el "
         "último pronóstico hecho ANTES del inicio. Brier: más bajo es mejor. Sigmas: modelo contra "
         "mercado, emparejado por partido (+ = el modelo mejor; hace falta +2 para creérselo). El peso "
         f"se aprende con {MIN_PARTIDOS} partidos o más.", "",
         "| mercado | n | Brier modelo | Brier mercado | modelo vs mercado | peso óptimo | en uso |",
         "|---|---|---|---|---|---|---|"]
    pesos = {}
    for k in MERCADOS:
        if k not in ev or f"mod_{k}" not in ev:
            continue
        d = ev[[f"mod_{k}", f"mkt_{k}", k]].dropna()
        n = len(d)
        if n == 0:
            L.append(f"| {k} | 0 | - | - | - | - | {PESOS_INICIALES.get(k, 0.0):.2f} (inicial) |")
            continue
        yy, pm, pk = d[k].values, d[f"mod_{k}"].values, d[f"mkt_{k}"].values
        bm, bk = (pm - yy) ** 2, (pk - yy) ** 2
        dif = bk - bm
        sig = dif.mean() / (dif.std(ddof=1) / np.sqrt(n)) if n > 2 and dif.std(ddof=1) > 0 else float("nan")
        rejilla = np.linspace(0, 1, 21)
        brier_w = [(((w * pm + (1 - w) * pk) - yy) ** 2).mean() for w in rejilla]
        w_opt = float(rejilla[int(np.argmin(brier_w))])
        aprendido = n >= MIN_PARTIDOS
        pesos[k] = {"peso": w_opt, "n": n, "aprendido": aprendido, "sigmas_modelo_vs_mercado": round(sig, 2)}
        en_uso = f"{w_opt:.2f} (aprendido)" if aprendido else f"{PESOS_INICIALES.get(k, 0.0):.2f} (inicial)"
        L.append(f"| {k} | {n} | {bm.mean():.4f} | {bk.mean():.4f} | {sig:+.2f}s | {w_opt:.2f} | {en_uso} |")
    json.dump(pesos, open(RUTA_PESOS, "w"), indent=1)
    L += ["", "Mientras n sea pequeño, el peso óptimo salta con cada resultado: no leer nada en él hasta "
          f"{MIN_PARTIDOS}. Un modelo que de verdad sepa más que las casas lo mostrará con sigmas "
          "positivos que se mantienen al crecer n; si se van hacia cero, no sabía nada.", ""]
    open(SALIDA, "w").write("\n".join(L) + "\n")
    print(f"Evaluados {len(ev)} partidos. Pesos: " +
          ", ".join(f"{k} {v['peso']:.2f}{'*' if v['aprendido'] else ''} (n={v['n']})" for k, v in pesos.items()))


if __name__ == "__main__":
    main()
