"""
Variables de FotMob (xG, xGOT, ocasiones claras, remates a puerta, toques en
el área rival, nota del equipo) para la tabla de modelo_goles.py, SIN fuga.

1. EMPAREJADO FotMob <-> football-data. No se empareja por parecido de nombre
   (así se coló la Premier de Jamaica). Se hace en dos pasos:
     a) partidos con la MISMA liga, fecha (±1 día: football-data da hora del
        Reino Unido, FotMob UTC) y MISMO marcador, y que sean el único
        candidato con ese marcador ese día -> pares de nombres (FotMob, fd);
     b) un nombre de FotMob queda emparejado con el nombre de fd con el que
        coincide en >= 90% de sus apariciones y al menos 5 veces. Si algún
        equipo que sale en FotMob no alcanza eso, se PARA y se lista.
   Después se cruza cada partido por liga + fecha ±1 + nombres ya traducidos.

2. RASGOS: por equipo, media de sus 8 partidos ANTERIORES (shift(1) antes de
   rolling) de lo que generó y lo que concedió. Un partido que no está en
   FotMob (antes de 2023) queda vacío, y XGBoost lo trata como hueco.
"""
import os
import numpy as np
import pandas as pd

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
MEDIDAS = ["xg", "xgot", "ocasiones", "remates_puerta", "toques_area", "remates_area", "nota_equipo"]
VENTANA = 8


def cargar_fotmob():
    ruta = os.path.join(CARPETA, "fotmob_partidos.csv")
    f = pd.read_csv(ruta)
    f["fecha"] = pd.to_datetime(f.fecha_utc.str[:16]).dt.normalize()
    return f.drop_duplicates("match_id")


def diccionario_nombres(d, f):
    pares = []
    for liga in f.liga.unique():
        a = d[d.liga == liga][["fecha", "Home", "Away", "hg", "ag"]].copy()
        a["dia"] = a.fecha.dt.normalize()
        b = f[f.liga == liga]
        m = pd.concat([b.assign(dia=b.fecha + pd.Timedelta(days=off)) for off in (0, -1, 1)]).merge(
            a, left_on=["dia", "goles_l", "goles_v"], right_on=["dia", "hg", "ag"])
        # un partido de FotMob solo cuenta si tiene UN candidato en todo el margen de ±1 día
        m = m[m.groupby("match_id").Home.transform("size") == 1]
        pares += list(zip([liga] * len(m), m.local, m.Home)) + list(zip([liga] * len(m), m.visitante, m.Away))
    p = pd.DataFrame(pares, columns=["liga", "fm", "fd"])
    c = p.groupby(["liga", "fm", "fd"]).size().rename("n").reset_index()
    tot = c.groupby(["liga", "fm"]).n.transform("sum")
    c["cuota"] = c.n / tot
    buenos = c[(c.cuota >= 0.9) & (c.n >= 5)]
    mapa = {(r.liga, r.fm): r.fd for r in buenos.itertuples()}
    vistos = {(l, n) for l, n in zip(f.liga, f.local)} | {(l, n) for l, n in zip(f.liga, f.visitante)}
    faltan = sorted(vistos - set(mapa))
    return mapa, faltan, c


def rasgos(d, parar=True, ligas=None):
    """Devuelve d con columnas fm_l_* y fm_v_* (medias previas) y el nº de
    partidos de FotMob emparejados."""
    f = cargar_fotmob()
    f = f[f.liga.isin(ligas or d.liga.unique())]
    mapa, faltan, _ = diccionario_nombres(d, f)
    if faltan:
        msg = f"Equipos de FotMob sin pareja fiable en football-data: {faltan}"
        if parar:
            raise SystemExit(msg)
        print("[!] " + msg + " (se ignoran sus partidos)")
    f["Home"] = [mapa.get((l, n)) for l, n in zip(f.liga, f.local)]
    f["Away"] = [mapa.get((l, n)) for l, n in zip(f.liga, f.visitante)]
    f = f[f.Home.notna() & f.Away.notna()]
    # cruce partido a partido: liga + nombres + fecha ±1 día
    a = d[["liga", "fecha", "Home", "Away"]].reset_index().rename(columns={"index": "i"})
    a["dia"] = a.fecha.dt.normalize()
    cruces = []
    for off in (0, -1, 1):
        m = f.assign(dia=f.fecha + pd.Timedelta(days=off)).merge(a, on=["liga", "Home", "Away", "dia"])
        cruces.append(m)
    m = pd.concat(cruces).drop_duplicates("i").drop_duplicates("match_id")
    cols = [c for c in f.columns if c[:2] in ("l_", "v_") and c[2:] in MEDIDAS]
    stats = m.set_index("i")[cols]
    # tabla larga por equipo: lo que generó (a favor) y lo que concedió (en contra)
    filas = []
    for lado, rival, eq in (("l", "v", "Home"), ("v", "l", "Away")):
        t = pd.DataFrame({"i": d.index, "liga": d.liga, "eq": d[eq], "fecha": d.fecha, "lado": lado})
        for med in MEDIDAS:
            t[f"af_{med}"] = stats[f"{lado}_{med}"].reindex(d.index).values if f"{lado}_{med}" in stats else np.nan
            t[f"ec_{med}"] = stats[f"{rival}_{med}"].reindex(d.index).values if f"{rival}_{med}" in stats else np.nan
        filas.append(t)
    t = pd.concat(filas).sort_values(["fecha", "i"])
    g = t.groupby(["liga", "eq"])
    nuevas = []
    for med in MEDIDAS:
        for k in ("af", "ec"):
            if k == "ec" and med == "nota_equipo":
                continue
            col = f"{k}_{med}"
            t[f"m_{col}"] = g[col].transform(lambda s: s.shift(1).rolling(VENTANA, min_periods=3).mean())
            nuevas.append(f"m_{col}")
    L = t[t.lado == "l"].set_index("i")[nuevas].add_prefix("fm_l_")
    V = t[t.lado == "v"].set_index("i")[nuevas].add_prefix("fm_v_")
    out = d.join(L).join(V)
    for med in ("xg", "ocasiones", "remates_puerta"):
        out[f"fm_dif_{med}"] = (out[f"fm_l_m_af_{med}"] - out[f"fm_l_m_ec_{med}"]) - (
            out[f"fm_v_m_af_{med}"] - out[f"fm_v_m_ec_{med}"])
    return out, len(m)


def columnas(d):
    return [c for c in d.columns if c.startswith("fm_")]
