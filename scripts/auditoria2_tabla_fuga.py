"""
Fuga en la posición de la tabla (30/09/2026). Sin API. No toca rasgos.py.

rasgos.calcular_tabla ordena por fecha y va partido a partido: lee la tabla,
apunta la posición y la actualiza con el resultado. Con dos partidos de la
misma liga a la MISMA hora, el que cae segundo en el orden ya ve el resultado
del primero: información que no existía al empezar (fuga). Además, en directo
(ambos_marcan_hoy) el histórico solo llega hasta ayer, así que un partido de
las 21:00 no ve los de las 16:00 del mismo día, y al entrenar sí.

Solo la POSICIÓN depende de otros equipos (puntos por partido y partidos
jugados son del propio equipo), así que solo cambian loc/vis/dif_tabla_pos.

Tres versiones de la posición:
  actual      la de rasgos.calcular_tabla
  estricta    los partidos a la misma hora (misma liga) no se ven entre sí: sin fuga
  inicio_dia  solo partidos de días anteriores: lo que ve el camino de directo
Comprobación: la reimplementación con grupos de un solo partido reproduce
la actual exactamente.

Reglas FIJADAS ANTES: la estricta es la correcta por principio (quita una
fuga), así que se recomienda aunque salga igual o un poco peor; solo se
avisa si empeora más de 2s (sería señal de que el modelo vivía de la fuga).
inicio_dia se recomienda en su lugar si no es peor que la estricta en más de
2s, porque además iguala entrenamiento y directo. Oficial y las dos variantes,
mes a mes sep-2024..sep-2026, 5 semillas, Brier y log loss, meses mejor y
contra el ambos marcan real.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A
import modelo_xgboost as M
import rasgos

EPS = 1e-4
POS = ["loc_tabla_pos", "vis_tabla_pos", "dif_tabla_pos"]


def posiciones(hist, clave):
    """Posición en la tabla ANTES de cada partido; los partidos con la misma clave
    (y misma liga) se leen todos antes de actualizar con cualquiera de ellos."""
    orden = hist.sort_values("fecha").reset_index(drop=True)
    orden["_g"] = clave(orden)
    tablas, filas = {}, []
    for _, g in orden.groupby("_g", sort=False):
        pend = []
        for f in g.itertuples():
            tabla = tablas.setdefault((f.liga_id, f.temporada), {})
            ranking = sorted(tabla, key=lambda e: (-tabla[e][0], -(tabla[e][1] - tabla[e][2])))
            pos = {e: i + 1 for i, e in enumerate(ranking)}
            n = len(ranking)
            filas.append((f.match_id, pos.get(f.local_id, n + 1), pos.get(f.visitante_id, n + 1)))
            if pd.notna(f.goles_l) and pd.notna(f.goles_v):
                pend.append((tabla, f.local_id, f.visitante_id, f.goles_l, f.goles_v))
        for tabla, l, v, gl, gv in pend:
            p, q = tabla.get(l, (0, 0, 0, 0)), tabla.get(v, (0, 0, 0, 0))
            pl3 = 3 if gl > gv else (1 if gl == gv else 0)
            pv3 = 3 if gv > gl else (1 if gl == gv else 0)
            tabla[l] = (p[0] + pl3, p[1] + gl, p[2] + gv, p[3] + 1)
            tabla[v] = (q[0] + pv3, q[1] + gv, q[2] + gl, q[3] + 1)
    d = pd.DataFrame(filas, columns=["match_id", "loc_tabla_pos", "vis_tabla_pos"])
    d["dif_tabla_pos"] = d.loc_tabla_pos - d.vis_tabla_pos
    return d


def sig(d):
    d = np.asarray(d, float)
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


def main():
    M.TEMPORADA_MINIMA = A.TEMPORADA_MINIMA
    hist = M.cargar()
    t = pd.to_datetime(hist.fecha, utc=True, format="ISO8601")
    fila = posiciones(hist, lambda o: np.arange(len(o)))
    act = rasgos.calcular_tabla(hist)[["match_id", "loc_tabla_pos", "vis_tabla_pos"]]
    chk = act.merge(fila, on="match_id", suffixes=("", "_r"))
    assert (chk.loc_tabla_pos == chk.loc_tabla_pos_r).all() and (chk.vis_tabla_pos == chk.vis_tabla_pos_r).all(), \
        "la reimplementación no reproduce rasgos.calcular_tabla"
    print(f"Comprobación: la reimplementación reproduce la tabla actual en {len(chk)} partidos.\n")
    hora = lambda o: pd.to_datetime(o.fecha, utc=True, format="ISO8601").astype("int64")
    dia = lambda o: pd.to_datetime(o.fecha, utc=True, format="ISO8601").dt.strftime("%Y-%m-%d")
    variantes = {"estricta": posiciones(hist, hora), "inicio_dia": posiciones(hist, dia)}

    # diagnóstico: cuántos partidos comparten hora con otro de su liga, y cuánto cambia la posición
    h = hist.assign(_t=t)
    misma_hora = h.groupby(["liga_id", "_t"]).match_id.transform("count") > 1
    print(f"Partidos que empiezan a la misma hora que otro de su liga: {misma_hora.mean():.1%} "
          f"({misma_hora.sum()} de {len(h)})")
    base = act.assign(dif_tabla_pos=act.loc_tabla_pos - act.vis_tabla_pos).set_index("match_id")
    e = variantes["estricta"].set_index("match_id").loc[base.index]
    i = variantes["inicio_dia"].set_index("match_id").loc[base.index]
    def dif(a, b, texto):
        d = (a[["loc_tabla_pos", "vis_tabla_pos"]] != b[["loc_tabla_pos", "vis_tabla_pos"]]).any(axis=1)
        m = (a[["loc_tabla_pos", "vis_tabla_pos"]] - b[["loc_tabla_pos", "vis_tabla_pos"]]).abs().max(axis=1)
        print(f"{texto:52s} difiere en {d.mean():5.1%} de los partidos; cuando difiere, "
              f"{m[d].mean():.2f} puestos de media (máx {m.max():.0f})")
    dif(base, e, "Fuga (actual frente a estricta):")
    dif(e, i, "Mismo día, antes (estricta frente a inicio del día):")
    dif(base, i, "Total (actual frente a inicio del día = directo):")
    ult = h[pd.to_datetime(h.fecha, utc=True, format="ISO8601") >= "2024-09-01"]
    print(f"Desde sep-2024: fuga en {(base.loc[ult.match_id] != e.loc[ult.match_id]).any(axis=1).mean():.1%} de los partidos\n")

    # efecto en el modelo oficial
    bt, cols = A.preparar()
    assert (bt.dif_tabla_pos == bt.loc_tabla_pos - bt.vis_tabla_pos).all(), "dif_tabla_pos no es loc - vis"
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if m >= "2024-09" and n >= 20]
    of = pd.concat([A.predecir_mes(bt, cols, m) for m in meses])
    y = of[A.OBJETIVO].values
    lo = lambda p: -(y * np.log(np.clip(p, EPS, 1)) + (1 - y) * np.log(np.clip(1 - p, EPS, 1)))
    import evaluar_mercados as EM
    c = EM.cargar_cuotas_crudas()
    b = c[c.familia == "Both Teams To Score"]
    piv = b.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
    piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
    piv["p"] = (1 / piv.yes) / (1 / piv.yes + 1 / piv.no)
    real = piv.groupby("match_id").p.median()
    en = of.match_id.isin(real.index).values
    yr, pr = y[en], of.match_id[en].map(real).values
    print(f"{len(of)} partidos, {len(meses)} meses. Oficial (tabla actual) contra el ambos marcan real "
          f"({en.sum()}): Brier {sig((pr - yr)**2 - (of.p_ambos.values[en] - yr)**2):+.2f}s\n")
    preds = {}
    for nombre, v in variantes.items():
        bv = bt.drop(columns=POS).merge(v, on="match_id", how="left")
        p = pd.concat([A.predecir_mes(bv, cols, m) for m in meses])
        preds[nombre] = p.set_index("match_id").loc[of.match_id].p_ambos.values
    preds["actual"] = of.p_ambos.values
    def comp(nuevo, ref, texto):
        pn, pf = preds[nuevo], preds[ref]
        db, dl = (pf - y) ** 2 - (pn - y) ** 2, lo(pf) - lo(pn)
        mes = sum(((pf[k] - y[k]) ** 2).mean() > ((pn[k] - y[k]) ** 2).mean()
                  for k in (of.mes.values == m for m in meses))
        print(f"{texto:32s} Brier {sig(db):+.2f}s  log loss {sig(dl):+.2f}s  mejor en {mes}/{len(meses)} meses  "
              f"|cambio| medio {np.abs(pn - pf).mean()*100:.2f} pts")
    comp("estricta", "actual", "estricta frente a actual")
    comp("inicio_dia", "actual", "inicio_dia frente a actual")
    comp("inicio_dia", "estricta", "inicio_dia frente a estricta")
    print("\nContra el ambos marcan real (+ = mejor que el mercado):")
    llr = lambda p: -(yr * np.log(np.clip(p, EPS, 1)) + (1 - yr) * np.log(np.clip(1 - p, EPS, 1)))
    for n in ("actual", "estricta", "inicio_dia"):
        print(f"  {n:11s} Brier {sig((pr - yr)**2 - (preds[n][en] - yr)**2):+.2f}s  "
              f"log loss {sig(llr(pr) - llr(preds[n][en])):+.2f}s")


if __name__ == "__main__":
    main()
