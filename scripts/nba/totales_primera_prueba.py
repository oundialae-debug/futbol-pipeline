"""NBA totales: primera prueba con lo que ya hay (sin gastar API).

Rasgos solo de marcadores (API, fase 1) + linea de cierre de MGM (Kaggle).
Pregunta: la prediccion del modelo, MENOS la linea, dice algo de hacia donde
cae el total real? Si no, un modelo de solo puntos no tiene nada que aportar.
"""
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

p = pd.read_csv("data/nba/partidos.csv")
p = p[p.estado == "Finished"].copy()
p["fecha_utc"] = pd.to_datetime(p.fecha, utc=True)
p["dia"] = p.fecha_utc.dt.tz_convert("America/New_York").dt.date.astype(str)
p["pl"] = p.cuartos_local.map(lambda s: sum(json.loads(s)))
p["pv"] = p.cuartos_visitante.map(lambda s: sum(json.loads(s)))
p["prorroga"] = p.cuartos_local.map(lambda s: len(json.loads(s)) > 4)
p = p.sort_values("fecha_utc").reset_index(drop=True)

# vista por equipo (una fila por equipo y partido)
a = pd.DataFrame({"id": p.id, "t": p.fecha_utc, "temp": p.temporada, "eq": p.local_id,
                  "pf": p.pl, "pc": p.pv, "local": 1})
b = pd.DataFrame({"id": p.id, "t": p.fecha_utc, "temp": p.temporada, "eq": p.visitante_id,
                  "pf": p.pv, "pc": p.pl, "local": 0})
e = pd.concat([a, b]).sort_values(["eq", "t"]).reset_index(drop=True)
g = e.groupby(["eq", "temp"])
for col in ["pf", "pc"]:
    e[f"{col}_temp"] = g[col].transform(lambda s: s.shift(1).expanding().mean())
    e[f"{col}_10"] = g[col].transform(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
e["jugados"] = g.cumcount()
e["descanso"] = e.groupby("eq").t.diff().dt.total_seconds().div(86400).clip(upper=7)
e["b2b"] = (e.descanso < 1.6).astype(int)
R = ["pf_temp", "pc_temp", "pf_10", "pc_10", "jugados", "descanso", "b2b"]
L = e[e.local == 1].set_index("id")[R].add_prefix("l_")
V = e[e.local == 0].set_index("id")[R].add_prefix("v_")
x = p.set_index("id").join(L).join(V)

# lineas de cierre MGM
k = pd.read_csv("data/nba/cuotas_kaggle/all_odds.csv").drop_duplicates("game_id")
k["dia"] = k.game_date.str[:10]
alias = {"LA Clippers": "LA Clippers", "LA Lakers": "Los Angeles Lakers"}
nombres = sorted(set(p.local))
def a_api(c):
    if c in alias: return alias[c]
    m = [n for n in nombres if n.startswith(c + " ")]
    assert len(m) == 1, (c, m); return m[0]
k["local"] = k.home_team.map(a_api)
x = x.reset_index().merge(k[["dia", "local", "total_over_points", "total_over_decimal_odds",
                              "total_under_decimal_odds", "total_over_won"]], on=["dia", "local"], how="left")
x["total"] = x.pl + x.pv
print(f"partidos terminados {len(x)}, con linea MGM {x.total_over_points.notna().sum()}")
chk = x.dropna(subset=["total_over_points"])
chk = chk[chk.total != chk.total_over_points]
print("comprobacion del cruce: over segun marcador == over segun MGM:",
      f"{((chk.total > chk.total_over_points) == chk.total_over_won).mean():.1%}")

F = ["l_" + r for r in R] + ["v_" + r for r in R]
d = x.dropna(subset=F + ["total_over_points"]).copy()
d = d[(d.l_jugados >= 5) & (d.v_jugados >= 5)]
ent, pru = d[d.temporada <= 2024], d[d.temporada >= 2025]
print(f"entreno {len(ent)} (2021-22..2023-24), prueba {len(pru)} (2024-25..2025-26)")
m = Ridge(alpha=1.0).fit(ent[F], ent.total)
pru = pru.assign(pred=m.predict(pru[F]))
rmse = lambda e: np.sqrt(np.mean(e ** 2))
print(f"\nerror (RMSE) del modelo {rmse(pru.pred - pru.total):.2f} | de la linea MGM {rmse(pru.total_over_points - pru.total):.2f}")
dif, res = pru.pred - pru.total_over_points, pru.total - pru.total_over_points
c = np.corrcoef(dif, res)[0, 1]
print(f"correlacion (modelo - linea) con (real - linea): {c:+.3f}  ({c*np.sqrt(len(pru)):+.2f}s aprox.)")
for umbral in [0, 2, 4, 6]:
    s = pru[dif.abs() > umbral]
    over = (s.pred > s.total_over_points)
    gana = np.where(over, s.total > s.total_over_points, s.total < s.total_over_points)
    cuota = np.where(over, s.total_over_decimal_odds, s.total_under_decimal_odds)
    gan = np.where(gana, cuota - 1, -1.0)
    print(f"  apostar donde |modelo - linea| > {umbral}: n={len(s)} acierto {gana.mean():.1%} "
          f"roi {gan.mean():+.2%} ({gan.mean()/gan.std(ddof=1)*np.sqrt(len(s)):+.2f}s)")
