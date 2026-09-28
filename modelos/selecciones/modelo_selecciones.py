"""
Modelo de conteos para selecciones (goles, xG, córners, tarjetas), 26/09/2026.
Tema APARTE del proyecto de ambos marcan.

  log(E[conteo de A contra B]) = mu + casa + amistoso + ataque_A - defensa_B
                                 + b_at * calidad_A - b_def * calidad_B

Poisson con encogimiento ridge, peso por recencia (vida media 365 días), con
los partidos de las 4 selecciones desde 2025. "Ataque" es generar el conteo
(goles, córners, tarjetas propias) y "defensa" es concederlo al rival.

Revisión del 26/09 (fallos silenciosos encontrados y arreglados):
  - Francia-Inglaterra (18/07/2026): la API da el MISMO xG (2.88) a los dos
    equipos. Una estadística idéntica en los dos lados se trata como dato
    roto: se descarta ese xG (los goles se quedan).
  - 5 rivales sin jugadores en la API (Brasil, Kosovo, Perú, San Marino,
    Guatemala) recibían la calidad MEDIA: San Marino pasaba por equipo normal
    y Brasil también. Esos partidos se descartan del ajuste.
  - "calidad" contaba minutos en cualquier competición de la ficha del
    jugador (Copa del Rey, Saudi Pro League...). Ahora: parte de los minutos
    de la selección jugados por futbolistas con >= 900' en 2025/26 en las 5
    grandes ligas.
"""
import numpy as np
import pandas as pd
from scipy.stats import nbinom, poisson
from sklearn.linear_model import PoissonRegressor

HOY = pd.Timestamp.today().normalize()
VIDA_MEDIA = 365.0
ALPHA = 0.02
ANFITRIONES_MUNDIAL = {"Mexico", "USA", "United States", "Canada"}
GRANDES_5 = {"Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1"}
CARPETA = "data/selecciones"
ESTADISTICAS = {"xg": "Expected Goals", "corners": "Corners", "amarillas": "Yellow cards"}


def calidad_equipos():
    j = pd.read_csv(f"{CARPETA}/jugadores_partido.csv")
    j["minutos"] = pd.to_numeric(j.minutos, errors="coerce").fillna(0)
    js = pd.read_csv("data/historico_jugador_stats.csv")
    js = js[(js.temporada == "25/26") & js.liga.isin(GRANDES_5)]
    buenos = set(js.groupby("jugador_id").minutos.sum().loc[lambda s: s >= 900].index)
    j["bueno"] = j.jugador_id.isin(buenos)
    t = j.groupby("equipo_id")[["minutos"]].sum()
    t["bueno"] = (j.minutos * j.bueno).groupby(j.equipo_id).sum()
    return t.bueno / t.minutos.clip(lower=1)


# Nombres de la API -> nombres del ranking FIFA (data/selecciones/ranking_fifa.csv)
ALIAS_FIFA = {"Bosnia & Herzegovina": "Bosnia and Herzegovina", "Cape Verde": "Cabo Verde",
              "Czech Republic": "Czechia", "Iran": "IR Iran", "Ivory Coast": "Côte d'Ivoire",
              "Kosovo National Team": "Kosovo", "North Korea": "Korea DPR", "South Korea": "Korea Republic",
              "St. Lucia": "St Lucia", "Turkey": "Türkiye", "Sao Tome and Principe": "São Tomé and Príncipe"}


def fifa_antes(fechas, equipos):
    """Puntos del último ranking FIFA publicado ANTES de cada fecha. Sin ranking (clubes
    en amistosos, selecciones sin clasificar): el percentil 10 de los puntos."""
    r = pd.read_csv(f"{CARPETA}/ranking_fifa.csv")
    r["fecha"] = pd.to_datetime(r.fecha)
    q = pd.DataFrame({"fecha": pd.to_datetime(list(fechas)) - pd.Timedelta(days=1),
                      "equipo": [ALIAS_FIFA.get(e, e) for e in equipos], "i": range(len(fechas))})
    out = pd.merge_asof(q.sort_values("fecha"), r.sort_values("fecha"), on="fecha", by="equipo",
                        direction="backward").sort_values("i")
    return out.puntos.fillna(r.puntos.quantile(0.1)).values


