"""
DIAGNÓSTICO DE LA API DE HIGHLIGHTLY -- solo lectura.

No escribe nada en el repositorio ni toca los CSV. Se lanza a mano desde la
pestaña Actions y vuelca lo que hace falta saber para decidir el siguiente
paso del proyecto. Responde a cinco preguntas:

  1. ¿Cuál es el límite real de peticiones del plan contratado?
  2. ¿Cómo se llama el estado de un partido EN JUEGO, y hay endpoint en vivo?
  3. ¿/matches/{id} devuelve los eventos PARCIALES durante el partido?
     (es lo que necesita el modelo de descanso: tarjetas vistas hasta el min. 45)
  4. Estructura de /odds, qué mercados sirve, en qué FORMATO viene la cuota
     y si hay cuotas en vivo además de las previas.
  5. ¿Viene informado el árbitro ANTES del partido, y con cuánta antelación?

Las preguntas 2 y 3, y la parte en vivo de la 4, solo se responden si hay
algún partido en juego mientras corre. Si no lo hay, el script lo dice y
deja constancia de qué quedó sin comprobar.
"""
import os
import time
import requests
from collections import Counter
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
LIGA_ID = 119924

# La clave nunca debe acabar en el log: se filtra cualquier cabecera sospechosa
CLAVES_PROHIBIDAS = ("key", "token", "auth", "secret")

# Mercados que interesan a la estrategia, para volcar sus valores reales
MERCADOS_CLAVE = ("Full Time Result", "Total Cards 4.5", "Total Cards 3.5",
                  "Total Corners 9.5", "Total Goals 2.5")


def pedir(path, params=None, espera=1.0):
    """GET con manejo de errores. Devuelve (respuesta, json) o (respuesta, None)."""
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception as exc:
        print(f"    ERROR de red: {type(exc).__name__}")
        return None, None
    time.sleep(espera)
    if r.status_code != 200:
        return r, None
    try:
        return r, r.json()
    except Exception:
        return r, None


def recortar(valor, largo=70):
    texto = str(valor)
    return texto if len(texto) <= largo else texto[:largo] + "..."


def describir(dato, prof=0, max_prof=4, max_claves=30):
    """Imprime la FORMA del JSON (claves y tipos), no el contenido entero."""
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
                print(f"{sangria}{clave}: {recortar(valor)}")
    elif isinstance(dato, list):
        if not dato:
            print(f"{sangria}(lista vacía)")
            return
        print(f"{sangria}-- primer elemento de {len(dato)} --")
        describir(dato[0], prof + 1, max_prof, max_claves)
    else:
        print(f"{sangria}{recortar(dato)}")


def aplanar_cuotas(datos):
    """La respuesta real es [{matchId, odds:[{type, market, values, bookmakerName}]}].
    Devuelve la lista plana de entradas de cuota."""
    bloques = datos.get("data", []) if isinstance(datos, dict) else (datos or [])
    planas = []
    for bloque in bloques:
        if isinstance(bloque, dict):
            planas.extend(bloque.get("odds", []) or [])
    return planas


def titulo(texto):
    print("\n" + "=" * 72)
    print(texto)
    print("=" * 72)


# ============ 1. LÍMITES DEL PLAN ============
def limites_del_plan():
    titulo("1. LÍMITE REAL DE PETICIONES DEL PLAN")
    hoy = datetime.now(timezone.utc).date().isoformat()
    r, _ = pedir("/matches", {"leagueId": LIGA_ID, "date": hoy})
    if r is None:
        print("  No se pudo contactar con la API.")
        return
    print(f"  Código de respuesta: {r.status_code}")
    cabeceras = {k: v for k, v in r.headers.items()
                 if ("limit" in k.lower() or "quota" in k.lower() or "retry" in k.lower())
                 and not any(p in k.lower() for p in CLAVES_PROHIBIDAS)}
    if cabeceras:
        print("  Cabeceras de límite devueltas por la API:")
        for k, v in sorted(cabeceras.items()):
            print(f"    {k}: {v}")
    else:
        print("  La API no devuelve cabeceras de límite reconocibles.")


