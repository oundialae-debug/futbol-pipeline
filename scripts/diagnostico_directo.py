"""
DIAGNÓSTICO EN DIRECTO -- solo lectura.

Las preguntas que quedan abiertas son sobre el COMPORTAMIENTO de la API, no
sobre LaLiga, así que sirve cualquier partido en juego del mundo. El
diagnóstico anterior solo miraba la liga 119924 y por eso nunca encontraba
nada: en España se juega en una franja horaria estrecha.

Contesta dos cosas:

  1. ¿Devuelve /matches/{id} los eventos PARCIALES (tarjetas ya mostradas y su
     minuto) mientras el partido se está jugando? Es la condición necesaria
     para el modelo de descanso, que en el histórico separa 48 puntos.
  2. ¿Hay cuotas EN VIVO, o solo previas congeladas? Se comprueba de dos
     formas: por el campo 'type' de cada cuota, y repitiendo la llamada a los
     60s para ver si los valores se mueven.

Para encontrar un partido en juego prueba varias vías, porque no sabemos de
antemano qué admite la API: búsqueda de ligas por nombre, /matches solo con
fecha, y una lista de ligas indicada a mano por LIGAS_EXTRA.
"""
import os
import time
import requests
from collections import Counter
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

# Estados que NO son "en juego". Todo lo demás se considera partido en curso.
ESTADOS_QUIETOS = {"Not started", "Scheduled", "Finished", "Postponed",
                   "Cancelled", "Canceled", "Abandoned", "Awarded", "TBD"}

# Prefijos de estado que también significan "ya no se juega" (la API usa
# variantes como "Finished after penalties", "Finished after extra time").
PREFIJOS_QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ")

# Ligas donde mirar si la búsqueda automática no da nada. Se pueden añadir por
# variable de entorno (LIGAS_EXTRA="119924,123456").
LIGAS_SEMILLA = [119924]  # LaLiga


def pedir(path, params=None, espera=0.6):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception as exc:
        return None, None, type(exc).__name__
    time.sleep(espera)
    if r.status_code != 200:
        return r, None, f"HTTP {r.status_code}"
    try:
        return r, r.json(), "ok"
    except Exception:
        return r, None, "respuesta no-JSON"


def desempaquetar(datos):
    """La API a veces devuelve una lista y a veces {'data': [...]}."""
    if isinstance(datos, dict):
        return datos.get("data", []) or []
    return datos or []


def describir(dato, prof=0, max_prof=4, max_claves=25):
    sangria = "      " + "  " * prof
    if prof > max_prof:
        print(f"{sangria}...")
        return
    if isinstance(dato, dict):
        for clave, valor in list(dato.items())[:max_claves]:
            if isinstance(valor, (dict, list)):
                print(f"{sangria}{clave}: {type(valor).__name__}[{len(valor)}]")
                describir(valor, prof + 1, max_prof, max_claves)
            else:
                texto = str(valor)
                print(f"{sangria}{clave}: {texto[:70]}")
    elif isinstance(dato, list):
        if not dato:
            print(f"{sangria}(lista vacía)")
            return
        print(f"{sangria}-- primero de {len(dato)} --")
        describir(dato[0], prof + 1, max_prof, max_claves)
    else:
        print(f"{sangria}{str(dato)[:70]}")


def titulo(texto):
    print("\n" + "=" * 72)
    print(texto)
    print("=" * 72)


def esta_en_juego(partido):
    """Un partido está en juego si su estado no es ninguno de los quietos.
    Ojo: la API usa variantes como "Finished after penalties", así que no
    basta con comparar contra una lista cerrada -- hay que mirar el prefijo,
    o se cuelan partidos ya terminados como si estuvieran en curso."""
    desc = ((partido.get("state") or {}).get("description") or "").strip()
    if not desc:
        return False
    if desc in ESTADOS_QUIETOS:
        return False
    bajo = desc.lower()
    return not any(bajo.startswith(p) for p in PREFIJOS_QUIETOS)


def nombre_de(partido):
    try:
        return f"{partido['homeTeam']['name']} vs {partido['awayTeam']['name']}"
    except (KeyError, TypeError):
        return f"partido {partido.get('id')}"


def minuto_de(partido):
    try:
        return int((partido.get("state") or {}).get("clock") or 0)
    except (TypeError, ValueError):
        return 0


# ============ BÚSQUEDA DE PARTIDOS EN JUEGO ============
def descubrir_ligas():
    """Prueba varias formas de listar ligas. Devuelve {id: nombre}."""
    print("  Probando endpoints de ligas:")
    ligas = {}
    intentos = [
        ("/leagues", {"limit": 100}),
        ("/leagues", {"leagueName": "Liga MX"}),
        ("/leagues", {"name": "Liga MX"}),
        ("/leagues", {"countryName": "Mexico"}),
        ("/leagues", None),
    ]
    for path, params in intentos:
        r, datos, estado = pedir(path, params)
        n = len(desempaquetar(datos)) if datos is not None else 0
        print(f"    {estado:16s} {path} {params or ''}  -> {n} elementos")
        for liga in desempaquetar(datos):
            if isinstance(liga, dict) and liga.get("id"):
                ligas[liga["id"]] = liga.get("name", "?")
    return ligas


