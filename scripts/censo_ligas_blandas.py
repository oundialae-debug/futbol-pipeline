"""
¿HAY LIGAS QUE NADIE VIGILA?

LA PREGUNTA QUE NUNCA HICIMOS
------------------------------
Todo el proyecto probo MERCADOS (corners, tarjetas, 1X2...) dentro de las
mismas seis ligas: Premier, La Liga, Serie A, Bundesliga, Ligue 1, Segunda.
Todas tienen 49-50 casas cotizando el 1X2 -- son de las ligas mas vigiladas
del planeta. Nunca variamos la LIGA.

Highlightly es un agregador global (la especificacion tiene /leagues con
filtro por pais, sin restringir a top-5). Este script mira si hay ligas de
verdad descuidadas -- segundas y terceras divisiones de paises medianos,
ligas de fuera de Europa -- y cuantas casas las cotizan.

QUE MIDE
--------
Para una muestra de ligas de distintos niveles, cuenta cuantas casas dan
cuotas de 1X2 en sus proximos partidos. Menos casas = menos ojos = mas
probable que el precio este mal, no solo caro (aunque eso habria que
comprobarlo aparte, como se hizo con corners).

No decide nada por si mismo: es el primer filtro, igual que
censo_endpoints.py lo fue para los datos por partido.
"""
import os
import time
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

# Una muestra deliberada: segundas/terceras divisiones y paises medianos,
# elegidos por ser candidatos plausibles a estar poco vigilados. Por PAIS,
# nunca por nombre suelto (Segunda hay en muchos sitios).
CANDIDATOS = [
    ("PL", "Polonia"), ("BE", "Belgica"), ("NL", "Holanda"),
    ("PT", "Portugal"), ("GR", "Grecia"), ("TR", "Turquia"),
    ("NO", "Noruega"), ("DK", "Dinamarca"), ("CZ", "Chequia"),
    ("RO", "Rumania"), ("MX", "Mexico"), ("AR", "Argentina"),
    ("JP", "Japon"), ("KR", "Corea del Sur"),
]

llamadas = [0]


def pedir(path, params=None):
    llamadas[0] += 1
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS,
                         params=params, timeout=25)
    except Exception as e:
        return None, f"[red] {type(e).__name__}"
    if r.status_code != 200:
        return None, f"[HTTP {r.status_code}]"
    try:
        return r.json(), "ok"
    except Exception:
        return None, "[no es JSON]"


def desempaquetar(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def main():
    hoy = datetime.now(timezone.utc).date()
    print(f"{'='*72}\n¿HAY LIGAS POCO VIGILADAS? -- {hoy}\n{'='*72}\n")

    filas = []
    for codigo, pais in CANDIDATOS:
        j, _ = pedir("/leagues", {"countryCode": codigo, "limit": 15})
        ligas = desempaquetar(j) if j else []
        if not ligas:
            print(f"  {pais:16s}  sin ligas devueltas")
            continue
        # coger 1-2 ligas por pais, evitando la de mayor nombre "obvio"
        for liga in ligas[:2]:
            lid, lname = liga.get("id"), liga.get("name")
            if not lid:
                continue
            # buscar un partido proximo en esa liga (hasta 10 dias)
            partido = None
            for dd in range(0, 10):
                fecha = (hoy + timedelta(days=dd)).isoformat()
                j2, _ = pedir("/matches", {"leagueId": lid, "date": fecha,
                                          "limit": 5})
                ms = desempaquetar(j2) if j2 else []
                if ms:
                    partido = ms[0]
                    break
            if not partido:
                print(f"  {pais:16s} {str(lname)[:28]:30s}  sin partidos proximos")
                continue
            j3, _ = pedir("/odds", {"matchId": partido["id"]})
            bloques = desempaquetar(j3) if j3 else []
            casas = set()
            for b in bloques:
                for o in (b.get("odds") or []):
                    if o.get("market") == "Full Time Result":
                        casas.add(o.get("bookmakerName"))
            print(f"  {pais:16s} {str(lname)[:28]:30s}  {len(casas):3d} casas  "
                  f"(llamadas {llamadas[0]})")
            filas.append((pais, lname, len(casas)))

    print(f"\n{'='*72}")
    if filas:
        filas.sort(key=lambda x: x[2])
        print("ORDENADAS DE MENOS A MAS VIGILADA:\n")
        for pais, lname, n in filas:
            marca = "  <== CANDIDATA A LIGA BLANDA" if 0 < n <= 15 else ""
            print(f"  {n:3d} casas   {pais:14s} {str(lname)[:32]:34s}{marca}")
        print(f"\nReferencia: las seis ligas del proyecto tienen 49-50 casas.")
    print(f"\nTotal llamadas: {llamadas[0]}")


if __name__ == "__main__":
    main()
