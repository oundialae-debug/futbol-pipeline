"""
DIAGNÓSTICO DE LA API DE HIGHLIGHTLY -- solo lectura.

No escribe nada en el repositorio ni toca los CSV. Se lanza a mano desde la
pestaña Actions y vuelca lo que hace falta saber para decidir el siguiente
paso del proyecto. Responde a cinco preguntas:

  1. ¿Cuál es el límite real de peticiones del plan contratado?
  2. ¿Cómo se llama el estado de un partido EN JUEGO, y hay endpoint en vivo?
  3. ¿/matches/{id} devuelve los eventos PARCIALES durante el partido?
     (es lo que necesita el modelo de descanso: tarjetas vistas hasta el min. 45)
  4. ¿Las cuotas son en vivo o solo previas, y qué estructura real tienen?
     (el parser actual solo encuentra "1 mercado" -- hay que ver el JSON de verdad)
  5. ¿Viene informado el árbitro ANTES del partido, y con cuánta antelación?

Las preguntas 2, 3 y 4 solo se responden del todo si hay algún partido en
juego mientras corre. Si no lo hay, el script lo dice y deja constancia de
qué quedó sin comprobar.
"""
import os
import time
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
LIGA_ID = 119924

# La clave nunca debe acabar en el log: se filtra cualquier cabecera sospechosa
CLAVES_PROHIBIDAS = ("key", "token", "auth", "secret")


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


def recolectar_nombres(dato, encontrados=None):
    """Recoge TODOS los valores de claves tipo 'name'/'market' a cualquier
    profundidad. Sirve para saber qué mercados sirve la API de verdad, sin
    depender de dónde estén anidados."""
    if encontrados is None:
        encontrados = []
    if isinstance(dato, dict):
        for clave, valor in dato.items():
            if clave.lower() in ("name", "market", "markettype", "label") and isinstance(valor, str):
                encontrados.append(valor)
            else:
                recolectar_nombres(valor, encontrados)
    elif isinstance(dato, list):
        for elemento in dato:
            recolectar_nombres(elemento, encontrados)
    return encontrados


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
        print("  (el plan habrá que confirmarlo en el panel de Highlightly)")


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
        print("  VEREDICTO: SÍ hay eventos parciales en directo -> el modelo de descanso es viable.")
        print("  Minutos de las tarjetas vistas hasta ahora:",
              [e.get("time") for e in tarjetas])
    else:
        print("  Sin tarjetas todavía (o no se informan en directo).")
        print("  Forma del bloque 'events':")
        describir(eventos[:1] if eventos else [])
    print("\n  Estructura del estado en vivo (marcador/minuto):")
    describir(m.get("state"))


# ============ 4. CUOTAS: ¿EN VIVO O SOLO PREVIAS? ============
def cuotas(en_vivo, proximos):
    titulo("4. CUOTAS: ESTRUCTURA REAL Y SI SE MUEVEN EN DIRECTO")
    objetivo = proximos[0] if proximos else None
    if objetivo:
        print(f"  Partido próximo: {objetivo['homeTeam']['name']} vs {objetivo['awayTeam']['name']}")
        _, datos = pedir("/odds", {"matchId": objetivo["id"]})
        if datos is None:
            print("  /odds no devolvió JSON.")
        else:
            bloque = datos.get("data", datos) if isinstance(datos, dict) else datos
            print(f"  Tipo devuelto: {type(bloque).__name__}, longitud {len(bloque) if hasattr(bloque,'__len__') else '?'}")
            print("  ESTRUCTURA REAL (esto es lo que hay que parsear):")
            # profundidad extra: las cuotas suelen ir casa -> mercados -> valores
            describir(bloque, max_prof=7)
            print()
            nombres = sorted(set(recolectar_nombres(bloque)))
            print(f"  MERCADOS / ETIQUETAS ENCONTRADOS ({len(nombres)}):")
            for n in nombres[:60]:
                print(f"    - {n}")
            print()
            interesantes = [n for n in nombres
                            if any(c in n.lower() for c in ("card", "tarjet", "corner", "winner", "1x2", "total"))]
            if interesantes:
                print("  Relevantes para nuestra estrategia:", ", ".join(interesantes))
            else:
                print("  AVISO: no aparece ningún mercado de tarjetas ni córners.")
                print("  Si se confirma en varios partidos, esos mercados NO se pueden")
                print("  valorar automáticamente con esta API: habría que mirar la cuota")
                print("  a mano o buscar otra fuente de cuotas.")
            print()
            print("  El código actual busca m.get('name') con 'Match Winner'/'1X2'/'Total Cards'.")
            print("  Compara ese supuesto con la estructura y los nombres reales de arriba.")
    else:
        print("  No hay partidos próximos para inspeccionar cuotas previas.")

    print("\n  --- ¿Las cuotas cambian en directo? ---")
    if not en_vivo:
        print("  SIN RESPUESTA: hace falta un partido en juego.")
        print("  Relanza el workflow durante un partido para contestar esto.")
        return
    mid = en_vivo[0]["id"]
    _, primera = pedir("/odds", {"matchId": mid})
    if primera is None:
        print("  El endpoint /odds no devuelve nada para un partido en juego")
        print("  -> indicio fuerte de que las cuotas son SOLO PREVIAS.")
        return
    print("  Hay cuotas para el partido en juego. Repitiendo la llamada en 60s")
    print("  para ver si los valores se mueven...")
    time.sleep(60)
    _, segunda = pedir("/odds", {"matchId": mid})
    if str(primera) == str(segunda):
        print("  IDÉNTICAS tras 60s -> probablemente son cuotas previas congeladas,")
        print("  no un feed en vivo. El valor en directo habría que mirarlo a mano.")
    else:
        print("  CAMBIARON tras 60s -> hay feed de cuotas EN VIVO.")
        print("  Eso permite calcular valor esperado en directo de forma automática.")


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
    for p in proximos[:6]:
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
        print(f"  VEREDICTO: el árbitro SÍ viene antes del partido ({encontrados} de {min(len(proximos),6)}).")
        print("  Se puede pasar a predecir_tarjetas() en vez del None actual.")
    else:
        print("  VEREDICTO: no llega con antelación en esta muestra.")
        print("  Habría que aplicarlo solo en el refinado tardío, o buscar otra fuente.")


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
