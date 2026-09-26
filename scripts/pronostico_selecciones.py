"""
4 pronósticos para esta noche (26/09/2026): 1X2 y ambos marcan de
Inglaterra-España y Chequia-Croacia. Tema APARTE del proyecto de ambos marcan.

Modelo (Poisson de ataque/defensa por selección, sin cuotas dentro):

  log(goles esperados de A contra B) = mu + casa + ataque_A - defensa_B
                                       + b_at * calidad_A - b_def * calidad_B

  - Se ajusta con TODOS los partidos de las 4 selecciones desde 2025 (76), con
    más peso a lo reciente (vida media 365 días). Dos versiones: con goles y
    con xG (el xG es menos ruidoso: el 4-6 de Francia-Inglaterra pesa menos);
    se promedian.
  - ataque/defensa van encogidos hacia cero (ridge): con 1-3 partidos un rival
    no puede quedarse con un valor extremo.
  - calidad = parte de los minutos de esa selección jugados por futbolistas
    con >= 900 minutos en 2025/26 en nuestras ligas (proxy exógeno de nivel).
    Sin esto, Gibraltar o Andorra se encogen hacia la media y golearles
    parecería mérito.
  - casa: se estima; los partidos del Mundial cuentan como campo neutral salvo
    para México.

Nota de jugador (notas_jugadores.csv): ajuste de forma sobre el once de hoy.
  forma_equipo = media de la nota justa del once de HOY - media de la nota con
  la selección de su once HABITUAL (los 11 con más minutos en sus últimos 4
  partidos, que es lo que el Poisson ya "conoce"). Recoge la forma de club y
  también las bajas: si falta una estrella, el once de hoy baja.
  -> multiplica sus goles esperados por exp(B_FORMA * forma) y divide los del
  rival por lo mismo a la mitad (la forma pesa más en ataque). B_FORMA fijado a
  mano (no hay partidos de selecciones con cuota para calibrarlo): se enseña
  también el pronóstico sin ajuste para ver cuánto mueve.

Salida: pronosticos_selecciones.md y comparación con el mercado (mediana de
casas sin margen, data/nations_league_hoy.csv).
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor

HOY = pd.Timestamp("2026-09-26")
VIDA_MEDIA = 365.0
ALPHA = 0.02            # fuerza del encogimiento ridge
B_FORMA = 0.5           # 0.1 puntos de nota del once -> ~5% de goles
ANFITRIONES_MUNDIAL = {"Mexico", "USA", "United States", "Canada"}
CARPETA = "data/selecciones"


def cargar():
    p = pd.read_csv(f"{CARPETA}/partidos.csv")
    p = p[p.terminado & p.goles_l.notna()].copy()
    e = pd.read_csv(f"{CARPETA}/estadisticas_partido.csv")
    xg = e[e.estadistica == "Expected Goals"].copy()
    xg["valor"] = pd.to_numeric(xg.valor, errors="coerce")
    xg = xg.set_index(["match_id", "equipo_id"]).valor
    p["xg_l"] = [xg.get((m, t), np.nan) for m, t in zip(p.match_id, p.local_id)]
    p["xg_v"] = [xg.get((m, t), np.nan) for m, t in zip(p.match_id, p.visitante_id)]
    neutral = (p.competicion == "World Cup") & ~p.local.isin(ANFITRIONES_MUNDIAL)
    p["casa"] = (~neutral).astype(float)
    p["w"] = 0.5 ** ((HOY - pd.to_datetime(p.fecha)).dt.days / VIDA_MEDIA)
    return p


def calidad_equipos():
    """Parte de minutos jugados por futbolistas con >= 900' en 2025/26 en nuestras ligas."""
    j = pd.read_csv(f"{CARPETA}/jugadores_partido.csv")
    j["minutos"] = pd.to_numeric(j.minutos, errors="coerce").fillna(0)
    js = pd.read_csv("data/historico_jugador_stats.csv")
    js = js[js.temporada == "25/26"]
    buenos = set(js.groupby("jugador_id").minutos.sum().loc[lambda s: s >= 900].index)
    j["bueno"] = j.jugador_id.isin(buenos)
    return j.groupby("equipo_id").apply(lambda g: (g.minutos * g.bueno).sum() / max(g.minutos.sum(), 1))


