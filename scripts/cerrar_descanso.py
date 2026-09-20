"""
CIERRE DEL REGISTRO DEL DESCANSO: quién acertó, el modelo o el mercado.

El registro anota, partido a partido, lo que dijo el modelo y lo que decía el
consenso de las casas en el descanso. Esto va después: busca el resultado
final de cada partido y puntúa las dos predicciones con el mismo rasero.

La medida es el BRIER SCORE, que es sencillo: (probabilidad - resultado)^2,
donde el resultado es 1 si el Over salió y 0 si no. Cuanto más bajo, mejor.
Comparar el Brier del modelo contra el del mercado es la única pregunta que
importa: acertar mucho no sirve de nada si el mercado acierta igual, porque
entonces no hay nada que ganarle.

Las líneas enteras que acaban en empate (push) se apartan: no son ni acierto
ni fallo, el dinero se devuelve, y meterlas en la puntuación la ensucia.

También calcula lo que habría pasado apostando 1 unidad a cada Over con valor
positivo. Eso NO es una recomendación: con pocas observaciones el resultado
está dominado por la suerte, y se imprime junto a su propio margen de error
para que se vea hasta qué punto no dice nada todavía.
"""
import os
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_LOG = "data/registro_descanso.csv"
RUTA_INFORME = "cierre_descanso.md"
EV_SOSPECHOSO = 0.20


