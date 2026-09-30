"""
Comprobaciones internas de los partidos de Sackmann y TennisMyLife (sin
tennis-data): imposibles físicos en las stats de saque, texto en columnas
numéricas, duplicados, ganador = perdedor, retiradas/walkovers y cobertura
de stats. Desde 2000. Escribe data/tenis/validacion_interna.md.

Pedido por el usuario el 30/09/2026 ("cuidado que los datos de Sackmann
sean erróneos"). El cruce con una fuente independiente (tennis-data) va
aparte.
"""
import glob

import pandas as pd

D = "data/tenis"
FUENTES = {
    "Sackmann ATP": f"{D}/sackmann/atp_matches_[12][0-9][0-9][0-9].csv",
    "Sackmann Challenger+previas ATP": f"{D}/sackmann/atp_matches_qual_chall_*.csv",
    "Sackmann WTA": f"{D}/sackmann/wta_matches_[12][0-9][0-9][0-9].csv",
    "Sackmann previas+ITF WTA": f"{D}/sackmann/wta_matches_qual_itf_*.csv",
    "TennisMyLife ATP": f"{D}/tennismylife/[12][0-9][0-9][0-9].csv",
    "TennisMyLife Challenger": f"{D}/tennismylife/*_challenger.csv",
    "TennisMyLife previas ATP": f"{D}/tennismylife/atp_quali/*.csv",
    "TennisMyLife WTA": f"{D}/tennismylife/*_wta.csv",
}
STATS = ["ace", "df", "svpt", "1stIn", "1stWon", "2ndWon", "SvGms", "bpSaved", "bpFaced"]
NUMERICAS = [f"{p}_{c}" for p in "wl" for c in STATS] + ["minutes", "winner_rank", "loser_rank"]


def cargar(patron):
    fs = sorted(glob.glob(patron))
    d = pd.concat([pd.read_csv(f, low_memory=False).assign(fichero=f.split("/")[-1]) for f in fs],
                  ignore_index=True)
    return d[d.tourney_date.astype(str).str[:4].astype(int) >= 2000].copy()


def main():
    out = ["# Validación interna de partidos (desde 2000)\n",
           "Generado por `modelos/tenis/scripts/validar_interno.py`.\n",
           "| fuente | partidos | con stats | stats imposibles | texto en numéricas | duplicados | ganador=perdedor | retirada/WO | sin marcador |",
           "|---|---|---|---|---|---|---|---|---|"]
    detalle = []
    for nombre, patron in FUENTES.items():
        d = cargar(patron)
        texto = []
        for c in NUMERICAS:
            num = pd.to_numeric(d[c], errors="coerce")
            malo = d[c].notna() & num.isna()
            for i in d.index[malo]:
                texto.append(f"{d.at[i, 'fichero']}: {c}={d.at[i, c]!r} ({d.at[i, 'winner_name']} - {d.at[i, 'loser_name']})")
            d[c] = num
        s = d.dropna(subset=["w_svpt", "l_svpt"])
        reglas = {}
        for p in "wl":
            reglas[f"{p}_ace+{p}_df>{p}_svpt"] = s[f"{p}_ace"] + s[f"{p}_df"] > s[f"{p}_svpt"]
            reglas[f"{p}_1stIn>{p}_svpt"] = s[f"{p}_1stIn"] > s[f"{p}_svpt"]
            reglas[f"{p}_1stWon>{p}_1stIn"] = s[f"{p}_1stWon"] > s[f"{p}_1stIn"]
            reglas[f"{p}_1stWon+{p}_2ndWon>{p}_svpt"] = s[f"{p}_1stWon"] + s[f"{p}_2ndWon"] > s[f"{p}_svpt"]
            reglas[f"{p}_bpSaved>{p}_bpFaced"] = s[f"{p}_bpSaved"] > s[f"{p}_bpFaced"]
            reglas[f"{p} negativo"] = (s[[f"{p}_{c}" for c in STATS]] < 0).any(axis=1)
        malas = pd.concat(reglas, axis=1).any(axis=1)
        dup = d.duplicated(subset=["tourney_id", "tourney_date", "winner_name", "loser_name", "round"]).sum()
        ret = d.score.astype(str).str.contains("RET|W/O|DEF|Walkover", case=False).sum()
        out.append(f"| {nombre} | {len(d)} | {len(s)} ({len(s)/len(d):.0%}) | {malas.sum()} | {len(texto)} | "
                   f"{dup} | {(d.winner_name == d.loser_name).sum()} | {ret} ({ret/len(d):.1%}) | {d.score.isna().sum()} |")
        if malas.sum() or texto:
            detalle.append(f"\n## {nombre}\n")
            detalle += [f"- regla {k}: {int(v.sum())}" for k, v in reglas.items() if v.sum()]
            detalle += [f"- texto: {t}" for t in texto]
            for i in s.index[malas][:10]:
                detalle.append(f"- imposible: {d.at[i, 'fichero']} {d.at[i, 'tourney_date']} "
                               f"{d.at[i, 'winner_name']} - {d.at[i, 'loser_name']}")
    open(f"{D}/validacion_interna.md", "w").write("\n".join(out + detalle) + "\n")
    print("\n".join(out + detalle))


if __name__ == "__main__":
    main()
