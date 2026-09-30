"""
Más/menos juegos totales en directo (30/09/2026): la regla de la señal, fijada ANTES de
medirla, y la tabla simple que se manda al usuario.

Por partido y pasada se toma la línea principal (la de probabilidad sin margen más cercana
al 50%). Señal = "vigilar el MENOS": el modelo da al "más" al menos 5 puntos MENOS que la
casa. Solo en esa dirección: el modelo sobreestima los juegos (visto en Kalshi y en
directo), así que un "más" del modelo por encima de la casa no se toma como señal.
Cuota mínima para apostar el menos = 1 / (1 - prob. del más según el mercado).
"""
import pandas as pd

UMBRAL = 0.05
LUCKIA = "https://www.luckia.es/apuestas/tenis/"
CATEG = {("Atp Singles", "tokyo"): "ATP 500", ("Atp Singles", "beijing"): "ATP 500",
         ("Wta Singles", "beijing"): "WTA 1000"}
TIPOS = {"Atp Singles": "ATP", "Wta Singles": "WTA", "Challenger Men Singles": "Challenger",
         "Challenger Women Singles": "WTA 125", "Itf Men Singles": "ITF M", "Itf Women Singles": "ITF F"}


def torneo(tipo, nombre):
    n = str(nombre).split(" - ")[0].strip()
    for (tt, k), c in CATEG.items():
        if tt == tipo and k in n.lower():
            return f"{c} {n}"
    return f"{TIPOS.get(tipo, tipo)} {n}"


def principales(reg):
    """Una fila por (hora, partido): la línea de total de juegos más cercana al 50% del mercado,
    con la señal y la cuota mínima del menos."""
    t = reg[reg.mercado == "total_juegos"].dropna(subset=["prob_mercado", "prob_modelo"]).copy()
    if t.empty:
        return t
    t["dist"] = (t.prob_mercado.astype(float) - 0.5).abs()
    t = t.sort_values("dist").groupby(["hora", "event_key"], as_index=False).first()
    t["linea"] = t.linea.astype(float)
    t["senal"] = t.prob_modelo.astype(float) < t.prob_mercado.astype(float) - UMBRAL
    t["cuota_min_menos"] = 1 / (1 - t.prob_mercado.astype(float))
    return t.sort_values(["hora", "event_key"])


def tabla(reg):
    """Markdown de la última pasada."""
    p = principales(reg)
    if p.empty:
        return "Ningún partido con cuota de total de juegos ahora.\n"
    p = p[p.hora == p.hora.max()]
    hora = pd.Timestamp(p.hora.iloc[0]) + pd.Timedelta(hours=2)
    lin = [f"**Más/menos juegos totales, {hora:%H:%M} (España)**\n",
           "| torneo | partido | marcador | **pronóstico** | prob. | apuesta solo si pagan más de | veredicto |",
           "|---|---|---|---|---|---|---|"]
    for _, r in p.iterrows():
        pm, mo = float(r.prob_mercado), float(r.prob_modelo)
        if r.senal:
            pron, prob, ver = f"**Menos de {r.linea:g}**", 1 - mo, f"**vigilar el menos** (casa {1 - pm:.0%})"
            cmin = r.cuota_min_menos
        elif pm >= 0.5:
            pron, prob, ver, cmin = f"Más de {r.linea:g}", pm, "sin valor", 1 / pm
        else:
            pron, prob, ver, cmin = f"Menos de {r.linea:g}", 1 - pm, "sin valor", 1 / (1 - pm)
        lin.append(f"| {torneo(r.tipo, r.torneo)} | {r.jugador1} vs {r.jugador2} | {r.sets} sets, {r.juegos} | "
                   f"{pron} | {prob:.0%} | {cmin:.2f} | {ver} |")
    return "\n".join(lin) + "\n"


def avisos(reg):
    """Señales de la última pasada, como texto corto para el móvil."""
    p = principales(reg)
    if p.empty:
        return []
    p = p[(p.hora == p.hora.max()) & p.senal]
    return [f"{torneo(r.tipo, r.torneo)}: {r.jugador1} vs {r.jugador2} ({r.sets} sets, {r.juegos}). "
            f"MENOS de {r.linea:g} juegos, solo si pagan {r.cuota_min_menos:.2f} o más. {LUCKIA}"
            for _, r in p.iterrows()]


if __name__ == "__main__":
    import glob
    import sys
    reg = pd.read_csv(sorted(glob.glob("data/tenis/api_tennis/registro/*.csv"))[-1])
    print(tabla(reg))
    if "--avisos" in sys.argv:
        print("\n".join(avisos(reg)))
