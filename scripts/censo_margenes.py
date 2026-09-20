"""
¿QUÉ MERCADO PREVIO ES MÁS FÁCIL DE GANAR?

No se decide por intuición, se mide. Y lo que lo decide no es el modelo: es
el MARGEN que cobra la casa.

Si un mercado te cobra un 8%, tu modelo tiene que ser un 8% mejor que el de
la casa solo para empatar. Si te cobra un 0.5% porque lo cotizan cuarenta
casas y puedes coger la mejor cuota de cada lado, te vale con una ventaja
mínima. Un modelo mediocre en un mercado barato gana más que un modelo
excelente en uno caro.

CÓMO SE CALCULA
---------------
El margen sale de sumar 1/cuota sobre un conjunto de resultados COMPLETO y
excluyente. Si esa suma da 1.08, la casa se queda un 8%.

Solo se miden mercados donde se puede comprobar que el conjunto está
completo:

    Full Time Result        Home + Draw + Away
    Total Goals X           Over + Under
    Total Cards X           Over + Under
    Total Corners X         Over + Under
    Both Teams to Score     Yes + No
    Asian Handicap X        Home + Away
    Odd or Even             Odd + Even
    Clean Sheet             Home + Away
    First Team To Score     Home + Away + None

Correct Score se queda fuera: no hay forma de verificar desde aquí que estén
todos los resultados posibles (son decenas de marcadores y algunas casas no
cotizan los más raros), y un margen calculado sobre un conjunto incompleto
sale absurdamente bajo y parece una ganga.

DOS MÁRGENES, Y EL SEGUNDO ES EL QUE IMPORTA
--------------------------------------------
  - El margen MEDIO por casa: lo que cobra una casa cualquiera.
  - El margen de la MEJOR COMBINACIÓN: coger la mejor cuota de cada lado,
    aunque sea de casas distintas. Es el margen que pagas de verdad si
    comparas precios, y es mucho menor. Si sale negativo, es arbitraje.

El segundo es el que decide dónde merece la pena buscar.
"""
import os
import time
import json
import requests
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_CALENDARIO = "data/calendario.csv"
RUTA_SALIDA = "data/censo_margenes.csv"
RUTA_INFORME = "censo_margenes.md"

MAX_PARTIDOS = int(os.environ.get("MAX_PARTIDOS", "40"))
LLAMADAS = [0]

# Cada familia con el conjunto de resultados que la completa. Si lo que trae
# la casa no coincide exactamente con el conjunto, esa cotización se descarta:
# un margen sobre un conjunto incompleto sale bajísimo y engaña.
FAMILIAS = {
    "Full Time Result": {"home", "draw", "away"},
    "Both Teams To Score": {"yes", "no"},
    "Odd or Even": {"odd", "even"},
    "Clean Sheet": {"home", "away"},
    # "First Team To Score" con T mayúscula: así lo devuelve la API de
    # verdad (censo_mercados_crudo.py lo confirmó). Estaba fuera de este
    # script sin más razón que no haberlo mirado.
    "First Team To Score": {"home", "away", "none"},
}
# Familias con línea dentro del nombre ("Total Goals 2.5"): prefijo -> lados
FAMILIAS_CON_LINEA = {
    "total goals": {"over", "under"},
    "total cards": {"over", "under"},
    "total corners": {"over", "under"},
    "asian handicap": {"home", "away"},
}


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


def familia_de(mercado):
    """'Total Goals 2.5' -> ('Total Goals', {'over','under'}). Devuelve
    (None, None) si es una familia que no sabemos completar."""
    nombre = (mercado or "").strip()
    if nombre in FAMILIAS:
        return nombre, FAMILIAS[nombre]
    bajo = nombre.lower()
    for prefijo, lados in FAMILIAS_CON_LINEA.items():
        if bajo.startswith(prefijo):
            return prefijo.title(), lados
    return None, None


