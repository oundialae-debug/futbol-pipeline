"""
Apuestas en PAPEL de la señal "vigilar el menos" (juegos_directo.py), cruzadas con el resultado
final (data/tenis/api_tennis/resultados/*.csv, de get_fixtures). Regla fijada antes de mirar:
- una apuesta por partido: la PRIMERA pasada en que sale la señal;
- 1 unidad al menos de esa línea, a la cuota del menos de esa pasada (cuota de la API, no de
  Luckia); gana si juegos totales < línea;
- solo partidos acabados de forma normal ("Finished"); retiradas fuera (la casa suele anular).
Controles: mismo partido y momento, apostar SIEMPRE el menos / el más de la línea principal
(primera pasada de cada partido), y Brier del modelo frente al mercado en esa misma línea.
Escribe data/tenis/api_tennis/evaluacion_juegos.md.
"""
import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import calibrar_juegos as C  # noqa: E402
import juegos_directo as J  # noqa: E402

SAL = "data/tenis/api_tennis/evaluacion_juegos.md"


def cargar():
    regs = [pd.read_csv(f) for f in sorted(glob.glob("data/tenis/api_tennis/registro/*.csv"))]
    res = [pd.read_csv(f) for f in sorted(glob.glob("data/tenis/api_tennis/resultados/*.csv"))]
    if not regs or not res:
        return None, None
    res = pd.concat(res).drop_duplicates("event_key", keep="last")
    return pd.concat(regs), res[res.estado == "Finished"]


def resumen(nombre, g):
    if g.empty:
        return f"| {nombre} | 0 | | | |"
    n = len(g)
    m, s = g.benef.mean(), g.benef.std(ddof=1) if n > 1 else float("nan")
    sig = m / (s / np.sqrt(n)) if n > 1 and s > 0 else float("nan")
    return f"| {nombre} | {n} | {g.gana.mean():.0%} | {m:+.1%} | {sig:+.2f} |"


