"""
Pronóstico de ambos marcan y más/menos 2.5 para partidos de una liga fuera del
proyecto (data/sueltos/<carpeta>/, lo baja descargar_partido.py). Tema aparte.

  modelo de la liga  Poisson de ataque/defensa con los partidos jugados de la
                     temporada (peso por recencia, vida media 120 días,
                     encogimiento ridge, factor campo).
  prueba             cada partido de las últimas ~40 fechas pronosticado solo
                     con los anteriores, contra la tasa de la liga (sigmas).
  mercado            mediana de casas sin margen (nada lo ha batido en el
                     proyecto: es la referencia).
Uso: python modelos/sueltos/pronostico_partido.py <carpeta>
"""
import sys, json, glob, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor

D = f"data/sueltos/{sys.argv[1]}"


def ajustar(d, hoy, vida=120, alpha=0.01):
    d = d.copy(); d["w"] = 0.5 ** ((hoy - d.dt).dt.days / vida)
    eq = sorted(set(d.local_id) | set(d.visitante_id)); ix = {e: i for i, e in enumerate(eq)}; n = len(eq)
    def X(at, de, casa):
        M = np.zeros((len(at), 2 * n + 1))
        for k, (a, b) in enumerate(zip(at, de)):
            if a in ix: M[k, ix[a]] = 1
            if b in ix: M[k, n + ix[b]] = -1
        M[:, 2 * n] = casa
        return M
    A = np.vstack([X(d.local_id, d.visitante_id, np.ones(len(d))), X(d.visitante_id, d.local_id, np.zeros(len(d)))])
    m = PoissonRegressor(alpha=alpha, max_iter=3000).fit(A, np.r_[d.goles_l, d.goles_v], sample_weight=np.r_[d.w, d.w])
    return lambda a, b, c: float(m.predict(X([a], [b], [c]))[0])


def probs(l1, l2):
    g = np.arange(11); M = np.outer(poisson.pmf(g, l1), poisson.pmf(g, l2)); tot = np.add.outer(g, g)
    return {"btts": (1 - np.exp(-l1)) * (1 - np.exp(-l2)), "o25": M[tot > 2.5].sum()}


def main():
    t = pd.read_csv(f"{D}/temporada.csv")
    f = t[t.estado.str.lower().str.contains("finish") & t.goles_l.notna()].copy()
    f["dt"] = pd.to_datetime(f.fecha, utc=True)
    f = f.sort_values("dt")
    g = f.goles_l + f.goles_v
    print(f"Liga: {len(f)} partidos jugados, {g.mean():.2f} goles/partido, ambos marcan "
          f"{((f.goles_l > 0) & (f.goles_v > 0)).mean()*100:.0f}%, más de 2.5 {(g > 2.5).mean()*100:.0f}%")
    res = []
    for d0 in sorted(f.dt.dt.date.unique())[-40:]:
        ent, te = f[f.dt.dt.date < d0], f[f.dt.dt.date == d0]
        if len(ent) < 100:
            continue
        fn = ajustar(ent, pd.Timestamp(d0, tz="UTC"))
        for _, r in te.iterrows():
            p = probs(fn(r.local_id, r.visitante_id, 1), fn(r.visitante_id, r.local_id, 0))
            res.append({"pb": p["btts"], "po": p["o25"], "yb": int(r.goles_l > 0 and r.goles_v > 0),
                        "yo": int(r.goles_l + r.goles_v > 2.5),
                        "bb": ((ent.goles_l > 0) & (ent.goles_v > 0)).mean(),
                        "bo": ((ent.goles_l + ent.goles_v) > 2.5).mean()})
    r = pd.DataFrame(res)
    sig = lambda d: d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    if len(r) > 10:
        print(f"Prueba hacia delante ({len(r)} partidos): ambos marcan {sig((r.bb-r.yb)**2-(r.pb-r.yb)**2):+.2f}s, "
              f"más de 2.5 {sig((r.bo-r.yo)**2-(r.po-r.yo)**2):+.2f}s contra la tasa de la liga")
    fn = ajustar(f, pd.Timestamp.now(tz="UTC"))
    for p in json.load(open(f"{D}/partidos.json")):
        l1, l2 = fn(p["local_id"], p["visitante_id"], 1), fn(p["visitante_id"], p["local_id"], 0)
        pr = probs(l1, l2)
        c = json.load(open(f"{D}/raw/cuotas_{p['match_id']}.json"))
        c = c.get("data", c) if isinstance(c, dict) else c
        rows = [(m["market"], m.get("bookmakerName"), str(v["value"]), float(v["odd"]))
                for b in c for m in b.get("odds", []) if m["market"] in ("Total Goals 2.5", "Both Teams To Score")
                for v in m.get("values", []) if v.get("odd")]
        q = pd.DataFrame(rows, columns=["mercado", "casa", "lado", "cuota"])
        print(f"\n{p['local']} - {p['visitante']} ({p['fecha']}): goles esperados {l1:.2f}-{l2:.2f}")
        print(f"  modelo liga: ambos marcan sí {pr['btts']*100:.0f}%, más de 2.5 {pr['o25']*100:.0f}%")
        for mk in ("Both Teams To Score", "Total Goals 2.5"):
            gq = q[q.mercado == mk]
            if gq.empty:
                print(f"  {mk}: sin cuotas"); continue
            med = gq.groupby("lado").cuota.median(); pm = (1 / med) / (1 / med).sum()
            print(f"  mercado {mk} ({gq.casa.nunique()} casas): " +
                  ", ".join(f"{l} {med[l]:.2f} ({pm[l]*100:.0f}%, mejor {gq[gq.lado==l].cuota.max():.2f})" for l in med.index))
        lu = json.load(open(f"{D}/raw/lineups_{p['match_id']}.json"))
        lu = lu[0] if isinstance(lu, list) and lu else lu
        n = [len((lu or {}).get(s, {}).get("initialLineup") or []) if isinstance(lu, dict) else 0 for s in ("homeTeam", "awayTeam")]
        print(f"  onces en la API: {n}")
    box = glob.glob(f"{D}/raw/boxscore_*.json")
    vacios = sum(1 for b in box if json.load(open(b)) in ([], {}))
    print(f"\nBox-scores de jugadores: {len(box)} pedidos, {vacios} vacíos")


if __name__ == "__main__":
    main()
