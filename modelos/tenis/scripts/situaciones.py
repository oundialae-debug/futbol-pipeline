"""
Cinco situaciones concretas que el mercado podría valorar mal. Hipótesis
fijadas ANTES de mirar (30/09/2026); cada una es un indicador del jugador A
menos el del B (+1, 0, -1):

1. local: juega en su país (ciudad del torneo -> país, tabla a mano abajo).
2. previa: entra al cuadro desde la previa (Q) o como lucky loser (LL).
3. cansancio: su partido anterior duró 180 minutos o más.
4. regreso: 60 días o más entre el inicio de su torneo anterior y este.
5. cambio_superficie: 120 días o más sin jugar en esta superficie.

Cada una: logística y ~ logit(mercado) + indicador (+ circuito, bo5),
entrenada con 2020-2023, juzgada en 2024-2025 (Pinnacle) y 2026 (Betfair)
contra el mercado recalibrado. Con cinco a la vez se pide >= 2,5 sigmas y
que aguante en los dos tramos de prueba. Coeficiente > 0 = el mercado
infravalora a quien está en esa situación.

Escribe data/tenis/situaciones.md.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/tenis/scripts")
import modelo_tenis as M  # noqa: E402

D = "data/tenis"
PAIS = {"'s-Hertogenbosch": "NED", "Abu Dhabi": "UAE", "Acapulco": "MEX", "Adelaide": "AUS", "Almaty": "KAZ",
        "Antalya": "TUR", "Antwerp": "BEL", "Athens": "GRE", "Atlanta": "USA", "Auckland": "NZL", "Austin": "USA",
        "Bad Homburg": "GER", "Banja Luka": "BIH", "Barcelona": "ESP", "Basel": "SUI", "Bastad": "SWE",
        "Beijing": "CHN", "Belgrade": "SRB", "Berlin": "GER", "Birmingham": "GBR", "Bogota": "COL",
        "Brisbane": "AUS", "Brussels": "BEL", "Bucharest": "ROU", "Budapest": "HUN", "Buenos Aires": "ARG",
        "Cagliari": "ITA", "Cancun": "MEX", "Charleston": "USA", "Chengdu": "CHN", "Chennai": "IND",
        "Chicago": "USA", "Cincinnati": "USA", "Cleveland": "USA", "Cluj-Napoca": "ROU", "Cologne": "GER",
        "Cordoba": "ARG", "Courmayeur": "ITA", "Dallas": "USA", "Delray Beach": "USA", "Doha": "QAT",
        "Dubai": "UAE", "Eastbourne": "GBR", "Estoril": "POR", "Florence": "ITA", "Fort Worth": "USA",
        "Gdynia": "POL", "Geneva": "SUI", "Gijon": "ESP", "Granby": "CAN", "Gstaad": "SUI", "Guadalajara": "MEX",
        "Guangzhou": "CHN", "Halle": "GER", "Hamburg": "GER", "Hangzhou": "CHN", "Hobart": "AUS",
        "Hong Kong": "HKG", "Houston": "USA", "Hua Hin": "THA", "Iasi": "ROU", "Indian Wells": "USA",
        "Istanbul": "TUR", "Jiujiang": "CHN", "Kitzbuhel": "AUT", "Lausanne": "SUI", "Lexington": "USA",
        "Linz": "AUT", "London": "GBR", "Los Cabos": "MEX", "Luxembourg": "LUX", "Lyon": "FRA", "Madrid": "ESP",
        "Mallorca": "ESP", "Marbella": "ESP", "Marrakech": "MAR", "Marseille": "FRA", "Melbourne": "AUS",
        "Memphis": "USA", "Merida": "MEX", "Metz": "FRA", "Miami": "USA", "Monastir": "TUN", "Monte Carlo": "MON",
        "Monterrey": "MEX", "Montpellier": "FRA", "Montreal": "CAN", "Moscow": "RUS", "Munich": "GER",
        "Nanchang": "CHN", "Napoli": "ITA", "New York": "USA", "Newport": "USA", "Ningbo": "CHN",
        "Nottingham": "GBR", "Nur-Sultan": "KAZ", "Osaka": "JPN", "Ostrava": "CZE", "Palermo": "ITA",
        "Paris": "FRA", "Parma": "ITA", "Portoroz": "SLO", "Prague": "CZE", "Pune": "IND", "Queens Club": "GBR",
        "Rabat": "MAR", "Rio de Janeiro": "BRA", "Riyadh": "KSA", "Rome": "ITA", "Rotterdam": "NED",
        "Rouen": "FRA", "San Diego": "USA", "San Jose": "USA", "Santiago": "CHI", "Sao Paulo": "BRA",
        "Sardinia": "ITA", "Seoul": "KOR", "Shanghai": "CHN", "Shenzhen": "CHN", "Singapore": "SGP",
        "Sofia": "BUL", "St. Petersburg": "RUS", "Stockholm": "SWE", "Strasbourg": "FRA", "Stuttgart": "GER",
        "Sydney": "AUS", "Tallinn": "EST", "Tel Aviv": "ISR", "Tenerife": "ESP", "Tokyo": "JPN",
        "Toronto": "CAN", "Turin": "ITA", "Umag": "CRO", "Vienna": "AUT", "Warsaw": "POL", "Washington": "USA",
        "Winston-Salem": "USA", "Wuhan": "CHN", "Zhengzhou": "CHN", "Zhuhai": "CHN"}


def indicadores(d, a_gana):
    s = np.where(a_gana, 1.0, -1.0)
    pais = d["Location"].astype(str).str.strip().map(PAIS)
    sin_pais = sorted(d.loc[pais.isna(), "Location"].astype(str).unique())
    ind = {}
    for lado in "wl":
        ind[f"local_{lado}"] = (d[f"ioc_{lado}"] == pais).astype(float)
        ind[f"previa_{lado}"] = d[f"entry_{lado}"].isin(["Q", "LL"]).astype(float)
        ind[f"cansancio_{lado}"] = (d[f"min_ant_{lado}"] >= 180).astype(float)
        ind[f"regreso_{lado}"] = (d[f"descanso_{lado}"] >= 60).astype(float)
        ind[f"cambio_superficie_{lado}"] = (d[f"dias_sup_{lado}"] >= 120).astype(float)
    for h in ("local", "previa", "cansancio", "regreso", "cambio_superficie"):
        d[f"h_{h}"] = s * (ind[f"{h}_w"] - ind[f"{h}_l"])
        d[f"n_{h}"] = (ind[f"{h}_w"] + ind[f"{h}_l"]).clip(upper=1)
    return sin_pais


def ajuste(tr, te, cols):
    mod = LogisticRegression(C=1e6, max_iter=2000).fit(tr[cols], tr["y"])
    return mod.predict_proba(te[cols])[:, 1], mod.coef_[0]


def main():
    d, a_gana = M.construir()
    sin_pais = indicadores(d, a_gana)
    comp = d[d["Comment"] == "Completed"]
    tr = comp[comp["fecha"] < "2024-01-01"]
    te = comp[comp["fecha"] >= "2024-01-01"]
    base_cols = ["m", "wta", "bo5"]
    p0, _ = ajuste(tr, te, base_cols)
    y = te["y"].values
    tramos = {"2024-2025 Pinnacle": (te["fuente_mkt"] == "Pinnacle").values,
              "2026 Betfair": ((te["fuente_mkt"] == "Betfair") & (te["fecha"] >= "2026-01-01")).values}
    out = ["# Cinco situaciones concretas contra el mercado recalibrado\n",
           "Generado por `modelos/tenis/scripts/situaciones.py`. Entrena 2020-2023, juzga 2024-2026.",
           "Coeficiente > 0: el mercado infravalora a quien está en la situación. Log-loss: negativo =",
           "mejora al mercado recalibrado. Se pide >= 2,5 sigmas y que aguante en los dos tramos.\n",
           f"Ciudades sin país en la tabla: {sin_pais or 'ninguna'}.\n",
           "| situación | partidos con ella (entreno / prueba) | coef. entreno (sigmas) | coef. en prueba (sigmas) | "
           "2024-2025 Pinnacle | 2026 Betfair |", "|---|---|---|---|---|---|"]
    for h in ("local", "previa", "cansancio", "regreso", "cambio_superficie"):
        cols = base_cols + [f"h_{h}"]
        p, _ = ajuste(tr, te, cols)
        coefs = []
        for g in (tr, te):
            X = g[cols].values
            mod = LogisticRegression(C=1e6, max_iter=2000).fit(X, g["y"])
            pp = mod.predict_proba(X)[:, 1]
            Xc = np.column_stack([np.ones(len(X)), X])
            cov = np.linalg.inv(Xc.T @ (Xc * (pp * (1 - pp))[:, None]))
            coefs.append((mod.coef_[0][-1], mod.coef_[0][-1] / np.sqrt(cov[-1, -1])))
        celdas = []
        for tn, m in tramos.items():
            dif, s = M.sig(M.ll(y[m], p[m]), M.ll(y[m], p0[m]))
            celdas.append(f"{dif:+.5f} ({s:+.2f})")
        out.append(f"| {h} | {int((tr[f'h_{h}'] != 0).sum())} / {int((te[f'h_{h}'] != 0).sum())} | "
                   f"{coefs[0][0]:+.3f} ({coefs[0][1]:+.2f}) | {coefs[1][0]:+.3f} ({coefs[1][1]:+.2f}) | "
                   f"{celdas[0]} | {celdas[1]} |")
    open(f"{D}/situaciones.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
