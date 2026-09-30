"""
¿Están mal puestos los precios de Kalshi en tenis? Por nivel (ATP, WTA,
Challenger, ITF) y en total de juegos / hándicap de juegos.

Reglas fijadas ANTES de ver ningún precio (30/09/2026):
- Precio = punto medio compra/venta si el diferencial es <= 0,10; si no, el
  último negociado; si tampoco, fuera (y se cuenta). Foto a cierre - 4 h
  (ATP 6 h); se repite con 2 h más de margen.
- Partido: un lado por partido (y = gana el jugador del lado "sí").
  Juegos/hándicap: UNA línea por partido, la más cercana al 50%, porque las
  líneas del mismo partido ganan y pierden juntas.
- Calibración en todo el rango, orientada al favorito; sigmas =
  (ganados - esperados) / sqrt(sum p(1-p)). Pendiente logística (1 =
  calibrado, >1 = el favorito gana más de lo que dice el precio).
- Apostar a ciegas al favorito / al marginado comprando al precio de VENTA
  (ask) más la comisión de Kalshi 0,07·p·(1-p) por contrato (redondeo al
  céntimo ignorado). Se compara con lo esperado si el punto medio fuese la
  verdad: el hueco en sigmas dice si el precio está torcido o solo es caro.
- Solo como referencia, en ATP/WTA: Kalshi (foto previa) contra el cierre de
  Betfair de tennis-data en los mismos partidos. NO es estrategia: el cierre
  es posterior a la foto y lleva información que entonces no existía.

Escribe data/tenis/calibracion_kalshi.md.
"""
import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import calibracion_cierre as CC  # noqa: E402
import cruce_fuentes as C  # noqa: E402

D = "data/tenis/kalshi"
PARTIDO = {"KXATPMATCH": "ATP", "KXWTAMATCH": "WTA", "KXATPCHALLENGERMATCH": "Challenger ATP",
           "KXWTACHALLENGERMATCH": "Challenger WTA", "KXITFMATCH": "ITF hombres", "KXITFWMATCH": "ITF mujeres"}
JUEGOS = {"KXATPGTOTAL": "Total de juegos ATP", "KXWTAGTOTAL": "Total de juegos WTA",
          "KXATPGSPREAD": "Hándicap de juegos ATP"}
COMISION = 0.07


def cargar(serie, sufijo=""):
    m = pd.read_csv(f"{D}/mercados_{serie}.csv")
    try:
        p = pd.read_csv(f"{D}/precios_{serie}.csv")
    except FileNotFoundError:
        return None
    d = m.merge(p, on="ticker")
    d = d[d["result"].isin(["yes", "no"])].copy()
    d["y"] = (d["result"] == "yes").astype(int)
    b, a, u = d[f"bid{sufijo}"], d[f"ask{sufijo}"], d[f"ultimo{sufijo}"]
    medio = (b + a) / 2
    usa_medio = b.notna() & a.notna() & (b > 0) & (a < 1) & (a - b <= 0.10)
    d["p"] = np.where(usa_medio, medio, u)
    d["ask_si"] = np.where(a.notna() & (a < 1), a, np.nan)
    d["ask_no"] = np.where(b.notna() & (b > 0), 1 - b, np.nan)      # comprar "no" = vender "sí" al bid
    d["diferencial"] = a - b
    d["fuente_p"] = np.where(usa_medio, "medio", np.where(u.notna(), "último", "sin precio"))
    return d


def resumen_precio(d):
    return (f"{(d.fuente_p != 'sin precio').mean():.0%} con precio "
            f"({(d.fuente_p == 'medio').mean():.0%} punto medio), diferencial mediano "
            f"{d.diferencial.median():.3f}")


def calibracion(d):
    x = d.dropna(subset=["p"]).copy()
    x = x[(x.p > 0) & (x.p < 1)]
    x["p_fav"] = np.maximum(x.p, 1 - x.p)
    x["fav_gana"] = np.where(x.p >= 0.5, x.y, 1 - x.y)
    x = x[x.p != 0.5]
    return x


def bloque_calibracion(x):
    cortes = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0001]
    x = x.assign(tramo=pd.cut(x.p_fav, cortes, right=False))
    filas = ["| favorito (Kalshi) | dice | gana de verdad | partidos | sigmas |", "|---|---|---|---|---|"]
    for t, g in x.groupby("tramo", observed=True):
        if len(g) < 20:
            continue
        v = (g.p_fav * (1 - g.p_fav)).sum()
        filas.append(f"| {t.left:.0%}-{min(t.right, 1):.0%} | {g.p_fav.mean():.1%} | {g.fav_gana.mean():.1%} | "
                     f"{len(g)} | {(g.fav_gana.sum() - g.p_fav.sum()) / np.sqrt(v):+.2f} |")
    return filas


def ciegas(x):
    """Comprar siempre al favorito / al marginado al precio de venta + comisión."""
    out = {}
    for lado in ("favorito", "marginado"):
        compra_si = (x.p >= 0.5) if lado == "favorito" else (x.p < 0.5)
        coste = np.where(compra_si, x.ask_si, x.ask_no)
        gana = np.where(compra_si, x.y == 1, x.y == 0)
        p_lado = np.where(compra_si, x.p, 1 - x.p)
        ok = ~np.isnan(coste) & (coste > 0) & (coste < 1)
        coste, gana, p_lado = coste[ok], gana[ok], p_lado[ok]
        coste = coste + COMISION * coste * (1 - coste)
        ret = np.where(gana, 1 / coste - 1, -1.0)
        esp = p_lado / coste - 1
        h = ret - esp
        out[lado] = (ok.sum(), ret.mean(), esp.mean(), h.mean() / (h.std(ddof=1) / np.sqrt(len(h))))
    return out


