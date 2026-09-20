"""
¿QUÉ CASAS SE DESCUELGAN DEL CONSENSO?

EL PROBLEMA QUE RESUELVE
------------------------
El margen combinado del 1X2 es del 1.43%, pero solo si coges la mejor cuota
de entre cuarenta y dos casas. Nadie tiene cuarenta y dos cuentas. Con una
sola cuenta el margen que pagas es del 3.81%.

Pero no hacen falta cuarenta y dos cuentas para USAR cuarenta y dos casas.
El consenso es el instrumento de medida y lo da la API gratis; la cuenta solo
hace falta donde vayas a apostar. La apuesta aparece cuando TU casa se
descuelga del consenso de las otras.

Así que la pregunta práctica no es "cuál es el mercado más barato" sino
"qué casas se salen de la fila y con qué frecuencia", porque ésas son las
que merece la pena abrir.

CÓMO SE MIDE
------------
Para cada mercado de cada partido:

  1. Se desmarginan las cuotas de cada casa (normalizar 1/cuota a que sume 1),
     que quita el margen y deja la opinión limpia de esa casa.
  2. El consenso es la mediana de las demás casas, EXCLUYENDO a la que se
     evalúa. Si no se excluye, una casa influye en el consenso contra el que
     se la compara y las desviaciones salen pequeñas para todas.
  3. La desviación es su probabilidad menos ese consenso.

Se usa mediana y no media porque una casa muy descolgada arrastra la media
justo en los casos que interesan.

QUÉ SIGNIFICA CADA COLUMNA
--------------------------
  - `desv_media`: cuánto se aparta de media, en puntos de probabilidad. Mide
    si la casa tiene opinión propia o copia al resto.
  - `sesgo`: si se aparta sistemáticamente hacia arriba o hacia abajo. Un
    sesgo grande no es una oportunidad, es una casa con otro modelo.
  - `generosas`: en qué porcentaje de casos ofrece MÁS probabilidad de la que
    dice el consenso, que es cuando la cuota está regalada.

UNA ADVERTENCIA QUE NO ES TÉCNICA
---------------------------------
Las casas que más se descuelgan suelen ser las que antes limitan o cierran
las cuentas que les ganan. Una casa con precios blandos y tolerancia a
perdedores no existe: es blanda porque no vigila, y en cuanto vigila, cierra.
Esto sale del análisis pero conviene saberlo antes de abrir cuentas.
"""
import os
import time
import requests
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_CALENDARIO = "data/calendario.csv"
RUTA_SALIDA = "data/casas_descolgadas.csv"
RUTA_INFORME = "casas_descolgadas.md"

MAX_PARTIDOS = int(os.environ.get("MAX_PARTIDOS", "40"))
MIN_CASAS = 8      # por debajo de esto el "consenso" no es consenso
LLAMADAS = [0]

FAMILIAS = {
    "Full Time Result": {"home", "draw", "away"},
    "Both Teams To Score": {"yes", "no"},
    "Odd or Even": {"odd", "even"},
    "Clean Sheet": {"home", "away"},
}
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
    nombre = (mercado or "").strip()
    if nombre in FAMILIAS:
        return nombre, FAMILIAS[nombre]
    bajo = nombre.lower()
    for prefijo, lados in FAMILIAS_CON_LINEA.items():
        if bajo.startswith(prefijo):
            return prefijo.title(), lados
    return None, None


def desmarginar(cuotas):
    """1/cuota normalizado a sumar 1: la opinión de la casa sin su margen."""
    inv = {k: 1 / v for k, v in cuotas.items()}
    total = sum(inv.values())
    return {k: v / total for k, v in inv.items()} if total else None


