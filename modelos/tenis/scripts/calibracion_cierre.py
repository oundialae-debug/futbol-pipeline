"""
¿Está bien puesto el precio de cierre de Pinnacle en ganador del partido?
ATP y WTA 2020-2026 (tennis-data). Antes de montar ningún modelo: si el
precio no está torcido, un modelo no tiene nada que corregir.

- Probabilidad de Pinnacle sin margen: 1/cuota normalizada (multiplicativa).
- Calibración por tramos de probabilidad del FAVORITO, rango completo
  50%-100% (en fútbol el recorte 15-85% escondió el sesgo favorito-marginado).
  Sigmas = (ganados - esperados) / sqrt(sum p(1-p)).
- Pendiente logística de logit(p): 1 = calibrado; >1 = el favorito gana más
  de lo que dice el precio (sesgo favorito-marginado).
- Apostar a ciegas (siempre favorito / siempre marginado) en cada casa:
  rendimiento real contra el esperado si Pinnacle sin margen fuese la verdad.
  El hueco (real - esperado) en sigmas dice si el precio está torcido o solo
  es caro. Un partido = una apuesta: observaciones independientes.
- Walkovers fuera siempre. Retiradas fuera de la tabla principal (cada casa
  liquida distinto) y medidas aparte.

Escribe data/tenis/calibracion_cierre.md.
"""
import glob

import numpy as np
import pandas as pd

D = "data/tenis"
N_MIN = 20


def cargar():
    partes = []
    for circuito in ("atp", "wta"):
        for f in sorted(glob.glob(f"{D}/tennis_data/{circuito}_*.csv")):
            d = pd.read_csv(f, low_memory=False)
            d["circuito"] = circuito.upper()
            d["nivel"] = d["Series"] if "Series" in d else d["Tier"]
            partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    d["fecha"] = pd.to_datetime(d["Date"], errors="coerce")
    for c in ("PSW", "PSL", "B365W", "B365L", "AvgW", "AvgL", "MaxW", "MaxL", "BFEW", "BFEL"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[(d["PSW"] > 1) & (d["PSL"] > 1) & (d["Comment"] != "Walkover")].copy()
    iw, il = 1 / d["PSW"], 1 / d["PSL"]
    d["margen_ps"] = iw + il - 1
    d["p_w"] = iw / (iw + il)                           # prob. sin margen del que ganó
    d["fav_gana"] = (d["PSW"] < d["PSL"]).astype(int)
    d.loc[d["PSW"] == d["PSL"], "fav_gana"] = np.nan    # sin favorito claro
    d = d.dropna(subset=["fav_gana"])
    d["p_fav"] = np.where(d["fav_gana"] == 1, d["p_w"], 1 - d["p_w"])
    d["ronda"] = np.where(d["Round"].isin(["1st Round", "2nd Round"]), "1ª-2ª ronda",
                          np.where(d["Round"].str.contains("Qualifying", na=False), "previa", "3ª ronda o más"))
    return d


def sig(obs, esp, var):
    return (obs - esp) / np.sqrt(var) if var > 0 else np.nan


def tabla_calibracion(d):
    cortes = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0001]
    d = d.assign(tramo=pd.cut(d["p_fav"], cortes, right=False))
    filas = ["| favorito (Pinnacle sin margen) | dice | gana de verdad | partidos | sigmas |", "|---|---|---|---|---|"]
    for t, g in d.groupby("tramo", observed=True):
        if len(g) < N_MIN:
            continue
        v = (g.p_fav * (1 - g.p_fav)).sum()
        filas.append(f"| {t.left:.0%}-{min(t.right,1):.0%} | {g.p_fav.mean():.1%} | {g.fav_gana.mean():.1%} | "
                     f"{len(g)} | {sig(g.fav_gana.sum(), g.p_fav.sum(), v):+.2f} |")
    return filas


def pendiente(d):
    """Regresión logística fav_gana ~ a + b·logit(p_fav), por Newton. Devuelve b y su error."""
    x = np.log(d.p_fav / (1 - d.p_fav)).clip(-10, 10).values
    y = d.fav_gana.values
    X = np.column_stack([np.ones_like(x), x])
    beta = np.array([0.0, 1.0])
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ beta))
        W = p * (1 - p)
        H = X.T @ (X * W[:, None])
        paso = np.linalg.solve(H, X.T @ (y - p))
        beta += paso
        if np.abs(paso).max() < 1e-10:
            break
    ee = np.sqrt(np.diag(np.linalg.inv(H)))
    return beta[1], ee[1]


