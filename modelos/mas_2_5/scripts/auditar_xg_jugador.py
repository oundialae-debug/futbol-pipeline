"""
Auditoría de xg_jugador.py (28/09/2026): ¿hay un fallo silencioso?

1. ¿Los IDs de jugador de las alineaciones coinciden con los del box-score?
   Si no, la variable sería casi una constante (solo medias de posición).
2. ¿Los titulares de historico_lineups son los mismos que los no suplentes
   del box-score del mismo partido?
3. ¿La variable varía y se relaciona con los goles (sin modelo)?
   Correlación de (xg90 local + visitante) con el total de goles, frente a
   la de las medias de tiros a puerta que ya usa el modelo.
4. ¿Cuántos titulares tienen historial real (minutos previos) en cada mes?
"""
import sys, io, contextlib, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd

x = pd.read_csv("data/historico_xg_jugador.csv")
x = x[x.jugador_id.notna()].copy()
x["jugador_id"] = x.jugador_id.astype(int)
lu = pd.read_csv("data/historico_lineups.csv")
m = lu[lu.match_id.isin(x.match_id)]

# 1
tit = set()
for s in pd.concat([m.local_ids, m.visitante_ids]).dropna():
    tit |= {int(v) for v in s.split("|")}
xs = set(x.jugador_id)
print(f"1. titulares distintos en alineaciones (partidos con box-score): {len(tit)}; "
      f"presentes en el box-score: {len(tit & xs)} ({len(tit & xs)/len(tit)*100:.1f}%)")

# 2
coinc = []
por = {k: g for k, g in x.groupby("match_id")}
for r in m.itertuples():
    g = por.get(r.match_id)
    if g is None or not isinstance(r.local_ids, str) or not isinstance(r.visitante_ids, str):
        continue
    b = set(g[g.suplente == False].jugador_id)
    l = {int(v) for v in (r.local_ids + "|" + r.visitante_ids).split("|")}
    coinc.append(len(l & b) / len(l))
print(f"2. titulares de la alineación que aparecen como titulares en el box-score: "
      f"{np.mean(coinc)*100:.1f}% (media de {len(coinc)} partidos); valores de 'suplente': "
      f"{x.suplente.value_counts(dropna=False).to_dict()}")

# 3 y 4: reconstruir la variable como xg_jugador.py
src = open("scripts/xg_jugador.py", encoding="utf-8").read().split("with contextlib.redirect_stdout")[0]
exec(src)
import modelo_xgboost as M, rasgos_mas25 as R
with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
v = variables(hist)
h = hist.merge(v, on="match_id")
h["f"] = pd.to_datetime(h.fecha, format="mixed", utc=True)
h["total"] = h.goles_l + h.goles_v
h = h[h.f >= "2025-10-01"].dropna(subset=["loc_xg90", "total"])
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"), pd.read_csv("data/historico_h2h_profundo.csv"))
h = h.merge(bc[["match_id", "loc_m_shots_on_target", "vis_m_shots_on_target",
                "loc_m_contra_shots_on_target", "vis_m_contra_shots_on_target",
                "loc_cp_del_ga90", "vis_cp_del_ga90"]], on="match_id")
h["xg_suma"] = h.loc_xg90 + h.vis_xg90
h["xga_suma"] = h.xg_suma + h.loc_xa90 + h.vis_xa90
h["tiros_suma"] = (h.loc_m_shots_on_target + h.vis_m_shots_on_target
                   + h.loc_m_contra_shots_on_target + h.vis_m_contra_shots_on_target)
h["ga_suma"] = h.loc_cp_del_ga90 + h.vis_cp_del_ga90
print(f"\n3. {len(h)} partidos oct 2025 - sep 2026. Correlación con el total de goles:")
for c in ("xg_suma", "xga_suma", "tiros_suma", "ga_suma"):
    print(f"   {c:10s} r = {h[c].corr(h.total):+.3f}   (desv. típica {h[c].std():.3f}, media {h[c].mean():.3f})")
print(f"   xg_suma vs tiros_suma: r = {h.xg_suma.corr(h.tiros_suma):+.3f}")