def previa(res):
    """Pronósticos PREVIOS (previa_juegos.py) contra el resultado: línea principal de juegos y ganador.
    'corregido' = modelo con la corrección aprendida del historial (historico_juegos.py)."""
    import json
    fs = sorted(glob.glob("data/tenis/api_tennis/previa/*.csv"))
    out = ["", "## Previos (antes de empezar), línea principal de juegos y ganador", ""]
    if not fs:
        return out + ["Todavía no hay previos registrados."]
    p = pd.concat(pd.read_csv(f) for f in fs)
    p = p[p.principal == 1].drop_duplicates("event_key", keep="last")
    p = p.merge(res[["event_key", "juegos_totales", "sets"]], on="event_key")
    if p.empty:
        return out + ["Ningún partido con previo ha terminado todavía."]
    try:
        coef = json.load(open("data/tenis/correccion_juegos_historica.json"))
    except (OSError, ValueError):
        coef = {}

    def corr(r):
        a, b, c = coef.get("wta" if ("wta" in str(r.tipo).lower() or "women" in str(r.tipo).lower()) else "atp",
                           [0, 1, 0])
        q = np.clip(r.mas_modelo, .01, .99)
        return 1 / (1 + np.exp(-(a + b * np.log(q / (1 - q)) + c * (r.linea - 21.5))))
    p["mas_corregido"] = p.apply(corr, axis=1)
    y = (p.juegos_totales > p.linea).astype(float)
    bri = {k: ((p[c] - y) ** 2).mean() for k, c in
           [("modelo", "mas_modelo"), ("modelo corregido con el historial", "mas_corregido"), ("casa", "mas_casa")]}
    out += [f"{len(p)} partidos. Juegos (más de la línea principal), Brier (menor es mejor): " +
            ", ".join(f"{k} {v:.4f}" for k, v in bri.items()) + f". Pasó el más en el {y.mean():.0%}."]
    # reglas de PAPEL de los previos, fijadas el 06/10/2026 a las 18:00 UTC: solo cuentan partidos posteriores
    # ("ATP circuito, el modelo da al más 10+ puntos sobre la casa" salió +38,7% en 46 partidos de Shanghái,
    # Tokio y Pekín MIRANDO esos mismos datos: hay que verlo en partidos nuevos antes de creérselo)
    nuevos = p[p.hora.astype(str) >= "2026-10-06 18:00"].copy()
    if "mas_ajustado" not in nuevos:
        nuevos["mas_ajustado"] = np.nan
    reglas = {"previo ATP circuito: más si modelo >= casa+10": nuevos[(nuevos.tipo == "Atp Singles") &
                                                                         (nuevos.mas_modelo - nuevos.mas_casa >= .10)].assign(lado="más"),
              "previo ajustado vs casa >= 10 (cualquier lado)": nuevos[(nuevos.mas_ajustado - nuevos.mas_casa).abs() >= .10]
              .assign(lado=lambda z: np.where(z.mas_ajustado > z.mas_casa, "más", "menos"))}
    out += ["", "| regla de previo (en papel desde el 06/10 18:00) | apuestas | aciertos | beneficio medio | sigmas |",
            "|---|---|---|---|---|"]
    for nombre, g_ in reglas.items():
        if len(g_):
            g_ = g_.copy()
            mas = g_.lado == "más"
            g_["gana"] = np.where(mas, g_.juegos_totales > g_.linea, g_.juegos_totales < g_.linea)
            g_["benef"] = np.where(g_.gana, np.where(mas, g_.cuota_mas, g_.cuota_menos) - 1, -1.0)
        else:
            g_ = pd.DataFrame(columns=["gana", "benef"])
        out.append(resumen(nombre, g_))
    g = p.dropna(subset=["gana1_casa"])
    if len(g):
        y1 = g.sets.astype(str).str.split("-").str[0].str.strip().astype(float) > \
            g.sets.astype(str).str.split("-").str[1].str.strip().astype(float)
        out.append(f"Ganador ({len(g)}): acierto modelo {((g.gana1_modelo > .5) == y1).mean():.0%}, "
                   f"casa {((g.gana1_casa > .5) == y1).mean():.0%}.")
    return out


