"""
COSECHAR CUOTAS ANTES DE QUE CADUQUEN

EL CUELLO DE BOTELLA QUE ESTO ATACA
-----------------------------------
`aporta_algo.py` encontro que mezclar mercado y modelo al 43% baja el Brier de
0.6558 a 0.6457. La curva tiene minimo claro en el medio, que es la forma de
una senal real. Pero el bootstrap da [0.00, 0.98]: con 89 partidos no se
demuestra nada.

Lo que falta NO es modelo ni rasgos: son partidos con cuotas. Y hay dos
motivos por los que tenemos tan pocos:

  1. El backtest tenia un tope de 150 partidos que puse yo.
  2. Las cuotas CADUCAN. La API las sirve hasta 28 dias despues del partido y
     7 antes. Lo que no se coseche en esa ventana se pierde para siempre.

Ahora mismo hay 204 partidos jugados dentro de la ventana y solo tenemos 120.

POR QUE ESTO SI MERECE RECOLECTAR, Y LO DE ANTES NO
---------------------------------------------------
Antes propuse recolectar 15 semanas "a ver si sale algo". Esto es distinto:
hay una hipotesis concreta y cuantificada (el peso de mezcla w es mayor que
cero) y un numero que la contestara. Recolectar para contestar una pregunta
que ya esta planteada no es lo mismo que recolectar por si acaso.

A ~50 partidos por semana, en ocho semanas el intervalo se estrecha lo
bastante para decidir.

QUE GUARDA
----------
Una fila por (partido, casa, mercado, lado, cuota), acumulando. No sobrescribe
como hacia backtest_valor.csv: lo que entra se queda, porque no se puede
volver a pedir.

NO REPIDE lo que ya tiene, asi que se puede lanzar a diario sin gastar de mas.
"""
import os
import csv
import time
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

LIGAS = {33973: "Premier League", 119924: "La Liga", 115669: "Serie A",
         67162: "Bundesliga", 52695: "Ligue 1", 120775: "Segunda",
         # Añadida el 21/09: unica senal del dia que no murio al auditarla.
         # +20,41% a ciegas en 31 partidos, pero un solo partido aporta 6,76
         # de esos puntos y sin el la significacion cae a 0,82 sigmas. No es
         # hallazgo todavia -- se acumula hasta tener muestra que decida.
         # Ver ligas_candidatas.md.
         223746: "Liga MX"}

RUTA = "data/cuotas_cosechadas.csv"
COLUMNAS = ["match_id", "fecha", "liga_id", "casa", "mercado", "lado",
            "cuota", "cosechado"]
# 27 hacia atras (la API da 28, se deja un dia de margen) y 7 hacia delante
DIAS_ATRAS = int(os.environ.get("DIAS_ATRAS", "27"))
DIAS_ADELANTE = int(os.environ.get("DIAS_ADELANTE", "7"))
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "1200"))

llamadas = [0]


def pedir(path, params=None):
    if llamadas[0] >= TOPE_LLAMADAS:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS,
                             params=params, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except Exception:
            return None
    return None


def desempaquetar(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def ya_tengo():
    if not os.path.exists(RUTA):
        return set()
    with open(RUTA, newline="", encoding="utf-8") as f:
        return {fila["match_id"] for fila in csv.DictReader(f)}


def main():
    os.makedirs("data", exist_ok=True)
    vistos = ya_tengo()
    hoy = datetime.now(timezone.utc).date()
    ahora = datetime.now(timezone.utc).isoformat()
    print(f"Ya tenia cuotas de {len(vistos)} partidos.")
    print(f"Ventana: {DIAS_ATRAS} dias atras, {DIAS_ADELANTE} adelante. "
          f"Tope {TOPE_LLAMADAS} llamadas.\n")

    # 1. que partidos hay en la ventana
    candidatos = {}
    for d in range(-DIAS_ATRAS, DIAS_ADELANTE + 1):
        fecha = (hoy + timedelta(days=d)).isoformat()
        for lid, liga in LIGAS.items():
            j = pedir("/matches", {"leagueId": lid, "date": fecha, "limit": 100})
            for p in desempaquetar(j) if j else []:
                candidatos[str(p["id"])] = (p.get("date"), lid)
    nuevos = [m for m in candidatos if m not in vistos]
    print(f"{len(candidatos)} partidos en la ventana, "
          f"{len(nuevos)} sin cuotas guardadas.  (llamadas {llamadas[0]})\n")

    # 2. cuotas de los que faltan
    nuevo_fichero = not os.path.exists(RUTA)
    f = open(RUTA, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=COLUMNAS)
    if nuevo_fichero:
        w.writeheader()

    guardados = sin_cuotas = filas = 0
    try:
        for mid in nuevos:
            if llamadas[0] >= TOPE_LLAMADAS:
                break
            j = pedir("/odds", {"matchId": mid})
            bloques = desempaquetar(j) if j else []
            fecha, lid = candidatos[mid]
            n_antes = filas
            for b in bloques:
                for o in b.get("odds", []) or []:
                    casa = o.get("bookmakerName")
                    mercado = o.get("market")
                    for v in o.get("values", []) or []:
                        try:
                            cuota = float(v.get("odd"))
                        except (TypeError, ValueError):
                            continue
                        w.writerow({"match_id": mid, "fecha": fecha,
                                    "liga_id": lid, "casa": casa,
                                    "mercado": mercado,
                                    "lado": v.get("value"), "cuota": cuota,
                                    "cosechado": ahora})
                        filas += 1
            if filas > n_antes:
                guardados += 1
            else:
                sin_cuotas += 1
            if guardados % 25 == 0:
                f.flush()
    finally:
        f.close()

    print(f"{guardados} partidos nuevos con cuotas, {filas} filas.")
    if sin_cuotas:
        print(f"{sin_cuotas} partidos de la ventana SIN cuotas en la API "
              f"(normal en ligas pequenas o partidos muy recientes).")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: quedan partidos. Vuelve a lanzarlo.")


if __name__ == "__main__":
    main()
