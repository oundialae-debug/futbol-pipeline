"""
MONITOR EN DIRECTO -- solo lectura.

Comprueba si el feed en vivo de la API es real: si el reloj avanza, si los
eventos crecen y si las cuotas en vivo (oddsType=live) se mueven. De ahí
depende que el modelo de descanso sirva de algo.

CUIDADO CON A QUIÉN SE SIGUE. Una pasada anterior ordenaba por minuto
descendente para coger "el más avanzado" y acabó siguiendo tres partidos
clavados en el minuto 90: terminados, con el estado sin actualizar. Medir
la frescura sobre esos es medir un cadáver. Por eso ahora se descartan los
que pasan de MINUTO_MAXIMO y se prefieren las ligas que nos importan.
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
# por encima de este minuto el partido probablemente ya acabó y la API no lo
# ha marcado: seguirlo daría un "congelado" falso
MINUTO_MAXIMO = int(os.environ.get("MINUTO_MAXIMO", "87"))
LIGAS_PREFERIDAS = [x.strip().lower() for x in
                    os.environ.get("LIGAS_PREFERIDAS", "la liga,segunda").split(",") if x.strip()]


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


def liga_de(p):
    return str((p.get("league") or {}).get("name", "?"))


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


def elegir_seguidos(vivos, cuantos=3):
    """Partidos que de verdad están corriendo, preferiendo las ligas que
    interesan. Se descartan los que pasan de MINUTO_MAXIMO porque suelen ser
    registros terminados que la API no ha cerrado."""
    candidatos = [p for p in vivos if 0 < minuto_de(p) <= MINUTO_MAXIMO]
    descartados = len(vivos) - len(candidatos)
    if descartados:
        print(f"  ({descartados} partidos descartados por pasar del minuto {MINUTO_MAXIMO} "
              f"o no tener reloj: probables registros muertos)")

    def prioridad(p):
        liga = liga_de(p).lower()
        preferida = 0 if any(x in liga for x in LIGAS_PREFERIDAS) else 1
        return (preferida, -minuto_de(p))

    return sorted(candidatos, key=prioridad)[:cuantos]


def main():
    print("MONITOR EN DIRECTO")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    titulo("1. ESCANEO (ayer / hoy / mañana)")
    todos, vivos = escanear()
    print(f"\n  Total partidos: {len(todos)}")
    estados = Counter((p.get("state") or {}).get("description") for p in todos)
    print(f"  Estados: {dict(estados.most_common(12))}")
    print(f"\n  EN JUEGO segun la API: {len(vivos)}")
    reparto = Counter(minuto_de(p) for p in vivos)
    print(f"  Reparto de minutos: {dict(sorted(reparto.items()))}")

    if not vivos:
        titulo("SIN PARTIDOS EN JUEGO -- no se puede medir la frescura")
        return

    titulo(f"2. ¿AVANZA EL RELOJ Y SE MUEVEN LAS CUOTAS? ({MUESTRAS} muestras cada {ESPERA_ENTRE_MUESTRAS}s)")
    seguidos = elegir_seguidos(vivos)
    if not seguidos:
        print("  Ningún partido en rango de minutos utilizable.")
        return

    historial = {p["id"]: [] for p in seguidos}
    huellas = {p["id"]: [] for p in seguidos}
    print()
    for p in seguidos:
        print(f"  Siguiendo: {nombre_de(p)}  min {minuto_de(p)}  ({liga_de(p)})")
    print()

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

            planas = aplanar_cuotas(pedir("/odds", {"matchId": p["id"], "oddsType": "live"}, espera=0.3))
            casas_live = {c.get("bookmakerName") for c in planas if c.get("bookmakerName")}
            mercados_tarj = sorted({(c.get("market") or "") for c in planas
                                    if any(x in (c.get("market") or "").lower() for x in PISTAS_TARJETAS)})
            huellas[p["id"]].append(huella_cuotas(planas))
            historial[p["id"]].append({
                "min": minuto_de(m), "estado": st.get("description"),
                "eventos": len(eventos), "tarjetas": tarj,
                "cuotas_live": len(planas), "mercados_tarjetas": mercados_tarj,
            })
            extra = f"  TARJETAS EN VIVO: {', '.join(mercados_tarj)}" if mercados_tarj else ""
            print(f"    [{sello}] {nombre_de(p)[:26]:26s} min={minuto_de(m):>3} "
                  f"{str(st.get('description'))[:12]:12s} ev={len(eventos):2d} tarj={tarj}  "
                  f"live={len(planas):3d}/{len(casas_live):2d} casas{extra}")
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
        tarj_live = sorted({m for x in h for m in x["mercados_tarjetas"]})

        algun_avance = algun_avance or avanza
        algun_movimiento = algun_movimiento or bool(cambiadas)
        hubo_tarjetas_live = hubo_tarjetas_live or bool(tarj_live)

        span = (len(h) - 1) * ESPERA_ENTRE_MUESTRAS / 60
        print(f"\n  {nombre_de(p)}  ({liga_de(p)})")
        print(f"    minutos:      {minutos}   (en {span:.1f} min reales)")
        print(f"    eventos:      {eventos}")
        print(f"    cuotas live:  {cuotas}")
        print(f"    -> reloj {'AVANZA' if avanza else 'CONGELADO'}, "
              f"eventos {'CRECEN' if crecen else 'iguales'}, "
              f"cuotas {'SE MUEVEN (' + str(len(cambiadas)) + ')' if cambiadas else 'quietas'}")
        if tarj_live:
            print(f"    -> MERCADO DE TARJETAS EN VIVO: {', '.join(tarj_live)}")

    print()
    if algun_avance and hubo_tarjetas_live and algun_movimiento:
        print("  >>> TODO FUNCIONA: reloj, eventos y cuotas en vivo con mercado de")
        print("  >>> tarjetas. El modelo de descanso es viable de punta a punta.")
    elif algun_avance and hubo_tarjetas_live:
        print("  >>> Reloj en vivo y mercado de tarjetas, pero sin movimiento de")
        print("  >>> cuotas en la ventana. Repetir para confirmar el refresco.")
    elif algun_avance:
        print("  >>> EL RELOJ AVANZA: el feed en vivo es real y el modelo de")
        print("  >>> descanso se puede alimentar. Pero NO hay mercado de tarjetas")
        print("  >>> en vivo, así que la cuota habría que buscarla en otra fuente.")
    else:
        print("  >>> El reloj no avanzó en ningún partido seguido. Comprobar que no")
        print("  >>> se estén siguiendo registros ya terminados antes de concluir.")


if __name__ == "__main__":
    main()