def main():
    reg, res = cargar()
    lin = ["# Más/menos juegos en directo: apuestas en papel\n"]
    if reg is None:
        open(SAL, "w").write("\n".join(lin + ["Sin resultados todavía.\n"]))
        return
    p = J.principales(reg).merge(res[["event_key", "juegos_totales"]], on="event_key")
    p["cuota_menos"] = p.cuota_rival.astype(float)
    p["cuota_mas"] = p.cuota.astype(float)
    p["menos_gana"] = p.juegos_totales < p.linea
    primera = p.groupby("event_key").first().reset_index()
    sen = p[p.senal].groupby("event_key").first().reset_index()

    def apuesta(g, lado):
        g = g.copy()
        g["gana"] = g.menos_gana if lado == "menos" else ~g.menos_gana & (g.juegos_totales != g.linea)
        c = g.cuota_menos if lado == "menos" else g.cuota_mas
        g["benef"] = np.where(g.gana, c - 1, -1.0)
        return g

    s = apuesta(sen, "menos")
    lin += [f"Partidos acabados con cuota de juegos en el registro: **{len(primera)}**. Una apuesta por partido "
            "(se agrupa por partido). Cuota = la de la API en esa pasada, no la de Luckia. "
            "Con menos de 20 apuestas el número no significa nada.\n",
            "| estrategia | apuestas | aciertos | beneficio medio | sigmas |", "|---|---|---|---|---|",
            resumen("**señal: vigilar el menos**", s),
            resumen("control: siempre el menos (1ª pasada)", apuesta(primera, "menos")),
            resumen("control: siempre el más (1ª pasada)", apuesta(primera, "mas"))]
    if len(primera):
        y = (~primera.menos_gana).astype(float)
        bm = ((primera.prob_modelo.astype(float) - y) ** 2).mean()
        bk = ((primera.prob_mercado.astype(float) - y) ** 2).mean()
        sesgo = primera.prob_modelo.astype(float).mean() - y.mean()
        lin += ["", f"Brier del 'más' en la línea principal (1ª pasada): modelo {bm:.4f}, mercado {bk:.4f} "
                f"(menor es mejor). El modelo da al más {sesgo:+.1%} sobre lo que pasa de verdad."]
    if len(s):
        lin += ["", "## Señales", "", "| partido | línea | cuota menos | juegos | resultado |", "|---|---|---|---|---|"]
        for _, r in s.iterrows():
            lin.append(f"| {J.torneo(r.tipo, r.torneo)}: {r.jugador1} vs {r.jugador2} | {r.linea:g} | "
                       f"{r.cuota_menos:.2f} | {r.juegos_totales} | {'gana' if r.gana else 'pierde'} |")
    # avisos del vigilante: hasta el 01/10 llegaban al móvil (regla "actual"); desde entonces, solo papel y
    # tres reglas (vigilante_juegos.py). Uno por partido, regla y lado.
    av = [pd.read_csv(f) for f in sorted(glob.glob("data/tenis/api_tennis/avisos/*.csv"))]
    if av:
        a = pd.concat(av)
        if "regla" not in a:
            a["regla"] = np.nan
        a["regla"] = a.regla.fillna("actual (al móvil)")
        a = a.sort_values("hora").drop_duplicates(["event_key", "regla", "lado"])
        a = a.merge(res[["event_key", "juegos_totales"]], on="event_key")
        a["gana"] = np.where(a.lado == "menos", a.juegos_totales < a.linea, a.juegos_totales > a.linea)
        a["benef"] = np.where(a.gana, a.cuota_api.astype(float) - 1, -1.0)
        lin += ["", "## Reglas del vigilante (desde el 01/10 solo en papel)", "",
                "| regla | apuestas resueltas | aciertos | beneficio medio (cuota API) | sigmas |", "|---|---|---|---|---|"]
        for regla, g in a.groupby("regla"):
            lin.append(resumen(regla, g))
    import reglas_papel                    # ganador, sets y juegos con las mismas reglas (desde el 10/10)
    lin += [""] + reglas_papel.tabla()
    import valor_casas
    lin += [""] + valor_casas.tabla()
    import ia_no_favorito_papel
    lin += [""] + ia_no_favorito_papel.tabla()
    lin += previa(res)
    cal = C.ajustar()
    lin += ["", "## Aprendizaje (recalibración del modelo)", "",
            f"Partidos resueltos: {cal['partidos']} ({cal['filas']} líneas). Activa: **{'sí' if cal['activo'] else 'no'}** "
            f"(hace falta {C.MIN_PARTIDOS}+ partidos y que mejore a la CASA en partidos que no vio)."]
    pp = cal.get("papel_por_dias")
    if pp:
        lin.append(f"**Apostando con lo aprendido, día a día** (cada día aprende solo de los anteriores): "
                   f"{pp['apuestas']} apuestas, aciertos {pp['aciertos']:.0%}, beneficio medio {pp['beneficio_medio']:+.1%}"
                   + (f", {pp['sigmas']:+.2f} sigmas." if pp.get("sigmas") is not None else "."))
    if cal.get("coef"):
        lin.append(f"Brier (menor es mejor): modelo {cal['brier_modelo']:.4f}, modelo con el saque de hoy "
                   f"{cal['brier_modelo_directo']:.4f}, casa {cal['brier_casa']:.4f}, "
                   f"recalibrado (validado por partidos) {cal['brier_recalibrado_cv']:.4f}. "
                   f"Sesgo del modelo hacia el más: {cal['sesgo_modelo_mas']:+.1%}.")
    open(SAL, "w").write("\n".join(lin) + "\n")
    print(f"evaluación: {len(primera)} partidos, {len(s)} señales")


if __name__ == "__main__":
    main()
