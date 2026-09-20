"""
HISTÓRICO POR LIGA: reconstruir el reparto de tarjetas de cada liga.

EL PROBLEMA QUE RESUELVE
------------------------
lambda(k) está ajustada sobre 440 partidos de La Liga -- 23 equipos
españoles, ni uno de fuera -- y se está aplicando a la MLS, a Brasil, a la
Ligue 1 y a la Premier. Para La Liga está bien: el modelo implica unas 4.35
tarjetas por partido y la media española es 4.51. Para el resto no:

    Ligue 1     3.40 tarjetas en la 2a parte
    Premier     2.33
    MLS         2.54

De 2.33 a 3.40 hay un 46%. Un árbitro inglés y uno francés no pitan igual, y
el modelo no lo sabe porque nunca ha visto un partido inglés.

CÓMO SE RECONSTRUYE
-------------------
Los eventos de /matches/{id} traen el MINUTO de cada tarjeta. Eso permite
separar las del primer tiempo de las de la segunda en partidos ya terminados,
que es exactamente el dato de entrenamiento que hace falta -- y que hasta
ahora solo teníamos para España.

Los minutos vienen a veces como "45+3": se parte por el "+" y se queda la
parte entera. Una tarjeta en el 45+3 es del primer tiempo.

Una llamada por partido. Con el tope diario en 7.500 y un consumo actual del
10%, cabe de sobra.
"""
import os
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_LIGAS = "data/ligas.json"
RUTA_SALIDA = "data/historico_por_liga.csv"
RUTA_INFORME = "historico_por_liga.md"

DIAS_ATRAS = int(os.environ.get("DIAS_ATRAS", "120"))
MAX_POR_LIGA = int(os.environ.get("MAX_POR_LIGA", "120"))
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


def minuto_de_evento(e):
    """'45+3' -> 45. Una tarjeta en el descuento del primer tiempo es del
    primer tiempo, no de la segunda parte."""
    bruto = str(e.get("time", "")).strip()
    if not bruto:
        return None
    try:
        return int(bruto.split("+")[0])
    except ValueError:
        return None


def reparto_de_tarjetas(match_id):
    datos = pedir(f"/matches/{match_id}")
    if not datos:
        return None
    m = datos[0] if isinstance(datos, list) else datos
    estado = ((m.get("state") or {}).get("description") or "").lower()
    if not estado.startswith("finish"):
        return None

    primera = segunda = sin_minuto = 0
    for e in (m.get("events") or []):
        if e.get("type") not in ("Yellow Card", "Red Card"):
            continue
        minuto = minuto_de_evento(e)
        if minuto is None:
            sin_minuto += 1
        elif minuto <= 45:
            primera += 1
        else:
            segunda += 1

    # Un partido cuyas tarjetas no traen minuto no sirve para entrenar el
    # reparto: se descarta entero en vez de contarlas como si fueran de la
    # primera parte, que es lo que haría un cero por defecto.
    if sin_minuto:
        return None

    return {
        "match_id": match_id,
        "fecha": str(m.get("date"))[:10],
        "local": (m.get("homeTeam") or {}).get("name"),
        "visitante": (m.get("awayTeam") or {}).get("name"),
        "tarjetas_ht": primera,
        "tarjetas_2a": segunda,
        "total": primera + segunda,
    }


def main():
    print("HISTÓRICO POR LIGA")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    if not os.path.exists(RUTA_LIGAS):
        print("Falta data/ligas.json -- hay que generar el calendario primero")
        return
    ligas = {k: v for k, v in json.load(open(RUTA_LIGAS, encoding="utf-8")).items()
             if not k.startswith("_")}

    previo = pd.read_csv(RUTA_SALIDA) if os.path.exists(RUTA_SALIDA) else pd.DataFrame()
    ya_vistos = set(previo["match_id"]) if "match_id" in previo.columns else set()
    print(f"Ya teníamos {len(ya_vistos)} partidos")

    hoy = datetime.now(timezone.utc).date()
    filas = []

    for nombre, lid in ligas.items():
        # Se piden los partidos de la liga y se quedan los terminados dentro
        # de la ventana. La temporada la resuelve la propia API con el rango
        # de fechas, así que no hay que acertar con el número.
        candidatos = []
        for offset in range(0, 1200, 100):
            lote = desempaquetar(pedir("/matches", {"leagueId": lid, "limit": 100,
                                                     "offset": offset}, espera=0.2))
            if not lote:
                break
            candidatos.extend(lote)
            if len(lote) < 100:
                break

        terminados = []
        for p in candidatos:
            estado = ((p.get("state") or {}).get("description") or "").lower()
            if not estado.startswith("finish"):
                continue
            try:
                cuando = datetime.fromisoformat(str(p["date"]).replace("Z", "+00:00")).date()
            except (ValueError, KeyError, TypeError):
                continue
            if (hoy - cuando).days > DIAS_ATRAS:
                continue
            if p["id"] in ya_vistos:
                continue
            terminados.append(p)

        terminados.sort(key=lambda x: str(x.get("date")), reverse=True)
        nuevos = 0
        for p in terminados[:MAX_POR_LIGA]:
            fila = reparto_de_tarjetas(p["id"])
            if fila:
                fila["liga"] = nombre
                filas.append(fila)
                nuevos += 1
        print(f"  {nombre}: {len(terminados)} terminados sin procesar, "
              f"{nuevos} con minutos utilizables")

    if not filas and previo.empty:
        print("Nada que guardar")
        return

    datos = pd.concat([previo, pd.DataFrame(filas)], ignore_index=True) if filas else previo
    datos = datos.drop_duplicates(subset="match_id", keep="last")
    os.makedirs("data", exist_ok=True)
    datos.to_csv(RUTA_SALIDA, index=False)

    resumen = datos.groupby("liga").agg(
        partidos=("total", "size"),
        ht=("tarjetas_ht", "mean"),
        segunda=("tarjetas_2a", "mean"),
        total=("total", "mean"),
    ).round(2).sort_values("segunda", ascending=False)

    lineas = [
        f"# Tarjetas por liga -- {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"{len(datos)} partidos terminados con el minuto de cada tarjeta, "
        f"de los últimos {DIAS_ATRAS} días.\n",
        "Sirve para contestar si mezclar ligas en el modelo del descanso es "
        "un error. lambda(k) está ajustada solo con La Liga.\n",
        "| Liga | Partidos | 1ª parte | 2ª parte | Total |",
        "|---|---|---|---|---|",
    ]
    for liga, f in resumen.iterrows():
        lineas.append(f"| {liga} | {int(f['partidos'])} | {f['ht']:.2f} | "
                      f"{f['segunda']:.2f} | {f['total']:.2f} |")

    if len(resumen) >= 2:
        alta, baja = resumen["segunda"].max(), resumen["segunda"].min()
        lineas.append(f"\nDe {baja:.2f} a {alta:.2f} tarjetas en la segunda "
                      f"parte: un **{(alta/baja-1)*100:.0f}%** de diferencia "
                      f"entre la liga más dura y la más suave.\n")

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n" + "\n".join(lineas))
    print(f"\n[api] {LLAMADAS[0]} llamadas")


if __name__ == "__main__":
    main()