def main():
    print("CENSO DE MÁRGENES (mercados previos)")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    if not os.path.exists(RUTA_CALENDARIO):
        print("Falta data/calendario.csv")
        return
    cal = pd.read_csv(RUTA_CALENDARIO)
    hoy = datetime.now(timezone.utc).date()
    # Las cuotas previas existen hasta 7 días antes del partido (documentado).
    cal = cal[(pd.to_datetime(cal["fecha"]).dt.date >= hoy)
              & (pd.to_datetime(cal["fecha"]).dt.date <= hoy + timedelta(days=7))]
    partidos = cal.head(MAX_PARTIDOS)
    print(f"{len(partidos)} partidos de los próximos 7 días")

    filas = []
    for _, p in partidos.iterrows():
        datos = pedir("/odds", {"matchId": int(p["match_id"]), "oddsType": "prematch"})
        bloques = (datos.get("data", []) if isinstance(datos, dict) else datos) or []
        planas = []
        for b in bloques:
            if isinstance(b, dict):
                planas.extend(b.get("odds", []) or [])
        if not planas:
            continue

        # {(familia, mercado concreto): {casa: {lado: cuota}}}
        por_mercado = defaultdict(lambda: defaultdict(dict))
        for c in planas:
            familia, lados = familia_de(c.get("market"))
            if familia is None:
                continue
            casa = c.get("bookmakerName")
            for v in (c.get("values") or []):
                lado = str(v.get("value", "")).strip().lower()
                if lado not in lados:
                    continue
                try:
                    cuota = float(v.get("odd"))
                except (TypeError, ValueError):
                    continue
                if cuota > 1:
                    por_mercado[(familia, c.get("market"))][casa][lado] = cuota

        for (familia, mercado), por_casa in por_mercado.items():
            lados = familia_de(mercado)[1]
            margenes, mejores = [], {}
            for casa, cuotas in por_casa.items():
                if set(cuotas) != lados:      # conjunto incompleto: fuera
                    continue
                margenes.append(sum(1 / q for q in cuotas.values()) - 1)
                for lado, q in cuotas.items():
                    if q > mejores.get(lado, 0):
                        mejores[lado] = q
            if not margenes or set(mejores) != lados:
                continue
            filas.append({
                "match_id": int(p["match_id"]),
                "liga": p["liga"],
                "familia": familia,
                "mercado": mercado,
                "casas": len(margenes),
                "margen_medio": sum(margenes) / len(margenes),
                "margen_mejor_casa": min(margenes),
                "margen_combinado": sum(1 / q for q in mejores.values()) - 1,
            })

    if not filas:
        print("Sin cotizaciones utilizables")
        return

    d = pd.DataFrame(filas)
    os.makedirs("data", exist_ok=True)
    d.to_csv(RUTA_SALIDA, index=False)

    resumen = d.groupby("familia").agg(
        cotizaciones=("margen_medio", "size"),
        partidos=("match_id", "nunique"),
        casas=("casas", "mean"),
        margen_medio=("margen_medio", "mean"),
        margen_mejor_casa=("margen_mejor_casa", "mean"),
        margen_combinado=("margen_combinado", "mean"),
    ).sort_values("margen_combinado")

    lineas = [
        f"# Margen por mercado -- {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"{len(d)} cotizaciones de {d['match_id'].nunique()} partidos, "
        f"cuotas PREVIAS de las seis ligas.\n",
        "El margen es lo que hay que batir antes de ganar un céntimo. La "
        "columna que decide es **combinado**: el margen que pagas cogiendo la "
        "mejor cuota de cada lado, aunque sean de casas distintas.\n",
        "| Mercado | Cotizaciones | Casas | Margen medio | Mejor casa | **Combinado** |",
        "|---|---|---|---|---|---|",
    ]
    for fam, f in resumen.iterrows():
        lineas.append(
            f"| {fam} | {int(f['cotizaciones'])} | {f['casas']:.1f} | "
            f"{f['margen_medio']*100:.2f}% | {f['margen_mejor_casa']*100:.2f}% | "
            f"**{f['margen_combinado']*100:.2f}%** |")

    mejor = resumen.index[0]
    lineas += [
        f"\n**{mejor}** es el mercado más barato: "
        f"{resumen.iloc[0]['margen_combinado']*100:.2f}% comparando precios. "
        f"El más caro cobra {resumen.iloc[-1]['margen_combinado']*100:.2f}%.\n",
        "> Un modelo mediocre en un mercado barato gana más que uno excelente "
        "en uno caro. El margen es el suelo que hay que superar, y no depende "
        "de lo listos que seamos.\n",
    ]

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n" + "\n".join(lineas))
    print(f"[api] {LLAMADAS[0]} llamadas")


if __name__ == "__main__":
    main()
