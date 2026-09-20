"""
SONDEO: ¿podemos saber las faltas del PRIMER TIEMPO?

El histórico trae faltas del partido entero, y ahí la señal es fuerte:
correlación +0.406 con las tarjetas, frente al -0.171 de las tarjetas al
descanso. Pero para el modelo del descanso hacen falta las faltas del primer
tiempo, y eso es otra cosa.

Dos preguntas, y las dos se contestan mirando, no razonando:

  1. ¿/statistics devuelve algún desglose por tiempos? Si lo devuelve, se
     puede ajustar el coeficiente con el histórico que ya tenemos y esto se
     resuelve hoy.
  2. Si no lo devuelve: ¿/statistics de un partido EN JUEGO da los acumulados
     hasta ese minuto? Si es así, llamándolo en el descanso salen las faltas
     del primer tiempo. No sirve para el histórico, pero sí para ir
     apuntándolas desde ahora.

El sondeo imprime la estructura cruda de las claves, sin inventar nada.
"""
import os
import time
import json
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ",
           "scheduled", "tbd", "to be")


def pedir(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception as e:
        print(f"  [error de red] {type(e).__name__}")
        return None
    time.sleep(0.3)
    if r.status_code != 200:
        print(f"  [HTTP {r.status_code}] {path}")
        return None
    try:
        return r.json()
    except Exception:
        return None


def desempaquetar(datos):
    if isinstance(datos, dict):
        return datos.get("data", []) or []
    return datos or []


def estado_de(p):
    return ((p.get("state") or {}).get("description") or "").strip()


def minuto_de(p):
    try:
        return int((p.get("state") or {}).get("clock") or 0)
    except (TypeError, ValueError):
        return 0


def volcar_estadisticas(match_id, etiqueta):
    datos = pedir(f"/statistics/{match_id}")
    if not datos:
        print(f"  sin datos de /statistics para {etiqueta}")
        return None
    print(f"  claves del bloque por equipo: {sorted(datos[0].keys()) if datos else '(vacío)'}")
    for bloque in datos:
        equipo = (bloque.get("team") or {}).get("name", "?")
        stats = bloque.get("statistics") or []
        nombres = [s.get("displayName") for s in stats]
        print(f"  {equipo}: {len(stats)} estadísticas")
        print(f"    disponibles: {nombres}")
        for s in stats:
            if "foul" in str(s.get("displayName", "")).lower():
                print(f"    -> FALTAS: {json.dumps(s, ensure_ascii=False)}")
    return datos


def main():
    print("SONDEO DE FALTAS -- ¿hay desglose por tiempos?")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    # 1. Un partido TERMINADO: ¿trae desglose por tiempos?
    print("\n=== 1. PARTIDO TERMINADO ===")
    ayer = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    terminados = [p for p in desempaquetar(pedir("/matches", {"date": ayer, "limit": 100}))
                  if estado_de(p).lower().startswith("finish")]
    if terminados:
        p = terminados[0]
        print(f"{p['homeTeam']['name']} vs {p['awayTeam']['name']} ({estado_de(p)})")
        volcar_estadisticas(p["id"], "terminado")
    else:
        print("No he encontrado ningún partido terminado ayer")

    # 2. Un partido EN JUEGO: ¿los acumulados van al minuto?
    print("\n=== 2. PARTIDO EN JUEGO ===")
    vivos = []
    for desplazamiento in (0, -1):
        fecha = (datetime.now(timezone.utc).date() + timedelta(days=desplazamiento)).isoformat()
        for offset in (0, 100, 200, 300, 400, 500):
            lote = desempaquetar(pedir("/matches", {"date": fecha, "limit": 100, "offset": offset}))
            if not lote:
                break
            vivos.extend(p for p in lote
                         if estado_de(p) and not any(estado_de(p).lower().startswith(q) for q in QUIETOS))
            if len(lote) < 100:
                break

    candidatos = [p for p in vivos if 0 < minuto_de(p) <= 87]
    print(f"Partidos en juego ahora: {len(vivos)} (utilizables: {len(candidatos)})")
    if not candidatos:
        print("No hay ningún partido en juego -- esta parte hay que repetirla "
              "cuando lo haya. No se concluye nada de un sondeo vacío.")
        return

    for p in candidatos[:2]:
        print(f"\n{p['homeTeam']['name']} vs {p['awayTeam']['name']} "
              f"-- {estado_de(p)}, minuto {minuto_de(p)}")
        datos = volcar_estadisticas(p["id"], "en juego")
        if datos:
            total = 0
            for bloque in datos:
                for s in (bloque.get("statistics") or []):
                    if "foul" in str(s.get("displayName", "")).lower():
                        try:
                            total += float(s.get("value") or 0)
                        except (TypeError, ValueError):
                            pass
            print(f"  faltas acumuladas hasta el minuto {minuto_de(p)}: {total:.0f}")
            print(f"  (un partido entero promedia 25 faltas; si esto es "
                  f"proporcional al minuto, los acumulados van al día)")


if __name__ == "__main__":
    main()
