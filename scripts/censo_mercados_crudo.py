"""
CENSO CRUDO: qué mercados ofrece de verdad la API, y con qué profundidad.

Los análisis anteriores (censo_margenes.py, backtest_valor.py) ya filtran por
familias conocidas y por MIN_CASAS. Eso es correcto para medir margen, pero
puede estar ocultando mercados que sí existen y que nunca hemos mirado
crudos: First Team to Score no apareció ni una vez en el backtest (0 de
137.301 filas) pese a estar en el código de clasificación, y Total Cards
apareció en el censo (384) pero cero veces en el backtest. Antes de descartar
nada hay que ver el dato sin filtrar.

Esto no calcula margen ni compara nada. Solo cuenta: qué nombres de mercado
aparecen, cuántas casas cotiza cada uno de media, y sobre cuántos partidos.
"""
import os
import time
import requests
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_CALENDARIO = "data/calendario.csv"
RUTA_INFORME = "censo_mercados_crudo.md"
MAX_PARTIDOS = int(os.environ.get("MAX_PARTIDOS", "30"))
LLAMADAS = [0]


def pedir(path, params=None, espera=0.25):
    LLAMADAS[0] += 1
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
    except Exception:
        return None
    time.sleep(espera)
    if r.status_code != 200:
        if r.status_code == 429:
            print("  [429] límite de peticiones -- se para aquí")
            raise SystemExit(0)
        return None
    try:
        return r.json()
    except Exception:
        return None


def desempaquetar(d):
    return (d.get("data", []) or []) if isinstance(d, dict) else (d or [])


def main():
    print("CENSO CRUDO DE MERCADOS")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    if not os.path.exists(RUTA_CALENDARIO):
        print("Falta data/calendario.csv")
        return
    cal = pd.read_csv(RUTA_CALENDARIO)
    hoy = datetime.now(timezone.utc).date()
    cal = cal[(pd.to_datetime(cal["fecha"]).dt.date >= hoy)
              & (pd.to_datetime(cal["fecha"]).dt.date <= hoy + timedelta(days=7))]
    partidos = cal.head(MAX_PARTIDOS)
    print(f"{len(partidos)} partidos de los próximos 7 días")

    # {nombre_de_mercado_exacto: {"partidos": set(), "casas": set(), "valores": set()}}
    censo = defaultdict(lambda: {"partidos": set(), "casas": set(), "valores": set()})
    detalle_valores = defaultdict(lambda: defaultdict(set))

    for _, p in partidos.iterrows():
        datos = pedir("/odds", {"matchId": int(p["match_id"]), "oddsType": "prematch"})
        bloques = (datos.get("data", []) if isinstance(datos, dict) else datos) or []
        planas = []
        for b in bloques:
            if isinstance(b, dict):
                planas.extend(b.get("odds", []) or [])
        for c in planas:
            mercado = c.get("market") or "(sin nombre)"
            casa = c.get("bookmakerName")
            censo[mercado]["partidos"].add(int(p["match_id"]))
            censo[mercado]["casas"].add(casa)
            for v in (c.get("values") or []):
                censo[mercado]["valores"].add(str(v.get("value")))

    if not censo:
        print("Sin cotizaciones")
        return

    filas = []
    for mercado, d in censo.items():
        filas.append({
            "mercado": mercado,
            "partidos": len(d["partidos"]),
            "casas_distintas": len(d["casas"]),
            "valores_posibles": ", ".join(sorted(d["valores"])[:8]),
        })
    r = pd.DataFrame(filas).sort_values("partidos", ascending=False)

    lineas = [
        f"# Censo crudo de mercados -- "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"Sobre {len(partidos)} partidos de los próximos 7 días, sin filtrar "
        f"por familia conocida ni por número mínimo de casas.\n",
        "| Mercado (nombre exacto) | Partidos | Casas distintas | Valores posibles |",
        "|---|---|---|---|",
    ]
    for _, f in r.iterrows():
        lineas.append(f"| {f['mercado']} | {f['partidos']} | "
                      f"{f['casas_distintas']} | {f['valores_posibles']} |")

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n" + "\n".join(lineas))
    print(f"\n[api] {LLAMADAS[0]} llamadas")


if __name__ == "__main__":
    main()