def buscar_en_vivo():
    titulo("1. BUSCANDO PARTIDOS EN JUEGO (en cualquier liga)")
    ahora = datetime.now(timezone.utc)
    hoy = ahora.date().isoformat()
    ayer = (ahora.date() - timedelta(days=1)).isoformat()
    en_vivo, estados_vistos = [], Counter()

    # Vía A: /matches solo con fecha, PAGINANDO. La API devuelve como mucho
    # 100 por página, así que sin paginar se pierden la mayoría de partidos
    # del día (y con ellos casi todos los que están en juego).
    print("  Vía A: /matches solo con fecha (sin leagueId), paginando")
    for fecha in (hoy, ayer):
        for offset in range(0, 800, 100):
            params = {"date": fecha, "limit": 100, "offset": offset}
            r, datos, estado = pedir("/matches", params, espera=0.35)
            partidos = desempaquetar(datos)
            if offset == 0 or partidos:
                print(f"    {estado:16s} date={fecha} offset={offset:3d}  -> {len(partidos)} partidos")
            if not partidos:
                break
            for p in partidos:
                estados_vistos[((p.get("state") or {}).get("description") or "?")] += 1
                if esta_en_juego(p):
                    en_vivo.append(p)
            if len(partidos) < 100:
                break

    # Vía B: descubrir ligas y mirar liga por liga
    if not en_vivo:
        print("\n  Vía B: descubrir ligas y recorrerlas")
        ligas = descubrir_ligas()
        print(f"    ligas descubiertas: {len(ligas)}")
        extra = [int(x) for x in os.environ.get("LIGAS_EXTRA", "").replace(" ", "").split(",") if x.isdigit()]
        orden = extra + list(ligas) + LIGAS_SEMILLA
        for liga_id in orden[:40]:
            for fecha in (hoy, ayer):
                _, datos, _ = pedir("/matches", {"leagueId": liga_id, "date": fecha}, espera=0.3)
                for p in desempaquetar(datos):
                    estados_vistos[((p.get("state") or {}).get("description") or "?")] += 1
                    if esta_en_juego(p):
                        en_vivo.append(p)
                        print(f"    EN JUEGO en liga {liga_id} ({ligas.get(liga_id,'?')}): {nombre_de(p)}")
            if en_vivo:
                break

    print(f"\n  Estados vistos en total: {dict(estados_vistos)}")
    print(f"  Partidos en juego encontrados: {len(en_vivo)}")
    for p in sorted(en_vivo, key=minuto_de, reverse=True)[:12]:
        estado = p.get("state") or {}
        print(f"    - min {minuto_de(p):>3}  {nombre_de(p)[:44]:44s} [{estado.get('description')}]")
    return en_vivo


# ============ TEST 1: EVENTOS PARCIALES ============
def test_eventos_parciales(partido):
    titulo("3. DETALLE DEL PARTIDO ELEGIDO")
    mid = partido["id"]
    print(f"  Partido: {nombre_de(partido)} (id {mid})")
    estado = partido.get("state") or {}
    print(f"  Estado: {estado.get('description')}  |  minuto: {estado.get('clock')}  "
          f"|  marcador: {(estado.get('score') or {}).get('current')}")

    _, datos, res = pedir(f"/matches/{mid}")
    if datos is None:
        print(f"  /matches/{{id}} no devolvió JSON ({res}).")
        return
    m = datos[0] if isinstance(datos, list) else datos

    eventos = m.get("events") or []
    print(f"\n  Eventos devueltos: {len(eventos)}")
    if eventos:
        print("  Tipos presentes:", dict(Counter(e.get("type") for e in eventos)))

    print("\n  Estructura del estado en vivo (para leer minuto y marcador):")
    describir(estado if estado else m.get("state"))


# ============ TEST 2: CUOTAS EN VIVO ============
def aplanar_cuotas(datos):
    planas = []
    for bloque in desempaquetar(datos):
        if isinstance(bloque, dict):
            planas.extend(bloque.get("odds", []) or [])
    return planas