def apuestas(d, casa):
    """Rendimiento de apostar siempre al favorito y siempre al marginado (según Pinnacle) en `casa`."""
    cw, cl = d[f"{casa}W"], d[f"{casa}L"]
    ok = (cw > 1) & (cl > 1)
    d, cw, cl = d[ok], cw[ok], cl[ok]
    out = {}
    for lado in ("favorito", "marginado"):
        gana = d.fav_gana == 1 if lado == "favorito" else d.fav_gana == 0
        # cuota de ese lado: el favorito es el que ganó si fav_gana
        cuota_fav = np.where(d.fav_gana == 1, cw, cl)
        cuota_mar = np.where(d.fav_gana == 1, cl, cw)
        cuota = cuota_fav if lado == "favorito" else cuota_mar
        p = d.p_fav.values if lado == "favorito" else 1 - d.p_fav.values
        ret = np.where(gana, cuota - 1, -1.0)
        esperado = p * cuota - 1
        hueco = ret - esperado
        out[lado] = (len(d), ret.mean(), esperado.mean(), hueco.mean() / (hueco.std(ddof=1) / np.sqrt(len(d))))
    return out


def bloque_apuestas(d, titulo):
    filas = [f"\n### {titulo}\n",
             "| casa | lado | partidos | rendimiento real | esperado si Pinnacle es la verdad | hueco (sigmas) |",
             "|---|---|---|---|---|---|"]
    for casa, nombre in (("PS", "Pinnacle"), ("B365", "Bet365"), ("Avg", "Media"), ("Max", "Máxima"), ("BFE", "Betfair Exch. (sin comisión)")):
        for lado, (n, real, esp, s) in apuestas(d, casa).items():
            filas.append(f"| {nombre} | {lado} | {n} | {real:+.2%} | {esp:+.2%} | {s:+.2f} |")
    return filas


def main():
    d = cargar()
    comp = d[d["Comment"] == "Completed"]
    ret = d[d["Comment"] != "Completed"]
    out = ["# Calibración del cierre de Pinnacle (ganador del partido)\n",
           "Generado por `modelos/tenis/scripts/calibracion_cierre.py`. tennis-data 2020-2026.",
           f"Partidos completos: {len(comp)} (ATP {sum(comp.circuito=='ATP')}, WTA {sum(comp.circuito=='WTA')}). "
           f"Retiradas y otros aparte: {len(ret)}. Walkovers fuera.",
           f"Margen medio de Pinnacle: ATP {d[d.circuito=='ATP'].margen_ps.mean():.2%}, "
           f"WTA {d[d.circuito=='WTA'].margen_ps.mean():.2%}.\n"]
    out.append("## Pendiente favorito-marginado (1 = calibrado, >1 = el favorito gana más de lo que dice)\n")
    out += ["| grupo | partidos | pendiente | error | sigmas contra 1 |", "|---|---|---|---|---|"]
    grupos = [("todo", comp), ("ATP", comp[comp.circuito == "ATP"]), ("WTA", comp[comp.circuito == "WTA"])]
    grupos += [(f"superficie {s}", g) for s, g in comp.groupby("Surface")]
    grupos += [(f"nivel {s}", g) for s, g in comp.groupby("nivel")]
    grupos += [(f"{s}", g) for s, g in comp.groupby("ronda")]
    grupos += [(f"año {int(s)}", g) for s, g in comp.groupby(comp.fecha.dt.year)]
    for nombre, g in grupos:
        if len(g) < 200:
            continue
        b, e = pendiente(g)
        out.append(f"| {nombre} | {len(g)} | {b:.3f} | {e:.3f} | {(b-1)/e:+.2f} |")
    for nombre, g in (("ATP", comp[comp.circuito == "ATP"]), ("WTA", comp[comp.circuito == "WTA"])):
        out += [f"\n## Calibración por tramos, {nombre} (partidos completos)\n"] + tabla_calibracion(g)
    out.append("\n## Apostar a ciegas: ¿precio torcido o solo caro?\n")
    out.append("Hueco = rendimiento real - esperado. Cerca de 0 sigmas: el precio es exacto y solo cobra margen.")
    out += bloque_apuestas(comp[comp.circuito == "ATP"], "ATP, partidos completos")
    out += bloque_apuestas(comp[comp.circuito == "WTA"], "WTA, partidos completos")
    out += bloque_apuestas(d, "ATP+WTA, incluidas retiradas (liquidadas como en tennis-data: gana quien avanza)")
    open(f"{D}/calibracion_cierre.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