# ============ 2. ESTADOS Y PARTIDOS EN VIVO ============
def estados_y_en_vivo():
    titulo("2. ESTADOS DE PARTIDO Y ENDPOINTS EN VIVO")
    ahora = datetime.now(timezone.utc)
    estados = {}
    en_vivo, proximos = [], []

    for desplazamiento in (-1, 0, 1):
        fecha = (ahora.date() + timedelta(days=desplazamiento)).isoformat()
        _, datos = pedir("/matches", {"leagueId": LIGA_ID, "date": fecha})
        partidos = (datos or {}).get("data", []) if isinstance(datos, dict) else (datos or [])
        for p in partidos:
            desc = (p.get("state") or {}).get("description", "?")
            estados[desc] = estados.get(desc, 0) + 1
            if desc not in ("Not started", "Scheduled", "Finished"):
                en_vivo.append(p)
            elif desc in ("Not started", "Scheduled"):
                proximos.append(p)

    print("  Estados encontrados (ayer/hoy/mañana):")
    for desc, n in sorted(estados.items(), key=lambda x: -x[1]):
        marca = "  <-- EN JUEGO" if desc not in ("Not started", "Scheduled", "Finished") else ""
        print(f"    {desc:24s} {n:3d}{marca}")
    print()
    print("  El pipeline actual solo reconoce 'Not started', 'Scheduled' y 'Finished'.")
    print("  Cualquier otro estado de la lista es un partido en curso que hoy se ignora.")

    print("\n  Sondeo de posibles endpoints en vivo:")
    candidatos = [
        ("/matches", {"leagueId": LIGA_ID, "live": "true"}),
        ("/matches/live", None),
        ("/live", None),
        ("/live-events", None),
        ("/livescores", None),
        ("/in-play", None),
    ]
    for path, params in candidatos:
        r, datos = pedir(path, params, espera=0.5)
        if r is None:
            continue
        pista = ""
        if r.status_code == 200 and datos is not None:
            n = len(datos.get("data", datos)) if isinstance(datos, (dict, list)) else "?"
            pista = f"  -> responde OK (elementos: {n})"
        print(f"    {r.status_code}  {path}{pista}")

    return en_vivo, proximos


# ============ 3. EVENTOS PARCIALES DURANTE EL PARTIDO ============
def eventos_parciales(en_vivo):
    titulo("3. ¿HAY EVENTOS PARCIALES EN DIRECTO? (clave para el modelo de descanso)")
    if not en_vivo:
        print("  SIN RESPUESTA: no hay ningún partido en juego ahora mismo.")
        print("  Vuelve a lanzar este workflow con un partido en curso para comprobarlo.")
        return
    p = en_vivo[0]
    mid = p["id"]
    print(f"  Partido en juego: {p['homeTeam']['name']} vs {p['awayTeam']['name']} (id {mid})")
    print(f"  Estado: {(p.get('state') or {}).get('description')}")
    _, datos = pedir(f"/matches/{mid}")
    if datos is None:
        print("  /matches/{id} no devolvió JSON utilizable.")
        return
    m = datos[0] if isinstance(datos, list) else datos
    eventos = m.get("events", [])
    tarjetas = [e for e in eventos if e.get("type") in ("Yellow Card", "Red Card")]
    print(f"  Eventos devueltos: {len(eventos)}  |  de ellos tarjetas: {len(tarjetas)}")
    if tarjetas:
        print("  VEREDICTO: SÍ hay eventos parciales en directo -> modelo de descanso viable.")
        print("  Minutos de las tarjetas vistas hasta ahora:",
              [e.get("time") for e in tarjetas])
    else:
        print("  Sin tarjetas todavía (o no se informan en directo).")
        print("  Forma del bloque 'events':")
        describir(eventos[:1] if eventos else [])
    print("\n  Estructura del estado en vivo (marcador/minuto):")
    describir(m.get("state"))