def cargar():
    p = pd.read_csv(f"{CARPETA}/partidos.csv")
    p = p[p.terminado & p.goles_l.notna()].copy()
    e = pd.read_csv(f"{CARPETA}/estadisticas_partido.csv")
    e["valor"] = pd.to_numeric(e.valor, errors="coerce")
    for clave, nombre in ESTADISTICAS.items():
        s = e[e.estadistica == nombre].set_index(["match_id", "equipo_id"]).valor
        p[f"{clave}_l"] = [s.get((m, t), np.nan) for m, t in zip(p.match_id, p.local_id)]
        p[f"{clave}_v"] = [s.get((m, t), np.nan) for m, t in zip(p.match_id, p.visitante_id)]
    roto = p.xg_l.notna() & (p.xg_l == p.xg_v)
    p.loc[roto, ["xg_l", "xg_v"]] = np.nan
    p["goles_l"], p["goles_v"] = p.goles_l.astype(float), p.goles_v.astype(float)
    neutral = (p.competicion == "World Cup") & ~p.local.isin(ANFITRIONES_MUNDIAL)
    p["casa"] = (~neutral).astype(float)
    p["amistoso"] = (p.competicion == "Friendlies").astype(float)
    q = calidad_equipos()
    sin_calidad = ~p.local_id.isin(q.index) | ~p.visitante_id.isin(q.index)
    p = p[~sin_calidad].copy()
    p["w"] = 0.5 ** ((HOY - pd.to_datetime(p.fecha)).dt.days / VIDA_MEDIA)
    # ranking FIFA (28/09/2026): +2.60s en 1X2 y +3.21s en más de 2.5 en la prueba hacia
    # delante (experimento_variables.md). Solo entra en el modelo de goles.
    p["fifa_l"], p["fifa_v"] = fifa_antes(p.fecha, p.local), fifa_antes(p.fecha, p.visitante)
    return p, q, int(roto.sum()), int(sin_calidad.sum())


def ajustar(p, q, objetivo, extras=()):
    """Devuelve f(atacante, defensor, casa, amistoso, ext) -> conteo esperado del atacante.
    extras: covariables por partido (columnas <e>_l/<e>_v, p. ej. "fifa"), estandarizadas con
    el entreno, del atacante y del defensor. ext = {e: (valor_atacante, valor_defensor)}."""
    a = pd.DataFrame({"at": p.local_id, "de": p.visitante_id, "casa": p.casa, "am": p.amistoso,
                      "y": p[f"{objetivo}_l"], "w": p.w,
                      **{f"{e}_at": p[f"{e}_l"] for e in extras}, **{f"{e}_de": p[f"{e}_v"] for e in extras}})
    b = pd.DataFrame({"at": p.visitante_id, "de": p.local_id, "casa": 0.0, "am": p.amistoso,
                      "y": p[f"{objetivo}_v"], "w": p.w,
                      **{f"{e}_at": p[f"{e}_v"] for e in extras}, **{f"{e}_de": p[f"{e}_l"] for e in extras}})
    d = pd.concat([a, b]).dropna(subset=["y"])
    idx = {t: i for i, t in enumerate(sorted(set(d["at"]) | set(d["de"])))}
    n = len(idx)
    escala = {}
    for e in extras:
        v = np.r_[p[f"{e}_l"], p[f"{e}_v"]]
        escala[e] = (v.mean(), v.std() or 1.0)

    def matriz(at, de, casa, am, ext_at, ext_de):
        X = np.zeros((len(at), 2 * n + 4 + 2 * len(extras)))
        for k, (x, y) in enumerate(zip(at, de)):
            if x in idx:
                X[k, idx[x]] = 1
            if y in idx:
                X[k, n + idx[y]] = -1
        X[:, 2 * n] = casa
        X[:, 2 * n + 1] = am
        X[:, 2 * n + 2] = [10 * q[x] for x in at]     # x10: que el ridge apenas toque la calidad
        X[:, 2 * n + 3] = [-10 * q[y] for y in de]
        for j, e in enumerate(extras):
            mu, sd = escala[e]
            X[:, 2 * n + 4 + 2 * j] = (np.asarray(ext_at[e], dtype=float) - mu) / sd
            X[:, 2 * n + 5 + 2 * j] = -(np.asarray(ext_de[e], dtype=float) - mu) / sd
        return X

    m = PoissonRegressor(alpha=ALPHA, max_iter=3000)
    m.fit(matriz(d["at"], d["de"], d["casa"], d["am"], {e: d[f"{e}_at"] for e in extras},
                 {e: d[f"{e}_de"] for e in extras}), d.y, sample_weight=d.w)

    def f(at, de, casa, am=0.0, ext=None):
        if extras and not ext:
            raise ValueError(f"el modelo lleva {extras}: falta ext para {at}-{de}")
        return float(m.predict(matriz([at], [de], [casa], [am], {e: [ext[e][0]] for e in extras},
                                      {e: [ext[e][1]] for e in extras}))[0])
    return f


