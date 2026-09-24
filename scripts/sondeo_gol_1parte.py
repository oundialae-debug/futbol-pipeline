"""
SONDEO: ¿existe un mercado "equipo X marca en la 1ª parte"?

Pregunta del usuario, sobre un mercado concreto -- no aparece en NINGUNO de
los ficheros de datos ya recogidos (censo_margenes.csv, backtest_valor.csv,
casas_descolgadas.csv), ni en los ejemplos de la spec de OpenAPI. Eso no
prueba que no exista (la regla de este mismo repositorio): solo dice que
nunca ha aparecido en lo que ya se ha mirado. Antes de descartarlo, se pide
la respuesta CRUDA de /odds para partidos reales y se listan TODOS los
nombres de mercado que aparezcan, sin filtrar por familia conocida --
mismo patrón que censo_mercados_crudo.py.
"""
import os
import time
import json
import requests
import pandas as pd
from collections import defaultdict

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

RUTA_CALENDARIO = "data/calendario.csv"
RUTA_INFORME = "sondeo_gol_1parte.md"
MAX_PARTIDOS = int(os.environ.get("MAX_PARTIDOS", "20"))

PALABRAS_CLAVE = ("half", "1st", "first half", "score a goal", "to score")


def pedir(path, params=None, espera=0.25):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
    except Exception as e:
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
    cal = pd.read_csv(RUTA_CALENDARIO).head(MAX_PARTIDOS)
    print(f"Sondeando /odds crudo en {len(cal)} partidos\n")

    # nombre de mercado exacto -> {partidos, casas, ejemplo de valores/lineas}
    censo = defaultdict(lambda: {"partidos": 0, "casas": set(), "ejemplos": set()})
    coincidencias_medio_tiempo = []

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
            censo[mercado]["casas"].add(c.get("bookmaker") or c.get("betSite") or "?")
            valor = c.get("name") or c.get("value") or c.get("handicap") or ""
            if valor:
                censo[mercado]["ejemplos"].add(str(valor)[:40])
            texto = f"{mercado} {valor}".lower()
            if any(k in texto for k in PALABRAS_CLAVE) and "score" in texto:
                coincidencias_medio_tiempo.append({
                    "match_id": p["match_id"], "local": p.get("local", ""),
                    "visitante": p.get("visitante", ""), "mercado": mercado,
                    "valor": str(valor)[:60],
                })
        for m in mercados_este_partido:
            censo[m]["partidos"] += 1

    print(f"{len(censo)} nombres de mercado distintos vistos en {len(cal)} partidos\n")
    filas_md = ["# Sondeo: gol de equipo en la 1ª parte\n",
                f"{len(cal)} partidos sondeados, {len(censo)} mercados distintos "
                "en /odds crudo (sin filtrar por familia conocida).\n",
                "| mercado | partidos | casas | ejemplos de línea/lado |",
                "|---|---|---|---|"]
    for mercado, info in sorted(censo.items(), key=lambda kv: -kv[1]["partidos"]):
        ejemplos = ", ".join(sorted(info["ejemplos"])[:5])
        filas_md.append(f"| {mercado} | {info['partidos']} | {len(info['casas'])} | {ejemplos} |")
        print(f"  {mercado:40s} partidos={info['partidos']:3d} casas={len(info['casas']):3d}  "
              f"ej: {ejemplos[:60]}")

    filas_md.append("\n## Coincidencias con \"gol en la 1ª parte / equipo concreto\"\n")
    if coincidencias_medio_tiempo:
        filas_md.append("| partido | mercado | valor |")
        filas_md.append("|---|---|---|")
        print(f"\n{len(coincidencias_medio_tiempo)} filas que mencionan medio "
              "tiempo/primera parte Y marcar/anotar:")
        for c in coincidencias_medio_tiempo[:30]:
            linea = f"{c['local']} vs {c['visitante']}: {c['mercado']} -- {c['valor']}"
            filas_md.append(f"| {c['local']} vs {c['visitante']} | {c['mercado']} | {c['valor']} |")
            print("  " + linea)
    else:
        filas_md.append("Ninguna. No se ha visto ningún mercado que combine "
                        "'gol/marcar' con 'primera parte/medio tiempo' en "
                        f"los {len(cal)} partidos sondeados.\n")
        print("\nNinguna coincidencia -- no aparece ese mercado en lo sondeado.")

    with open(RUTA_INFORME, "w", encoding="utf-8") as f:
        f.write("\n".join(filas_md) + "\n")
    print(f"\nEscrito {RUTA_INFORME}")


if __name__ == "__main__":
    main()
