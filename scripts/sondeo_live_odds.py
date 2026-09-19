"""
CUOTAS EN VIVO: QUÉ TRAEN Y SI SE MUEVEN -- solo lectura.

Sabemos ya que /odds?oddsType=live devuelve cotizaciones donde la llamada
por defecto (prematch) no devolvía ninguna. Falta lo que decide si el
modelo de descanso sirve para algo:

  1. ¿Qué mercados hay en vivo? Concretamente, ¿hay tarjetas?
  2. ¿Se mueven los valores mientras se juega, o están congelados como el
     estado del partido?

Se recorre cada partido en juego, se vuelcan sus mercados en vivo y se
toman dos muestras separadas para ver el movimiento.
"""
import os
import time
import requests
from collections import Counter
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

PISTAS_TARJETAS = ("card", "booking", "tarjeta")
QUIETOS = ("finished", "not ", "scheduled", "cancel", "postpon", "abandon", "await", "tbd", "to be")
ESPERA_MUESTRA = int(os.environ.get("ESPERA", "70"))


def pedir(path, params=None, espera=0.35):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception:
        return None
    time.sleep(espera)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def desempaquetar(datos):
    if isinstance(datos, dict):
        return datos.get("data", []) or []
    return datos or []


def aplanar(datos):
    planas = []
    for bloque in desempaquetar(datos):
        if isinstance(bloque, dict):
            planas.extend(bloque.get("odds", []) or [])
    return planas


def en_juego(p):
    desc = ((p.get("state") or {}).get("description") or "").strip().lower()
    return bool(desc) and not any(desc.startswith(q) for q in QUIETOS)


def minuto_de(p):
    try:
        return int((p.get("state") or {}).get("clock") or 0)
    except (TypeError, ValueError):
        return 0


def nombre_de(p):
    try:
        return f"{p['homeTeam']['name']} vs {p['awayTeam']['name']}"
    except (KeyError, TypeError):
        return f"partido {p.get('id')}"


def titulo(t):
    print("\n" + "=" * 76)
    print(t)
    print("=" * 76)


def huella(planas):
    return {(c.get("market"), c.get("bookmakerName")):
            tuple((v.get("value"), v.get("odd")) for v in (c.get("values") or []))
            for c in planas}


def buscar_en_juego():
    ahora = datetime.now(timezone.utc)
    vivos = []
    for desplazamiento in (0, -1):
        fecha = (ahora.date() + timedelta(days=desplazamiento)).isoformat()
        for offset in range(0, 900, 100):
            datos = pedir("/matches", {"date": fecha, "limit": 100, "offset": offset}, espera=0.25)
            lote = desempaquetar(datos)
            if not lote:
                break
            vivos.extend(p for p in lote if en_juego(p))
            if len(lote) < 100:
                break
    return vivos


def main():
    print("CUOTAS EN VIVO: MERCADOS Y MOVIMIENTO")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    vivos = buscar_en_juego()
    print(f"\nPartidos en juego encontrados: {len(vivos)}")
    if not vivos:
        print("Ninguno. Relanzar con fútbol en marcha.")
        return

    titulo("1. ¿QUÉ MERCADOS HAY EN VIVO EN CADA PARTIDO?")
    con_live = []
    for p in sorted(vivos, key=minuto_de, reverse=True)[:6]:
        planas = aplanar(pedir("/odds", {"matchId": p["id"], "oddsType": "live"}))
        if not planas:
            print(f"  min {minuto_de(p):>3}  {nombre_de(p)[:40]:40s}  sin cuotas en vivo")
            continue
        casas = {c.get("bookmakerName") for c in planas if c.get("bookmakerName")}
        mercados = Counter((c.get("market") or "?") for c in planas)
        tarjetas = sorted({m for m in mercados
                           if any(x in m.lower() for x in PISTAS_TARJETAS)})
        print(f"  min {minuto_de(p):>3}  {nombre_de(p)[:40]:40s}  "
              f"{len(planas):4d} cuotas, {len(casas):2d} casas, {len(mercados):3d} mercados")
        if tarjetas:
            print(f"        TARJETAS EN VIVO: {', '.join(tarjetas)}")
        con_live.append((p, planas, mercados, tarjetas))

    if not con_live:
        titulo("Sin cuotas en vivo en ningún partido -- nada más que medir")
        return

    p, planas, mercados, tarjetas = con_live[0]
    titulo(f"2. MERCADOS EN VIVO DE {nombre_de(p)}")
    for mercado, n in mercados.most_common(30):
        marca = "  <-- TARJETAS" if any(x in mercado.lower() for x in PISTAS_TARJETAS) else ""
        print(f"    {n:3d} casas  {mercado}{marca}")

    titulo("3. ¿SE MUEVEN LAS CUOTAS EN VIVO?")
    antes = huella(planas)
    print(f"  Primera muestra: {len(antes)} mercados. Esperando {ESPERA_MUESTRA}s...")
    time.sleep(ESPERA_MUESTRA)
    despues = huella(aplanar(pedir("/odds", {"matchId": p["id"], "oddsType": "live"})))
    comunes = set(antes) & set(despues)
    cambiadas = [k for k in comunes if antes[k] != despues[k]]
    print(f"  Comparables: {len(comunes)}  |  que han cambiado: {len(cambiadas)}")
    if cambiadas:
        print("\n  >>> LAS CUOTAS EN VIVO SE MUEVEN. Hay feed real.")
        for k in cambiadas[:8]:
            print(f"    {k[0]} ({k[1]}): {antes[k]}  ->  {despues[k]}")
    else:
        print("\n  >>> No se movió ninguna en esta ventana. Puede ser un partido")
        print("  >>> parado, o un feed que refresca más despacio. Repetir.")

    titulo("VEREDICTO")
    hay_tarjetas = any(t for _, _, _, t in con_live)
    if hay_tarjetas and cambiadas:
        print("  Hay tarjetas en vivo Y las cuotas se mueven: el modelo de descanso")
        print("  es viable y además se puede calcular valor esperado en directo.")
    elif cambiadas:
        print("  Las cuotas en vivo se mueven, pero NO hay mercado de tarjetas en")
        print("  vivo en los partidos mirados. El modelo de descanso podría dar la")
        print("  probabilidad, pero la cuota habría que buscarla fuera de esta API.")
    elif hay_tarjetas:
        print("  Hay mercado de tarjetas en vivo pero no se vio movimiento. Repetir")
        print("  con un partido claramente en marcha antes de concluir.")
    else:
        print("  Ni tarjetas en vivo ni movimiento en esta pasada.")


if __name__ == "__main__":
    main()