def filas_largas(p, objetivo):
    """Una fila por equipo y partido: (atacante, defensor, casa, y, peso)."""
    a = pd.DataFrame({"at": p.local_id, "de": p.visitante_id, "casa": p.casa,
                      "y": p[f"{objetivo}_l"], "w": p.w})
    b = pd.DataFrame({"at": p.visitante_id, "de": p.local_id, "casa": 0.0,
                      "y": p[f"{objetivo}_v"], "w": p.w})
    return pd.concat([a, b]).dropna(subset=["y"])


def ajustar(p, q, objetivo):
    d = filas_largas(p, objetivo)
    equipos = sorted(set(d["at"]) | set(d["de"]))
    idx = {t: i for i, t in enumerate(equipos)}
    n = len(equipos)
    q_def = float(q.mean())

    def matriz(at, de, casa):
        X = np.zeros((len(at), 2 * n + 3))
        for k, (x, y) in enumerate(zip(at, de)):
            if x in idx:
                X[k, idx[x]] = 1
            if y in idx:
                X[k, n + idx[y]] = -1
        X[:, 2 * n] = casa
        # calidad escalada x10 para que el ridge apenas la toque (es la variable
        # que ancla a los rivales con pocos partidos)
        X[:, 2 * n + 1] = [10 * q.get(x, q_def) for x in at]
        X[:, 2 * n + 2] = [-10 * q.get(y, q_def) for y in de]
        return X

    m = PoissonRegressor(alpha=ALPHA, max_iter=3000)
    m.fit(matriz(d["at"], d["de"], d["casa"]), d.y, sample_weight=d.w)
    return lambda at, de, casa: float(m.predict(matriz([at], [de], [casa]))[0]), m.coef_[2 * n:]


def probabilidades(lam_l, lam_v, maxg=10):
    g = np.arange(maxg + 1)
    M = np.outer(poisson.pmf(g, lam_l), poisson.pmf(g, lam_v))
    return {"1": np.tril(M, -1).sum(), "X": np.trace(M), "2": np.triu(M, 1).sum(),
            "btts": (1 - poisson.pmf(0, lam_l)) * (1 - poisson.pmf(0, lam_v)),
            "o25": 1 - sum(M[i, j] for i in g for j in g if i + j <= 2)}


def forma(notas, equipo):
    n = notas[notas.seleccion == equipo]
    o, h = n[n.once_probable], n[n.once_habitual]
    return float(o.nota.mean() - h.sel_nota_bruta.fillna(h.nota).mean()), o


def mercado(partido):
    """Mediana de casas sin margen: {"1","X","2","btts"} en tanto por uno."""
    try:
        c = pd.read_csv("data/nations_league_hoy.csv")
    except FileNotFoundError:
        return {}
    c = c[c.partido == partido]
    out = {}
    for m, claves in (("Full Time Result", {"Home": "1", "Draw": "X", "Away": "2"}),
                      ("Both Teams To Score", {"Yes": "btts"})):
        g = c[c.mercado == m]
        tot = (1 / g.mediana).sum()
        for lado, o in zip(g.lado, g.mediana):
            if lado in claves:
                out[claves[lado]] = 1 / o / tot
    return out


