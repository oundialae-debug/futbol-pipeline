"""
Precio de ANTES del partido de cada mercado de tenis cerrado en Kalshi (API
pública sin clave; aprobado por el usuario el 30/09/2026).

Regla fijada antes de mirar ningún precio: la hora de inicio que publica
Kalshi (occurrence_datetime) no sirve (en ITF el 90% de los partidos ya había
terminado a esa hora). Se toma el último precio anterior a
T = cierre - margen, con margen = 6 h en ATP (5 sets) y 4 h en el resto. El
cierre es cuando se declara el ganador, así que T queda antes del inicio
salvo suspensiones. Se guarda también T - 2 h para probar que el resultado
no depende del margen.

Precio: velas de 1 hora. Se guardan compra (yes_bid), venta (yes_ask) y
último precio negociado del lado "sí" de la vela que acaba justo antes de T,
y el volumen acumulado hasta T.

Mercados de partido: un lado por partido (el otro es el complementario).
Total de juegos y hándicap: todas las líneas.
Los liquidados antes del corte (01/08/2026) van por /historical/... y sus
campos no llevan el sufijo _dollars.

Los liquidados tras el corte van en lotes de 100 (/markets/candlesticks);
los antiguos, de uno en uno a 8 peticiones/s como mucho (el límite de Kalshi
devuelve 429 con más). `--recientes` / `--antiguos` para hacer solo una parte; `--max=N` limita
los antiguos a una muestra al azar fija de N (para ir más rápido en ITF).

Los liquidados tras el corte van en lotes de 100 (/markets/candlesticks);
los antiguos, de uno en uno a 8 peticiones/s como mucho (el límite de Kalshi
devuelve 429 con más). `--recientes` / `--antiguos` para hacer solo una parte; `--max=N` limita
los antiguos a una muestra al azar fija de N (para ir más rápido en ITF).
Corre en GitHub Actions (kalshi_tenis.yml) para no gastar la sesión.

Reanudable: data/tenis/kalshi/precios_<serie>.csv se completa sin repetir.
"""
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

API = "https://api.elections.kalshi.com/trade-api/v2"
D = "data/tenis/kalshi"
MARGEN_H = {"KXATPMATCH": 6}
PARTIDO = {"KXATPMATCH", "KXWTAMATCH", "KXATPCHALLENGERMATCH", "KXWTACHALLENGERMATCH", "KXITFMATCH", "KXITFWMATCH"}
sesion = requests.Session()
RITMO = 8.0                      # peticiones por segundo como mucho (el límite de Kalshi da 429 con más)
_cerrojo, _ultima = threading.Lock(), [0.0]


def esperar_turno():
    with _cerrojo:
        ahora = time.time()
        espera = _ultima[0] + 1 / RITMO - ahora
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = max(ahora, _ultima[0] + 1 / RITMO)


def pedir(url, params):
    for intento in range(6):
        try:
            esperar_turno()
            r = sesion.get(url, params=params, timeout=60)
            if r.status_code == 429:
                time.sleep(1.0 + intento)
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(1.5 * 2 ** intento)
    return None


def valor(x, campo):
    if not isinstance(x, dict):
        return None
    v = x.get(f"{campo}_dollars", x.get(campo))
    return float(v) if v not in (None, "") else None


def precio_en(velas, t):
    antes = [v for v in velas if v["end_period_ts"] <= t]
    if not antes:
        return None, None, None, 0.0, None
    v = antes[-1]
    vol = sum(float(x.get("volume_fp", x.get("volume")) or 0) for x in antes)
    ultimo = None
    for x in reversed(antes):                         # último precio negociado hasta t
        ultimo = valor(x.get("price"), "close")
        if ultimo is not None:
            break
    return valor(v.get("yes_bid"), "close"), valor(v.get("yes_ask"), "close"), ultimo, vol, v["end_period_ts"]


