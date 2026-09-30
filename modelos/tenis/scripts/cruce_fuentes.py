"""
Cruce independiente: cada partido de tennis-data (fuente independiente, con
cuotas) contra Sackmann y TennisMyLife. Pedido por el usuario el 30/09/2026:
"cuidado que los datos de Sackmann sean erróneos".

Emparejamiento: tennis-data escribe "Nadal R." y las otras "Rafael Nadal".
Clave de jugador = última palabra del apellido normalizada + inicial del
nombre. Un partido empareja si coinciden los dos jugadores y la fecha de
tennis-data cae entre el inicio del torneo (tourney_date) -3 y +20 días.
Se prueba también con ganador y perdedor cambiados: eso es un desacuerdo
en quién ganó, no un fallo de emparejamiento.

Se compara: ganador, marcador set a set (juegos, sin tie-break) en partidos
completos, y superficie. Escribe data/tenis/cruce_fuentes.md.
"""
import glob
import re
import unicodedata

import pandas as pd

D = "data/tenis"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def clave_td(nombre):
    """'Carreno Busta P.' -> ('busta', 'p'); 'O Connell C.' -> ('connell', 'c')."""
    partes = str(nombre).strip().split()
    if len(partes) < 2:
        return None
    apellido = partes[:-1]
    return norm(apellido[-1]) + "|" + norm(partes[-1])[:1]


def clave_completo(nombre):
    """'Pablo Carreno Busta' -> ('busta', 'p')."""
    partes = str(nombre).replace("-", " ").strip().split()
    if len(partes) < 2:
        return None
    return norm(partes[-1]) + "|" + norm(partes[0])[:1]


def clave_td_guion(nombre):
    partes = str(nombre).replace("-", " ").strip().split()
    if len(partes) < 2:
        return None
    return norm(partes[-2]) + "|" + norm(partes[-1])[:1]


def sets_td(fila):
    out = []
    for i in range(1, 6):
        w, l = fila.get(f"W{i}"), fila.get(f"L{i}")
        if pd.notna(w) and pd.notna(l):
            out.append(f"{int(w)}-{int(l)}")
    return " ".join(out)


def sets_fuente(score):
    s = re.sub(r"\(\d+\)", "", str(score))
    return " ".join(x for x in s.split() if re.fullmatch(r"\d+-\d+", x))


def cargar_td(circuito):
    fs = sorted(glob.glob(f"{D}/tennis_data/{circuito}_*.csv"))
    td = pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True)
    td["fecha"] = pd.to_datetime(td["Date"], errors="coerce")
    td["kw"] = td["Winner"].map(clave_td)
    td["kl"] = td["Loser"].map(clave_td)
    td["sets"] = td.apply(sets_td, axis=1)
    td["i"] = range(len(td))
    return td


def cargar_fuente(patron):
    fs = sorted(glob.glob(patron))
    d = pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True)
    d["inicio"] = pd.to_datetime(d["tourney_date"].astype(str).str[:8], format="%Y%m%d", errors="coerce")
    d = d[d["inicio"] >= "2019-12-01"].copy()
    d["kw"] = d["winner_name"].map(clave_completo)
    d["kl"] = d["loser_name"].map(clave_completo)
    d["sets"] = d["score"].map(sets_fuente)
    return d


def emparejar(td, f, kw, kl):
    m = td.merge(f, left_on=[kw, kl], right_on=["kw", "kl"], suffixes=("", "_f"))
    dias = (m["fecha"] - m["inicio"]).dt.days
    m = m[(dias >= -3) & (dias <= 20)].copy()
    m["dist"] = (m["fecha"] - m["inicio"]).dt.days.abs()
    return m.sort_values("dist").drop_duplicates("i")


def cruzar(td, f):
    directo = emparejar(td, f, "kw", "kl")
    resto = td[~td["i"].isin(directo["i"])]
    alt = resto.assign(kw2=resto["Winner"].map(clave_td_guion), kl2=resto["Loser"].map(clave_td_guion))
    directo2 = emparejar(alt, f, "kw2", "kl2")
    ok = pd.concat([directo, directo2])
    resto = td[~td["i"].isin(ok["i"])]
    cambiado = emparejar(resto, f, "kl", "kw")          # TD ganador = fuente perdedor
    return ok, cambiado, td[~td["i"].isin(ok["i"]) & ~td["i"].isin(cambiado["i"])]


