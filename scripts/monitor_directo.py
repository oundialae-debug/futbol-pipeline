"""
MONITOR EN DIRECTO -- solo lectura.

Separa dos hipótesis que explican por qué apenas aparecen partidos en juego:

  a) COBERTURA: la API solo sigue en vivo las ligas grandes, y a ciertas
     horas solo se juegan competiciones menores que no cubre.
  b) FRESCURA: sí los tiene, pero actualiza con retraso o se queda
     congelada.

Solo la (b) invalida el modelo de descanso, así que hay que distinguirlas.
La prueba decisiva es muestrear el MISMO partido varias veces y ver si el
reloj avanza. Un feed en vivo real sube el minuto; uno congelado no.

También escanea ayer, hoy y mañana, por si el filtro de fecha de la API
usa un huso distinto y los partidos en curso caen en otro cajón.
"""
import os
import time
import requests
from collections import Counter
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ", "scheduled", "tbd")

MUESTRAS = int(os.environ.get("MUESTRAS", "5"))
ESPERA_ENTRE_MUESTRAS = int(os.environ.get("ESPERA", "75"))


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


def titulo(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


def escanear():
    """Ayer, hoy y mañana, paginando. Devuelve (todos, en_vivo)."""
    ahora = datetime.now(timezone.utc)
    todos = []
    for desplazamiento in (-1, 0, 1):
        fecha = (ahora.date() + timedelta(days=desplazamiento)).isoformat()
        n_fecha = 0
        for offset in range(0, 900, 100):
            datos = pedir("/matches", {"date": fecha, "limit": 100, "offset": offset})
            partidos = desempaquetar(datos)
            if not partidos:
                break
            todos.extend(partidos)
            n_fecha += len(partidos)
            if len(partidos) < 100:
                break
        print(f"    {fecha}: {n_fecha} partidos")
    return todos, [p for p in todos if en_juego(p)]


def main():
    print("MONITOR EN DIRECTO")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    titulo("1. ESCANEO (ayer / hoy / mañana)")
    todos, vivos = escanear()
    print(f"\n  Total partidos: {len(todos)}")
    estados = Counter((p.get("state") or {}).get("description") for p in todos)
    print(f"  Estados: {dict(estados.most_common(12))}")
    print(f"\n  EN JUEGO segun la API: {len(vivos)}")
    for p in sorted(vivos, key=minuto_de, reverse=True):
        liga = str((p.get("league") or {}).get("name", "?"))
        st = p.get("state") or {}
        print(f"    min {minuto_de(p):>3}  {nombre_de(p)[:38]:38s} "
              f"[{st.get('description')}]  ({liga[:26]})")

    if not vivos:
        titulo("SIN PARTIDOS EN JUEGO -- no se puede medir la frescura")
        print("  Vuelve a lanzarlo cuando haya fútbol en marcha.")
        return

    # ---- LA PRUEBA DECISIVA ----
    titulo(f"2. ¿AVANZA EL RELOJ? ({MUESTRAS} muestras cada {ESPERA_ENTRE_MUESTRAS}s)")
    print("  Si el minuto sube, el feed en vivo es real y el problema sería solo")
    print("  de cobertura. Si no se mueve, el dato en directo no sirve.\n")

    seguidos = sorted(vivos, key=minuto_de, reverse=True)[:3]
    historial = {p["id"]: [] for p in seguidos}
    for p in seguidos:
        print(f"  Siguiendo: {nombre_de(p)} (id {p['id']})")

    for i in range(MUESTRAS):
        sello = datetime.now(timezone.utc).strftime("%H:%M:%S")
        for p in seguidos:
            datos = pedir(f"/matches/{p['id']}", espera=0.3)
            if datos is None:
                continue
            m = datos[0] if isinstance(datos, list) else datos
            st = m.get("state") or {}
            eventos = m.get("events") or []
            tarj = sum(1 for e in eventos if e.get("type") in ("Yellow Card", "Red Card"))
            historial[p["id"]].append({
                "hora": sello, "min": minuto_de(m),
                "estado": st.get("description"),
                "marcador": (st.get("score") or {}).get("current"),
                "eventos": len(eventos), "tarjetas": tarj,
            })
            print(f"    [{sello}] {nombre_de(p)[:30]:30s} min={minuto_de(m):>3}  "
                  f"{st.get('description'):20s} {(st.get('score') or {}).get('current')}  "
                  f"eventos={len(eventos):2d} tarjetas={tarj}")
        if i < MUESTRAS - 1:
            time.sleep(ESPERA_ENTRE_MUESTRAS)

    titulo("3. VEREDICTO")
    algun_avance = False
    for p in seguidos:
        h = historial[p["id"]]
        if len(h) < 2:
            continue
        minutos = [x["min"] for x in h]
        eventos = [x["eventos"] for x in h]
        avanza = minutos[-1] > minutos[0]
        crecen = eventos[-1] > eventos[0]
        algun_avance = algun_avance or avanza or crecen
        span = (len(h) - 1) * ESPERA_ENTRE_MUESTRAS / 60
        print(f"\n  {nombre_de(p)}")
        print(f"    minutos observados: {minutos}   (en {span:.1f} min reales)")
        print(f"    eventos observados: {eventos}")
        print(f"    -> reloj {'AVANZA' if avanza else 'CONGELADO'}, "
              f"eventos {'CRECEN' if crecen else 'iguales'}")

    print()
    if algun_avance:
        print("  >>> El feed en vivo SÍ se actualiza. El problema entonces es de")
        print("  >>> COBERTURA: habrá que comprobar liga por liga cuáles sigue en")
        print("  >>> directo. El modelo de descanso sería viable donde sí cubra.")
    else:
        print("  >>> NADA se movió en toda la ventana. El dato en directo está")
        print("  >>> congelado: no es una cuestión de cobertura sino de frescura.")
        print("  >>> Con esta fuente, el modelo de descanso NO es viable.")
        print("  >>> (ojo: un partido parado o en el descanso también daría esto,")
        print("  >>>  así que conviene repetirlo con varios partidos distintos)")


if __name__ == "__main__":
    main()
