"""
Ambos marcan y más/menos 2.5 para Liga Profesional (ARG), Brasileirão (BRA) y
Liga MX (MEX), SIN la API de Highlightly (29/09/2026, cuota agotada).

Fuente: football-data.co.uk/new/{ARG,BRA,MEX}.csv (resultados + cuota de
CIERRE del 1X2, 2012-hoy). Todo aislado en modelos/ligas_america/.

LO QUE NO HAY Y SE CREA A PARTIR DE LAS CUOTAS
  football-data solo da el 1X2 en estas ligas: ni más/menos 2.5 ni ambos
  marcan. Se crean así:
    1. p_local, p_empate, p_visitante sin margen (media del mercado, Avg*;
       Pinnacle no existe en 2026 y mezclar fuentes por temporada mete un
       salto artificial).
    2. Goles esperados lambda_l, lambda_v: el par Poisson independiente que
       reproduce ESE 1X2 (dos incógnitas, dos ecuaciones: p_local y
       p_visitante). De ahí p_btts_mkt y p_mas25_mkt implícitas.
  El total de goles que implica un 1X2 está poco determinado (un 1X2
  igualado es compatible con 0-0 y con 3-3): por eso además se ajusta el
  nivel de goles de la liga y de cada equipo con los datos propios.

VARIABLES DEL PROPIO JUEGO (solo partidos ANTERIORES: shift antes de rolling)
  Elo (K=20, ventaja local 60), goles a favor/en contra, tasa de ambos
  marcan y de más de 2.5 de cada equipo (últimos 8), las mismas en su
  condición (local en casa, visitante fuera, últimos 6), nivel de la liga en
  la temporada hasta ese día, días de descanso.

EVALUACIÓN (mes a mes, como el oficial): cada mes de prueba se entrena con
TODO lo anterior. Brazos:
  base      tasa de la liga en los 365 días anteriores (lo tonto)
  poisson   p implícita del 1X2 por Poisson, sin entrenar nada
  mercado   XGBoost solo con variables de cuota
  completo  XGBoost con cuota + juego
  (y "completo" entrenando SOLO con la liga propia vs con las tres juntas)
Brier emparejado, sigmas contra base y entre brazos. NO hay cuota histórica
de ambos marcan ni de más/menos 2.5 en estas ligas: no se puede medir
contra ESE mercado; se dice en el informe.
"""
import os
import sys
import numpy as np
import pandas as pd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CARPETA = os.path.join(RAIZ, "modelos", "ligas_america")
FD = os.path.join(CARPETA, "data", "football_data")
LIGAS = {"ARG": "Liga Profesional", "BRA": "Brasileirão", "MEX": "Liga MX",
         "COLB": "Primera B Colombia"}   # COLB: resultados de FotMob, SIN cuotas (fotmob_resultados.py)
OBJETIVOS = {"ambos_marcan": "btts", "mas_2_5": "o25"}
SEMILLAS = (0, 1, 2)
DESDE_PRUEBA = os.environ.get("DESDE_PRUEBA", "2024-01")

MKT = ["m_pl", "m_pe", "m_pv", "m_lam_l", "m_lam_v", "m_lam_tot", "m_p_btts", "m_p_o25"]


# ---------------------------------------------------------------- datos
def cargar():
    tabs = []
    for cod in LIGAS:
        ruta = os.path.join(FD, f"{cod}.csv")
        if not os.path.exists(ruta):
            continue
        d = pd.read_csv(ruta, encoding="utf-8-sig")
        d["liga"] = cod
        tabs.append(d)
    d = pd.concat(tabs, ignore_index=True)
    d["fecha"] = pd.to_datetime(d.Date, dayfirst=True)
    d = d[d.HG.notna() & d.AG.notna()].copy()
    d["hg"], d["ag"] = d.HG.astype(int), d.AG.astype(int)
    d["btts"] = ((d.hg > 0) & (d.ag > 0)).astype(int)
    d["o25"] = ((d.hg + d.ag) > 2).astype(int)
    d["Home"], d["Away"] = d.Home.str.strip(), d.Away.str.strip()
    d["temporada"] = d.Season.astype(str).str[:4]
    return d.sort_values(["fecha", "liga"]).reset_index(drop=True)


