"""Sondeo de fuentes alternativas a Highlightly (jugadores y Champions). Solo lee, no guarda datos de terceros.
Se ejecuta en GitHub Actions (sondeo_fuentes.yml) porque el contenedor de Claude no sale a estas webs.
Escribe data/sondeo_fuentes.md con estado HTTP y forma de los datos de cada fuente."""
import json
import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept": "application/json,text/plain,*/*"}
SAL = []


def get(url, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=30, **kw)
        return r
    except Exception as e:
        SAL.append(f"- `{url}` -> ERROR {type(e).__name__}: {str(e)[:120]}")
        return None


def nota(txt):
    print(txt)
    SAL.append(txt)


def espn(liga, fecha, titulo):
    nota(f"\n## ESPN {titulo} ({liga}, {fecha})")
    r = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard?dates={fecha}")
    if r is None:
        return
    nota(f"- scoreboard HTTP {r.status_code}")
    if r.status_code != 200:
        return
    ev = r.json().get("events", [])
    nota(f"- partidos: {len(ev)}")
    for e in ev[:12]:
        c = e["competitions"][0]
        eq = [(x["team"]["displayName"], x.get("score")) for x in c["competitors"]]
        nota(f"  - {e['id']} {eq} {e['status']['type']['name']}")
    fin = [e for e in ev if e["status"]["type"]["completed"]]
    if not fin:
        return
    eid = fin[0]["id"]
    s = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/summary?event={eid}")
    if s is None or s.status_code != 200:
        nota(f"- summary {eid}: HTTP {getattr(s, 'status_code', None)}")
        return
    j = s.json()
    nota(f"- summary {eid} claves: {list(j.keys())}")
    bs = j.get("boxscore", {})
    for t in bs.get("teams", [])[:2]:
        nota(f"  - equipo {t['team']['displayName']}: " + ", ".join(f"{x['name']}={x['displayValue']}" for x in t.get("statistics", [])))
    ros = j.get("rosters", [])
    nota(f"- rosters: {len(ros)}")
    for ro in ros[:1]:
        lista = ro.get("roster", [])
        nota(f"  - jugadores en roster: {len(lista)}")
        if lista:
            p = lista[0]
            nota(f"  - ejemplo: {p['athlete'].get('displayName')} stats: " + ", ".join(f"{x['name']}={x['displayValue']}" for x in p.get("stats", [])))


def otros():
    nota("\n## Sofascore")
    r = get("https://api.sofascore.com/api/v1/sport/football/scheduled-events/2026-10-12")
    if r is not None:
        nota(f"- scheduled-events HTTP {r.status_code} {r.text[:150]!r}")
    nota("\n## FotMob")
    r = get("https://www.fotmob.com/api/data/matches?date=20261012")
    if r is not None:
        nota(f"- matches HTTP {r.status_code} {r.text[:150]!r}")
    nota("\n## openfootball Champions")
    for u in ("https://raw.githubusercontent.com/openfootball/champions-league/master/2026-27/cl.txt",
              "https://raw.githubusercontent.com/openfootball/champions-league/master/2025-26/cl.txt"):
        r = get(u)
        if r is not None:
            nota(f"- {u.split('master/')[1]} HTTP {r.status_code} {len(r.text)} bytes")
    nota("\n## TheSportsDB (clave gratuita 3)")
    for lid in (4328, 4332, 4331, 4335, 4334, 4480):
        r = get(f"https://www.thesportsdb.com/api/v1/json/3/eventsround.php?id={lid}&r=7&s=2026-2027")
        if r is not None:
            try:
                n = len(r.json().get("events") or [])
            except Exception:
                n = "?"
            nota(f"- liga {lid} ronda 7: HTTP {r.status_code} eventos {n}")
    nota("\n## football-data.org (sin clave)")
    r = get("https://api.football-data.org/v4/competitions/CL/matches?dateFrom=2026-10-13&dateTo=2026-10-13")
    if r is not None:
        nota(f"- CL matches HTTP {r.status_code} {r.text[:200]!r}")


if __name__ == "__main__":
    espn("ita.1", "20261012", "Serie A lunes")
    espn("eng.1", "20261011", "Premier domingo")
    espn("uefa.champions", "20261013", "Champions hoy")
    espn("uefa.champions", "20260916", "Champions jornada 1")
    espn("esp.1", "20261011", "La Liga domingo")
    otros()
    open("data/sondeo_fuentes.md", "w").write("# Sondeo de fuentes (13/10/2026)\n" + "\n".join(SAL) + "\n")