def esperados(p, q, objetivos, loc, vis, casa=1.0, am=0.0):
    """Media de los ajustes de cada objetivo (p. ej. goles y xG) para local y visitante."""
    fs = [ajustar(p, q, o) for o in objetivos]
    return (np.mean([f(loc, vis, casa, am) for f in fs]), np.mean([f(vis, loc, 0.0, am) for f in fs]))


def prob_mas(media, linea, phi=1.0):
    """P(total > linea) con Poisson (phi<=1) o binomial negativa de varianza phi*media."""
    k = int(np.floor(linea))
    if phi <= 1.0001:
        return 1 - poisson.cdf(k, media)
    r = media / (phi - 1)
    return 1 - nbinom.cdf(k, r, r / (r + media))


def goles(lam_l, lam_v, maxg=10):
    g = np.arange(maxg + 1)
    M = np.outer(poisson.pmf(g, lam_l), poisson.pmf(g, lam_v))
    tot = np.add.outer(g, g)
    p0 = M[0, 0]
    return {"1": np.tril(M, -1).sum(), "X": np.trace(M), "2": np.triu(M, 1).sum(),
            "btts": (1 - poisson.pmf(0, lam_l)) * (1 - poisson.pmf(0, lam_v)),
            **{f"mas_{l}": M[tot > l].sum() for l in (0.5, 1.5, 2.5, 3.5, 4.5)},
            "local_marca": 1 - poisson.pmf(0, lam_l), "visitante_marca": 1 - poisson.pmf(0, lam_v),
            "primero_local": (1 - p0) * lam_l / (lam_l + lam_v),
            "primero_visitante": (1 - p0) * lam_v / (lam_l + lam_v), "sin_goles": p0,
            "marcador": max(((i, j) for i in g for j in g), key=lambda ij: M[ij])}


def prueba_hacia_delante(p, q, objetivos, desde="2025-10-01"):
    """Cada partido desde `desde`, pronosticado solo con los anteriores. Devuelve medias y reales."""
    filas = []
    for f in sorted(p.fecha[p.fecha >= desde].unique()):
        ent = p[p.fecha < f].copy()
        ent["w"] = 0.5 ** ((pd.Timestamp(f) - pd.to_datetime(ent.fecha)).dt.days / VIDA_MEDIA)
        fs = [ajustar(ent[ent[f"{o}_l"].notna()], q, o) for o in objetivos]
        for _, r in p[p.fecha == f].iterrows():
            filas.append({"match_id": r.match_id, "fecha": f,
                          "mu_l": np.mean([g(r.local_id, r.visitante_id, r.casa, r.amistoso) for g in fs]),
                          "mu_v": np.mean([g(r.visitante_id, r.local_id, 0.0, r.amistoso) for g in fs])})
    return pd.DataFrame(filas).merge(p, on=["match_id", "fecha"])