# ---------------------------------------------------- lo que sale de la cuota
def poisson_1x2(ll, lv, n=11):
    k = np.arange(n)
    from math import factorial
    f = np.array([factorial(i) for i in k], float)
    pl = np.exp(-ll) * ll ** k / f
    pv = np.exp(-lv) * lv ** k / f
    m = np.outer(pl, pv)
    return np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum(), m


def lambdas_de_1x2(p_l, p_v):
    """Par (lambda_l, lambda_v) cuyo Poisson da ese p_local y p_visitante.
    Newton en 2D desde (1.4, 1.1), con varios arranques si no converge."""
    for inicio in ((1.4, 1.1), (1.0, 1.0), (2.0, 0.8), (0.8, 2.0)):
        x = np.array(inicio, float)
        for _ in range(60):
            a, _, c, _ = poisson_1x2(*x)
            r = np.array([a - p_l, c - p_v])
            if np.abs(r).max() < 1e-7:
                return x
            h = 1e-5
            J = np.zeros((2, 2))
            for j in range(2):
                xx = x.copy(); xx[j] += h
                a2, _, c2, _ = poisson_1x2(*xx)
                J[:, j] = [(a2 - a) / h, (c2 - c) / h]
            try:
                paso = np.linalg.solve(J, r)
            except np.linalg.LinAlgError:
                break
            x = np.clip(x - paso, 0.05, 6.0)
        a, _, c, _ = poisson_1x2(*x)
        if abs(a - p_l) < 1e-4 and abs(c - p_v) < 1e-4:
            return x
    return np.array([np.nan, np.nan])


def rasgos_mercado(cuota_l, cuota_e, cuota_v):
    """De un 1X2 (cuotas) a las 8 variables MKT. Sirve igual para el
    histórico (cierre de football-data) que para un partido de hoy."""
    inv = np.array([1 / cuota_l, 1 / cuota_e, 1 / cuota_v])
    if not np.isfinite(inv).all():
        return dict.fromkeys(MKT, np.nan)
    pl, pe, pv = inv / inv.sum()
    ll, lv = lambdas_de_1x2(pl, pv)
    if np.isnan(ll):
        out = dict.fromkeys(MKT, np.nan)
        out.update(m_pl=pl, m_pe=pe, m_pv=pv)
        return out
    _, _, _, m = poisson_1x2(ll, lv)
    p_btts = 1 - m[0, :].sum() - m[:, 0].sum() + m[0, 0]
    tot = np.add.outer(np.arange(len(m)), np.arange(len(m)))
    return dict(m_pl=pl, m_pe=pe, m_pv=pv, m_lam_l=ll, m_lam_v=lv, m_lam_tot=ll + lv,
                m_p_btts=p_btts, m_p_o25=m[tot > 2].sum())


def añadir_mercado(d):
    filas = [rasgos_mercado(a, b, c) for a, b, c in zip(d.AvgCH, d.AvgCD, d.AvgCA)]
    return pd.concat([d.reset_index(drop=True), pd.DataFrame(filas)], axis=1)


# ---------------------------------------------------------- lo del juego
def elo(d, k=20.0, ventaja=60.0):
    r, el, ev = {}, [], []
    for liga, h, a, hg, ag in zip(d.liga, d.Home, d.Away, d.hg, d.ag):
        kh, ka = (liga, h), (liga, a)
        rh, ra = r.get(kh, 1500.0), r.get(ka, 1500.0)
        el.append(rh); ev.append(ra)
        if pd.isna(hg) or pd.isna(ag):      # partido futuro: se lee el rating, no se actualiza
            continue
        e = 1 / (1 + 10 ** ((ra - rh - ventaja) / 400))
        s = 1.0 if hg > ag else 0.5 if hg == ag else 0.0
        g = np.log1p(abs(hg - ag)) + 1
        r[kh], r[ka] = rh + k * g * (s - e), ra - k * g * (s - e)
    d["elo_l"], d["elo_v"] = el, ev
    d["elo_dif"] = d.elo_l - d.elo_v
    return d