def test_cuotas_en_vivo(partido):
    titulo("4. ¿HAY CUOTAS EN VIVO O SOLO PREVIAS?")
    mid = partido["id"]
    _, primera, res = pedir("/odds", {"matchId": mid})
    if primera is None:
        print(f"  /odds no devuelve nada para un partido en juego ({res}).")
        print("  >>> VEREDICTO: cuotas SOLO PREVIAS. El valor en directo habría que")
        print("  >>> mirarlo a mano en la casa; no se puede automatizar con esta API.")
        return

    planas = aplanar_cuotas(primera)
    tipos = Counter(c.get("type") for c in planas)
    print(f"  Entradas de cuota: {len(planas)}")
    print(f"  TIPOS presentes: {dict(tipos)}")
    if any(str(t).lower() not in ("prematch", "none") for t in tipos):
        print("  >>> Hay un tipo distinto de 'prematch': indicio de feed EN VIVO.")

    mercados = Counter((c.get("market") or "?") for c in planas)
    tarjetas = [m for m in mercados if "card" in m.lower()]
    print(f"  Mercados distintos: {len(mercados)}  |  de tarjetas: {tarjetas[:8]}")

    # Prueba decisiva: ¿se mueven los valores mientras rueda el balón?
    def huella(entradas):
        return {(c.get("market"), c.get("bookmakerName")):
                tuple((v.get("value"), v.get("odd")) for v in (c.get("values") or []))
                for c in entradas}

    antes = huella(planas)
    print("\n  Repitiendo la llamada en 60s para ver si los valores se mueven...")
    time.sleep(60)
    _, segunda, _ = pedir("/odds", {"matchId": mid})
    despues = huella(aplanar_cuotas(segunda))

    comunes = set(antes) & set(despues)
    cambiadas = [k for k in comunes if antes[k] != despues[k]]
    print(f"  Mercados comparables: {len(comunes)}  |  que han cambiado: {len(cambiadas)}")
    if cambiadas:
        print("  >>> VEREDICTO: las cuotas SE MUEVEN -> hay feed EN VIVO.")
        print("  >>> Se puede calcular valor esperado en directo automáticamente.")
        for k in cambiadas[:5]:
            print(f"    {k[0]} ({k[1]}): {antes[k]}  ->  {despues[k]}")
    else:
        print("  >>> VEREDICTO: idénticas tras 60s -> cuotas PREVIAS CONGELADAS.")
        print("  >>> Se puede modelar en directo, pero la cuota hay que mirarla a mano.")


def main():
    print("DIAGNÓSTICO EN DIRECTO")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    en_vivo = buscar_en_vivo()
    if not en_vivo:
        titulo("SIN PARTIDOS EN JUEGO AHORA MISMO")
        print("  No se encontró ninguno por las vías probadas. Revisa arriba qué")
        print("  endpoints respondieron: si /matches con solo fecha da 400, hay que")
        print("  pasar ligas concretas con la variable LIGAS_EXTRA.")
        return

    # Se recorren varios partidos en juego, del más avanzado al menos, hasta
    # dar con uno que YA tenga tarjetas. Es la única forma de confirmar que
    # las tarjetas concretas (y no solo los goles) llegan en directo, que es
    # el dato del que depende el modelo de descanso.
    candidatos = sorted(en_vivo, key=minuto_de, reverse=True)[:6]
    titulo("2. BUSCANDO TARJETAS EN DIRECTO ENTRE LOS PARTIDOS EN JUEGO")
    con_tarjetas = None
    for p in candidatos:
        _, datos, _ = pedir(f"/matches/{p['id']}", espera=0.4)
        if datos is None:
            continue
        m = datos[0] if isinstance(datos, list) else datos
        eventos = m.get("events") or []
        tarj = [e for e in eventos if e.get("type") in ("Yellow Card", "Red Card")]
        print(f"    min {minuto_de(p):>3}  {nombre_de(p)[:42]:42s} "
              f"eventos={len(eventos):2d}  tarjetas={len(tarj):2d}")
        if tarj and con_tarjetas is None:
            con_tarjetas = (p, tarj)

    if con_tarjetas:
        p, tarj = con_tarjetas
        print(f"\n  >>> CONFIRMADO: hay TARJETAS en directo en {nombre_de(p)}")
        print("  >>> El modelo de descanso es VIABLE con datos observados, no inferidos.")
        for e in tarj:
            print(f"    min {str(e.get('time')):>4}  {str(e.get('type')):11s} "
                  f"{str(e.get('player'))[:28]:28s} "
                  f"({str((e.get('team') or {}).get('name'))[:20]})")
        elegido = p
    else:
        print("\n  >>> Ningún partido en juego tiene tarjetas ahora mismo.")
        print("  >>> Los eventos sí llegan en directo, pero lo de las tarjetas")
        print("  >>> sigue sin confirmarse. Repetir en otra pasada.")
        elegido = candidatos[0]

    test_eventos_parciales(elegido)
    test_cuotas_en_vivo(elegido)
    titulo("FIN -- no se ha escrito nada en el repositorio")


if __name__ == "__main__":
    main()
