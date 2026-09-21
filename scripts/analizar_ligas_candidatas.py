"""
LIGA MX Y RUMANIA LIGA II: ¿EL PRECIO ESTA MAL, O SOLO TIENE MENOS OJOS?

LA MISMA PREGUNTA QUE MATO LA HIPOTESIS DE CORNERS, APLICADA AL EJE CORRECTO
------------------------------------------------------------------------------
Pocas casas es necesario pero no suficiente. Corners tenia 6,5 casas y el
precio resulto ser exacto -- caro, no malo (precio_malo_o_caro.md). La unica
forma de saberlo aqui es la misma: comparar lo que se pierde contra un precio
PERFECTO (-margen/(1+margen)) con lo que se pierde de verdad, sobre resultados
reales.

LA RESTRICCION DE VERDAD: LA VENTANA DE 28 DIAS
-------------------------------------------------
Las cuotas solo estan disponibles hasta 28 dias despues del partido. Estas
ligas nunca se han tocado, asi que no hay historico previo: la muestra son
los partidos jugados en las ultimas ~4 semanas, que van a ser pocos. Si la
muestra es minuscula, este script lo dice en voz alta en vez de fingir una
conclusion (regla del proyecto: n<20 no se ensena sin avisar).

QUE HACE
--------
1. Encuentra el ID exacto de cada liga candidata (por pais, nunca por nombre
   suelto -- Liga MX y Liga II son nombres genericos que podrian coincidir
   con otras competiciones).
2. Trae los partidos TERMINADOS de las ultimas 4 semanas.
3. Pide las cuotas de 1X2 de esos partidos.
4. Calcula: margen por casa, calibracion (precio mal vs caro), y retorno real
   de apostar a ciegas, agrupado por partido.

NO INVENTA UN VEREDICTO CON POCOS DATOS
-----------------------------------------
Con n<15 partidos, se imprime el numero pero con la advertencia explicita de
que no es una conclusion, es una primera mirada.
"""
import os
import time
import requests
from datetime import datetime, timedelta, timezone
import numpy as np

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

# Por pais, nunca por nombre suelto.
CANDIDATAS = [("RO", "Rumania", "Liga II"), ("MX", "Mexico", "Liga MX")]

llamadas = [0]


