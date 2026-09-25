"""
Otra arquitectura: modelo de GOLES tipo Dixon-Coles (25/09/2026).

En vez de clasificar "Más 2.5 sí/no", predice los goles de cada equipo:
    log(goles esperados) = liga + ventaja_local + ataque_equipo + defensa_rival
(regresión de Poisson, un ataque y una defensa por equipo). Usa el marcador
entero: un 4-3 enseña más que "Más". Total ~ Poisson(λ_local + λ_visit),
P(Más 2.5) = 1 - P(0, 1 o 2 goles).

Todo fijado ANTES de mirar resultados (no se ajusta nada contra la prueba):
  - pesos por antigüedad: vida media 365 días
  - regularización alpha=0.01 (solo para que ataque/defensa sean estimables)
  - mezcla con el XGBoost de 28: 50/50, sin buscar el peso
Evaluación: mes a mes (cada mes, ajustado solo con lo anterior) sobre los
mismos 2.527 partidos con cuota de cuota_como_variable.py, contra la media
de casas y Pinnacle cierre, y apuestas con la cuota media.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import poisson
from scipy.sparse import csr_matrix, hstack
from sklearn.linear_model import PoissonRegressor

VIDA_MEDIA, ALPHA = 365.0, 0.01
h = pd.read_csv("data/historico_partidos.csv").dropna(subset=["goles_l", "goles_v"])
h["f"] = pd.to_datetime(h.fecha, format="mixed", utc=True)
h["mes"] = h.f.dt.strftime("%Y-%m")
prev = pd.read_csv("data/cuota_como_variable.csv")        # p_28 mes a mes + cuotas, mismos partidos

equipos = {e: i for i, e in enumerate(pd.unique(h[["local_id", "visitante_id"]].values.ravel()))}
ligas = {l: i for i, l in enumerate(h.liga_id.unique())}
nE, nL = len(equipos), len(ligas)


def diseno(att, dfn, liga, casa):
    n = len(att)
    fila = np.arange(n)
    A = csr_matrix((np.ones(n), (fila, [equipos[e] for e in att])), shape=(n, nE))
    D = csr_matrix((np.ones(n), (fila, [equipos[e] for e in dfn])), shape=(n, nE))
    L = csr_matrix((np.ones(n), (fila, [ligas[x] for x in liga])), shape=(n, nL))
    return hstack([A, D, L, csr_matrix(np.asarray(casa, float).reshape(-1, 1))]).tocsr()


def ajustar(ent, hoy):
    X = diseno(np.r_[ent.local_id, ent.visitante_id], np.r_[ent.visitante_id, ent.local_id],
               np.r_[ent.liga_id, ent.liga_id], np.r_[np.ones(len(ent)), np.zeros(len(ent))])
    y = np.r_[ent.goles_l, ent.goles_v]
    dias = np.r_[(hoy - ent.f).dt.days, (hoy - ent.f).dt.days]
    w = 0.5 ** (dias / VIDA_MEDIA)
    return PoissonRegressor(alpha=ALPHA, max_iter=1000).fit(X, y, sample_weight=w)


res = []
for mes in sorted(prev.mes.unique()):
    hoy = pd.Timestamp(mes + "-01", tz="UTC")
    ent = h[h.f < hoy]
    val = h[(h.mes == mes) & h.match_id.isin(prev.match_id)]
    # equipos nuevos (ascendidos sin historial): ataque/defensa = 0 (media)
    for e in pd.unique(val[["local_id", "visitante_id"]].values.ravel()):
        equipos.setdefault(e, len(equipos))
    m = ajustar(ent, hoy)
    lam_l = m.predict(diseno(val.local_id, val.visitante_id, val.liga_id, np.ones(len(val))))
    lam_v = m.predict(diseno(val.visitante_id, val.local_id, val.liga_id, np.zeros(len(val))))
    res.append(pd.DataFrame({"match_id": val.match_id.values,
                             "p_goles": 1 - poisson.cdf(2, lam_l + lam_v),
                             "goles_esperados": lam_l + lam_v}))
d = prev.merge(pd.concat(res), on="match_id")
d["p_mezcla"] = (d.p_goles + d.p_28) / 2
d.to_csv("data/modelo_goles_poisson.csv", index=False)


def sig(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


print(f"{len(d)} partidos, {d.mes.min()} a {d.mes.max()}; goles esperados medios "
      f"{d.goles_esperados.mean():.2f} (reales {(d.y).mean():.3f} de Más 2.5)\n")
bm = 2 * (d.p_mercado - d.y) ** 2
gp = d.dropna(subset=["p_pc"])
print(f"{'modelo':30s} {'vs media casas':>15s} {'vs Pinnacle cierre':>19s} {'acierto':>8s} {'vs XGB 28':>10s}")
b28 = 2 * (d.p_28 - d.y) ** 2
for c, n in (("p_28", "XGBoost 28 (actual)"), ("p_goles", "Poisson de goles"), ("p_mezcla", "mezcla 50/50")):
    b = 2 * (d[c] - d.y) ** 2
    print(f"{n:30s} {sig(bm - b):+14.2f}s {sig(2*(gp.p_pc-gp.y)**2 - 2*(gp[c]-gp.y)**2):+18.2f}s "
          f"{((d[c] > .5) == d.y).mean()*100:7.1f}% {sig(b28 - b) if c != 'p_28' else 0:+9.2f}s")
print(f"{'media de casas':30s} {'':15s} {sig(2*(gp.p_pc-gp.y)**2 - 2*(gp.p_mercado-gp.y)**2):+18.2f}s "
      f"{((d.p_mercado > .5) == d.y).mean()*100:7.1f}%")
print("\nPor temporada (vs media de casas):")
d["temp"] = np.where(d.mes < "2026-07", "2025/26", "2026/27")
for t, g in d.groupby("temp"):
    bmg = 2 * (g.p_mercado - g.y) ** 2
    print(f"  {t} n={len(g)}: " + "  ".join(f"{c} {sig(bmg - 2*(g[c]-g.y)**2):+.2f}s"
                                            for c in ("p_28", "p_goles", "p_mezcla")))
print("\nApostando 1 unidad con la cuota MEDIA al lado con valor:")
for c in ("p_goles", "p_mezcla"):
    for umbral in (0.0, 0.03, 0.05):
        vo, vu = d[c] * d["Avg>2.5"] - 1, (1 - d[c]) * d["Avg<2.5"] - 1
        over, under = (vo > umbral) & (vo >= vu), (vu > umbral) & (vu > vo)
        ret = np.concatenate([(d.y[over] * d["Avg>2.5"][over] - 1).values,
                              ((1 - d.y[under]) * d["Avg<2.5"][under] - 1).values])
        print(f"  {c:9s} umbral {umbral:>3.0%}: {len(ret):5d} apuestas  rentabilidad {ret.mean()*100:+6.2f}% "
              f"(±{ret.std(ddof=1)/np.sqrt(len(ret))*100:.2f}, {sig(ret):+.2f}s)")