def una_linea(d):
    d = d.dropna(subset=["p"]).copy()
    d["dist"] = (d.p - 0.5).abs()
    return d.sort_values("dist").drop_duplicates("event_ticker")


def contra_betfair(d, circuito):
    td = C.cargar_td(circuito)
    td = td[td["Comment"] != "Walkover"].copy()
    w, l = pd.to_numeric(td.get("BFEW"), errors="coerce"), pd.to_numeric(td.get("BFEL"), errors="coerce")
    td["p_bf_w"] = (1 / w) / (1 / w + 1 / l)
    td = td[td.p_bf_w.notna()]
    x = d.dropna(subset=["p"]).copy()
    partes = x["event_ticker"].str.split("-").str[-1]
    x["fecha_k"] = pd.to_datetime(x["close_time"], utc=True, format="ISO8601").dt.tz_localize(None).dt.normalize()
    x["k_si"] = x["yes_sub_title"].map(C.clave_completo)
    x["k_no"] = x["no_sub_title"].map(C.clave_completo) if x["no_sub_title"].notna().any() else None
    filas = []
    tdi = td.set_index(["kw", "kl"])
    for _, r in x.iterrows():
        for kw, kl, si_gana in ((r.k_si, r.k_no, True), (r.k_no, r.k_si, False)):
            if (kw, kl) in tdi.index:
                c = tdi.loc[[(kw, kl)]]
                c = c[(c.fecha - r.fecha_k).dt.days.abs() <= 2]
                if len(c):
                    pb = c.iloc[0].p_bf_w
                    filas.append({"p_k": r.p, "p_bf": pb if si_gana else 1 - pb, "y": r.y,
                                  "y_td": int(si_gana)})
                    break
    return pd.DataFrame(filas)


def main():
    out = ["# Precios de Kalshi en tenis: ¿están mal puestos?\n",
           "Generado por `modelos/tenis/scripts/calibracion_kalshi.py`. Foto a cierre - 4 h (ATP 6 h).",
           "Apuestas al precio de venta con comisión 0,07·p·(1-p). Hueco = real - esperado si el punto",
           "medio fuese la verdad; cerca de 0 sigmas = precio exacto, solo caro.\n"]
    for sufijo, titulo in (("", "foto principal"), ("_2h", "foto 2 h antes (control)")):
        out += [f"## Resumen ({titulo})\n",
                "| mercado | partidos | calidad del precio | pendiente fav.-marg. (sigmas vs 1) | favorito a ciegas | "
                "hueco fav. (s) | marginado a ciegas | hueco marg. (s) |", "|---|---|---|---|---|---|---|---|"]
        for serie, nombre in {**PARTIDO, **JUEGOS}.items():
            d = cargar(serie, sufijo)
            if d is None:
                out.append(f"| {nombre} | (sin precios todavía) | | | | | | |")
                continue
            base = d if serie in PARTIDO else una_linea(d)
            x = calibracion(base)
            if len(x) < 100:
                out.append(f"| {nombre} | {len(x)} | {resumen_precio(base)} | pocos | | | | |")
                continue
            b, e = CC.pendiente(x)
            c = ciegas(x)
            out.append(f"| {nombre} | {len(x)} | {resumen_precio(base)} | {b:.3f} ({(b - 1) / e:+.2f}) | "
                       f"{c['favorito'][1]:+.2%} | {c['favorito'][3]:+.2f} | {c['marginado'][1]:+.2%} | "
                       f"{c['marginado'][3]:+.2f} |")
        out.append("")
    out.append("## Calibración por tramos (foto principal)\n")
    for serie, nombre in {**PARTIDO, **JUEGOS}.items():
        d = cargar(serie)
        if d is None:
            continue
        base = d if serie in PARTIDO else una_linea(d)
        x = calibracion(base)
        if len(x) >= 100:
            out += [f"\n### {nombre}\n"] + bloque_calibracion(x)
    out.append("\n## Referencia: Kalshi (foto previa) contra el cierre de Betfair, mismos partidos\n")
    out.append("No es estrategia: el cierre de Betfair es posterior a la foto de Kalshi.\n")
    out += ["| circuito | partidos | log-loss Kalshi | log-loss Betfair cierre | Kalshi - Betfair (sigmas) | "
            "resultado igual en las dos fuentes |", "|---|---|---|---|---|---|"]
    for serie, circuito in (("KXATPMATCH", "atp"), ("KXWTAMATCH", "wta")):
        d = cargar(serie)
        if d is None:
            continue
        m = contra_betfair(d, circuito)
        if len(m) < 50:
            continue
        m = m[(m.p_k > 0) & (m.p_k < 1)]
        llk = -(m.y * np.log(m.p_k) + (1 - m.y) * np.log(1 - m.p_k))
        llb = -(m.y * np.log(m.p_bf) + (1 - m.y) * np.log(1 - m.p_bf))
        dif = llk - llb
        out.append(f"| {circuito.upper()} | {len(m)} | {llk.mean():.4f} | {llb.mean():.4f} | "
                   f"{dif.mean():+.4f} ({dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif))):+.2f}) | "
                   f"{(m.y == m.y_td).mean():.1%} |")
    open("data/tenis/calibracion_kalshi.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