def main():
    p = cargar()
    q = calidad_equipos()
    eq = json.load(open(f"{CARPETA}/equipos.json"))
    ids = eq["equipos"]
    notas = pd.read_csv(f"{CARPETA}/notas_jugadores.csv")

    f_goles, coef_g = ajustar(p, q, "goles")
    f_xg, coef_x = ajustar(p[p.xg_l.notna()], q, "xg")
    print(f"{len(p)} partidos ({p.xg_l.notna().sum()} con xG). "
          f"Casa: goles x{np.exp(coef_g[0]):.2f}, xG x{np.exp(coef_x[0]):.2f}")
    print("Calidad (parte de minutos de jugadores de nuestras ligas):",
          {k: round(q.get(v, np.nan), 2) for k, v in ids.items()}, "\n")

    lineas = ["# Pronósticos Nations League, 26/09/2026", "",
              "Tema aparte del proyecto de ambos marcan. Modelo: Poisson ataque/defensa con los "
              f"{len(p)} partidos de las 4 selecciones desde 2025 (goles y xG promediados), "
              "anclado con la calidad de plantilla, más ajuste de forma del once con la nota justa "
              "de cada jugador (`notas_jugadores.csv`). Mercado = mediana de casas sin margen.", ""]
    for loc, vis, _ in eq["cruces"]:
        lam = [np.mean([f(ids[loc], ids[vis], 1.0) for f in (f_goles, f_xg)]),
               np.mean([f(ids[vis], ids[loc], 0.0) for f in (f_goles, f_xg)])]
        fl, ol = forma(notas, loc)
        fv, ov = forma(notas, vis)
        lam_f = [lam[0] * np.exp(B_FORMA * fl - 0.5 * B_FORMA * fv),
                 lam[1] * np.exp(B_FORMA * fv - 0.5 * B_FORMA * fl)]
        sin, con = probabilidades(*lam), probabilidades(*lam_f)
        print(f"== {loc} - {vis} ==")
        print(f"  goles esperados sin forma {lam[0]:.2f}-{lam[1]:.2f}, con forma {lam_f[0]:.2f}-{lam_f[1]:.2f}")
        print(f"  forma del once: {loc} {fl:+.2f}, {vis} {fv:+.2f} (nota justa - nota con selección)")
        for k in ("1", "X", "2", "btts", "o25"):
            print(f"  {k:5s} sin forma {sin[k]*100:5.1f}%   con forma {con[k]*100:5.1f}%")
        lineas += [f"## {loc} - {vis}", "",
                   f"Goles esperados: {lam_f[0]:.2f} - {lam_f[1]:.2f} (sin ajuste de forma "
                   f"{lam[0]:.2f} - {lam[1]:.2f}). Forma del once: {loc} {fl:+.2f}, {vis} {fv:+.2f}.", "",
                   "| | modelo | sin forma | mercado (sin margen) | cuota justa del modelo |",
                   "|---|---|---|---|---|"]
        mk = mercado(f"{loc} - {vis}")
        for k, nombre in (("1", f"gana {loc}"), ("X", "empate"), ("2", f"gana {vis}"),
                          ("btts", "ambos marcan: sí")):
            m_ = f"{mk[k]*100:.1f}%" if k in mk else "-"
            lineas.append(f"| {nombre} | {con[k]*100:.1f}% | {sin[k]*100:.1f}% | {m_} | {1/con[k]:.2f} |")
        lineas += ["", f"Once {ol.fuente_once.iloc[0]} {loc}: " + ", ".join(ol.jugador),
                   f"Once {ov.fuente_once.iloc[0]} {vis}: " + ", ".join(ov.jugador), ""]
        print()
    lineas += ["## Cuánto fiarse", "",
               "Prueba hacia delante (26/09): cada partido de las 4 selecciones desde oct-2025 (53) "
               "pronosticado solo con los anteriores.", "",
               "- 1X2: Brier 0.540 contra 0.627 de las frecuencias (+1.37s), acierta el 64%. Algo "
               "sabe, pero la mayoría eran partidos fáciles contra selecciones pequeñas.",
               "- Ambos marcan: Brier 0.514 contra 0.498 de la tasa base (-0.40s). **No bate a la "
               "tasa base**: en ambos marcan este modelo no aporta.",
               "- No hay cuotas históricas de selecciones para medirlo contra el mercado. El ajuste "
               "de forma (B_FORMA) está puesto a mano, no calibrado.", ""]
    open("pronosticos_selecciones.md", "w").write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    main()