# ============ 4. CUOTAS ============
def cuotas(en_vivo, proximos):
    titulo("4. CUOTAS: MERCADOS, FORMATO DE LA CUOTA Y TIPOS DISPONIBLES")
    objetivo = proximos[0] if proximos else None
    if not objetivo:
        print("  No hay partidos próximos para inspeccionar cuotas.")
    else:
        print(f"  Partido próximo: {objetivo['homeTeam']['name']} vs {objetivo['awayTeam']['name']}")
        _, datos = pedir("/odds", {"matchId": objetivo["id"]})
        if datos is None:
            print("  /odds no devolvió JSON.")
        else:
            planas = aplanar_cuotas(datos)
            print(f"  Entradas de cuota tras aplanar: {len(planas)}")

            tipos = Counter(c.get("type") for c in planas)
            print(f"  TIPOS presentes: {dict(tipos)}")
            if len(tipos) > 1 or "prematch" not in tipos:
                print("  -> hay más de un tipo: comprobar si uno corresponde a cuotas en vivo.")
            else:
                print("  -> solo 'prematch' en un partido que aún no ha empezado (esperable).")

            casas = Counter(c.get("bookmakerName") for c in planas)
            print(f"\n  CASAS DE APUESTAS ({len(casas)}): {', '.join(list(casas)[:12])}")
            print("  (conviene filtrar a las casas en las que realmente puedas apostar)")

            print("\n  VALORES REALES DE LOS MERCADOS CLAVE")
            print("  (sirve para saber si la cuota es DECIMAL (1.85, 2.10) o AMERICANA (-110, +150))")
            for patron in MERCADOS_CLAVE:
                ejemplos = [c for c in planas
                            if (c.get("market") or "").strip().lower() == patron.lower()]
                print(f"\n    {patron}: {len(ejemplos)} entradas")
                for c in ejemplos[:5]:
                    vals = ", ".join(f"{v.get('value')}={v.get('odd')}"
                                     for v in (c.get("values") or []))
                    print(f"      [{c.get('type')}] {str(c.get('bookmakerName'))[:22]:22s} {vals}")

            # Suma de probabilidades implícitas: confirma el formato de forma objetiva.
            # En decimal, sum(1/cuota) de un mercado completo debe dar ~1.02-1.10 (el margen).
            print("\n  PRUEBA OBJETIVA DEL FORMATO (suma de 1/cuota en Full Time Result):")
            print("  Si sale ~1.0-1.1 son DECIMALES. Si sale muy lejos, es otro formato.")
            for c in [x for x in planas
                      if (x.get("market") or "").strip().lower() == "full time result"][:5]:
                try:
                    cuotas_num = [float(v.get("odd")) for v in (c.get("values") or [])]
                    if all(v > 0 for v in cuotas_num):
                        suma = sum(1 / v for v in cuotas_num)
                        print(f"    {str(c.get('bookmakerName'))[:22]:22s} "
                              f"cuotas={cuotas_num}  suma 1/c = {suma:.4f}")
                except (TypeError, ValueError):
                    continue

    print("\n  --- ¿Las cuotas cambian en directo? ---")
    if not en_vivo:
        print("  SIN RESPUESTA: hace falta un partido en juego.")
        return
    mid = en_vivo[0]["id"]
    _, primera = pedir("/odds", {"matchId": mid})
    if primera is None:
        print("  /odds no devuelve nada para un partido en juego")
        print("  -> indicio fuerte de que las cuotas son SOLO PREVIAS.")
        return
    tipos_vivo = Counter(c.get("type") for c in aplanar_cuotas(primera))
    print(f"  Tipos durante el partido: {dict(tipos_vivo)}")
    print("  Repitiendo la llamada en 60s para ver si los valores se mueven...")
    time.sleep(60)
    _, segunda = pedir("/odds", {"matchId": mid})
    if str(primera) == str(segunda):
        print("  IDÉNTICAS tras 60s -> cuotas previas congeladas, no feed en vivo.")
    else:
        print("  CAMBIARON tras 60s -> hay feed de cuotas EN VIVO.")
        print("  Eso permite calcular valor esperado en directo automáticamente.")


# ============ 5. ÁRBITRO ANTES DEL PARTIDO ============
def arbitro_previo(proximos):
    titulo("5. ¿SE CONOCE EL ÁRBITRO ANTES DEL PARTIDO?")
    if not proximos:
        print("  No hay partidos próximos para comprobarlo.")
        return
    ahora = datetime.now(timezone.utc)
    print("  (el árbitro explica el 10.8% de la varianza de tarjetas; hoy no se usa)")
    print()
    encontrados = 0
    # ordenados por cercanía: si aparece, será en los más próximos al inicio
    ordenados = sorted(proximos, key=lambda p: p["date"])
    for p in ordenados[:6]:
        _, datos = pedir(f"/matches/{p['id']}")
        if datos is None:
            continue
        m = datos[0] if isinstance(datos, list) else datos
        arb = m.get("referee")
        nombre = arb.get("name") if isinstance(arb, dict) else arb
        inicio = datetime.fromisoformat(p["date"].replace("Z", "+00:00"))
        horas = (inicio - ahora).total_seconds() / 3600
        estado = f"SÍ -> {nombre}" if nombre else "no informado todavía"
        if nombre:
            encontrados += 1
        print(f"    T-{horas:5.1f}h  {p['homeTeam']['name'][:18]:18s} vs "
              f"{p['awayTeam']['name'][:18]:18s}  {estado}")
    print()
    if encontrados:
        print(f"  VEREDICTO: el árbitro SÍ llega antes del partido ({encontrados} de "
              f"{min(len(ordenados), 6)}). Se puede pasar a predecir_tarjetas().")
    else:
        print("  VEREDICTO: no llega con antelación en esta muestra.")
        print("  Relanza cerca del inicio (T-2h) para ver si aparece entonces;")
        print("  si tampoco, hay que sacarlo de otra fuente (designaciones RFEF).")


def main():
    print("DIAGNÓSTICO DE LA API DE HIGHLIGHTLY")
    print("Momento de ejecución:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    limites_del_plan()
    en_vivo, proximos = estados_y_en_vivo()
    eventos_parciales(en_vivo)
    cuotas(en_vivo, proximos)
    arbitro_previo(proximos)
    titulo("FIN -- nada se ha escrito en el repositorio")


if __name__ == "__main__":
    main()