def uno(fila, serie):
    cierre = int(pd.Timestamp(fila["close_time"]).timestamp())
    apertura = int(pd.Timestamp(fila["open_time"]).timestamp())
    t = cierre - MARGEN_H.get(serie, 4) * 3600
    t2 = t - 2 * 3600
    ruta = (f"{API}/series/{serie}/markets/{fila['ticker']}/candlesticks" if fila["origen"] == "markets"
            else f"{API}/historical/markets/{fila['ticker']}/candlesticks")
    j = pedir(ruta, {"start_ts": max(apertura, t - 72 * 3600), "end_ts": t, "period_interval": 60})
    velas = (j or {}).get("candlesticks", [])
    b, a, u, vol, ts = precio_en(velas, t)
    b2, a2, u2, vol2, ts2 = precio_en(velas, t2)
    return {"ticker": fila["ticker"], "t": t, "bid": b, "ask": a, "ultimo": u, "vol": vol, "vela": ts,
            "bid_2h": b2, "ask_2h": a2, "ultimo_2h": u2, "vol_2h": vol2, "ok": j is not None}


def lote_recientes(filas, serie):
    """Mercados liquidados tras el corte: /markets/candlesticks, 100 por petición.
    Ventana común: desde 76 h antes del primer cierre hasta el último cierre del lote."""
    res = []
    for i in range(0, len(filas), 100):
        grupo = filas[i:i + 100]
        cierres = [int(pd.Timestamp(f["close_time"]).timestamp()) for f in grupo]
        j = pedir(f"{API}/markets/candlesticks", {"market_tickers": ",".join(f["ticker"] for f in grupo),
                                                 "start_ts": min(cierres) - 76 * 3600, "end_ts": max(cierres),
                                                 "period_interval": 60})
        velas = {m["market_ticker"]: m["candlesticks"] for m in (j or {}).get("markets", [])}
        for f, cierre in zip(grupo, cierres):
            t = cierre - MARGEN_H.get(serie, 4) * 3600
            v = [x for x in velas.get(f["ticker"], []) if x["end_period_ts"] <= t]
            b, a, u, vol, ts = precio_en(v, t)
            b2, a2, u2, vol2, ts2 = precio_en(v, t - 2 * 3600)
            res.append({"ticker": f["ticker"], "t": t, "bid": b, "ask": a, "ultimo": u, "vol": vol, "vela": ts,
                        "bid_2h": b2, "ask_2h": a2, "ultimo_2h": u2, "vol_2h": vol2,
                        "ok": j is not None and f["ticker"] in velas})
    return res


def main():
    args = sys.argv[1:]
    solo, maximo = None, None
    if args and args[0] in ("--recientes", "--antiguos"):
        solo, args = args[0][2:], args[1:]
    if args and args[0].startswith("--max="):
        maximo, args = int(args[0].split("=")[1]), args[1:]
    series = args
    for serie in series:
        m = pd.read_csv(f"{D}/mercados_{serie}.csv")
        m = m[m["result"].isin(["yes", "no"])]
        if serie in PARTIDO:
            m = m.sort_values("ticker").drop_duplicates("event_ticker")
        salida = f"{D}/precios_{serie}.csv"
        hechos = set(pd.read_csv(salida)["ticker"]) if os.path.exists(salida) else set()
        pend = m[~m["ticker"].isin(hechos)]
        recientes = pend[pend["origen"] == "markets"].sort_values("close_time").to_dict("records")
        antiguos = pend[pend["origen"] != "markets"]
        if maximo is not None:
            # muestra al azar fija de los antiguos (semilla 1), descontando los ya hechos
            todos = m[m["origen"] != "markets"].sample(frac=1, random_state=1).head(maximo)
            antiguos = antiguos[antiguos["ticker"].isin(todos["ticker"])]
        antiguos = antiguos.to_dict("records")
        print(f"{serie}: {len(m)} mercados, {len(pend)} pendientes ({len(recientes)} recientes)", flush=True)
        if solo != "antiguos" and recientes:
            pd.DataFrame(lote_recientes(recientes, serie)).to_csv(salida, mode="a", header=not os.path.exists(salida),
                                                                  index=False)
            print(f"  {serie}: recientes hechos", flush=True)
        filas = antiguos if solo != "recientes" else []
        for i in range(0, len(filas), 500):
            with ThreadPoolExecutor(8) as ex:
                res = list(ex.map(lambda f: uno(f, serie), filas[i:i + 500]))
            pd.DataFrame(res).to_csv(salida, mode="a", header=not os.path.exists(salida), index=False)
            print(f"  {serie}: {min(i + 500, len(filas))}/{len(filas)}", flush=True)


if __name__ == "__main__":
    main()
