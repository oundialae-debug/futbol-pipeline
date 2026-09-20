"""
¿QUÉ NOS DA ESTA API QUE NUNCA HEMOS PEDIDO?

EL AGUJERO QUE TAPA
-------------------
En veredicto.md escribí que la API no sirve alineaciones. Es falso: el
endpoint `/lineups/{matchId}` está en la tabla de refrescos de API.md desde el
principio (cada 15 minutos) y jamás lo hemos llamado. Los scripts solo han
usado /matches, /odds, /statistics, /leagues y /live*.

Eso importa porque la conclusión del proyecto ("no hay ventaja porque no
tenemos información que el mercado no tenga") se apoyaba en un inventario
incompleto que yo di por cerrado sin comprobarlo.

QUÉ HACE ESTE SCRIPT
--------------------
Pide cada endpoint plausible una vez y cuenta lo que devuelve. No analiza
nada: solo levanta acta de qué existe, con qué forma y con cuánto detalle.
Las decisiones vienen después, sobre el inventario real.

Para cada endpoint imprime el código HTTP, cuántos elementos trae y las claves
del primer elemento hasta dos niveles. Con los valores de muestra recortados,
porque lo que interesa es el ESQUEMA, no el contenido.

SOBRE LA CLAVE
--------------
La cabecera de autenticación no se imprime nunca. Las URLs sí, pero la clave
va en cabecera, no en la URL.

COSTE
-----
Un partido próximo y uno ya jugado, por unos veinte endpoints: unas 40
llamadas de las 7.500 diarias. Despreciable.
"""
import os
import json
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

# Las seis ligas del proyecto, por ID (nunca por nombre: hay Serie A en Italia
# y en Brasil, Premier League en Inglaterra y en Jamaica)
LIGAS = {
    "Premier League": 33973, "La Liga": 119924, "Serie A": 115669,
    "Bundesliga": 67162, "Ligue 1": 52695, "Segunda": 121085,
}

MAX = 900   # recorte al imprimir una muestra


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
            if k in d and isinstance(d[k], list):
                return d[k]
        return [d]
    return d or []


def esquema(o, prefijo="", nivel=0):
    """Claves y tipos, hasta dos niveles. Los valores se recortan."""
    if nivel > 1 or not isinstance(o, dict):
        return []
    fuera = []
    for k, v in list(o.items())[:30]:
        if isinstance(v, dict):
            fuera.append(f"{prefijo}{k}: objeto")
            fuera += esquema(v, prefijo + "  ", nivel + 1)
        elif isinstance(v, list):
            fuera.append(f"{prefijo}{k}: lista[{len(v)}]")
            if v and isinstance(v[0], dict):
                fuera += esquema(v[0], prefijo + "  ", nivel + 1)
            elif v:
                fuera.append(f"{prefijo}  -> {str(v[0])[:60]}")
        else:
            fuera.append(f"{prefijo}{k} = {str(v)[:60]}")
    return fuera


def probar(nombre, path, params=None):
    d, estado = pedir(path, params)
    if d is None:
        print(f"\n### {nombre}  ->  {estado}")
        return None
    items = desempaquetar(d)
    print(f"\n### {nombre}  ->  ok, {len(items)} elementos")
    if items:
        for linea in esquema(items[0])[:40]:
            print(f"    {linea}")
    return items


def main():
    hoy = datetime.now(timezone.utc).date()
    print("=" * 70)
    print(f"CENSO DE ENDPOINTS -- {hoy}")
    print("=" * 70)

    # --- un partido PRÓXIMO y uno YA JUGADO de las ligas del proyecto ---
    proximo = jugado = None
    for dias, destino in ((1, "proximo"), (-3, "jugado")):
        fecha = (hoy + timedelta(days=dias)).isoformat()
        for liga_id in LIGAS.values():
            d, _ = pedir("/matches", {"leagueId": liga_id, "date": fecha,
                                      "limit": 5})
            ms = desempaquetar(d) if d else []
            if ms:
                if destino == "proximo":
                    proximo = ms[0]
                else:
                    jugado = ms[0]
                break

    for etiqueta, p in (("PRÓXIMO", proximo), ("YA JUGADO", jugado)):
        if not p:
            print(f"\n[!] sin partido {etiqueta}: los endpoints por matchId no "
                  f"se prueban con él")
            continue
        mid = p.get("id")
        print(f"\n{'='*70}\nPARTIDO {etiqueta}: id={mid} "
              f"estado={str(p.get('state'))[:60]}\n{'='*70}")

        # el inventario: lo que nunca hemos pedido va primero
        probar("lineups/{id}   <-- NUNCA LLAMADO", f"/lineups/{mid}")
        probar("events/{id}", f"/events/{mid}")
        probar("statistics/{id}", f"/statistics/{mid}")
        probar("head-2-head", "/head-2-head",
               {"teamIdOne": (p.get("homeTeam") or {}).get("id"),
                "teamIdTwo": (p.get("awayTeam") or {}).get("id")})

    # --- endpoints que no dependen de un partido ---
    print(f"\n{'='*70}\nENDPOINTS GENERALES\n{'='*70}")
    liga = LIGAS["La Liga"]
    probar("standings", "/standings", {"leagueId": liga, "season": hoy.year})
    probar("teams", "/teams", {"leagueId": liga, "limit": 3})
    probar("players", "/players", {"limit": 3})
    probar("injuries", "/injuries", {"leagueId": liga})
    probar("transfers", "/transfers", {"leagueId": liga})
    probar("coaches", "/coaches", {"leagueId": liga})
    probar("referees", "/referees", {"leagueId": liga})
    probar("odds-bookmakers", "/bookmakers", {"limit": 5})
    probar("last-five-games", "/last-five-games",
           {"teamId": (proximo or {}).get("homeTeam", {}).get("id")}
           if proximo else None)

    print(f"\n{'='*70}\nFIN. Lo que salga en verde y no estuviera en API.md "
          f"es inventario nuevo.\n{'='*70}")


if __name__ == "__main__":
    main()
