"""
LAS 39 ESTADÍSTICAS QUE LLEVAMOS TODO EL PROYECTO SIN MIRAR

QUÉ DESTAPÓ EL CENSO DE ENDPOINTS
---------------------------------
Dos cosas que cambian el inventario del proyecto:

  1. `/lineups/{id}` funciona: formación, once inicial por líneas y suplentes.
  2. `/statistics/{id}` devuelve **39 estadísticas por equipo**, y la primera
     que imprimió fue `Expected Goals`.

Llevamos el proyecto entero usando /statistics para sacar UNA cosa (las faltas
al descanso). Nunca miramos qué más venía en la misma respuesta, que ya
estábamos pagando en la misma llamada.

LAS DOS PREGUNTAS QUE CONTESTA ESTE SCRIPT
------------------------------------------
1. **Qué son esas 39.** Se imprimen todas con su valor, de un partido
   terminado. Si hay xG, tiros, posesión y córners por equipo, entonces sí
   tenemos con qué modelar córners, que es el mercado menos vigilado con
   consenso utilizable (6,5 casas).

2. **¿Hay alineación ANTES del partido?** Es la pregunta que decide. Una
   alineación publicada después del pitido no vale nada. Se prueba sobre
   partidos que todavía no han empezado, a distintas distancias del inicio, y
   se imprime cuántos minutos faltan en cada caso.

   Ojo con el modo de fallo silencioso: el endpoint puede responder 200 con
   un objeto vacío o con los equipos sin jugadores. Por eso se cuenta
   JUGADORES, no se mira el código HTTP.

NO CONCLUYE NADA
----------------
Levanta acta. Si sale que la alineación solo aparece con el partido empezado,
la vía se cierra aquí y se dice.
"""
import os
import json
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

LIGAS = {
    "Premier League": 33973, "La Liga": 119924, "Serie A": 115669,
    "Bundesliga": 67162, "Ligue 1": 52695, "Segunda": 121085,
}
NO_EMPEZADOS = ("not started", "scheduled", "to be", "tbd")


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


def estado_de(p):
    e = p.get("state")
    if isinstance(e, dict):
        return str(e.get("description") or "")
    return str(e or "")


def cuenta_jugadores(bloque):
    """Jugadores del once inicial. initialLineup viene agrupado por LÍNEAS
    (un 4-4-2 da 4 listas), así que hay que aplanar."""
    if not isinstance(bloque, dict):
        return 0
    total = 0
    for linea in bloque.get("initialLineup") or []:
        total += len(linea) if isinstance(linea, list) else 1
    return total


def partidos_de(dias, filtro=None, tope=40):
    hoy = datetime.now(timezone.utc).date()
    fuera = []
    for d in dias:
        fecha = (hoy + timedelta(days=d)).isoformat()
        for liga, lid in LIGAS.items():
            j, _ = pedir("/matches", {"leagueId": lid, "date": fecha,
                                      "limit": 10})
            for p in desempaquetar(j) if j else []:
                if filtro and not filtro(p):
                    continue
                p["_liga"] = liga
                fuera.append(p)
                if len(fuera) >= tope:
                    return fuera
    return fuera


def main():
    ahora = datetime.now(timezone.utc)
    print("=" * 70)
    print(f"CENSO DE ESTADÍSTICAS Y ALINEACIONES -- {ahora:%Y-%m-%d %H:%M} UTC")
    print("=" * 70)

    # ---------- 1. LAS 39 ESTADÍSTICAS ----------
    print("\n\n### 1. QUÉ TRAE /statistics (partido ya jugado)\n")
    jugados = partidos_de([-1, -2, -3, -4],
                          lambda p: "finish" in estado_de(p).lower(), tope=1)
    if not jugados:
        print("  [!] sin partido terminado a mano")
    else:
        p = jugados[0]
        j, est = pedir(f"/statistics/{p['id']}")
        equipos = desempaquetar(j) if j else []
        print(f"  {p['_liga']}: "
              f"{(p.get('homeTeam') or {}).get('name')} vs "
              f"{(p.get('awayTeam') or {}).get('name')}  ({est})")
        for eq in equipos:
            nombre = (eq.get("team") or {}).get("name", "?")
            stats = eq.get("statistics") or []
            print(f"\n  --- {nombre} ({len(stats)} estadísticas) ---")
            for s in stats:
                print(f"      {str(s.get('displayName'))[:38]:40s} "
                      f"{str(s.get('value'))[:20]}")

    # ---------- 2. ¿HAY ALINEACIÓN ANTES DEL PARTIDO? ----------
    print("\n\n### 2. ¿APARECE LA ALINEACIÓN ANTES DEL PITIDO INICIAL?\n")
    print("  Se cuenta JUGADORES, no el código HTTP: el endpoint puede")
    print("  responder 200 con los equipos vacíos.\n")
    proximos = partidos_de([0, 1, 2, 3],
                           lambda p: any(x in estado_de(p).lower()
                                         for x in NO_EMPEZADOS), tope=25)
    if not proximos:
        print("  [!] no hay partidos sin empezar en las seis ligas "
              "para los próximos 4 días")
    else:
        print(f"  {'falta':>9s}  {'liga':16s} {'partido':38s} "
              f"{'once':>5s} {'supl':>5s}  formación")
        for p in sorted(proximos, key=lambda x: str(x.get("date"))):
            try:
                inicio = datetime.fromisoformat(
                    str(p["date"]).replace("Z", "+00:00"))
                falta = (inicio - ahora).total_seconds() / 60
            except Exception:
                falta = float("nan")
            j, est = pedir(f"/lineups/{p['id']}")
            al = (desempaquetar(j) or [{}])[0] if j else {}
            casa, fuera = al.get("homeTeam"), al.get("awayTeam")
            n1, n2 = cuenta_jugadores(casa), cuenta_jugadores(fuera)
            form = (casa or {}).get("formation") or "-"
            nombre = (f"{(p.get('homeTeam') or {}).get('name','?')} vs "
                      f"{(p.get('awayTeam') or {}).get('name','?')}")
            marca = "  <-- HAY ALINEACIÓN" if n1 and n2 else ""
            print(f"  {falta:7.0f}m  {p['_liga'][:16]:16s} {nombre[:38]:38s} "
                  f"{n1:5d} {len((casa or {}).get('substitutes') or []):5d}  "
                  f"{form}{marca}" if j else
                  f"  {falta:7.0f}m  {p['_liga'][:16]:16s} {nombre[:38]:38s} "
                  f"  {est}")

    print("\n" + "=" * 70)
    print("Si ninguna fila trae once con el partido sin empezar, la vía de")
    print("las alineaciones se cierra aquí.")
    print("=" * 70)


if __name__ == "__main__":
    main()
