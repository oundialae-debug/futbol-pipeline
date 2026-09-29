"""
SONDEO: ¿el /box-score de 2023/24 dice quién fue TITULAR? (29/09/2026)

/lineups no tiene nada antes de abril de 2024 (1.500 llamadas lo
confirmaron, ver CLAUDE.md "2023/24: ... alineaciones solo desde abril de
2024"). Pero el sondeo de xG por jugador vio que /box-score SÍ trae ~40
jugadores por partido en 2023/24. Si además marca isSubstitute (esquema
FootballPlayerBoxScore de la spec: isSubstitute, minutesPlayed, position),
los titulares de 2023/24 se pueden reconstruir sin /lineups -- y con ellos
la calidad de plantilla (g/a de la temporada anterior), la variable que más
ha ayudado a los modelos.

Antes de gastar ~1.900 llamadas, se mira con ~16:
  - 2 partidos (ligas distintas) por mes de ago-2023 a mar-2024 (sin /lineups)
  - Segunda 2023/24 aparte (ahí /lineups dio cero en TODA la temporada)
  - CONTROL: 2 partidos con /lineups ya guardado (may-2024 y oct-2025): los
    titulares del box-score deben coincidir con los de historico_lineups.csv
Un partido no mide una temporada (ya engañó dos veces): por eso varios meses
y varias ligas. Escribe sondeo_titulares_boxscore.md.
"""
import os
import time
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
BASE_URL = "https://soccer.highlightly.net"
MESES = ["2023-08", "2023-10", "2023-11", "2024-01", "2024-02", "2024-03"]
POR_MES = 2


def pedir(path):
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            return None, r.status_code
        try:
            return r.json(), 200
        except Exception:
            return None, "no-json"
    return None, "sin respuesta"


def titulares(j):
    """Por equipo: (n jugadores, n con isSubstitute informado, ids titulares, n con minutos, n con posición)."""
    equipos = (j.get("data") if isinstance(j, dict) else j) or []
    out = []
    for e in equipos:
        if not isinstance(e, dict):
            continue
        jug = e.get("players") or []
        informado = [p for p in jug if p.get("isSubstitute") is not None]
        tit = [p.get("id") for p in informado if p.get("isSubstitute") is False]
        out.append((len(jug), len(informado), tit,
                    sum(p.get("minutesPlayed") is not None for p in jug),
                    sum(bool(p.get("position")) for p in jug)))
    return out


def main():
    h = pd.read_csv("data/historico_partidos.csv")
    lu = pd.read_csv("data/historico_lineups.csv")
    h["mes"] = h.fecha.str[:7]
    muestra = []
    ligas = sorted(h.loc[h.liga != "Segunda", "liga"].unique())
    for i, mes in enumerate(MESES):          # ligas rotando: las 5 grandes salen varias veces
        for k in range(POR_MES):
            liga = ligas[(i * POR_MES + k) % len(ligas)]
            c = h[(h.mes == mes) & (h.liga == liga)].head(1)
            muestra += [("sin /lineups", r) for _, r in c.iterrows()]
    seg = h[(h.liga == "Segunda") & (h.temporada == 2023) & (h.fecha < "2024-04-01")].sort_values("fecha")
    for q in (0.2, 0.7):
        muestra.append(("Segunda 23/24", seg.iloc[int(len(seg) * q)]))
    ctrl = h[h.match_id.isin(lu.match_id)]
    for mes in ("2024-05", "2025-10"):
        c = ctrl[ctrl.mes == mes].drop_duplicates("liga").head(1)
        muestra += [("CONTROL", r) for _, r in c.iterrows()]

    lu_ids = {r.match_id: {int(x) for s in (r.local_ids, r.visitante_ids) if isinstance(s, str) for x in s.split("|")}
              for r in lu.itertuples()}
    lineas = ["# Sondeo: titulares en /box-score de 2023/24\n",
              "| tipo | fecha | liga | partido | estado | jugadores (loc/vis) | isSubstitute informado | "
              "titulares (loc/vis) | con minutos | con posición | coincide con /lineups |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    ok = 0
    for tipo, f in muestra:
        j, est = pedir(f"/box-score/{f.match_id}")
        t = titulares(j) if j else []
        coinc = "-"
        if tipo == "CONTROL" and t and f.match_id in lu_ids:
            box = {int(i) for e in t for i in e[2] if i is not None}
            coinc = f"{len(box & lu_ids[f.match_id])}/{len(lu_ids[f.match_id])}"
        if len(t) == 2 and all(len(e[2]) == 11 for e in t):
            ok += 1
        fila = (f"| {tipo} | {f.fecha[:10]} | {f.liga} | {f.local} - {f.visitante} | {est} | "
                f"{'/'.join(str(e[0]) for e in t) or '-'} | {'/'.join(str(e[1]) for e in t) or '-'} | "
                f"{'/'.join(str(len(e[2])) for e in t) or '-'} | {'/'.join(str(e[3]) for e in t) or '-'} | "
                f"{'/'.join(str(e[4]) for e in t) or '-'} | {coinc} |")
        print(fila)
        lineas.append(fila)
    lineas.append(f"\n**{ok} de {len(muestra)} partidos con exactamente 11 titulares por equipo.**")
    open("sondeo_titulares_boxscore.md", "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print(f"\n{ok}/{len(muestra)} con 11+11 titulares. Escrito sondeo_titulares_boxscore.md")


if __name__ == "__main__":
    main()
