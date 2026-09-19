"""
CONTRASTE EN DIRECTO -- solo lectura.

Prueba definitiva de la cobertura y la frescura del directo de Highlightly.

Hasta ahora preguntábamos a la API qué partidos creía estar siguiendo, y
respondía "uno" (y encima congelado). Eso deja la duda de si es que
realmente no había fútbol. Aquí se invierte: se parte de una lista de
partidos VERIFICADOS en juego, con su minuto real, y se busca cada uno en
el fixture de la API.

Cada partido cae en uno de tres casos, y cada caso significa algo distinto:

  - NO ESTÁ en el fixture                    -> fallo de COBERTURA
  - ESTÁ pero como "Not started"/"Finished"  -> fallo de FRESCURA
  - ESTÁ en juego con minuto parecido        -> el feed funciona

La lista se pasa por la variable PARTIDOS_REALES con el formato
"local|visitante|minuto", separados por punto y coma. Si no se pasa nada,
se usa la de referencia de abajo.
"""
import os
import time
import unicodedata
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

# Partidos verificados en juego (vistos en una app de resultados).
# Formato: (local, visitante, minuto real, competición)
REFERENCIA = [
    ("Perez Zeledon", "Sporting", 40, "Primera Division CRC"),
    ("Choloma", "Estrella Roja", 51, "Liga Nacional HON"),
    ("Piratas", "Venados", 75, "Liga de Expansion MEX"),
    ("Tepatitlan", "Mineros", 81, "Liga de Expansion MEX"),
    ("Alianza Lima", "Tarma", 72, "Liga 1 PER"),
    ("San Francisco", "Arabe Unido", 49, "LPF PAN"),
    ("Comunicaciones", "Guastatoya", 37, "Liga Nacional GUA"),
    ("San Diego Wave", "Kansas City Current", 30, "NWSL USA"),
    ("Bayside Argonauts", "Essendon Royals", 41, "Victoria Premier AUS"),
    ("Tigres de Alica", "Lobos", 7, "Primera Premier MEX"),
]

QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ", "scheduled", "tbd", "to be")


def normalizar(texto):
    """Sin acentos y en minúsculas, para comparar nombres de equipo."""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().strip()


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


def cargar_referencia():
    crudo = os.environ.get("PARTIDOS_REALES", "").strip()
    if not crudo:
        return REFERENCIA
    salida = []
    for trozo in crudo.split(";"):
        partes = [x.strip() for x in trozo.split("|")]
        if len(partes) >= 2:
            try:
                minuto = int(partes[2]) if len(partes) > 2 else 0
            except ValueError:
                minuto = 0
            salida.append((partes[0], partes[1], minuto, partes[3] if len(partes) > 3 else "?"))
    return salida or REFERENCIA


def recoger_fixture():
    """Todos los partidos de ayer, hoy y mañana, paginando."""
    ahora = datetime.now(timezone.utc)
    todos = []
    for desplazamiento in (-1, 0, 1):
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


def buscar(fixture, local, visitante):
    """Busca un partido por nombres de equipo (subcadena, sin acentos).
    Devuelve el mejor candidato o None."""
    l, v = normalizar(local), normalizar(visitante)
    for p in fixture:
        try:
            pl = normalizar(p["homeTeam"]["name"])
            pv = normalizar(p["awayTeam"]["name"])
        except (KeyError, TypeError):
            continue
        # coincidencia en ambos sentidos y por subcadena, porque los nombres
        # varían entre proveedores ("AD Tarma" vs "Tarma", "Arabe Unido" vs "CD Arabe")
        if (l in pl or pl in l) and (v in pv or pv in v):
            return p
        if (l in pv or pv in l) and (v in pl or pl in v):
            return p
    return None


def main():
    ahora = datetime.now(timezone.utc)
    print("CONTRASTE: REALIDAD vs API")
    print("Momento:", ahora.strftime("%Y-%m-%d %H:%M UTC"))

    referencia = cargar_referencia()
    print(f"\nPartidos verificados en juego a contrastar: {len(referencia)}")

    print("\nRecogiendo el fixture completo de la API (ayer/hoy/mañana)...")
    fixture = recoger_fixture()
    print(f"  {len(fixture)} partidos en el fixture")
    vivos_api = [p for p in fixture if en_juego(p)]
    print(f"  la API da como EN JUEGO: {len(vivos_api)}")

    print("\n" + "=" * 78)
    print(f"{'PARTIDO REAL':<40} {'MIN':>4}  {'QUÉ DICE LA API':<30}")
    print("=" * 78)

    sin_cobertura, sin_frescura, correctos = [], [], []
    for local, visitante, minuto, comp in referencia:
        etiqueta = f"{local} vs {visitante}"[:39]
        p = buscar(fixture, local, visitante)
        if p is None:
            veredicto = "NO ESTÁ EN EL FIXTURE"
            sin_cobertura.append((local, visitante, comp))
        else:
            st = p.get("state") or {}
            desc = st.get("description")
            if en_juego(p):
                veredicto = f"en juego, min {minuto_de(p)}"
                correctos.append((local, visitante, minuto, minuto_de(p)))
            else:
                veredicto = f"'{desc}'  (kickoff {str(p.get('date'))[11:16]})"
                sin_frescura.append((local, visitante, desc))
        print(f"{etiqueta:<40} {minuto:>3}'  {veredicto:<30}")

    print("\n" + "=" * 78)
    print("RESUMEN")
    print("=" * 78)
    total = len(referencia)
    print(f"  Partidos reales en juego:            {total}")
    print(f"  Que la API ni tiene en el fixture:   {len(sin_cobertura)}  <- COBERTURA")
    print(f"  Que tiene pero con estado erróneo:   {len(sin_frescura)}  <- FRESCURA")
    print(f"  Que refleja correctamente en juego:  {len(correctos)}")

    if sin_frescura:
        print("\n  Detalle de los que tiene pero no refleja en juego:")
        for l, v, d in sin_frescura:
            print(f"    {l} vs {v}  ->  '{d}'")

    if correctos:
        print("\n  Detalle de los que sí refleja (minuto real vs minuto API):")
        for l, v, real, api in correctos:
            print(f"    {l} vs {v}  ->  real {real}'  API {api}'  "
                  f"(desfase {api - real:+d})")

    print("\n" + "=" * 78)
    print("LECTURA")
    print("=" * 78)
    if not correctos and sin_frescura:
        print("  La API TIENE los partidos pero no los marca en juego: el fixture está")
        print("  bien y lo que falla es la actualización del estado. Es un fallo de")
        print("  FRESCURA, y con él no se puede construir nada en directo.")
    elif not correctos and not sin_frescura:
        print("  La API no tiene siquiera estos partidos: fallo de COBERTURA puro.")
        print("  Habría que comprobar si en las ligas que sí cubre va al día.")
    elif len(correctos) == total:
        print("  La API refleja todos los partidos en juego: el feed en directo")
        print("  funciona y el modelo de descanso sería viable.")
    else:
        print(f"  Mixto: refleja {len(correctos)} de {total}. El directo funciona solo")
        print("  en parte de las competiciones; habría que acotar en cuáles.")


if __name__ == "__main__":
    main()
