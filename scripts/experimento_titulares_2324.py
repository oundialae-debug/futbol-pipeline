"""
Titulares de 2023/24 (29/09/2026): ¿cómo le sirven al modelo de ambos marcan?

El otro chat sacó de /box-score los onces de ago-2023 a mar-2024 (1.734
partidos, 11 titulares por equipo, portero primero), que /lineups no tenía.
Con ellos se rellenan para 2023/24 las variables que salen del once
(calidad de plantilla) y las que probamos con cobertura del 52% (edad, valor,
bajas por lesión). Los 385 jugadores nuevos se descargaron (perfil y
estadísticas de temporada).

Prueba FIJADA ANTES, mes a mes de sep-2024 a sep-2026 (mismos partidos):
  1. PRINCIPAL: modelo oficial (102 variables) SIN esos onces contra CON
     ellos. Mismas columnas en los dos brazos (se comprueba: un umbral de
     cobertura podría cambiar las columnas sin avisar). Listón +2s.
  2. Con los onces dentro, se vuelven a probar edad, valor y bajas (ahora
     con más partidos de entrenamiento). 3 intentos más: listón ~+2.4s.
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
import experimento_edad_valor as EV
import experimento_lesiones as EL

COLS_ONCE = ["local_formacion", "local_ids", "visitante_formacion", "visitante_ids"]


def nuevos():
    h = pd.read_csv("data/historico_partidos.csv", usecols=["match_id", "fecha", "temporada"])
    lu = pd.read_csv("data/historico_lineups.csv", usecols=["match_id"])
    m = (h.temporada == 2023) & (h.fecha < "2024-04-01") & h.match_id.isin(lu.match_id)
    return set(h[m].match_id)


def preparar(sin_nuevos):
    M.TEMPORADA_MINIMA = A.TEMPORADA_MINIMA
    hist = M.cargar()
    if sin_nuevos:
        hist.loc[hist.match_id.isin(nuevos()), COLS_ONCE] = np.nan
    bt = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    cols = A.columnas(bt)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    bt = bt.merge(A.rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    bt = bt.merge(portero.historico(), on="match_id", how="left")
    bt = bt[bt.goles_l.notna()].reset_index(drop=True)
    bt["mes"] = pd.to_datetime(bt.fecha, utc=True).dt.strftime("%Y-%m")
    return bt, cols


def comparar(base, v, meses, nombre):
    y = base[A.OBJETIVO].values
    d = (base.p_ambos.values - y) ** 2 - (v.p_ambos.values - y) ** 2
    pos = sum(((base[base.mes == m].p_ambos - base[base.mes == m][A.OBJETIVO]) ** 2).mean() >
              ((v[v.mes == m].p_ambos - v[v.mes == m][A.OBJETIVO]) ** 2).mean() for m in meses)
    ini = (base.mes >= "2026-08").values
    s = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    print(f"{nombre:34s} {s:+.2f}s  (Brier {((v.p_ambos.values - y)**2).mean():.4f} vs "
          f"{((base.p_ambos.values - y)**2).mean():.4f}; mejora en {pos}/{len(meses)} meses; "
          f"arranque 2026/27 {d[ini].mean()*100:+.2f} pts)", flush=True)
    return {"prueba": nombre, "sigmas": round(s, 2), "meses_mejor": pos, "meses": len(meses)}


def main():
    a, cols_a = preparar(True)
    b, cols_b = preparar(False)
    assert cols_a == cols_b, f"las columnas cambian: {set(cols_a) ^ set(cols_b)}"
    n = nuevos()
    for nom, t in (("sin", a), ("con", b)):
        x = t[t.match_id.isin(n)]
        print(f"  {nom} onces 23/24: calidad de plantilla en {x.loc_calidad_ga.notna().mean():.0%} de sus {len(x)} partidos")
    meses = [m for m, k in a.mes.value_counts().sort_index().items() if m >= "2024-09" and k >= 20]
    print(f"{len(cols_a)} variables; meses {meses[0]}..{meses[-1]} ({len(meses)})\n")
    pa = pd.concat([A.predecir_mes(a, cols_a, m) for m in meses])
    pb = pd.concat([A.predecir_mes(b, cols_b, m) for m in meses])
    filas = [comparar(pa, pb, meses, "1. CON onces 23/24 vs SIN")]
    b = b.merge(EV.rasgos(), on="match_id", how="left").merge(EL.rasgos(), on="match_id", how="left")
    print(f"\nCobertura con los onces nuevos: edad {b.loc_edad_campo.notna().mean():.0%}, "
          f"bajas {b.loc_bajas.notna().mean():.0%} (antes 52%)")
    for nombre, extra in (("2a. + edad media", EV.VARIANTES["A edad"]),
                          ("2b. + valor medio", EV.VARIANTES["B valor"]),
                          ("2c. + bajas por lesión", EL.VARIANTES["A bajas"])):
        v = pd.concat([A.predecir_mes(b, cols_b, m, extra=extra) for m in meses])
        filas.append(comparar(pb, v, meses, nombre))
    pd.DataFrame(filas).to_csv("data/experimento_titulares_2324.csv", index=False)


if __name__ == "__main__":
    main()
