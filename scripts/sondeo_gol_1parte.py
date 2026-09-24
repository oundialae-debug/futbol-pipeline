"""
SONDEO: ¿existe un mercado "equipo X marca en la 1ª parte"?

Segundo intento. El primero (18:11 UTC) tenía dos fallos:
1. Sondeó los primeros 20 partidos de data/calendario.csv, que resultaron
   ser sobre todo Segunda División -- el usuario dice que ese mercado solo
   está en las 5 grandes ligas europeas. Este sondeo filtra por liga.
2. El filtro de "coincidencias" usaba "to score" como palabra clave, que
   ya está DENTRO de "Both Teams To Score" y "First Team To Score" -- dio
   falsos positivos con mercados que no tienen nada que ver con medio
   tiempo. Corregido: exige "half"/"1st"/"1er"/"primera parte" Y algo de
   marcar/gol a la vez, no cualquiera de las dos por separado.
   También corregidos los nombres de campo reales de /odds (bookmakerName,
   values[].value, values[].odd -- sacados de backtest_valor.py, que sí
   los usa bien), así que ahora se ve el número de casas y las líneas de
   verdad, no "?" y vacío.
"""
import os
import time
import requests
import pandas as pd
from collections import defaultdict

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

RUTA_CALENDARIO = "data/calendario.csv"
RUTA_INFORME = "sondeo_gol_1parte.md"
MAX_PARTIDOS = int(os.environ.get("MAX_PARTIDOS", "20"))
LIGAS_GRANDES = ("Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1")

CLAVES_TIEMPO = ("half", "1st", "1er", "primera parte", "1ª parte", "ht ")
CLAVES_GOL = ("score", "goal", "marca", "gol")


def pedir(path, params=None, espera=0.25):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
    except Exception:
        return None
    time.sleep(espera)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def main():
    if not os.path.exists(RUTA_CALENDARIO):
        print(f"Falta {RUTA_CALENDARIO}")
        return
    cal = pd.read_csv(RUTA_CALENDARIO)
    cal = cal[cal["liga"].isin(LIGAS_GRANDES)].head(MAX_PARTIDOS)
    print(f"Sondeando /odds crudo en {len(cal)} partidos de las 5 grandes ligas "
          f"({', '.join(sorted(cal['liga'].unique()))})\n")

    censo = defaultdict(lambda: {"partidos": 0, "casas": set(), "ejemplos": set()})
    coincidencias = []

    for _, p in cal.iterrows():
        datos = pedir("/odds", {"matchId": int(p["match_id"]), "oddsType": "prematch"})
        bloques = (datos.get("data", []) if isinstance(datos, dict) else datos) or []
        planas = []
        for b in bloques:
            if isinstance(b, dict):
                planas.extend(b.get("odds", []) or [])
        mercados_este_partido = set()
        for c in planas:
            mercado = c.get("market") or "(sin nombre)"
            mercados_este_partido.add(mercado)
            casa = c.get("bookmakerName") or "(sin casa)"
            censo[mercado]["casas"].add(casa)
            valores = c.get("values") or []
            for v in valores:
                censo[mercado]["ejemplos"].add(str(v.get("value")))
            m_baja = mercado.lower()
            if any(t in m_baja for t in CLAVES_TIEMPO) and any(g in m_baja for g in CLAVES_GOL):
                coincidencias.append({
                    "match_id": p["match_id"], "local": p.get("local", ""),
                    "visitante": p.get("visitante", ""), "liga": p.get("liga", ""),
                    "mercado": mercado, "casa": casa,
                    "valores": ", ".join(str(v.get("value")) for v in valores[:6]),
                })
        for m in mercados_este_partido:
            censo[m]["partidos"] += 1

    print(f"{len(censo)} nombres de mercado distintos vistos en {len(cal)} partidos\n")
    filas_md = ["# Sondeo: gol de equipo en la 1ª parte (5 grandes ligas)\n",
                f"{len(cal)} partidos sondeados ({', '.join(sorted(cal['liga'].unique()))}), "
                f"{len(censo)} mercados distintos en /odds crudo.\n",
                "| mercado | partidos | casas | valores/líneas vistas |",
                "|---|---|---|---|"]
    for mercado, info in sorted(censo.items(), key=lambda kv: -kv[1]["partidos"]):
        ejemplos = ", ".join(sorted(info["ejemplos"])[:6])
        filas_md.append(f"| {mercado} | {info['partidos']} | {len(info['casas'])} | {ejemplos} |")

    filas_md.append("\n## Coincidencias reales con \"medio tiempo/1ª parte\" + \"marcar/gol\"\n")
    if coincidencias:
        filas_md.append("| liga | partido | mercado | casa | valores |")
        filas_md.append("|---|---|---|---|---|")
        print(f"{len(coincidencias)} coincidencias reales encontradas:")
        for c in coincidencias[:40]:
            filas_md.append(f"| {c['liga']} | {c['local']} vs {c['visitante']} | "
                            f"{c['mercado']} | {c['casa']} | {c['valores']} |")
            print(f"  [{c['liga']}] {c['local']} vs {c['visitante']}: {c['mercado']} "
                  f"({c['casa']}) -- {c['valores']}")
    else:
        filas_md.append("Ninguna, ni siquiera en las 5 grandes ligas.\n")
        print("Ninguna coincidencia real, ni en las 5 grandes ligas.")

    with open(RUTA_INFORME, "w", encoding="utf-8") as f:
        f.write("\n".join(filas_md) + "\n")
    print(f"\nEscrito {RUTA_INFORME}. Llamadas usadas: {len(cal)}")


if __name__ == "__main__":
    main()
