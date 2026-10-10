"""
Reglas en PAPEL para todos los mercados del directo (10/10/2026, usuario: "no te centres solo en juegos";
"si acierta más, podemos elegir a qué apostar"). Se miden con el registro de cada 5 minutos, SOLO con
partidos desde INICIO (fijadas antes de verlos). Una apuesta por partido, regla y mercado: la PRIMERA
pasada que cumple la condición, a la cuota de la API de esa pasada.

Para cada mercado, "favorito de la casa >= 65%" y dos formas de ELEGIR, sacadas de mirar casa65 en
juegos del 01 al 10/10 (8 cortes; puede ser suerte, por eso se prueban en partidos nuevos):
  - con cuota >= 1,30 (la casa entre 65% y ~77%: salía +11%);
  - sin Challenger/WTA 125 (salía −9% en Challenger).
Mercados: total de juegos (lado "menos"; el "más" nunca llega al 65% en la línea principal casi nunca),
ganador (cualquiera de los dos) y resultado en sets (solo pasadas con TODOS los resultados posibles
cotizados: si falta uno, la prob. sin margen de los demás se infla).
"""
import glob

import numpy as np
import pandas as pd

INICIO = "2026-10-10 07:00"
UMBRAL, CUOTA_MIN = 0.65, 1.30
POSIBLES = {(0, 0): 4, (1, 0): 3, (0, 1): 3, (1, 1): 2}


def cargar(inicio=INICIO):
    d = pd.concat(pd.read_csv(f, low_memory=False) for f in sorted(glob.glob("data/tenis/api_tennis/registro/*.csv")))
    d = d[d.hora.astype(str) >= inicio]
    r = pd.concat(pd.read_csv(f) for f in glob.glob("data/tenis/api_tennis/resultados/*.csv")).drop_duplicates(
        "event_key", keep="last")
    r = r[r.estado == "Finished"].copy()
    s = r.sets.astype(str).str.split("-", expand=True)
    r["s1"], r["s2"] = pd.to_numeric(s[0], errors="coerce"), pd.to_numeric(s[1], errors="coerce")
    d = d.merge(r[["event_key", "s1", "s2", "juegos_totales"]], on="event_key")
    for c in ("cuota", "cuota_rival", "prob_mercado"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.sort_values("hora")


def candidatas(d):
    """Filas (una por pasada y selección) con: mercado, lado, prob_casa, cuota, gana."""
    out = []
    t = d[d.mercado == "total_juegos"].dropna(subset=["prob_mercado"]).copy()
    t["dist"] = (t.prob_mercado - .5).abs()
    t = t.sort_values(["hora", "dist"]).groupby(["hora", "event_key"]).head(1)        # línea principal
    out.append(t.assign(mercado_="juegos (menos)", p=1 - t.prob_mercado, c=t.cuota_rival,
                        gana=t.juegos_totales < t.linea.astype(float)))
    g = d[d.mercado == "ganador"].dropna(subset=["prob_mercado"]).copy()
    out.append(g.assign(mercado_="ganador", p=g.prob_mercado, c=g.cuota, gana=g.s1 > g.s2))
    out.append(g.assign(mercado_="ganador", p=1 - g.prob_mercado, c=g.cuota_rival, gana=g.s2 > g.s1))
    s = d[d.mercado == "sets"].dropna(subset=["prob_mercado"]).copy()
    if s.empty:
        return pd.concat(out)
    lab = s.linea.astype(str).str.split(":", expand=True)
    s["a"], s["b"] = pd.to_numeric(lab[0], errors="coerce"), pd.to_numeric(lab[1], errors="coerce")
    st = s.sets.astype(str).str.split("-", expand=True)
    s["sa"], s["sb"] = pd.to_numeric(st[0], errors="coerce"), pd.to_numeric(st[1], errors="coerce")
    n = s.groupby(["event_key", "hora"]).linea.transform("size")
    s = s[np.array([k == POSIBLES.get((x, y), -1) for k, x, y in zip(n, s.sa, s.sb)]) & (s.cuota < 50).values]
    out.append(s.assign(mercado_="resultado en sets", p=s.prob_mercado, c=s.cuota, gana=(s.a == s.s1) & (s.b == s.s2)))
    return pd.concat(out)


def tabla(inicio=INICIO):
    lin = [f"## Reglas de todos los mercados (en papel, partidos desde el {inicio} UTC)", "",
           "| mercado | regla | apuestas | aciertos | hacen falta | beneficio medio | sigmas |", "|---|---|---|---|---|---|---|"]
    d = cargar(inicio)
    if d.empty:
        return lin + ["Todavía no ha terminado ningún partido desde que se fijaron."]
    c = candidatas(d)
    chall = c.tipo.astype(str).str.lower().str.contains("challenger")
    reglas = {"favorito casa >= 65%": c.p >= UMBRAL,
              "  y cuota >= 1,30": (c.p >= UMBRAL) & (c.c >= CUOTA_MIN),
              "  y sin Challenger/WTA 125": (c.p >= UMBRAL) & ~chall}
    for mer in ("juegos (menos)", "ganador", "resultado en sets"):
        for nombre, cond in reglas.items():
            # la PRIMERA pasada en el tiempo: candidatas() apila un lado detrás del otro, y sin ordenar por hora
            # se elegía un lado que solo llegó al 65% más tarde (ya remontando): mirar al futuro (+4,3% falso)
            x = c[cond & (c.mercado_ == mer)].sort_values("hora", kind="stable").groupby("event_key").head(1)
            if len(x) < 2:
                lin.append(f"| {mer} | {nombre} | {len(x)} | | | | |")
                continue
            b = np.where(x.gana, x.c - 1, -1.0)
            sig = b.mean() / (b.std(ddof=1) / np.sqrt(len(b)))
            lin.append(f"| {mer} | {nombre} | {len(x)} | {x.gana.mean():.0%} | {np.mean(1 / x.c):.0%} | "
                       f"{b.mean():+.1%} | {sig:+.2f} |")
    return lin


if __name__ == "__main__":
    import sys
    print("\n".join(tabla(sys.argv[1] if len(sys.argv) > 1 else INICIO)))
