"""
¿Se puede cobrar el sesgo favorito-marginado del cierre? Prueba limpia.

Regla fijada ANTES de mirar resultados (30/09/2026):
- 15 reglas candidatas: apostar al favorito del cierre cuando su probabilidad
  sin margen es >= t, t en {60, 70, 80, 85, 90%}, en tres ámbitos: todos los
  partidos, solo 1ª-2ª ronda, solo 1ª-2ª ronda de Grand Slam.
- ATP y WTA juntos. Walkovers fuera; retiradas dentro, liquidadas como en
  tennis-data (gana quien avanza).
- Se elige UNA regla: la de mejor rendimiento en 2020-2023 contra Pinnacle.
- Se juzga solo esa, en 2024-2025 (Pinnacle) y 2026 (Betfair Exchange, bruto
  y con 5% de comisión sobre la ganancia).

Escribe data/tenis/regla_favorito.md.
"""
import glob

import numpy as np
import pandas as pd

D = "data/tenis"
UMBRALES = (0.6, 0.7, 0.8, 0.85, 0.9)
AMBITOS = ("todos", "1ª-2ª ronda", "Grand Slam 1ª-2ª ronda")


def cargar():
    partes = []
    for c in ("atp", "wta"):
        for f in sorted(glob.glob(f"{D}/tennis_data/{c}_*.csv")):
            x = pd.read_csv(f, low_memory=False)
            x["nivel"] = x["Series"] if "Series" in x else x["Tier"]
            partes.append(x)
    d = pd.concat(partes, ignore_index=True)
    d = d[d["Comment"] != "Walkover"].copy()
    d["fecha"] = pd.to_datetime(d["Date"], errors="coerce")
    d["temprana"] = d["Round"].isin(["1st Round", "2nd Round"])
    d["gs"] = d["nivel"] == "Grand Slam"
    return d


def lado_favorito(d, casa):
    w, l = pd.to_numeric(d.get(f"{casa}W"), errors="coerce"), pd.to_numeric(d.get(f"{casa}L"), errors="coerce")
    ok = (w > 1) & (l > 1) & (w != l)
    x = d[ok].copy()
    w, l = w[ok], l[ok]
    x["p_fav"] = np.maximum(1 / w, 1 / l) / (1 / w + 1 / l)
    x["fav_gana"] = w < l
    x["cuota_fav"] = np.minimum(w, l)
    return x


def filtrar(x, t, ambito):
    m = x["p_fav"] >= t
    if ambito != "todos":
        m &= x["temprana"]
    if ambito.startswith("Grand Slam"):
        m &= x["gs"]
    return x[m]


def rendimiento(x, comision=0.0):
    r = np.where(x["fav_gana"], (x["cuota_fav"] - 1) * (1 - comision), -1.0)
    if len(r) < 2:
        return len(r), np.nan, np.nan
    return len(r), r.mean(), r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))


def main():
    d = cargar()
    eleg = lado_favorito(d[d["fecha"] < "2024-01-01"], "PS")
    out = ["# Regla del favorito: elegida en 2020-2023, juzgada en 2024-2026\n",
           "Generado por `modelos/tenis/scripts/regla_favorito.py`. ATP+WTA, retiradas incluidas.\n",
           "## Elección (2020-2023, Pinnacle): las 15 candidatas\n",
           "| ámbito | favorito >= | apuestas | rendimiento | sigmas |", "|---|---|---|---|---|"]
    res = []
    for a in AMBITOS:
        for t in UMBRALES:
            n, r, s = rendimiento(filtrar(eleg, t, a))
            res.append((r, a, t))
            out.append(f"| {a} | {t:.0%} | {n} | {r:+.2%} | {s:+.2f} |")
    _, a, t = max(res)
    out.append(f"\n**Elegida: {a}, favorito >= {t:.0%}.** (La mejor de 15: su número en la elección"
               " está inflado por haberla elegido entre 15.)\n")
    out += ["## Prueba (solo la elegida)\n", "| tramo | referencia | apuestas | rendimiento | sigmas |", "|---|---|---|---|---|"]
    ps = lado_favorito(d[(d["fecha"] >= "2024-01-01") & (d["fecha"] < "2026-01-01")], "PS")
    n, r, s = rendimiento(filtrar(ps, t, a))
    out.append(f"| 2024-2025 | Pinnacle | {n} | {r:+.2%} | {s:+.2f} |")
    bf = lado_favorito(d[d["fecha"] >= "2026-01-01"], "BFE")
    for com, nombre in ((0.0, "Betfair bruto"), (0.05, "Betfair con 5% comisión")):
        n, r, s = rendimiento(filtrar(bf, t, a), com)
        out.append(f"| 2026 | {nombre} | {n} | {r:+.2%} | {s:+.2f} |")
    open(f"{D}/regla_favorito.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
