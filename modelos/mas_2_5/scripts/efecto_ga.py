"""
¿De dónde vino la mejora al copiar los datos de main (-2.65s -> -1.09s)?
Hipótesis: de las alineaciones y el g/a de 2024/25, no de tener más partidos.
Mismo modelo de 28 con y sin g/a (cp_ataque), mismos datos nuevos, mes a mes,
mismos partidos. Cobertura de g/a por temporada, antes y después de la copia.
"""
import sys, io, contextlib, subprocess, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
import modelo_xgboost as M, rasgos_mas25 as R, evaluar_mercados as EM

fd = pd.read_csv("data/cuotas_football_data.csv")
fd["p_mercado"] = (1 / fd["Avg>2.5"]) / (1 / fd["Avg>2.5"] + 1 / fd["Avg<2.5"])
with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
bc = R.construir(hist, pd.read_csv("data/historico_jugador_stats.csv"), pd.read_csv("data/historico_h2h_profundo.csv"))
bc = bc[bc.goles_l.notna() & bc.goles_v.notna()].merge(fd[["match_id", "p_mercado"]], on="match_id")
f = pd.to_datetime(bc.fecha, utc=True)
bc["mes"], bc["t"] = f.dt.strftime("%Y-%m"), f.dt.year - (f.dt.month < 7)
print("Cobertura de g/a de delanteros (partidos con dato), por temporada:")
print(bc.groupby("t").loc_cp_del_ga90.apply(lambda s: f"{s.notna().mean()*100:.0f}% de {len(s)}").to_string())
C28 = R.columnas_produccion(bc)
SIN = [c for c in C28 if "_cp_" not in c]


def pred(cols, ent, val):
    y = ent.mas_2_5.values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s), val[cols].values, 2)[:, 1]
                    for s in EM.SEMILLAS], axis=0)


ev = bc[f >= "2025-08-01"]
res = []
for mes in sorted(ev.mes.unique()):
    val, ent = ev[ev.mes == mes], bc[f < pd.Timestamp(mes + "-01", tz="UTC")]
    res.append(pd.DataFrame({"y": val.mas_2_5.values, "pm": val.p_mercado.values,
                             "con": pred(C28, ent, val), "sin": pred(SIN, ent, val)}))
d = pd.concat(res)
sig = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
bm = 2 * (d.pm - d.y) ** 2
for c in ("con", "sin"):
    print(f"28 {c} g/a ({len(C28) if c=='con' else len(SIN)} rasgos): vs media casas {sig(bm - 2*(d[c]-d.y)**2):+.2f}s")
print(f"con g/a frente a sin g/a: {sig(2*(d.sin-d.y)**2 - 2*(d.con-d.y)**2):+.2f}s  (n={len(d)})")