def pedir(path, params=None):
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS,
                             params=params, timeout=25)
        except Exception:
            time.sleep(2*(intento+1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            return None, f"[HTTP {r.status_code}]"
        try:
            return r.json(), "ok"
        except Exception:
            return None, "[no es JSON]"
    return None, "[fallo tras reintentos]"


def desempaquetar(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def terminado(p):
    e = p.get("state")
    desc = (e.get("description") if isinstance(e, dict) else e) or ""
    return "finish" in str(desc).lower()


def goles(p):
    e = p.get("state") or {}
    s = (e.get("score") or {}).get("current") if isinstance(e, dict) else None
    if not s or "-" not in str(s):
        return None, None
    try:
        a, b = str(s).split("-")
        return int(a.strip()), int(b.strip())
    except Exception:
        return None, None


def encontrar_liga_id(codigo_pais, nombre_buscado):
    j, _ = pedir("/leagues", {"countryCode": codigo_pais, "limit": 30})
    for liga in desempaquetar(j) if j else []:
        if nombre_buscado.lower() in str(liga.get("name", "")).lower():
            return liga.get("id"), liga.get("name")
    return None, None


def analizar(liga_id, nombre, pais):
    hoy = datetime.now(timezone.utc).date()
    partidos = {}
    for dd in range(28, -1, -1):
        fecha = (hoy - timedelta(days=dd)).isoformat()
        j, _ = pedir("/matches", {"leagueId": liga_id, "date": fecha, "limit": 50})
        for p in desempaquetar(j) if j else []:
            if terminado(p):
                gl, gv = goles(p)
                if gl is not None:
                    partidos[p["id"]] = (p, gl, gv)

    print(f"\n{'='*72}\n{pais} -- {nombre} (id {liga_id})\n{'='*72}")
    print(f"Partidos TERMINADOS en las ultimas 4 semanas: {len(partidos)}  "
          f"(llamadas {llamadas[0]})")
    if not partidos:
        print("  Sin partidos terminados en la ventana. No se puede analizar.")
        return

    filas = []
    for mid, (p, gl, gv) in partidos.items():
        j, _ = pedir("/odds", {"matchId": mid})
        for bloque in desempaquetar(j) if j else []:
            for o in (bloque.get("odds") or []):
                if o.get("market") != "Full Time Result":
                    continue
                casa = o.get("bookmakerName")
                for v in (o.get("values") or []):
                    try:
                        cuota = float(v.get("odd"))
                    except (TypeError, ValueError):
                        continue
                    lado = str(v.get("value", "")).lower()
                    filas.append((mid, casa, lado, cuota, gl, gv))

    if not filas:
        print("  Ningun partido tenia cuotas de 1X2 en la API. No se puede "
              "medir nada -- puede que el plan no cubra esta liga.")
        return

    import pandas as pd
    d = pd.DataFrame(filas, columns=["match_id","casa","lado","cuota","gl","gv"])
    ncasas = d.groupby("match_id").casa.nunique().mean()
    npartidos = d.match_id.nunique()
    aviso = "  [!] MUESTRA MINUSCULA -- no es conclusion, es una primera mirada" \
            if npartidos < 15 else ""
    print(f"Partidos CON cuotas de 1X2: {npartidos}  |  casas por partido: "
          f"{ncasas:.1f}{aviso}")

    # margen por casa (sobre las que tienen los 3 lados)
    margenes = []
    for (mid, casa), g in d.groupby(["match_id","casa"]):
        if set(g.lado) == {"home","draw","away"}:
            margenes.append((1/g.cuota).sum() - 1)
    if margenes:
        print(f"Margen medio de una casa: {np.mean(margenes)*100:.2f}%")

    # calibracion: lo que perderias contra un precio PERFECTO vs lo real
    def resultado(lado, gl, gv):
        if lado == "home": return 1.0 if gl>gv else (0.5 if gl==gv else 0.0)
        if lado == "away": return 1.0 if gv>gl else (0.5 if gl==gv else 0.0)
        if lado == "draw": return 1.0 if gl==gv else 0.0
        return None
    d["resultado"] = d.apply(lambda r: resultado(r.lado, r.gl, r.gv), axis=1)
    d = d.dropna(subset=["resultado"])
    d["retorno"] = np.where(d.resultado==1.0, d.cuota-1,
                    np.where(d.resultado==0.5, 0.0, -1.0))

    m = d.retorno.mean()
    g = d.groupby("match_id").retorno.agg(["sum","count"])
    ee = np.sqrt(((g["sum"]-g["count"]*m)**2).sum()/(g["count"].sum()**2)) if len(g)>1 else np.nan
    sigmas = m/ee if ee and ee > 0 else float("nan")
    margen_medio = np.mean(margenes) if margenes else np.nan
    esperado = -margen_medio/(1+margen_medio) if margen_medio==margen_medio else np.nan
    hueco = m - esperado if esperado==esperado else np.nan

    print(f"\nRETORNO REAL apostando a ciegas, agrupado por partido:")
    print(f"  {m*100:+.2f}%  (±{ee*100:.2f} pts, {sigmas:+.2f} sigmas, "
          f"n={len(g)} partidos)")
    if esperado==esperado:
        print(f"  esperado con precio perfecto: {esperado*100:+.2f}%  "
              f"->  hueco: {hueco*100:+.2f}%")
    if npartidos < 15:
        print(f"\n  [!] Con {npartidos} partidos este numero puede moverse "
              f"mucho al anadir mas. NO es una conclusion todavia.")


def main():
    for codigo, pais, nombre in CANDIDATAS:
        lid, lname = encontrar_liga_id(codigo, nombre)
        if not lid:
            print(f"\n[!] No se encontro '{nombre}' en {pais}")
            continue
        analizar(lid, lname, pais)
    print(f"\n{'='*72}\nTotal llamadas: {llamadas[0]}\n{'='*72}")


if __name__ == "__main__":
    main()
