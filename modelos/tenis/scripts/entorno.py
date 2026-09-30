"""
Tres variables de la propuesta de "pipeline de tenis" que SÍ se pueden
construir con datos que tenemos (30/09/2026). Reglas fijadas antes de mirar:

1. desfase: horas de diferencia horaria (por longitud/15) entre la sede del
   torneo anterior del jugador y la actual, menos los días transcurridos
   desde su último partido allí (se recupera ~1 h por día). Lo pendiente, A - B.
   Limitación: solo se conoce la sede de torneos de tennis-data (circuito
   principal); quien viene de un Challenger no tiene torneo anterior visible.
2. altitud: altitud de la sede (km) x diferencia de puntos ganados al saque
   (A - B). En altura la bola vuela más: debería favorecer al mejor sacador.
3. pista: velocidad de la pista (tasa de aces de la edición ANTERIOR del
   torneo, relativa a su superficie y año) x diferencia de puntos ganados al
   saque. Pista rápida debería favorecer al mejor sacador.

Variables estandarizadas con 2020-2023 (sin eso, el ajuste daba coeficiente 0
en altitud y pista por su escala minúscula, sin avisar). Logística mercado + variable (+ circuito, bo5), entrena 2020-2023, juzga
2024-2025 (Pinnacle) y 2026 (Betfair) contra el mercado recalibrado. Se
pide >= 2,5 sigmas y que aguante en los dos tramos. Escribe
data/tenis/entorno.md.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/tenis/scripts")
import modelo_tenis as M  # noqa: E402

# ciudad de tennis-data -> (latitud, longitud, altitud en metros), aproximadas
SEDE = {"'s-Hertogenbosch": (51.7, 5.3, 5), "Abu Dhabi": (24.5, 54.4, 5), "Acapulco": (16.9, -99.9, 10),
        "Adelaide": (-34.9, 138.6, 50), "Almaty": (43.2, 76.9, 800), "Antalya": (36.9, 30.7, 30),
        "Antwerp": (51.2, 4.4, 10), "Athens": (38.0, 23.7, 70), "Atlanta": (33.7, -84.4, 320),
        "Auckland": (-36.8, 174.8, 20), "Austin": (30.3, -97.7, 150), "Bad Homburg": (50.2, 8.6, 190),
        "Banja Luka": (44.8, 17.2, 160), "Barcelona": (41.4, 2.2, 60), "Basel": (47.6, 7.6, 260),
        "Bastad": (56.4, 12.9, 10), "Beijing": (39.9, 116.4, 45), "Belgrade": (44.8, 20.5, 117),
        "Berlin": (52.5, 13.4, 35), "Birmingham": (52.5, -1.9, 140), "Bogota": (4.7, -74.1, 2640),
        "Brisbane": (-27.5, 153.0, 30), "Brussels": (50.8, 4.4, 60), "Bucharest": (44.4, 26.1, 70),
        "Budapest": (47.5, 19.0, 100), "Buenos Aires": (-34.6, -58.4, 25), "Cagliari": (39.2, 9.1, 10),
        "Cancun": (21.2, -86.8, 10), "Charleston": (32.8, -79.9, 5), "Chengdu": (30.7, 104.1, 500),
        "Chennai": (13.1, 80.3, 10), "Chicago": (41.9, -87.6, 180), "Cincinnati": (39.1, -84.5, 250),
        "Cleveland": (41.5, -81.7, 200), "Cluj-Napoca": (46.8, 23.6, 360), "Cologne": (50.9, 7.0, 50),
        "Cordoba": (-31.4, -64.2, 390), "Courmayeur": (45.8, 7.0, 1224), "Dallas": (32.8, -96.8, 130),
        "Delray Beach": (26.5, -80.1, 5), "Doha": (25.3, 51.5, 10), "Dubai": (25.2, 55.3, 5),
        "Eastbourne": (50.8, 0.3, 10), "Estoril": (38.7, -9.4, 40), "Florence": (43.8, 11.3, 50),
        "Fort Worth": (32.8, -97.3, 200), "Gdynia": (54.5, 18.5, 10), "Geneva": (46.2, 6.1, 375),
        "Gijon": (43.5, -5.7, 10), "Granby": (45.4, -72.7, 150), "Gstaad": (46.5, 7.3, 1050),
        "Guadalajara": (20.7, -103.3, 1566), "Guangzhou": (23.1, 113.3, 20), "Halle": (52.1, 8.4, 70),
        "Hamburg": (53.6, 10.0, 10), "Hangzhou": (30.3, 120.2, 20), "Hobart": (-42.9, 147.3, 20),
        "Hong Kong": (22.3, 114.2, 10), "Houston": (29.8, -95.4, 20), "Hua Hin": (12.6, 99.9, 5),
        "Iasi": (47.2, 27.6, 95), "Indian Wells": (33.7, -116.3, 50), "Istanbul": (41.0, 29.0, 40),
        "Jiujiang": (29.7, 116.0, 30), "Kitzbuhel": (47.4, 12.4, 762), "Lausanne": (46.5, 6.6, 495),
        "Lexington": (38.0, -84.5, 300), "Linz": (48.3, 14.3, 266), "London": (51.5, -0.2, 20),
        "Los Cabos": (22.9, -109.9, 20), "Luxembourg": (49.6, 6.1, 300), "Lyon": (45.8, 4.8, 170),
        "Madrid": (40.4, -3.7, 657), "Mallorca": (39.6, 2.7, 20), "Marbella": (36.5, -4.9, 20),
        "Marrakech": (31.6, -8.0, 470), "Marseille": (43.3, 5.4, 20), "Melbourne": (-37.8, 145.0, 30),
        "Memphis": (35.1, -90.0, 80), "Merida": (21.0, -89.6, 10), "Metz": (49.1, 6.2, 180),
        "Miami": (25.8, -80.2, 5), "Monastir": (35.8, 10.8, 10), "Monte Carlo": (43.7, 7.4, 30),
        "Monterrey": (25.7, -100.3, 540), "Montpellier": (43.6, 3.9, 30), "Montreal": (45.5, -73.6, 50),
        "Moscow": (55.8, 37.6, 150), "Munich": (48.1, 11.6, 519), "Nanchang": (28.7, 115.9, 30),
        "Napoli": (40.9, 14.3, 20), "New York": (40.7, -73.8, 10), "Newport": (41.5, -71.3, 10),
        "Ningbo": (29.9, 121.6, 10), "Nottingham": (53.0, -1.2, 50), "Nur-Sultan": (51.2, 71.4, 347),
        "Osaka": (34.7, 135.5, 10), "Ostrava": (49.8, 18.3, 220), "Palermo": (38.1, 13.4, 20),
        "Paris": (48.8, 2.3, 40), "Parma": (44.8, 10.3, 60), "Portoroz": (45.5, 13.6, 5),
        "Prague": (50.1, 14.4, 250), "Pune": (18.5, 73.9, 560), "Queens Club": (51.5, -0.2, 20),
        "Rabat": (34.0, -6.8, 50), "Rio de Janeiro": (-22.9, -43.2, 10), "Riyadh": (24.7, 46.7, 610),
        "Rome": (41.9, 12.5, 30), "Rotterdam": (51.9, 4.5, 0), "Rouen": (49.4, 1.1, 20),
        "San Diego": (32.7, -117.2, 20), "San Jose": (37.3, -121.9, 25), "Santiago": (-33.4, -70.6, 570),
        "Sao Paulo": (-23.5, -46.6, 760), "Sardinia": (39.2, 9.1, 10), "Seoul": (37.6, 127.0, 40),
        "Shanghai": (31.2, 121.5, 5), "Shenzhen": (22.5, 114.1, 10), "Singapore": (1.3, 103.8, 15),
        "Sofia": (42.7, 23.3, 550), "St. Petersburg": (59.9, 30.3, 10), "Stockholm": (59.3, 18.1, 20),
        "Strasbourg": (48.6, 7.8, 140), "Stuttgart": (48.8, 9.2, 250), "Sydney": (-33.9, 151.2, 20),
        "Tallinn": (59.4, 24.8, 20), "Tel Aviv": (32.1, 34.8, 10), "Tenerife": (28.3, -16.5, 100),
        "Tokyo": (35.7, 139.7, 40), "Toronto": (43.7, -79.4, 100), "Turin": (45.1, 7.7, 240),
        "Umag": (45.4, 13.5, 10), "Vienna": (48.2, 16.4, 190), "Warsaw": (52.2, 21.0, 100),
        "Washington": (38.9, -77.0, 20), "Winston-Salem": (36.1, -80.2, 280), "Wuhan": (30.6, 114.3, 30),
        "Zhengzhou": (34.7, 113.6, 110), "Zhuhai": (22.3, 113.6, 10)}


def desfase(d):
    """Horas de desfase pendientes, antes del partido, para ganador y perdedor de cada fila.
    Al cambiar de sede: base = |diferencia horaria| y fecha base = último partido en la sede
    anterior. En cualquier partido en la sede nueva: max(0, base - días desde la fecha base).
    Sin sede anterior conocida (primer partido visto, o sede sin coordenadas): vacío."""
    x = d[["fecha", "Location", "kw", "kl", "wta"]].copy()
    x["loc"] = x["Location"].astype(str).str.strip()
    x["lon"] = x["loc"].map(lambda c: SEDE.get(c, (np.nan, np.nan, np.nan))[1])
    x = x.reset_index().sort_values(["fecha", "index"])
    estado = {}                          # jugador -> [sede, lon, último partido allí, base_h, fecha base]
    res = {"w": {}, "l": {}}
    for _, r in x.iterrows():
        claves = (("w", (r.wta, r.kw)), ("l", (r.wta, r.kl)))
        for lado, k in claves:                            # leer (antes del partido)
            e = estado.get(k)
            if e is None:
                val = np.nan
            elif e[0] == r["loc"]:
                val = np.nan if np.isnan(e[3]) else max(0.0, e[3] - (r.fecha - e[4]).days)
            elif np.isnan(e[1]) or np.isnan(r.lon):
                val = np.nan
            else:
                dh = abs(((r.lon - e[1]) / 15 + 12) % 24 - 12)
                val = max(0.0, dh - (r.fecha - e[2]).days)
            res[lado][r["index"]] = val
        for lado, k in claves:                            # actualizar (después)
            e = estado.get(k)
            if e is not None and e[0] == r["loc"]:
                e[2] = r.fecha
            elif e is None or np.isnan(e[1]) or np.isnan(r.lon):
                estado[k] = [r["loc"], r.lon, r.fecha, np.nan, r.fecha]
            else:
                dh = abs(((r.lon - e[1]) / 15 + 12) % 24 - 12)
                estado[k] = [r["loc"], r.lon, r.fecha, dh, e[2]]
    return pd.Series(res["w"]).reindex(d.index), pd.Series(res["l"]).reindex(d.index)


def main():
    d, a_gana = M.construir()
    s = np.where(a_gana, 1.0, -1.0)
    loc = d["Location"].astype(str).str.strip()
    falta = sorted(set(loc) - set(SEDE))
    alt_km = loc.map(lambda c: SEDE.get(c, (np.nan, np.nan, np.nan))[2]) / 1000
    jw, jl = desfase(d)
    d["h_desfase"] = s * (jw.fillna(0) - jl.fillna(0))
    d["h_altitud"] = alt_km.fillna(0) * d["d_spw"].fillna(0)
    d["h_pista"] = d["pista_rapida"].fillna(0) * d["d_spw"].fillna(0)
    # estandarizar con la media y desviación de 2020-2023: sin esto el ajustador se queda parado
    # cerca de 0 con variables minúsculas (altitud x saque ~ 0,005) y da coef. 0 sin avisar
    ent = d["fecha"] < "2024-01-01"
    for c in ("h_desfase", "h_altitud", "h_pista"):
        d[c] = (d[c] - d.loc[ent, c].mean()) / d.loc[ent, c].std()
    comp = d[d["Comment"] == "Completed"]
    tr, te = comp[comp["fecha"] < "2024-01-01"], comp[comp["fecha"] >= "2024-01-01"]
    base = ["m", "wta", "bo5"]
    y = te["y"].values
    tramos = {"2024-2025 Pinnacle": (te["fuente_mkt"] == "Pinnacle").values,
              "2026 Betfair": ((te["fuente_mkt"] == "Betfair") & (te["fecha"] >= "2026-01-01")).values}
    p0 = LogisticRegression(C=1e6, max_iter=2000).fit(tr[base], tr["y"]).predict_proba(te[base])[:, 1]
    out = ["# Desfase horario, altitud y velocidad de pista contra el mercado recalibrado\n",
           "Generado por `modelos/tenis/scripts/entorno.py`. Entrena 2020-2023, juzga 2024-2026.",
           "Se pide >= 2,5 sigmas y que aguante en los dos tramos. Log-loss negativo = mejora.\n",
           f"Sedes sin coordenadas: {falta or 'ninguna'}. Partidos con desfase > 0: "
           f"{int(((jw > 0) | (jl > 0)).sum())}; con pista conocida: {int(d['pista_rapida'].notna().sum())} "
           f"de {len(d)}; en sede >= 1.000 m: {int((alt_km >= 1).sum())}.\n",
           "| variable | coef. entreno (sigmas) | coef. prueba (sigmas) | 2024-2025 Pinnacle | 2026 Betfair |",
           "|---|---|---|---|---|"]
    for nombre, cols in (("desfase", ["h_desfase"]), ("altitud", ["h_altitud"]), ("pista", ["h_pista"]),
                         ("las tres", ["h_desfase", "h_altitud", "h_pista"])):
        c = base + cols
        coefs = []
        for g in (tr, te):
            mod = LogisticRegression(C=1e6, max_iter=2000).fit(g[c], g["y"])
            pp = mod.predict_proba(g[c])[:, 1]
            X = np.column_stack([np.ones(len(g)), g[c].values])
            cov = np.linalg.inv(X.T @ (X * (pp * (1 - pp))[:, None]))
            coefs.append(" / ".join(f"{mod.coef_[0][len(base) + k]:+.3f} ({mod.coef_[0][len(base) + k] / np.sqrt(cov[len(base) + 1 + k, len(base) + 1 + k]):+.2f})"
                                    for k in range(len(cols))))
        p = LogisticRegression(C=1e6, max_iter=2000).fit(tr[c], tr["y"]).predict_proba(te[c])[:, 1]
        celdas = []
        for tn, m in tramos.items():
            dif, sg = M.sig(M.ll(y[m], p[m]), M.ll(y[m], p0[m]))
            celdas.append(f"{dif:+.5f} ({sg:+.2f})")
        out.append(f"| {nombre} | {coefs[0]} | {coefs[1]} | {celdas[0]} | {celdas[1]} |")
    open("data/tenis/entorno.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
