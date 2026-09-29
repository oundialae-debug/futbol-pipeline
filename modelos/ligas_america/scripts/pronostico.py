"""
Pronóstico de ambos marcan y más/menos 2.5 para los próximos partidos de
Liga Profesional (ARG), Brasileirão (BRA) y Liga MX (MEX), SIN la API de
Highlightly.

  - Calendario y cuotas 1X2 de HOY: Promiedos (api.promiedos.com.ar, lo
    mismo que sirve su web; hora de Argentina con country_id=ba). La cuota
    1X2 de un partido futuro sale en su página de partido
    (prediction.odds) o en main_odds cuando la publican, días antes.
  - Histórico y modelo: modelo_goles.py (football-data, cierre del 1X2).
  - Sin cuota publicada todavía: se da el brazo "juego" (sin precio). Con
    cuota: el brazo "completo" (precio + juego). La cuota de Promiedos es la
    de UNA casa en ese momento, no la media de cierre con la que se entrenó:
    fuente y hora distintas (mismo aviso que ambos_marcan_hoy.py).

Emparejado de nombres Promiedos -> football-data: tabla fija ALIAS, y si un
equipo no está ni en la tabla ni con el mismo nombre, se PARA y se dice
(nunca se empareja "por parecido" a ciegas: así se coló la Premier de
Jamaica).

Uso: python3 modelos/ligas_america/scripts/pronostico.py [DIAS=7]
Escribe modelos/ligas_america/pronosticos.md y data/pronosticos.csv, y
añade al registro en papel data/registro_papel.csv (una fila por partido y
momento, sin sobrescribir).
"""
import os
import re
import sys
import json
import unicodedata
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelo_goles as G

PROMIEDOS = {"ARG": "hc", "BRA": "bbd", "MEX": "beb"}
DIAS = int(os.environ.get("DIAS", "7"))
UA = {"User-Agent": "Mozilla/5.0"}
ART = timezone(timedelta(hours=-3))

ALIAS = {
    # ARG
    "Argentinos Juniors": "Argentinos Jrs", "Atlético Tucumán": "Atl. Tucuman",
    "Central Córdoba SdE": "Central Cordoba", "Deportivo Riestra": "Dep. Riestra",
    "Estudiantes de La Plata": "Estudiantes L.P.", "Estudiantes RC": "Estudiantes Rio Cuarto",
    "Gimnasia La Plata": "Gimnasia L.P.", "Gimnasia de Mendoza": "Gimnasia Mendoza",
    "Huracán": "Huracan", "Independiente Rivadavia": "Ind. Rivadavia", "Lanús": "Lanus",
    "Newell's Old Boys": "Newells Old Boys", "Sarmiento Junín": "Sarmiento Junin",
    "Talleres de Córdoba": "Talleres Cordoba", "Unión de Santa Fe": "Union de Santa Fe",
    "Vélez Sarsfield": "Velez Sarsfield",
    # BRA
    "Athletico Paranaense": "Athletico-PR", "Atlético Mineiro": "Atletico-MG",
    "Botafogo": "Botafogo RJ", "Chapecoense": "Chapecoense-SC", "Flamengo": "Flamengo RJ",
    "Grêmio": "Gremio", "São Paulo": "Sao Paulo", "Vasco Da Gama": "Vasco", "Vitória": "Vitoria",
    # MEX
    "Atlético San Luis": "Atl. San Luis", "Club América": "Club America", "León": "Club Leon",
    "Chivas de Guadalajara": "Guadalajara Chivas", "Juárez": "Juarez", "Pumas": "UNAM Pumas",
    "Querétaro FC": "Queretaro", "U.A.N.L. - Tigres": "Tigres UANL",
}


def pedir(url):
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    return r.json()


def cuota_partido(juego):
    """1X2 del partido: main_odds si viene en el listado; si no, la página
    del partido (prediction.odds)."""
    o = (juego.get("main_odds") or {}).get("options") or []
    if len(o) == 3:
        return [float(x["value"]) for x in o]
    try:
        html = requests.get(f"https://www.promiedos.com.ar/game/{juego['url_name']}/{juego['id']}",
                            headers=UA, timeout=20).text
        d = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))
        g = d["props"]["pageProps"]["initialData"]["game"]
        o = (g.get("prediction") or {}).get("odds") or []
        arb = next((x["value"] for x in g.get("game_info") or [] if x.get("name") == "Árbitro"), None)
        if len(o) == 3:
            return [float(x["value"]) for x in o] + [arb]
        return [np.nan, np.nan, np.nan, arb]
    except Exception:
        return [np.nan, np.nan, np.nan, None]


