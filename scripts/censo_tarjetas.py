"""
CENSO DE MERCADOS DE TARJETAS -- solo lectura.

Corrige un error de método: la afirmación de que "solo una casa cotiza
tarjetas" salía de mirar UN partido y UNA línea ("Total Cards 4.5") con
coincidencia exacta de nombre. Eso no vale para concluir nada.

Aquí no se supone ningún nombre. Se recorre cada partido próximo, se
recoge cualquier mercado cuyo nombre contenga card / booking / tarjeta, y
se cuenta cuántas casas distintas cotizan cada línea. De paso se hace lo
mismo con córners y goles, para tener la comparación de liquidez.
"""
import os
import time
import requests
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
LIGA_ID = int(os.environ.get("LIGA_ID", "119924"))

PISTAS_TARJETAS = ("card", "booking", "tarjeta")
PISTAS_CORNERS = ("corner",)
PISTAS_GOLES = ("total goals",)


def pedir(path, params=None, espera=0.4):
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


def titulo(t):
    print("\n" + "=" * 76)
    print(t)
    print("=" * 76)


def proximos_partidos(dias=7):
    partidos = {}
    hoy = datetime.now(timezone.utc).date()
    for offset in range(dias):
        fecha = (hoy + timedelta(days=offset)).isoformat()
        datos = pedir("/matches", {"leagueId": LIGA_ID, "date": fecha})
        for p in desempaquetar(datos):
            if (p.get("state") or {}).get("description") in ("Not started", "Scheduled"):
                partidos[p["id"]] = p
    return list(partidos.values())


def main():
    print("CENSO DE MERCADOS DE TARJETAS")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("Liga:", LIGA_ID)

    partidos = proximos_partidos()
    print(f"\nPartidos próximos encontrados: {len(partidos)}")
    if not partidos:
        print("Sin partidos que inspeccionar.")
        return

    # linea -> conjunto de casas que la cotizan (agregado de todos los partidos)
    casas_por_linea = defaultdict(set)
    casas_por_linea_corners = defaultdict(set)
    casas_por_linea_goles = defaultdict(set)
    # por partido: cuántas casas cotizan ALGO de tarjetas
    resumen_partido = []
    nombres_tarjetas_vistos = Counter()

    for p in sorted(partidos, key=lambda x: x["date"]):
        local = p["homeTeam"]["name"]
        visitante = p["awayTeam"]["name"]
        planas = aplanar_cuotas(pedir("/odds", {"matchId": p["id"]}))
        if not planas:
            resumen_partido.append((local, visitante, 0, 0, 0))
            continue

        casas_tarjetas = set()
        n_entradas_tarjetas = 0
        for c in planas:
            mercado = (c.get("market") or "").strip()
            casa = c.get("bookmakerName")
            bajo = mercado.lower()
            if any(x in bajo for x in PISTAS_TARJETAS):
                casas_por_linea[mercado].add(casa)
                casas_tarjetas.add(casa)
                nombres_tarjetas_vistos[mercado] += 1
                n_entradas_tarjetas += 1
            elif any(x in bajo for x in PISTAS_CORNERS):
                casas_por_linea_corners[mercado].add(casa)
            elif any(x in bajo for x in PISTAS_GOLES):
                casas_por_linea_goles[mercado].add(casa)

        casas_totales = len({c.get("bookmakerName") for c in planas if c.get("bookmakerName")})
        resumen_partido.append((local, visitante, casas_totales, len(casas_tarjetas), n_entradas_tarjetas))

    titulo("1. POR PARTIDO: ¿CUÁNTAS CASAS COTIZAN ALGO DE TARJETAS?")
    print(f"  {'PARTIDO':<44} {'CASAS':>6} {'C/TARJ':>7} {'ENTRADAS':>9}")
    for local, visitante, casas, casas_t, entradas in resumen_partido:
        print(f"  {local[:20] + ' vs ' + visitante[:20]:<44} {casas:>6} {casas_t:>7} {entradas:>9}")

    titulo("2. TODOS LOS MERCADOS DE TARJETAS ENCONTRADOS")
    if not casas_por_linea:
        print("  NINGUNO. No hay mercados con card/booking/tarjeta en el feed.")
    else:
        print(f"  {'MERCADO':<34} {'CASAS':>6}   CASAS CONCRETAS")
        for mercado in sorted(casas_por_linea, key=lambda m: -len(casas_por_linea[m])):
            casas = sorted(x for x in casas_por_linea[mercado] if x)
            print(f"  {mercado[:33]:<34} {len(casas):>6}   {', '.join(casas[:6])}"
                  f"{' ...' if len(casas) > 6 else ''}")

    titulo("3. COMPARACIÓN DE LIQUIDEZ (casas por línea, top 8 de cada mercado)")
    for etiqueta, mapa in (("TARJETAS", casas_por_linea),
                            ("CÓRNERS", casas_por_linea_corners),
                            ("GOLES", casas_por_linea_goles)):
        if not mapa:
            print(f"\n  {etiqueta}: sin mercados")
            continue
        mejores = sorted(mapa.items(), key=lambda kv: -len(kv[1]))[:8]
        print(f"\n  {etiqueta}:")
        for mercado, casas in mejores:
            print(f"    {len(casas):>3} casas  {mercado}")

    titulo("VEREDICTO")
    if casas_por_linea:
        maximo = max(len(v) for v in casas_por_linea.values())
        total_casas_tarj = len(set().union(*casas_por_linea.values()))
        print(f"  Líneas de tarjetas distintas: {len(casas_por_linea)}")
        print(f"  Casas distintas que cotizan tarjetas en algún momento: {total_casas_tarj}")
        print(f"  Máximo de casas en una misma línea: {maximo}")
        if maximo == 1:
            print("  -> Confirmado: ninguna línea la cotiza más de una casa. Sin contraste.")
        elif maximo < 4:
            print("  -> Poca liquidez, pero MÁS DE UNA casa: se puede comparar algo.")
        else:
            print("  -> Hay liquidez real. Mi afirmación anterior era incorrecta:")
            print("     se pueden comparar líneas entre casas y buscar la mejor cuota.")
    else:
        print("  No hay mercados de tarjetas en el feed de esta liga.")


if __name__ == "__main__":
    main()