def pedir(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception:
        return None
    time.sleep(0.3)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def resultado_final(match_id):
    """Total de tarjetas del partido entero, contando los eventos igual que
    los contó el comparador en el descanso. Devuelve None si el partido no ha
    terminado: puntuar un partido a medias sería contar solo parte."""
    datos = pedir(f"/matches/{match_id}")
    if not datos:
        return None, None
    m = datos[0] if isinstance(datos, list) else datos
    estado = ((m.get("state") or {}).get("description") or "").lower()
    if "finish" not in estado and "ended" not in estado and "ft" != estado.strip():
        return None, estado
    eventos = m.get("events") or []
    total = len([e for e in eventos if e.get("type") in ("Yellow Card", "Red Card")])
    return total, estado


def brier(prob, resultado):
    return float(np.mean((np.asarray(prob) - np.asarray(resultado)) ** 2))


def main():
    if not os.path.exists(RUTA_LOG):
        print("No hay registro que cerrar")
        return
    log = pd.read_csv(RUTA_LOG)
    if log.empty:
        print("El registro está vacío")
        return

    print(f"{len(log)} observaciones sobre {log['match_id'].nunique()} partidos")

    finales, estados = {}, {}
    for mid in log["match_id"].unique():
        total, estado = resultado_final(int(mid))
        finales[mid], estados[mid] = total, estado
        nombre = log[log["match_id"] == mid]["partido"].iloc[0]
        print(f"  {nombre}: {'sin terminar (' + str(estado) + ')' if total is None else str(total) + ' tarjetas'}")

    log["total_final"] = log["match_id"].map(finales)
    cerrados = log[log["total_final"].notna()].copy()
    if cerrados.empty:
        print("\nNingún partido ha terminado todavía -- nada que puntuar")
        return

    cerrados["over"] = (cerrados["total_final"] > cerrados["linea"]).astype(int)
    cerrados["push"] = (cerrados["total_final"] == cerrados["linea"])
    puntuables = cerrados[~cerrados["push"]].copy()

    bm = brier(puntuables["prob_modelo"], puntuables["over"])
    bc = brier(puntuables["prob_mercado"], puntuables["over"])
    base = puntuables["over"].mean()
    bb = brier([base] * len(puntuables), puntuables["over"])

    lineas = [
        f"# Cierre del registro del descanso -- "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"{len(cerrados)} observaciones cerradas sobre "
        f"{cerrados['match_id'].nunique()} partidos terminados "
        f"({int(cerrados['push'].sum())} empates apartados).\n",
        "## Quién acierta más\n",
        "| | Brier | Frente a la tasa base |",
        "|---|---|---|",
        f"| Modelo | {bm:.4f} | {(bb-bm)/bb*100:+.1f}% |",
        f"| Mercado | {bc:.4f} | {(bb-bc)/bb*100:+.1f}% |",
        f"| Tasa base ({base*100:.0f}% Over) | {bb:.4f} | — |\n",
    ]
    if bm < bc:
        lineas.append(f"El modelo puntúa mejor que el mercado por {bc-bm:.4f}. "
                      "Con esta muestra eso no demuestra ventaja: hace falta que "
                      "aguante durante semanas.\n")
    else:
        lineas.append(f"**El mercado puntúa mejor que el modelo** por {bm-bc:.4f}. "
                      "Mientras esto siga así no hay nada que apostar: el modelo "
                      "no sabe más que la casa.\n")

    # Lo que habría dado apostar al Over cuando el modelo veía valor
    apuestas = puntuables[(puntuables["ev"] > 0) & (puntuables["ev"] <= EV_SOSPECHOSO)].copy()
    if not apuestas.empty:
        apuestas["retorno"] = np.where(apuestas["over"] == 1, apuestas["mejor_cuota"] - 1, -1.0)
        n = len(apuestas)
        media = apuestas["retorno"].mean()

        # El error hay que calcularlo AGRUPANDO POR PARTIDO. Las líneas de un
        # mismo partido no son apuestas independientes: si el partido se va de
        # tarjetas, el Over entra en todas a la vez. Tratarlas como 31 apuestas
        # sueltas cuando son 9 partidos infla la muestra y encoge el margen de
        # error, que es justo el número que dice si el resultado significa algo.
        por_partido = apuestas.groupby("match_id")["retorno"].sum()
        m = len(por_partido)
        error = (por_partido.std(ddof=1) * np.sqrt(m) / n) if m > 1 else float("nan")

        mayor = por_partido.abs().max()
        parte_mayor = mayor / abs(apuestas["retorno"].sum()) if apuestas["retorno"].sum() else 0

        lineas += [
            "## Si se hubiera apostado\n",
            f"{n} apuestas de 1 unidad al Over, solo donde el modelo veía valor "
            f"positivo y no disparatado (hasta {EV_SOSPECHOSO*100:.0f}%). "
            f"Repartidas en **{m} partidos**, que es la muestra de verdad.\n",
            f"- Resultado: **{apuestas['retorno'].sum():+.2f} unidades** "
            f"({media*100:+.1f}% por apuesta)",
            f"- Margen de error (1 sigma, agrupando por partido): "
            f"±{error*100:.1f} puntos por apuesta"
            if m > 1 else "- Margen de error: incalculable con un solo partido",
            f"- Aciertos: {int(apuestas['over'].sum())} de {n}",
            f"- El partido que más pesa se lleva el {parte_mayor*100:.0f}% "
            f"del resultado\n",
            "> El margen de error se come el resultado entero, salga como salga. "
            "Es un punto de una serie, no una conclusión.\n",
            "| Partido | Apuestas | Resultado |",
            "|---|---|---|",
        ]
        for mid, total in por_partido.sort_values().items():
            nombre = apuestas[apuestas["match_id"] == mid]["partido"].iloc[0]
            cuantas = int((apuestas["match_id"] == mid).sum())
            lineas.append(f"| {nombre} | {cuantas} | {total:+.2f} u |")
        lineas.append("")

    # Las faltas del primer tiempo todavía no entran en el modelo, pero se
    # apuntan desde que el sondeo confirmó que se pueden leer en el descanso.
    # Aquí se vigila si la relación aparece, y sobre todo CUÁNTA muestra hay:
    # una correlación sobre diez partidos no significa nada, y sin decir el
    # número de partidos una correlación parece siempre más sólida de lo que es.
    por_partido = cerrados.groupby("match_id").first().reset_index()
    if "faltas_ht" in por_partido.columns:
        con_faltas = por_partido[por_partido["faltas_ht"].notna()].copy()
    else:
        con_faltas = por_partido.iloc[0:0]

    lineas.append("## Las faltas del primer tiempo\n")
    if len(con_faltas) < 3:
        lineas.append(
            f"Solo {len(con_faltas)} partido(s) con faltas apuntadas. Se "
            "empezaron a registrar cuando el sondeo confirmó que /statistics "
            "da los acumulados al minuto en partidos en juego; hay que "
            "acumular descansos antes de poder ajustar nada.\n")
    else:
        con_faltas["segunda"] = con_faltas["total_final"] - con_faltas["tarjetas_ht"]
        r_faltas = con_faltas["faltas_ht"].corr(con_faltas["segunda"])
        r_tarjetas = con_faltas["tarjetas_ht"].corr(con_faltas["segunda"])
        lineas += [
            f"Sobre **{len(con_faltas)} partidos** con faltas apuntadas:\n",
            f"- Faltas al descanso contra tarjetas de la 2ª parte: **{r_faltas:+.3f}**",
            f"- Tarjetas al descanso contra tarjetas de la 2ª parte: **{r_tarjetas:+.3f}** "
            "(lo que usa el modelo hoy)\n",
        ]
        if len(con_faltas) < 60:
            lineas.append(
                f"> Con {len(con_faltas)} partidos una correlación se mueve "
                "sola de un fin de semana a otro. Hacen falta del orden de 60 "
                "para que el coeficiente valga algo, y más para fiarse del "
                "signo si sale pequeño.\n")

    lineas.append("## Partido a partido\n")
    hay_faltas = "faltas_ht" in cerrados.columns
    lineas.append("| Partido | Tarjetas al descanso |"
                  + (" Faltas al descanso |" if hay_faltas else "")
                  + " Total final | 2ª parte |")
    lineas.append("|---|---|---|---|" + ("---|" if hay_faltas else ""))
    for mid, grupo in cerrados.groupby("match_id"):
        f = grupo.iloc[0]
        faltas = ""
        if hay_faltas:
            v = f.get("faltas_ht")
            faltas = f" {int(v)} |" if pd.notna(v) else " — |"
        lineas.append(f"| {f['partido']} | {int(f['tarjetas_ht'])} |{faltas} "
                      f"{int(f['total_final'])} | "
                      f"{int(f['total_final']) - int(f['tarjetas_ht'])} |")

    sin_cerrar = log[log["total_final"].isna()]["partido"].unique()
    if len(sin_cerrar):
        lineas.append(f"\n*Sin terminar todavía: {', '.join(sin_cerrar)}*")

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n" + "\n".join(lineas))

    # el registro se queda con el resultado ya pegado, para no volver a pedirlo
    log.to_csv(RUTA_LOG, index=False)


if __name__ == "__main__":
    main()
