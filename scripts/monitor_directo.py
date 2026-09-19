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

En la misma pasada se muestrean las CUOTAS EN VIVO (oddsType=live, que sí
existe: devuelve cotizaciones donde la llamada por defecto, que es
prematch, daba cero). De ahí salen las dos cosas que faltan por saber:
si hay mercado de tarjetas en vivo y si los valores se mueven.

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

QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ", "scheduled", "tbd", "to be")
PISTAS_TARJETAS = ("card", "booking", "tarjeta")

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


def aplanar_cuotas(datos):
    planas = []
    for bloque in desempaquetar(datos):
        if isinstance(bloque, dict):
            planas.extend(bloque.get("odds", []) or [])
    return planas


def huella_cuotas(planas):
    return {(c.get("market"), c.get("bookmakerName")):
            tuple((v.get("value"), v.get("odd")) for v in (c.get("values") or []))
            for c in planas}


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
    titulo(f"2. ¿AVANZA EL RELOJ Y SE MUEVEN LAS CUOTAS? ({MUESTRAS} muestras cada {ESPERA_ENTRE_MUESTRAS}s)")
    print("  Reloj: si el minuto sube, el feed en vivo es real.")
    print("  Cuotas: se piden con oddsType=live, que es donde están de verdad.\n")

    seguidos = sorted(vivos, key=minuto_de, reverse=True)[:3]
    historial = {p["id"]: [] for p in seguidos}
    huellas = {p["id"]: [] for p in seguidos}
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

            # cuotas EN VIVO del mismo partido, en la misma muestra
            planas = aplanar_cuotas(pedir("/odds", {"matchId": p["id"], "oddsType": "live"}, espera=0.3))
            casas_live = {c.get("bookmakerName") for c in planas if c.get("bookmakerName")}
            mercados_tarj = sorted({(c.get("market") or "") for c in planas
                                    if any(x in (c.get("market") or "").lower() for x in PISTAS_TARJETAS)})
            huellas[p["id"]].append(huella_cuotas(planas))

            historial[p["id"]].append({
                "hora": sello, "min": minuto_de(m),
                "estado": st.get("description"),
                "eventos": len(eventos), "tarjetas": tarj,
                "cuotas_live": len(planas), "casas_live": len(casas_live),
                "mercados_tarjetas": mercados_tarj,
            })
            extra = f"  TARJETAS EN VIVO: {', '.join(mercados_tarj)}" if mercados_tarj else ""
            print(f"    [{sello}] {nombre_de(p)[:28]:28s} min={minuto_de(m):>3}  "
                  f"ev={len(eventos):2d} tarj={tarj}  "
                  f"live={len(planas):3d} cuotas/{len(casas_live):2d} casas{extra}")
        if i < MUESTRAS - 1:
            time.sleep(ESPERA_ENTRE_MUESTRAS)

    titulo("3. VEREDICTO")
    algun_avance = algun_movimiento = hubo_tarjetas_live = False
    for p in seguidos:
        h = historial[p["id"]]
        if len(h) < 2:
            continue
        minutos = [x["min"] for x in h]
        eventos = [x["eventos"] for x in h]
        cuotas = [x["cuotas_live"] for x in h]
        avanza = minutos[-1] > minutos[0]
        crecen = eventos[-1] > eventos[0]

        hs = huellas[p["id"]]
        comunes = set(hs[0]) & set(hs[-1]) if hs[0] and hs[-1] else set()
        cambiadas = [k for k in comunes if hs[0][k] != hs[-1][k]]
        se_mueven = bool(cambiadas)

        tarj_live = sorted({m for x in h for m in x["mercados_tarjetas"]})
        algun_avance = algun_avance or avanza or crecen
        algun_movimiento = algun_movimiento or se_mueven
        hubo_tarjetas_live = hubo_tarjetas_live or bool(tarj_live)

        span = (len(h) - 1) * ESPERA_ENTRE_MUESTRAS / 60
        print(f"\n  {nombre_de(p)}")
        print(f"    minutos:      {minutos}   (en {span:.1f} min reales)")
        print(f"    eventos:      {eventos}")
        print(f"    cuotas live:  {cuotas}")
        print(f"    -> reloj {'AVANZA' if avanza else 'CONGELADO'}, "
              f"eventos {'CRECEN' if crecen else 'iguales'}, "
              f"cuotas {'SE MUEVEN (' + str(len(cambiadas)) + ')' if se_mueven else 'quietas'}")
        if tarj_live:
            print(f"    -> MERCADO DE TARJETAS EN VIVO: {', '.join(tarj_live)}")

    print()
    if algun_avance and algun_movimiento and hubo_tarjetas_live:
        print("  >>> TODO FUNCIONA: reloj, eventos y cuotas en vivo, con mercado de")
        print("  >>> tarjetas. El modelo de descanso es viable de punta a punta.")
    elif algun_avance and hubo_tarjetas_live:
        print("  >>> Hay datos en vivo y mercado de tarjetas, pero las cuotas no se")
        print("  >>> movieron en la ventana. Repetir para confirmar el refresco.")
    elif algun_avance:
        print("  >>> Los datos del partido llegan en vivo, pero NO hay mercado de")
        print("  >>> tarjetas en vivo. Se puede modelar al descanso; la cuota habría")
        print("  >>> que buscarla en otra fuente.")
    else:
        print("  >>> Nada se movió: ni reloj ni eventos. Con esta fuente el modelo")
        print("  >>> de descanso no es viable. (Ojo: un partido parado daría lo")
        print("  >>>  mismo, así que conviene repetir con varios partidos.)")


if __name__ == "__main__":
    main()
