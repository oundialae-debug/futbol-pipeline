"""
Bajas por lesión para ambos marcan (petición del usuario, 29/09/2026). Datos:
data/jugador_lesiones.csv (backfill_perfil_jugador.py, 27.792 lesiones).

Un lesionado no sale en el once, y el once real ya lo ve el modelo (calidad de
plantilla, portero). Lo nuevo es QUIÉN FALTA: los titulares habituales de
cada equipo (titular en al menos 3 de sus 5 onces anteriores) que están de
baja el día del partido. Variantes FIJADAS ANTES de mirar resultados:

  A  bajas        cuántos habituales están lesionados.     loc_/vis_/dif_
  B  bajas_valor  su valor de mercado sumado, en millones (última valoración
                  anterior al partido; nunca la de hoy).    loc_/vis_/dif_

Sin fuga: la lesión tiene que haber EMPEZADO antes del día del partido (una
que empieza ese día puede ser del propio partido) y no haber terminado. Los
habituales salen solo de onces anteriores. Hace falta que el equipo tenga al
menos 3 onces previos; si no, hueco.

Misma prueba mes a mes que el modelo oficial (102 variables, 5 semillas).
Con 2 intentos, listón +2s para A y ~+2.2s para B.
"""
import sys
import bisect
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
from collections import defaultdict
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A

VENTANA, MIN_TITULAR, MIN_ONCES = 5, 3, 3


def lesiones():
    l = pd.read_csv("data/jugador_lesiones.csv")
    l["desde"] = pd.to_datetime(l.desde, format="%d.%m.%Y", errors="coerce")
    l["hasta"] = pd.to_datetime(l.hasta, format="%d.%m.%Y", errors="coerce")
    l = l.dropna(subset=["desde", "hasta"])
    d = defaultdict(list)
    for r in l.itertuples():
        d[int(r.jugador_id)].append((r.desde, r.hasta))
    return d


def valores():
    v = pd.read_csv("data/jugador_valor_mercado.csv")
    v["fecha"] = pd.to_datetime(v.fecha, errors="coerce")
    v = v.dropna(subset=["fecha", "valor"]).sort_values("fecha")
    return {int(j): (list(g.fecha), list(g.valor / 1e6)) for j, g in v.groupby("jugador_id")}


def valor_antes(vals, j, dia):
    if j not in vals:
        return 0.0
    fechas, vs = vals[j]
    k = bisect.bisect_left(fechas, dia) - 1          # estrictamente anterior
    return vs[k] if k >= 0 else 0.0


def rasgos():
    lu = pd.read_csv("data/historico_lineups.csv")
    h = pd.read_csv("data/historico_partidos.csv", usecols=["match_id", "fecha", "local_id", "visitante_id"])
    lu = lu.merge(h, on="match_id")
    filas = []
    for r in lu.itertuples():
        for lado, eq in (("loc", r.local_id), ("vis", r.visitante_id)):
            ids = getattr(r, "local_ids" if lado == "loc" else "visitante_ids")
            if isinstance(ids, str):
                filas.append((r.match_id, lado, eq, r.fecha, [int(x) for x in ids.split("|") if x.strip().isdigit()]))
    t = pd.DataFrame(filas, columns=["match_id", "lado", "equipo", "fecha", "once"])
    t["dia"] = pd.to_datetime(t.fecha, utc=True).dt.tz_localize(None).dt.normalize()
    les, vals = lesiones(), valores()
    out = []
    for eq, g in t.sort_values("dia").groupby("equipo"):
        previos = []
        for r in g.itertuples():
            if len(previos) >= MIN_ONCES:
                cuenta = defaultdict(int)
                for o in previos[-VENTANA:]:
                    for j in o:
                        cuenta[j] += 1
                habituales = [j for j, n in cuenta.items() if n >= MIN_TITULAR]
                baja = [j for j in habituales if any(d < r.dia <= hsta for d, hsta in les.get(j, ()))]
                out.append((r.match_id, r.lado, len(baja), sum(valor_antes(vals, j, r.dia) for j in baja)))
            else:
                out.append((r.match_id, r.lado, np.nan, np.nan))
            previos.append(r.once)
    o = pd.DataFrame(out, columns=["match_id", "lado", "bajas", "bajas_valor"])
    w = o.pivot_table(index="match_id", columns="lado", values=["bajas", "bajas_valor"])
    w.columns = [f"{lado}_{c}" for c, lado in w.columns]
    w = w.reset_index()
    for c in ("bajas", "bajas_valor"):
        w[f"dif_{c}"] = w[f"loc_{c}"] - w[f"vis_{c}"]
    return w


VARIANTES = {
    "A bajas": ["loc_bajas", "vis_bajas", "dif_bajas"],
    "B bajas_valor": ["loc_bajas_valor", "vis_bajas_valor", "dif_bajas_valor"],
}


def main():
    bt, cols = A.preparar()
    bt = bt.merge(rasgos(), on="match_id", how="left")
    c = bt.loc_bajas.notna()
    print(f"Cobertura {c.mean():.0%} de {len(bt)} partidos. Bajas de habituales por equipo: media "
          f"{bt.loc_bajas.mean():.2f}, con al menos una {(bt.loc_bajas[c] > 0).mean():.0%}; "
          f"valor de las bajas (media) {bt.loc_bajas_valor.mean():.1f} M")
    cob = bt.groupby("mes").loc_bajas.apply(lambda s: s.notna().mean())
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if n >= 20 and cob.get(m, 0) >= 0.5]
    print(f"Meses de prueba: {meses[0]}..{meses[-1]} ({len(meses)})")
    base = pd.concat([A.predecir_mes(bt, cols, m) for m in meses])
    y = base[A.OBJETIVO].values
    filas = []
    for nombre, extra in VARIANTES.items():
        v = pd.concat([A.predecir_mes(bt, cols, m, extra=extra) for m in meses])
        d = (base.p_ambos.values - y) ** 2 - (v.p_ambos.values - y) ** 2
        pos = sum(((base[base.mes == m].p_ambos - base[base.mes == m][A.OBJETIVO]) ** 2).mean() >
                  ((v[v.mes == m].p_ambos - v[v.mes == m][A.OBJETIVO]) ** 2).mean() for m in meses)
        di = d[(base.mes >= "2026-08").values]
        s = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
        print(f"{nombre:14s} vs oficial {s:+.2f}s  (Brier {((v.p_ambos.values - y)**2).mean():.4f} vs "
              f"{((base.p_ambos.values - y)**2).mean():.4f}; mejora en {pos}/{len(meses)} meses; "
              f"arranque 2026/27: {di.mean()*100:+.2f} pts en {len(di)} partidos)", flush=True)
        filas.append({"variante": nombre, "sigmas": round(s, 2), "meses_mejor": pos, "meses": len(meses)})
    pd.DataFrame(filas).to_csv("data/experimento_lesiones.csv", index=False)


if __name__ == "__main__":
    main()