def forma(d, ventana=8, ventana_cond=6):
    """Medias de los partidos ANTERIORES de cada equipo (shift(1) antes de
    rolling: el partido de hoy nunca entra en su propia variable)."""
    lado_l = pd.DataFrame({"i": d.index, "liga": d.liga, "eq": d.Home, "fecha": d.fecha, "cond": "L",
                           "gf": d.hg, "gc": d.ag, "btts": d.btts, "o25": d.o25})
    lado_v = pd.DataFrame({"i": d.index, "liga": d.liga, "eq": d.Away, "fecha": d.fecha, "cond": "V",
                           "gf": d.ag, "gc": d.hg, "btts": d.btts, "o25": d.o25})
    t = pd.concat([lado_l, lado_v]).sort_values(["fecha", "i"])
    t["marca"] = (t.gf > 0).astype(int)
    t["encaja"] = (t.gc > 0).astype(int)
    medidas = ["gf", "gc", "btts", "o25", "marca", "encaja"]
    g = t.groupby(["liga", "eq"])
    for m in medidas:
        t[f"f_{m}"] = g[m].transform(lambda s: s.shift(1).rolling(ventana, min_periods=3).mean())
    gc = t.groupby(["liga", "eq", "cond"])
    for m in ("gf", "gc", "btts", "o25"):
        t[f"c_{m}"] = gc[m].transform(lambda s: s.shift(1).rolling(ventana_cond, min_periods=3).mean())
    t["descanso"] = g.fecha.transform(lambda s: s.diff().dt.days.clip(upper=30))
    cols = [c for c in t.columns if c.startswith(("f_", "c_"))] + ["descanso"]
    L = t[t.cond == "L"].set_index("i")[cols].add_prefix("l_")
    V = t[t.cond == "V"].set_index("i")[cols].add_prefix("v_")
    d = d.join(L).join(V)
    # nivel de la liga en la temporada, hasta el día anterior
    for m in ("btts", "o25"):
        d[f"liga_{m}"] = d.groupby(["liga", "temporada"])[m].transform(
            lambda s: s.shift(1).expanding(min_periods=10).mean())
    d["liga_goles"] = d.groupby(["liga", "temporada"])["hg"].transform(
        lambda s: s.shift(1).expanding(min_periods=10).mean()) + d.groupby(["liga", "temporada"])["ag"].transform(
        lambda s: s.shift(1).expanding(min_periods=10).mean())
    return d


def construir():
    d = cargar()
    d = añadir_mercado(d)
    d = elo(d)
    d = forma(d)
    d["mes"] = d.fecha.dt.strftime("%Y-%m")
    return d


def columnas_juego(d):
    return [c for c in d.columns if c.startswith(("l_", "v_", "liga_"))] + ["elo_l", "elo_v", "elo_dif"]


# ---------------------------------------------------------- modelos
def xgb(X, y, semilla):
    from xgboost import XGBClassifier
    m = XGBClassifier(n_estimators=400, max_depth=2, learning_rate=0.03, subsample=0.8,
                      colsample_bytree=0.8, min_child_weight=20, reg_lambda=5.0,
                      objective="binary:logistic", random_state=semilla, n_jobs=4,
                      eval_metric="logloss", tree_method="hist")
    m.fit(X, y)
    return m


def predecir(ent, test, cols, y):
    ent = ent[ent[y].notna()]
    return np.mean([xgb(ent[cols].values, ent[y].values.astype(int), s).predict_proba(test[cols].values)[:, 1]
                    for s in SEMILLAS], axis=0)


def sig(dif):
    dif = np.asarray(dif, float)
    return dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif)))


