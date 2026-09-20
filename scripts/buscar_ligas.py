"""
ENCONTRAR EL ID BUENO DE CADA LIGA

EL FALLO QUE ARREGLA
--------------------
El backfill trajo 2.004 partidos de cinco ligas. De la Segunda trajo CERO, y
el script no se quejo: conte los partidos sin estadisticas pero no las ligas
que vuelven vacias. El ID 121085 no devuelve nada y nadie se entero hasta
mirar la tabla por liga a mano.

Es el fallo de siempre en este repositorio -- cero error, cero filas -- y esta
vez en codigo escrito hoy por mi.

COMO SE BUSCA
-------------
Por pais, no por nombre suelto: hay Premier League en Inglaterra y en Jamaica,
Serie A en Italia y en Brasil, Segunda en Espana y Division 2 en media docena
de sitios. Se piden las ligas de cada pais y se imprimen con su ID, su nombre
exacto y las temporadas que tienen, para elegir mirando.

No adivina ni elige sola: imprime y decide una persona. Elegir por parecido de
nombre es como se colo la Premier de Jamaica.
"""
import os
import requests

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

PAISES = {"ES": "Espana", "GB": "Reino Unido", "IT": "Italia",
          "DE": "Alemania", "FR": "Francia", "GB-ENG": "Inglaterra"}

# Lo que el proyecto cree tener. Se marca para ver si sigue siendo verdad.
ESPERADOS = {33973: "Premier League", 119924: "La Liga", 115669: "Serie A",
             67162: "Bundesliga", 52695: "Ligue 1", 121085: "Segunda (?)"}


def pedir(path, params=None):
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
    print("=" * 74)
    print("LIGAS POR PAIS, con su ID exacto")
    print("=" * 74)
    for codigo, pais in PAISES.items():
        j, estado = pedir("/leagues", {"countryCode": codigo, "limit": 100})
        ligas = desempaquetar(j) if j else []
        print(f"\n### {pais} ({codigo}) -- {estado}, {len(ligas)} ligas")
        for l in ligas:
            lid = l.get("id")
            marca = "  <== EL QUE USAMOS" if lid in ESPERADOS else ""
            temporadas = l.get("seasons") or []
            anios = sorted({s.get("season") for s in temporadas
                            if isinstance(s, dict)} - {None})
            print(f"    {str(lid):>10s}  {str(l.get('name'))[:40]:42s} "
                  f"{str(anios[-3:]) if anios else ''}{marca}")

    print("\n" + "=" * 74)
    print("COMPROBACION DIRECTA de los IDs que usa el proyecto")
    print("=" * 74)
    for lid, nombre in ESPERADOS.items():
        j, estado = pedir(f"/leagues/{lid}")
        ligas = desempaquetar(j) if j else []
        if not ligas or not ligas[0].get("id"):
            print(f"  {lid}  {nombre:20s}  ->  {estado}  [!] NO EXISTE")
            continue
        l = ligas[0]
        pais = (l.get("country") or {})
        print(f"  {lid}  {nombre:20s}  ->  {l.get('name')} "
              f"({pais.get('name')})")


if __name__ == "__main__":
    main()
