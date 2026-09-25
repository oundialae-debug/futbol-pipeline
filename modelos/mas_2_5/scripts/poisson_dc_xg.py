"""
Poisson de goles con las dos mejoras (25/09/2026), fijadas antes de mirar:

  DC  corrección Dixon-Coles de los marcadores bajos (0-0, 1-0, 0-1, 1-1):
      tau(0,0)=1-λl·λv·ρ, tau(0,1)=1+λl·ρ, tau(1,0)=1+λv·ρ, tau(1,1)=1-ρ.
      ρ se estima CADA MES por máxima verosimilitud (rejilla -0.25..0.25) solo
      con los partidos de entrenamiento.
  xG  el Poisson aprende de los goles ESPERADOS (xG) en vez de los goles:
      menos suerte. Donde no hay xG (casi todo 2024/25) usa los goles.

Versiones: goles, goles+DC, xG, xG+DC; cada una sola y mezclada 50/50 con el
XGBoost de 28. Resto igual que modelo_goles_poisson.py (vida media 365 días,
alpha 0.01, mes a mes, mismos 2.527 partidos con cuota).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import poisson
from scipy.sparse import csr_matrix, hstack
from sklearn.linear_model import PoissonRegressor

VIDA_MEDIA, ALPHA = 365.0, 0.01
RHOS = np.round(np.arange(-0.25, 0.2501, 0.01), 2)
h = pd.read_csv("data/historico_partidos.csv").dropna(subset=["goles_l", "goles_v"])
h["f"] = pd.to_datetime(h.fecha, format="mixed", utc=True)
h["mes"] = h.f.dt.strftime("%Y-%m")
for lado, g in (("l", "goles_l"), ("v", "goles_v")):
    xg = pd.to_numeric(h.get(f"{lado}_expected_goals"), errors="coerce")
    h[f"xg_{lado}"] = xg.where(xg.notna(), h[g])
print(f"xG disponible en {pd.to_numeric(h.l_expected_goals, errors='coerce').notna().mean()*100:.0f}% "
      f"de los partidos (resto: goles)")
prev = pd.read_csv("data/cuota_como_variable.csv")

equipos = {e: i for i, e in enumerate(pd.unique(h[["local_id", "visitante_id"]].values.ravel()))}
ligas = {l: i for i, l in enumerate(h.liga_id.unique())}
nE, nL = len(equipos), len(ligas)


def diseno(att, dfn, liga, casa):
    n = len(att); fila = np.arange(n)
    A = csr_matrix((np.ones(n), (fila, [equipos[e] for e in att])), shape=(n, nE))
    D = csr_matrix((np.ones(n), (fila, [equipos[e] for e in dfn])), shape=(n, nE))
    L = csr_matrix((np.ones(n), (fila, [ligas[x] for x in liga])), shape=(n, nL))
    return hstack([A, D, L, csr_matrix(np.asarray(casa, float).reshape(-1, 1))]).tocsr()


def lambdas(m, df):
    return (m.predict(diseno(df.local_id, df.visitante_id, df.liga_id, np.ones(len(df)))),
            m.predict(diseno(df.visitante_id, df.local_id, df.liga_id, np.zeros(len(df)))))


def ajustar(ent, hoy, obj_l, obj_v):
    X = diseno(np.r_[ent.local_id, ent.visitante_id], np.r_[ent.visitante_id, ent.local_id],
               np.r_[ent.liga_id, ent.liga_id], np.r_[np.ones(len(ent)), np.zeros(len(ent))])
    dias = (hoy - ent.f).dt.days.values
    w = 0.5 ** (np.r_[dias, dias] / VIDA_MEDIA)
    return PoissonRegressor(alpha=ALPHA, max_iter=1000).fit(X, np.r_[ent[obj_l], ent[obj_v]], sample_weight=w)


def tau(i, j, ll, lv, rho):
    t = np.ones_like(ll)
    t = np.where((i == 0) & (j == 0), 1 - ll * lv * rho, t)
    t = np.where((i == 0) & (j == 1), 1 + ll * rho, t)
    t = np.where((i == 1) & (j == 0), 1 + lv * rho, t)
    t = np.where((i == 1) & (j == 1), 1 - rho, t)
    return np.clip(t, 1e-6, None)


def p_mas25(ll, lv, rho):
    p_bajo = sum(tau(i, j, ll, lv, rho) * poisson.pmf(i, ll) * poisson.pmf(j, lv)
                 for i in range(3) for j in range(3) if i + j <= 2)
    return 1 - p_bajo


def estimar_rho(ent, ll, lv, hoy):
    """Máxima verosimilitud de ρ sobre los marcadores REALES de entrenamiento."""
    gl, gv = ent.goles_l.values.astype(int), ent.goles_v.values.astype(int)
    w = 0.5 ** ((hoy - ent.f).dt.days.values / VIDA_MEDIA)
    ll_ = [np.sum(w * np.log(tau(gl, gv, ll, lv, r))) for r in RHOS]
    return RHOS[int(np.argmax(ll_))]


res, rhos = [], {}
for mes in sorted(prev.mes.unique()):
    hoy = pd.Timestamp(mes + "-01", tz="UTC")
    ent = h[h.f < hoy]
    val = h[(h.mes == mes) & h.match_id.isin(prev.match_id)]
    fila = {"match_id": val.match_id.values}
    for fuente, (ol, ov) in (("goles", ("goles_l", "goles_v")), ("xg", ("xg_l", "xg_v"))):
        m = ajustar(ent, hoy, ol, ov)
        ll_e, lv_e = lambdas(m, ent)
        rho = estimar_rho(ent, ll_e, lv_e, hoy)
        rhos[(mes, fuente)] = rho
        ll, lv = lambdas(m, val)
        fila[f"p_{fuente}"] = p_mas25(ll, lv, 0.0)
        fila[f"p_{fuente}_dc"] = p_mas25(ll, lv, rho)
    res.append(pd.DataFrame(fila))
d = prev.merge(pd.concat(res), on="match_id")
MOD = ["p_goles", "p_goles_dc", "p_xg", "p_xg_dc"]
for c in MOD:
    d[f"{c}_mezcla"] = (d[c] + d.p_28) / 2
d.to_csv("data/poisson_dc_xg.csv", index=False)
r = pd.Series(rhos)
print(f"ρ estimado por mes: goles {r.xs('goles', level=1).min():+.2f}..{r.xs('goles', level=1).max():+.2f}, "
      f"xG {r.xs('xg', level=1).min():+.2f}..{r.xs('xg', level=1).max():+.2f}\n")


def sig(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


bm = 2 * (d.p_mercado - d.y) ** 2
b28 = 2 * (d.p_28 - d.y) ** 2
gp = d.dropna(subset=["p_pc"])
print(f"{len(d)} partidos mes a mes. Positivo = el modelo es mejor.")
print(f"{'modelo':26s} {'vs XGB 28':>10s} {'vs media casas':>15s} {'vs Pinnacle':>12s} {'acierto':>8s} {'apuesta cuota media':>21s}")
for c in ["p_28"] + MOD + [f"{m}_mezcla" for m in MOD]:
    b = 2 * (d[c] - d.y) ** 2
    vo, vu = d[c] * d["Avg>2.5"] - 1, (1 - d[c]) * d["Avg<2.5"] - 1
    over, under = (vo > 0) & (vo >= vu), (vu > 0) & (vu > vo)
    ret = np.concatenate([(d.y[over] * d["Avg>2.5"][over] - 1).values,
                          ((1 - d.y[under]) * d["Avg<2.5"][under] - 1).values])
    print(f"{c:26s} {sig(b28 - b) if c != 'p_28' else 0:+9.2f}s {sig(bm - b):+14.2f}s "
          f"{sig(2*(gp.p_pc-gp.y)**2 - 2*(gp[c]-gp.y)**2):+11.2f}s {((d[c] > .5) == d.y).mean()*100:7.1f}% "
          f"{ret.mean()*100:+8.2f}% ({len(ret)} ap.)")
print(f"{'media de casas':26s} {'':10s} {'':15s} {sig(2*(gp.p_pc-gp.y)**2 - bm[gp.index]):+11.2f}s "
      f"{((d.p_mercado > .5) == d.y).mean()*100:7.1f}%")