def walk_forward(d):
    cj = columnas_juego(d)
    brazos = {"mercado": MKT, "completo": MKT + cj, "juego": cj}
    meses = sorted(m for m in d.mes.unique() if m >= DESDE_PRUEBA)
    salida = []
    for mes in meses:
        pasado, test = d[d.mes < mes], d[(d.mes == mes) & d.m_pl.notna()]
        if test.empty:
            continue
        for obj, y in OBJETIVOS.items():
            t = test[["liga", "fecha", "Home", "Away", y, "m_p_btts" if y == "btts" else "m_p_o25"]].copy()
            t.columns = ["liga", "fecha", "local", "visitante", "y", "poisson"]
            t["objetivo"], t["mes"] = obj, mes
            # base: tasa de la liga en los 365 días anteriores
            ult = pasado[pasado.fecha > test.fecha.min() - pd.Timedelta(days=365)]
            t["base"] = test.liga.map(ult.groupby("liga")[y].mean()).values
            for nombre, cols in brazos.items():
                t[nombre] = predecir(pasado, test, cols, y)
                # misma config entrenada SOLO con la liga propia
            for cod in LIGAS:
                sel = (test.liga == cod).values
                if sel.any():
                    t.loc[sel, "completo_sola"] = predecir(pasado[pasado.liga == cod], test[sel], MKT + cj, y)
            salida.append(t)
        print(f"  {mes}: {len(test)} partidos", flush=True)
    return pd.concat(salida, ignore_index=True)


def informe(r):
    brazos = ["base", "poisson", "mercado", "juego", "completo", "completo_sola"]
    lineas = ["# Ambos marcan y más/menos 2.5 en ARG, BRA y MEX (sin API)\n",
              f"Mes a mes desde {DESDE_PRUEBA}, entrenando cada mes con todo lo anterior. "
              "Brier (más bajo mejor) y sigmas del Brier emparejado partido a partido "
              "(positivo = mejor que la referencia). Fuente: football-data.co.uk (cierre del 1X2).\n",
              "**No hay cuota histórica de ambos marcan ni de más/menos 2.5 en estas ligas**: "
              "aquí no se mide contra ESE mercado. 'poisson' es lo que el 1X2 del mercado implica "
              "para esos mercados, sin entrenar nada.\n"]
    for obj in OBJETIVOS:
        lineas.append(f"\n## {obj}\n")
        lineas.append("| liga | n | tasa real | " + " | ".join(f"Brier {b}" for b in brazos)
                      + " | completo vs base | completo vs poisson | completo vs mercado | sola vs juntas |")
        lineas.append("|" + "---|" * (3 + len(brazos) + 4))
        for liga in list(LIGAS) + ["todas"]:
            s = r[(r.objetivo == obj) & ((r.liga == liga) | (liga == "todas"))].dropna(subset=brazos)
            if s.empty:
                continue
            e = {b: (s[b] - s.y) ** 2 for b in brazos}
            lineas.append(f"| {liga} | {len(s)} | {s.y.mean():.3f} | "
                          + " | ".join(f"{e[b].mean():.4f}" for b in brazos)
                          + f" | {sig(e['base'] - e['completo']):+.2f}s | {sig(e['poisson'] - e['completo']):+.2f}s"
                          f" | {sig(e['mercado'] - e['completo']):+.2f}s | {sig(e['completo'] - e['completo_sola']):+.2f}s |")
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    d = construir()
    print(f"{len(d)} partidos, {d.m_lam_l.notna().mean()*100:.1f}% con lambdas del 1X2")
    d.to_csv(os.path.join(CARPETA, "data", "tabla_rasgos.csv"), index=False)
    r = walk_forward(d)
    r.to_csv(os.path.join(CARPETA, "data", "walk_forward.csv"), index=False)
    txt = informe(r)
    open(os.path.join(CARPETA, "evaluacion.md"), "w", encoding="utf-8").write(txt)
    print(txt)
