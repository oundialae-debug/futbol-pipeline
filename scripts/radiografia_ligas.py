"""
RADIOGRAFÍA POR LIGA -- solo lectura.

Pregunta concreta: ¿la API conoce los partidos que sabemos que se están
jugando ahora mismo, y en qué estado los tiene?

Hace falta porque tres pasadas seguidas del diagnóstico en directo, a lo
largo de 10 minutos, devolvieron el MISMO partido en el MISMO minuto (72),
con el mismo marcador y los mismos 4 eventos. Y ningún partido de Liga MX
ni de Argentina, estando en juego. Hay dos explicaciones muy distintas:

  a) la API no cubre esas ligas -> el modelo de descanso solo valdría donde
     sí haya cobertura
  b) las cubre pero va con retraso o se queda congelada -> el modelo de
     descanso NO es viable con esta fuente, por muy bueno que sea el 48
     puntos de separación del histórico

Esto separa las dos. Agrupa los partidos de hoy y ayer por liga y enseña
los estados y el reloj de cada una.
"""
import os
import time
import requests
from collections import Counter
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

# Ligas cuyo nombre nos interesa mirar de cerca
INTERES = ("liga mx", "mexic", "méxic", "argentin", "profesional", "brasil",
           "brazil", "mls", "major league", "colombia", "chile", "paraguay")

QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ", "scheduled")


def pedir(path, params=None, espera=0.3):
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


def minuto_de(p):
    try:
        return int((p.get("state") or {}).get("clock") or 0)
    except (TypeError, ValueError):
        return 0


def en_juego(p):
    desc = ((p.get("state") or {}).get("description") or "").strip().lower()
    return bool(desc) and not any(desc.startswith(q) for q in QUIETOS)


def nombre_de(p):
    try:
        return f"{p['homeTeam']['name']} vs {p['awayTeam']['name']}"
    except (KeyError, TypeError):
        return f"partido {p.get('id')}"


def recoger():
    ahora = datetime.now(timezone.utc)
    todos = []
    for desplazamiento in (0, -1):
        fecha = (ahora.date() + timedelta(days=desplazamiento)).isoformat()
        for offset in range(0, 900, 100):
            datos = pedir("/matches", {"date": fecha, "limit": 100, "offset": offset})
            partidos = desempaquetar(datos)
            if not partidos:
                break
            todos.extend(partidos)
            if len(partidos) < 100:
                break
    return todos


def main():
    ahora = datetime.now(timezone.utc)
    print("RADIOGRAFÍA POR LIGA")
    print("Momento:", ahora.strftime("%Y-%m-%d %H:%M UTC"))

    todos = recoger()
    print(f"\nPartidos recogidos (hoy + ayer): {len(todos)}")

    por_liga = {}
    for p in todos:
        nombre = str((p.get("league") or {}).get("name", "?"))
        por_liga.setdefault(nombre, []).append(p)
    print(f"Ligas distintas: {len(por_liga)}")

    vivos = [p for p in todos if en_juego(p)]
    print(f"Partidos que la API da como EN JUEGO: {len(vivos)}")
    for p in sorted(vivos, key=minuto_de, reverse=True):
        st = p.get("state") or {}
        liga = str((p.get("league") or {}).get("name", "?"))
        print(f"   min {minuto_de(p):>3}  {nombre_de(p)[:38]:38s} "
              f"[{st.get('description')}]  ({liga[:28]})")

    print("\n" + "=" * 72)
    print("LIGAS DE INTERÉS (América): ¿las conoce la API?")
    print("=" * 72)
    relevantes = {n: ps for n, ps in por_liga.items()
                  if any(c in n.lower() for c in INTERES)}
    if not relevantes:
        print("  >>> NINGUNA aparece. La API no sirve esas ligas en estas fechas.")
    else:
        for nombre, ps in sorted(relevantes.items()):
            estados = Counter((p.get("state") or {}).get("description") for p in ps)
            print(f"\n  {nombre}  ({len(ps)} partidos)  {dict(estados)}")
            for p in sorted(ps, key=lambda x: str(x.get("date")))[:8]:
                st = p.get("state") or {}
                print(f"      {str(p.get('date'))[:16]:16s}  min {minuto_de(p):>3}  "
                      f"{nombre_de(p)[:38]:38s} [{st.get('description')}]")

    print("\n" + "=" * 72)
    print("MUESTRA DE LIGAS DEVUELTAS (para ver qué cubre de verdad)")
    print("=" * 72)
    for nombre in sorted(por_liga)[:40]:
        print(f"    {len(por_liga[nombre]):3d}  {nombre}")

    print("\n" + "=" * 72)
    print("LECTURA")
    print("=" * 72)
    if not vivos:
        print("  Ningún partido en juego según la API, a una hora en la que sí")
        print("  hay fútbol -> la cobertura en directo es mala o va con retraso.")
    elif len(vivos) <= 2:
        print(f"  Solo {len(vivos)} partido(s) en juego a esta hora es poco creíble.")
        print("  Apunta a que el estado se actualiza tarde, no a que no haya fútbol.")
    else:
        print(f"  {len(vivos)} partidos en juego: la cobertura en directo parece real.")
    print("  Compara el minuto de arriba con el minuto real del partido: si no")
    print("  coincide o no avanza entre dos pasadas, el feed va con retraso y el")
    print("  modelo de descanso no es viable con esta fuente.")


if __name__ == "__main__":
    main()
