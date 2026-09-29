"""
Pronóstico de ambos marcan y más/menos 2.5 para Colombia Primera B (sin
cuotas históricas: modelo "juego", Elo + forma de goles + nivel de la liga).
Calendario de FotMob (9125), nombres de FotMob en los dos lados (el
histórico COLB.csv sale de la misma fuente, no hace falta tabla de alias).

ENTRENO (env ENTRENO): "juntas" (4 ligas) o "sola" (solo Primera B). Se
elige con evaluacion_colb.md, no a ojo.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelo_goles as G

DIAS = int(os.environ.get("DIAS", "7"))
ENTRENO = os.environ.get("ENTRENO", "juntas")
COT = timezone(timedelta(hours=-5))


def main():
    hist = G.cargar()
    d = requests.get("https://www.fotmob.com/api/data/leagues?id=9125", headers={"User-Agent": "Mozilla/5.0"},
                     timeout=30).json()
    ahora = datetime.now(timezone.utc)
    equipos = set(hist[hist.liga == "COLB"].Home) | set(hist[hist.liga == "COLB"].Away)
    filas = []
    for m in d["fixtures"]["allMatches"]:
        s = m["status"]
        if s.get("finished") or s.get("cancelled") or s.get("started"):
            continue
        f = datetime.strptime(s["utcTime"][:16], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        if not (ahora - timedelta(hours=1) <= f <= ahora + timedelta(days=DIAS)):
            continue
        h, a = m["home"]["name"], m["away"]["name"]
        falta = [x for x in (h, a) if x not in equipos]
        if falta:
            raise SystemExit(f"Equipo sin historia en COLB.csv: {falta} (no se empareja por parecido)")
        filas.append({"liga": "COLB", "fecha": pd.Timestamp(f.replace(tzinfo=None)), "Home": h, "Away": a,
                      "hora_col": f.astimezone(COT).strftime("%a %d/%m %H:%M"), "ronda": m.get("round"),
                      "futuro": 1})
    if not filas:
        print("Sin partidos en los próximos días"); return
    fut = pd.DataFrame(filas)
    fut["temporada"] = hist[hist.liga == "COLB"].temporada.max()
    todo = pd.concat([hist.assign(futuro=0), fut], ignore_index=True).sort_values(["fecha", "liga"]).reset_index(drop=True)
    todo = G.añadir_mercado(todo)
    todo = G.elo(todo)
    todo = G.forma(todo)
    cj = G.columnas_juego(todo)
    pasado = todo[todo.futuro == 0]
    if ENTRENO == "sola":
        pasado = pasado[pasado.liga == "COLB"]
    futuro = todo[todo.futuro == 1].copy()
    for obj, y in G.OBJETIVOS.items():
        futuro[f"p_{obj}"] = G.predecir(pasado, futuro, cj, y)
    tasa = hist[(hist.liga == "COLB") & (hist.fecha > hist.fecha.max() - pd.Timedelta(days=365))]
    lin = [f"# Colombia Primera B (generado {ahora:%Y-%m-%d %H:%M} UTC, hora de Colombia, entreno '{ENTRENO}')\n",
           f"Tasa de la liga último año: ambos marcan {tasa.btts.mean()*100:.0f}%, más de 2.5 {tasa.o25.mean()*100:.0f}%. "
           "Modelo SIN cuotas (no hay históricas de esta liga).\n",
           "| hora | partido | ambos marcan sí | justa sí | justa no | más de 2.5 | justa más | justa menos |",
           "|---|---|---|---|---|---|---|---|"]
    for _, r in futuro.iterrows():
        pb, po = r.p_ambos_marcan, r.p_mas_2_5
        lin.append(f"| {r.hora_col} | {r.Home} - {r.Away} | {pb*100:.0f}% | {1/pb:.2f} | {1/(1-pb):.2f} | "
                   f"{po*100:.0f}% | {1/po:.2f} | {1/(1-po):.2f} |")
    txt = "\n".join(lin) + "\n"
    open(os.path.join(G.CARPETA, "pronosticos_colb.md"), "w", encoding="utf-8").write(txt)
    reg = os.path.join(G.CARPETA, "data", "registro_papel_colb.csv")
    futuro.assign(generado_utc=f"{ahora:%Y-%m-%d %H:%M}")[["liga", "ronda", "hora_col", "Home", "Away",
        "p_ambos_marcan", "p_mas_2_5", "generado_utc"]].to_csv(reg, mode="a", header=not os.path.exists(reg), index=False)
    print(txt)


if __name__ == "__main__":
    main()