def proximos(historico):
    ahora = datetime.now(ART)
    filas, sin_pareja = [], []
    for liga, pid in PROMIEDOS.items():
        equipos = set(historico[historico.liga == liga].Home) | set(historico[historico.liga == liga].Away)
        for x in pedir(f"https://api.promiedos.com.ar/league/games/{pid}/latest?country_id=ba").get("games") or []:
            if x["status"]["enum"] != 1:        # 1 = programado
                continue
            ini = datetime.strptime(x["start_time"], "%d-%m-%Y %H:%M").replace(tzinfo=ART)
            if not (ahora - timedelta(hours=2) <= ini <= ahora + timedelta(days=DIAS)):
                continue
            nom = [ALIAS.get(t["name"], t["name"]) for t in x["teams"]]
            falta = [n for n in nom if n not in equipos]
            if falta:
                sin_pareja += [(liga, n) for n in falta]
                continue
            c = cuota_partido(x)
            filas.append({"liga": liga, "fecha": pd.Timestamp(ini.astimezone(timezone.utc).replace(tzinfo=None)),
                          "hora_arg": ini.strftime("%a %d/%m %H:%M"), "ronda": x.get("stage_round_name"),
                          "Home": nom[0], "Away": nom[1], "AvgCH": c[0], "AvgCD": c[1], "AvgCA": c[2],
                          "arbitro": c[3] if len(c) > 3 else None, "promiedos_id": x["id"]})
    if sin_pareja:
        raise SystemExit("Equipos de Promiedos sin pareja en football-data (añadir a ALIAS, "
                         f"no emparejar por parecido): {sorted(set(sin_pareja))}")
    return pd.DataFrame(filas)


def main():
    hist = G.cargar()
    fut = proximos(hist)
    if fut.empty:
        print(f"Sin partidos programados en los próximos {DIAS} días.")
        return
    # los partidos futuros se añaden SIN resultado: sus rasgos salen solo de
    # partidos anteriores (mismo shift que el histórico) y no entran al entreno
    fut["hg"] = fut["ag"] = fut["btts"] = fut["o25"] = np.nan
    fut["temporada"] = fut.liga.map(hist.groupby("liga").temporada.max())
    todo = pd.concat([hist, fut], ignore_index=True).sort_values(["fecha", "liga"]).reset_index(drop=True)
    todo = G.añadir_mercado(todo)
    todo = G.elo(todo)          # un partido futuro lee el rating previo y no lo actualiza
    todo = G.forma(todo)
    futuro = todo[todo.promiedos_id.notna()].copy()
    pasado = todo[todo.promiedos_id.isna()]
    cj = G.columnas_juego(todo)
    for obj, y in G.OBJETIVOS.items():
        futuro[f"p_{obj}_juego"] = G.predecir(pasado, futuro, cj, y)
        con = futuro.m_pl.notna()
        futuro[f"p_{obj}_completo"] = np.nan
        if con.any():
            futuro.loc[con, f"p_{obj}_completo"] = G.predecir(pasado, futuro[con], G.MKT + cj, y)
        futuro[f"p_{obj}"] = futuro[f"p_{obj}_completo"].fillna(futuro[f"p_{obj}_juego"])
    futuro["con_cuota"] = futuro.m_pl.notna()
    futuro["generado_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    cols = ["liga", "ronda", "hora_arg", "Home", "Away", "AvgCH", "AvgCD", "AvgCA", "con_cuota",
            "p_ambos_marcan", "p_mas_2_5", "p_ambos_marcan_juego", "p_mas_2_5_juego",
            "p_ambos_marcan_completo", "p_mas_2_5_completo", "m_p_btts", "m_p_o25",
            "liga_btts", "liga_o25", "arbitro", "promiedos_id", "generado_utc"]
    out = futuro[cols]
    carpeta = G.CARPETA
    out.to_csv(os.path.join(carpeta, "data", "pronosticos.csv"), index=False)
    reg = os.path.join(carpeta, "data", "registro_papel.csv")
    out.to_csv(reg, mode="a", header=not os.path.exists(reg), index=False)
    lin = [f"# Pronósticos (generado {out.generado_utc.iloc[0]} UTC, hora argentina)\n",
           "Probabilidad del modelo. 'con cuota' = modelo completo (precio 1X2 + juego); "
           "si no hay cuota publicada todavía, modelo sin precio (peor, ver evaluacion.md). "
           "Cuota justa = 1/p: solo hay valor si la casa paga MÁS que eso.\n"]
    for liga in G.LIGAS:
        s = out[out.liga == liga]
        if s.empty:
            continue
        lin.append(f"\n## {G.LIGAS[liga]}\n")
        lin.append("| hora | partido | 1X2 | ambos marcan sí | justa | más de 2.5 | justa | modelo |")
        lin.append("|---|---|---|---|---|---|---|---|")
        for _, r in s.iterrows():
            c = f"{r.AvgCH:.2f}/{r.AvgCD:.2f}/{r.AvgCA:.2f}" if r.con_cuota else "sin publicar"
            lin.append(f"| {r.hora_arg} | {r.Home} - {r.Away} | {c} | {r.p_ambos_marcan*100:.0f}% | "
                       f"{1/r.p_ambos_marcan:.2f} | {r.p_mas_2_5*100:.0f}% | {1/r.p_mas_2_5:.2f} | "
                       f"{'completo' if r.con_cuota else 'sin precio'} |")
    txt = "\n".join(lin) + "\n"
    open(os.path.join(carpeta, "pronosticos.md"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
