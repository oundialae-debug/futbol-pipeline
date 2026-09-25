"""
Empareja las cuotas de football-data.co.uk con historico_partidos.csv y
guarda probabilidades de CIERRE sin margen por partido.

Lo que trae de verdad (data/football_data/columnas.md, 25/09/2026): 1X2,
más/menos 2.5 y hándicap asiático. NINGUNA columna de ambos marcan.
Fuente del precio, por orden: Pinnacle cierre (PSC*, PC>2.5; 2023/24,
2024/25 y la mitad de 2025/26), Betfair Exchange cierre (BFEC*; desde
2024/25), media del mercado de cierre (AvgC*). Se guarda qué fuente se usó.

Emparejar: liga + día + marcador da colisiones (1.253 claves repetidas, dos
1-1 el mismo día en la misma liga). Se desempata por parecido de nombres
(los nombres difieren: "Man United" / "Manchester United") y se DESCARTA
lo que no se parezca lo bastante -- un emparejamiento dudoso es peor que
ninguno.
"""
import glob
import unicodedata
from difflib import SequenceMatcher
import numpy as np
import pandas as pd

COD = {"E0": 33973, "SP1": 119924, "I1": 115669, "D1": 67162, "F1": 52695, "SP2": 120775}
RUTA = "data/cuotas_historicas_fd.csv"
PARECIDO_MINIMO = 0.45
# Nombres que ningún parecido de texto empareja (revisados a mano).
ALIAS = {"ath bilbao": "athletic", "athletic club": "athletic"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    for q in (" fc", "fc ", " cf", "cf ", "ac ", " ac", "afc ", "ssc ", "as ", "rc ", "cd ",
              "ud ", "sd ", "real ", "club ", "1. ", "vfb ", "vfl ", "tsg ", "sv ", "united", "utd"):
        s = s.replace(q, " ")
    s = " ".join(s.replace(".", " ").replace("'", " ").split())
    return ALIAS.get(s, s)


def parecido(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def cargar_fd():
    partes = []
    for f in sorted(glob.glob("data/football_data/*.csv")):
        d = pd.read_csv(f, encoding="latin-1")
        d.columns = [c.replace("﻿", "").replace("ï»¿", "") for c in d.columns]
        d["liga_id"] = COD[f.split("_")[-1][:-4]]
        partes.append(d)
    fd = pd.concat(partes, ignore_index=True)
    fd["dia"] = pd.to_datetime(fd.Date, dayfirst=True).dt.strftime("%Y-%m-%d")
    return fd.rename(columns={"FTHG": "goles_l", "FTAG": "goles_v"})


def sin_margen(*cuotas):
    inv = np.array([1.0 / c for c in cuotas])
    return inv / inv.sum()


def elegir(fila, grupos):
    for fuente, cols in grupos:
        v = [fila.get(c) for c in cols]
        if all(pd.notna(x) and x > 1 for x in v):
            return fuente, sin_margen(*v)
    return None, None


def previa(f):
    r_f, r_p = elegir(f, [("pinnacle", ["PSH", "PSD", "PSA"]), ("betfair", ["BFEH", "BFED", "BFEA"])])
    o_f, o_p = elegir(f, [("pinnacle", ["P>2.5", "P<2.5"]), ("betfair", ["BFE>2.5", "BFE<2.5"])])
    return {"fuente_previa_1x2": r_f,
            "p_local_previa": None if r_p is None else r_p[0],
            "p_empate_previa": None if r_p is None else r_p[1],
            "p_visitante_previa": None if r_p is None else r_p[2],
            "fuente_previa_mas_2_5": o_f,
            "p_mas_2_5_previa": None if o_p is None else o_p[0]}


def main():
    fd = cargar_fd()
    h = pd.read_csv("data/historico_partidos.csv")
    h["dia"] = pd.to_datetime(h.fecha, format="mixed", utc=True).dt.strftime("%Y-%m-%d")
    k = ["liga_id", "dia", "goles_l", "goles_v"]
    m = h[["match_id", "temporada", "local", "visitante"] + k].merge(fd, on=k, how="inner")
    m["parecido"] = [min(parecido(a, b), parecido(c, d)) for a, b, c, d in
                     zip(m.local, m.HomeTeam, m.visitante, m.AwayTeam)]
    m = m.sort_values("parecido", ascending=False).drop_duplicates("match_id")
    dudosos = m[m.parecido < PARECIDO_MINIMO]
    m = m[m.parecido >= PARECIDO_MINIMO]
    m = m.sort_values("parecido", ascending=False).drop_duplicates(["liga_id", "dia", "HomeTeam", "AwayTeam"])

    filas = []
    for _, f in m.iterrows():
        r_f, r_p = elegir(f, [("pinnacle", ["PSCH", "PSCD", "PSCA"]),
                              ("betfair", ["BFECH", "BFECD", "BFECA"]),
                              ("media", ["AvgCH", "AvgCD", "AvgCA"])])
        o_f, o_p = elegir(f, [("pinnacle", ["PC>2.5", "PC<2.5"]),
                              ("betfair", ["BFEC>2.5", "BFEC<2.5"]),
                              ("media", ["AvgC>2.5", "AvgC<2.5"])])
        filas.append({"match_id": f.match_id,
                      "fuente_1x2": r_f, "p_local": None if r_p is None else r_p[0],
                      "p_empate": None if r_p is None else r_p[1],
                      "p_visitante": None if r_p is None else r_p[2],
                      "fuente_mas_2_5": o_f, "p_mas_2_5": None if o_p is None else o_p[0],
                      # PREVIA (no cierre): football-data la toma días antes
                      # del partido (viernes/martes). Sirve de referencia sin
                      # mirar al futuro: se conocía antes de apostar.
                      **previa(f)})
    out = pd.DataFrame(filas)
    out.to_csv(RUTA, index=False)

    t = h.set_index("match_id").temporada
    out["temporada"] = out.match_id.map(t)
    print(f"Emparejados {len(out)} de {len(h)} partidos del histórico "
          f"({len(dudosos)} descartados por nombres que no se parecen).")
    print(out.groupby("temporada").size().to_string())
    print("\nFuente del 1X2:", out.fuente_1x2.value_counts(dropna=False).to_dict())
    print("Fuente del +2.5:", out.fuente_mas_2_5.value_counts(dropna=False).to_dict())
    if len(dudosos):
        print("\nEjemplos descartados:")
        print(dudosos[["local", "HomeTeam", "visitante", "AwayTeam", "parecido"]].head(8).to_string())
    print(f"\nEscrito {RUTA}")


if __name__ == "__main__":
    main()