def main():
    out = ["# Cruce tennis-data contra Sackmann y TennisMyLife\n",
           "Generado por `modelos/tenis/scripts/cruce_fuentes.py`. Cada fila de tennis-data",
           "(2020-2026) se busca en la otra fuente. \"ganador distinto\" = mismo partido con",
           "ganador y perdedor al revés. Marcador comparado solo en partidos completos",
           "(`Comment == Completed`), por juegos de cada set.\n",
           "| circuito | fuente | partidos td (en su rango) | emparejados | ganador distinto | sin encontrar | marcador distinto | superficie distinta |",
           "|---|---|---|---|---|---|---|---|"]
    ejemplos = []
    fuentes = {"atp": {"Sackmann": f"{D}/sackmann/atp_matches_20[12][0-9].csv",
                       "TennisMyLife": f"{D}/tennismylife/20[12][0-9].csv"},
               "wta": {"Sackmann": f"{D}/sackmann/wta_matches_20[12][0-9].csv",
                       "TennisMyLife": f"{D}/tennismylife/20[12][0-9]_wta.csv"}}
    for circuito, fs in fuentes.items():
        td_total = cargar_td(circuito)
        for nombre, patron in fs.items():
            f = cargar_fuente(patron)
            td = td_total[td_total["fecha"] <= f["inicio"].max() + pd.Timedelta(days=14)]
            ok, cambiado, falta = cruzar(td, f)
            comp = ok[ok["Comment"] == "Completed"]
            marc = comp[comp["sets"] != comp["sets_f"]]
            sup = ok[ok["Surface"].str.lower() != ok["surface"].astype(str).str.lower()]
            n = len(td)
            out.append(f"| {circuito.upper()} | {nombre} | {n} | {len(ok)} ({len(ok)/n:.1%}) | {len(cambiado)} | "
                       f"{len(falta)} ({len(falta)/n:.1%}) | {len(marc)} de {len(comp)} ({len(marc)/max(len(comp),1):.2%}) | "
                       f"{len(sup)} |")
            ejemplos.append(f"\n## {circuito.upper()} {nombre}\n")
            ejemplos.append("Sin encontrar, por año: " + ", ".join(
                f"{a}: {c}" for a, c in falta["fecha"].dt.year.value_counts().sort_index().items()))
            ejemplos.append("Sin encontrar, por tipo de torneo: " + ", ".join(
                f"{a}: {c}" for a, c in falta[falta.columns[falta.columns.isin(['Series', 'Tier'])][0]].value_counts().items()))
            for _, r in cambiado.head(5).iterrows():
                ejemplos.append(f"- ganador distinto: {r['fecha']:%Y-%m-%d} {r['Tournament']}: td {r['Winner']} gana a {r['Loser']} "
                                f"({r['sets']}); {nombre}: {r['winner_name']} gana a {r['loser_name']} ({r['score']})")
            for _, r in marc.head(5).iterrows():
                ejemplos.append(f"- marcador: {r['fecha']:%Y-%m-%d} {r['Tournament']} {r['Winner']} - {r['Loser']}: "
                                f"td '{r['sets']}' / {nombre} '{r['score']}'")
            for _, r in sup.head(3).iterrows():
                ejemplos.append(f"- superficie: {r['fecha']:%Y-%m-%d} {r['Tournament']}: td {r['Surface']} / {nombre} {r['surface']}")
            for _, r in falta.sample(min(5, len(falta)), random_state=1).iterrows():
                ejemplos.append(f"- sin encontrar: {r['fecha']:%Y-%m-%d} {r['Tournament']} {r['Winner']} - {r['Loser']} ({r['Round']})")
    open(f"{D}/cruce_fuentes.md", "w").write("\n".join(out + ejemplos) + "\n")
    print("\n".join(out + ejemplos))


if __name__ == "__main__":
    main()