def main():
    print("CASAS DESCOLGADAS DEL CONSENSO")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    if not os.path.exists(RUTA_CALENDARIO):
        print("Falta data/calendario.csv")
        return
    cal = pd.read_csv(RUTA_CALENDARIO)
    hoy = datetime.now(timezone.utc).date()
    cal = cal[(pd.to_datetime(cal["fecha"]).dt.date >= hoy)
              & (pd.to_datetime(cal["fecha"]).dt.date <= hoy + timedelta(days=7))]
    partidos = cal.head(MAX_PARTIDOS)
    print(f"{len(partidos)} partidos")

    filas = []
    for _, p in partidos.iterrows():
        datos = pedir("/odds", {"matchId": int(p["match_id"]), "oddsType": "prematch"})
        bloques = (datos.get("data", []) if isinstance(datos, dict) else datos) or []
        planas = []
        for b in bloques:
            if isinstance(b, dict):
                planas.extend(b.get("odds", []) or [])

        por_mercado = defaultdict(lambda: defaultdict(dict))
        for c in planas:
            familia, lados = familia_de(c.get("market"))
            if familia is None:
                continue
            for v in (c.get("values") or []):
                lado = str(v.get("value", "")).strip().lower()
                if lado not in lados:
                    continue
                try:
                    cuota = float(v.get("odd"))
                except (TypeError, ValueError):
                    continue
                if cuota > 1:
                    por_mercado[(familia, c.get("market"))][c.get("bookmakerName")][lado] = cuota

        for (familia, mercado), por_casa in por_mercado.items():
            lados = familia_de(mercado)[1]
            limpias = {}
            for casa, cuotas in por_casa.items():
                if set(cuotas) != lados:
                    continue
                d = desmarginar(cuotas)
                if d:
                    limpias[casa] = d
            if len(limpias) < MIN_CASAS:
                continue

            for casa, probs in limpias.items():
                for lado in lados:
                    # consenso SIN la casa evaluada: si se incluye, cada casa
                    # tira del consenso hacia sí misma y todas parecen menos
                    # descolgadas de lo que están
                    otras = [q[lado] for c, q in limpias.items() if c != casa]
                    if len(otras) < MIN_CASAS - 1:
                        continue
                    consenso = float(np.median(otras))
                    cuota = por_casa[casa][lado]
                    # LO QUE DECIDE. No basta con que la casa opine distinto:
                    # su CUOTA REAL tiene que pagar más de lo que vale la
                    # apuesta según el consenso. 1/cuota lleva el margen
                    # dentro, así que compararla con el consenso ya descuenta
                    # lo que la casa se queda. Si 1/cuota < consenso, esa
                    # cuota está por encima de su valor: eso es una apuesta
                    # con valor de verdad, no una diferencia de opinión.
                    prob_cuota = 1 / cuota
                    filas.append({
                        "casa": casa, "familia": familia, "mercado": mercado,
                        "lado": lado, "match_id": int(p["match_id"]),
                        "cuota": cuota,
                        "prob_cuota": prob_cuota,
                        "prob_casa": probs[lado], "consenso": consenso,
                        "desviacion": probs[lado] - consenso,
                        "valor": consenso / prob_cuota - 1,
                    })

    if not filas:
        print("Sin datos suficientes")
        return

    d = pd.DataFrame(filas)
    os.makedirs("data", exist_ok=True)
    d.to_csv(RUTA_SALIDA, index=False)

    r = d.groupby("casa").agg(
        cotizaciones=("desviacion", "size"),
        partidos=("match_id", "nunique"),
        desv_media=("desviacion", lambda x: x.abs().mean()),
        valor_medio=("valor", "mean"),
        con_valor=("valor", lambda x: (x > 0).mean()),
        valor_2pc=("valor", lambda x: (x > 0.02).mean()),
        mejor=("valor", "max"),
    )
    r = r[r["cotizaciones"] >= 30].sort_values("valor_2pc", ascending=False)

    lineas = [
        f"# Casas descolgadas del consenso -- "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"{len(d)} comparaciones sobre {d['match_id'].nunique()} partidos y "
        f"{d['casa'].nunique()} casas.\n",
        "No hacen falta cuarenta y dos cuentas para usar cuarenta y dos casas: "
        "el consenso es el instrumento de medida, y la cuenta solo hace falta "
        "donde se apuesta. Esta tabla dice **qué cuentas merece la pena "
        "abrir**: las que más se salen de la fila.\n",
        "| Casa | Cotizaciones | Desviación | Valor medio | % con valor | "
        "**% valor >2%** | Mejor |",
        "|---|---|---|---|---|---|---|",
    ]
    for casa, f in r.head(25).iterrows():
        lineas.append(f"| {casa} | {int(f['cotizaciones'])} | "
                      f"{f['desv_media']*100:.2f} pts | "
                      f"{f['valor_medio']*100:+.2f}% | "
                      f"{f['con_valor']*100:.1f}% | "
                      f"**{f['valor_2pc']*100:.1f}%** | "
                      f"{f['mejor']*100:+.1f}% |")

    lineas += [
        "\n## Cómo leerla\n",
        "- **Desviación**: cuánto se aparta su OPINIÓN del resto, ya sin "
        "margen. Mide si tiene modelo propio, no si paga bien.",
        "- **Valor**: lo que de verdad importa. Compara la CUOTA REAL contra "
        "el consenso, así que el margen que cobra la casa ya está "
        "descontado. Un +3% significa que esa cuota paga un 3% más de lo que "
        "vale la apuesta.",
        "- **% valor >2%**: con qué frecuencia esa casa ofrece una apuesta "
        "que bate al consenso por un margen que aguanta el ruido. Es la "
        "columna por la que está ordenada la tabla.\n",
        "> Ojo con la diferencia entre desviación y valor: una casa puede "
        "opinar muy distinto y no pagar nada, si se descuelga hacia el lado "
        "que le conviene o si cobra un margen que se come la diferencia.\n",
        "> Las casas que más se descuelgan suelen ser las que antes limitan o "
        "cierran las cuentas que les ganan. Una casa blanda y a la vez "
        "tolerante con los ganadores no existe: es blanda porque no vigila, y "
        "en cuanto vigila, cierra. Conviene saberlo antes de abrir cuentas.\n",
    ]

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n" + "\n".join(lineas[:40]))
    print(f"[api] {LLAMADAS[0]} llamadas")


if __name__ == "__main__":
    main()
