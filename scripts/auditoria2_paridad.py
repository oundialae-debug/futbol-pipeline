"""
Segunda auditoría externa, paso 2 (30/09/2026): test de paridad entre el camino
de ENTRENAMIENTO (modelo_ambos_marcan.preparar) y el de DIRECTO
(ambos_marcan_hoy.pronosticar), reconstruyendo días pasados. Sin API.

Para cada día de sep-2026 con partidos:
  entrenamiento  las variables tal como las ve el modelo al entrenar
  directo        lo que habría calculado ambos_marcan_hoy ese día: histórico
                 SOLO con partidos de días anteriores + los del día sin
                 resultado (con su once y árbitro), portero con
                 portero.para_partido(), precio con la mediana de casas de
                 Highlightly (cosechado) como en directo
Se compara, por grupo (portero, calidad de plantilla, precio, resto): en
cuántos partidos difiere y cuánto. Y el efecto final: el oficial entrenado con
todo lo anterior a sep-2026 predice esos partidos con cada juego de
variables (5 semillas): cambio de probabilidad, Brier y log loss.

Regla fijada antes: un grupo "tiene paridad" si difiere en menos del 1% de los
partidos o su diferencia media absoluta es menor que el 1% del rango típico.
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
import portero
import auditoria_precio_directo as PD

MES = "2026-09"
EPS = 1e-4


def grupo(c):
    if c in portero.COLS:
        return "portero"
    if "calidad" in c:
        return "calidad"
    if c in A.MKT:
        return "precio"
    return "resto"


def main():
    bt, cols = A.preparar()                    # camino de entrenamiento
    obj = bt[bt.mes == MES].copy()
    obj["dia"] = pd.to_datetime(obj.fecha, utc=True).dt.strftime("%Y-%m-%d")
    M.TEMPORADA_MINIMA = A.TEMPORADA_MINIMA
    rasgos.COBERTURA_MINIMA = 0.2              # como ambos_marcan_hoy
    hist = M.cargar()
    hist["dia"] = pd.to_datetime(hist.fecha, utc=True).dt.strftime("%Y-%m-%d")
    hl = PD.precio_directo().set_index("match_id")
    vivos = []
    for dia, g in obj.groupby("dia"):
        pasado = hist[hist.dia < dia].drop(columns="dia")
        hoy = hist[hist.match_id.isin(g.match_id)].drop(columns="dia").copy()
        for c in hoy.columns:                   # sin resultado ni estadísticas del propio partido
            if c not in ("match_id", "fecha", "liga_id", "liga", "temporada", "local_id", "local",
                         "visitante_id", "visitante", "arbitro", "local_ids", "visitante_ids",
                         "local_formacion", "visitante_formacion", "ronda"):
                hoy[c] = np.nan
        b = rasgos.construir(pd.concat([pasado, hoy], ignore_index=True))
        b = b[b.match_id.isin(g.match_id)].copy()
        for i, r in b.iterrows():
            h = hoy[hoy.match_id == r.match_id].iloc[0]
            for lado, eq, ids in (("loc", h.local_id, h.local_ids), ("vis", h.visitante_id, h.visitante_ids)):
                lista = str(ids).split("|") if isinstance(ids, str) else []
                b.loc[i, f"{lado}_gk_gp90"] = portero.para_partido(lista, eq, h.fecha)
        for c in A.MKT:
            b[c] = b.match_id.map(hl[c]) if c in hl.columns else np.nan
        vivos.append(b)
        print(f"  {dia}: {len(b)} partidos", flush=True)
    viv = pd.concat(vivos).set_index("match_id")
    ent = obj.set_index("match_id").loc[viv.index]
    print(f"\n{len(viv)} partidos de {MES}\n")
    print(f"{'grupo':9s} {'variables':>9s} {'partidos que difieren':>22s} {'|dif| media':>12s} {'|dif| máx':>10s}")
    filas = []
    for c in cols:
        a, v = ent[c].astype(float), viv[c].astype(float)
        dif = (a - v).abs()
        distinto = ~((a.isna() & v.isna()) | (dif < 1e-6))
        filas.append({"var": c, "grupo": grupo(c), "distinto": distinto.mean(),
                      "dif_media": dif.mean(), "dif_max": dif.max(), "nan_ent": a.isna().mean(), "nan_viv": v.isna().mean()})
    f = pd.DataFrame(filas)
    for gname, gg in f.groupby("grupo"):
        print(f"{gname:9s} {len(gg):9d} {gg.distinto.mean():21.1%} {gg.dif_media.mean():12.4f} {gg.dif_max.max():10.3f}")
    print("\nVariables que más difieren:")
    print(f.sort_values("distinto", ascending=False).head(12).round(4).to_string(index=False))
    f.to_csv("data/auditoria2_paridad_variables.csv", index=False)
    # efecto en la predicción
    tr = bt[(bt.mes < MES) & bt.goles_l.notna()]
    y = tr[A.OBJETIVO].values.astype(int)
    mods = [A.entrenar(tr[cols].values, y, semilla=s) for s in A.SEMILLAS]
    pe = np.mean([m.predict_proba(ent[cols].values)[:, 1] for m in mods], axis=0)
    pv = np.mean([m.predict_proba(viv[cols].values)[:, 1] for m in mods], axis=0)
    yt = ent[A.OBJETIVO].values
    br = lambda p: (p - yt) ** 2
    lo = lambda p: -(yt * np.log(np.clip(p, EPS, 1)) + (1 - yt) * np.log(np.clip(1 - p, EPS, 1)))
    s = lambda d: d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    dp = pv - pe
    print(f"\nPredicción, directo menos entrenamiento: media {dp.mean()*100:+.2f} pts, |media| {np.abs(dp).mean()*100:.2f} pts, "
          f"máx {np.abs(dp).max()*100:.1f} pts, >3 pts en {np.mean(np.abs(dp) > .03):.0%}")
    print(f"Brier entrenamiento {br(pe).mean():.4f}, directo {br(pv).mean():.4f} (directo vs entrenamiento {s(br(pe)-br(pv)):+.2f}s); "
          f"log loss {lo(pe).mean():.4f} vs {lo(pv).mean():.4f} ({s(lo(pe)-lo(pv)):+.2f}s)")
    # sin el precio: ¿cuánto viene solo de portero/calidad/resto?
    viv2 = viv[cols].copy()
    for c in A.MKT:
        viv2[c] = ent[c]
    pv2 = np.mean([m.predict_proba(viv2.values)[:, 1] for m in mods], axis=0)
    print(f"Con el MISMO precio en los dos (solo portero/calidad/resto difieren): |cambio| medio "
          f"{np.abs(pv2 - pe).mean()*100:.2f} pts, máx {np.abs(pv2 - pe).max()*100:.1f} pts")


if __name__ == "__main__":
    main()
