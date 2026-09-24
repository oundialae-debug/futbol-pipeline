"""
SONDEO: mercado "gol de equipo en la 1ª parte" en la Nations League

Ninguna de las 5 grandes ligas europeas lo tiene (sondeo_gol_1parte.py,
24/09, 207 mercados distintos vistos, cero relacionados con medio tiempo).
Petición del usuario: probar con la Nations League, partidos de los
próximos días.

Este proyecto NO tiene la Nations League configurada (solo sigue 6 ligas
domésticas, ver buscar_ligas.py) -- hace falta encontrar su ID primero.
/leagues acepta `leagueName` como filtro de texto (visto en la spec), así
que se busca por nombre en vez de por país (la Nations League es un
torneo de selecciones, no de un país concreto). Puede haber varias
"Nations League" (UEFA, CONCACAF...) -- se listan todas para elegir a
mano, mismo principio que buscar_ligas.py: no adivinar por parecido de
nombre.
"""
import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from collections import defaultdict

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

RUTA_INFORME = "sondeo_nations_league.md"
DIAS_ADELANTE = int(os.environ.get("DIAS_ADELANTE", "10"))
MAX_PARTIDOS = int(os.environ.get("MAX_PARTIDOS", "20"))
CLAVES_TIEMPO = ("half", "1st", "1er", "primera parte", "1ª parte", "ht ")
CLAVES_GOL = ("score", "goal", "marca", "gol")


def pedir(path, params=None, espera=0.25):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
    except Exception:
        return None
    time.sleep(espera)
    if r.status_code != 200:
        print(f"  [HTTP {r.status_code}] {path} {params}")
        return None
    try:
        return r.json()
    except Exception:
        return None


def desempaquetar(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def main():
    lineas_md = ["# Sondeo: Nations League -- gol de equipo en la 1ª parte\n"]

    print("Buscando ligas con nombre 'Nations League'...")
    j = pedir("/leagues", {"leagueName": "Nations League", "limit": 50})
    ligas = desempaquetar(j) if j else []
    print(f"{len(ligas)} ligas encontradas:")
    lineas_md.append("## Ligas encontradas por nombre\n")
    lineas_md.append("| id | nombre | pais |")
    lineas_md.append("|---|---|---|")
    for l in ligas:
        pais = (l.get("country") or {}).get("name")
        print(f"  {l.get('id')}  {l.get('name')}  ({pais})")
        lineas_md.append(f"| {l.get('id')} | {l.get('name')} | {pais} |")

    if not ligas:
        lineas_md.append("\nNinguna liga con ese nombre encontrada. Fin del sondeo.\n")
        with open(RUTA_INFORME, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas_md) + "\n")
        print("Sin ligas. Escrito informe vacio.")
        return

    # UEFA es la que interesa aqui (la que sigue el usuario) -- preferir
    # la que tenga pais None/Europa o "UEFA" en el nombre; si no, coger
    # la primera y dejarlo anotado para que se revise a mano.
    elegida = None
    for l in ligas:
        nombre = (l.get("name") or "").lower()
        pais = (l.get("country") or {}).get("name") or ""
        if "uefa" in nombre or pais.lower() in ("europe", "world", ""):
            elegida = l
            break
    if elegida is None:
        elegida = ligas[0]
    league_id = elegida.get("id")
    print(f"\nUsando league_id={league_id} ({elegida.get('name')})")
    lineas_md.append(f"\nElegida para el sondeo: **{elegida.get('name')}** (id {league_id})\n")

    print(f"\nBuscando partidos en los próximos {DIAS_ADELANTE} días...")
    hoy = datetime.now(timezone.utc).date()
    match_ids = []
    for i in range(DIAS_ADELANTE):
        fecha = (hoy + timedelta(days=i)).isoformat()
        j = pedir("/matches", {"leagueId": league_id, "date": fecha})
        partidos = desempaquetar(j) if j else []
        if partidos:
            print(f"  {fecha}: {len(partidos)} partidos")
        for p in partidos:
            mid = p.get("id")
            if mid:
                match_ids.append({
                    "match_id": mid, "fecha": fecha,
                    "local": (p.get("homeTeam") or {}).get("name", ""),
                    "visitante": (p.get("awayTeam") or {}).get("name", ""),
                })
        if len(match_ids) >= MAX_PARTIDOS:
            break

    print(f"\n{len(match_ids)} partidos de Nations League encontrados en total")
    lineas_md.append(f"\n{len(match_ids)} partidos encontrados en los próximos "
                     f"{DIAS_ADELANTE} días.\n")
    if not match_ids:
        lineas_md.append("Sin partidos próximos -- no se puede sondear /odds.\n")
        with open(RUTA_INFORME, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas_md) + "\n")
        print("Sin partidos. Fin.")
        return

    censo = defaultdict(lambda: {"partidos": 0, "casas": set(), "ejemplos": set()})
    coincidencias = []
    for p in match_ids[:MAX_PARTIDOS]:
        datos = pedir("/odds", {"matchId": int(p["match_id"]), "oddsType": "prematch"})
        bloques = (datos.get("data", []) if isinstance(datos, dict) else datos) or []
        planas = []
        for b in bloques:
            if isinstance(b, dict):
                planas.extend(b.get("odds", []) or [])
        mercados_este_partido = set()
        for c in planas:
            mercado = c.get("market") or "(sin nombre)"
            mercados_este_partido.add(mercado)
            casa = c.get("bookmakerName") or "(sin casa)"
            censo[mercado]["casas"].add(casa)
            valores = c.get("values") or []
            for v in valores:
                censo[mercado]["ejemplos"].add(str(v.get("value")))
            m_baja = mercado.lower()
            if any(t in m_baja for t in CLAVES_TIEMPO) and any(g in m_baja for g in CLAVES_GOL):
                coincidencias.append({
                    "local": p["local"], "visitante": p["visitante"],
                    "mercado": mercado, "casa": casa,
                    "valores": ", ".join(str(v.get("value")) for v in valores[:6]),
                })
        for m in mercados_este_partido:
            censo[m]["partidos"] += 1

    print(f"\n{len(censo)} mercados distintos vistos en {len(match_ids[:MAX_PARTIDOS])} partidos")
    lineas_md.append(f"## {len(censo)} mercados distintos vistos "
                     f"({len(match_ids[:MAX_PARTIDOS])} partidos con /odds sondeado)\n")
    lineas_md.append("| mercado | partidos | casas | valores |")
    lineas_md.append("|---|---|---|---|")
    for mercado, info in sorted(censo.items(), key=lambda kv: -kv[1]["partidos"]):
        ejemplos = ", ".join(sorted(info["ejemplos"])[:6])
        lineas_md.append(f"| {mercado} | {info['partidos']} | {len(info['casas'])} | {ejemplos} |")
        print(f"  {mercado:40s} partidos={info['partidos']:3d} casas={len(info['casas']):3d}")

    lineas_md.append("\n## Coincidencias con \"medio tiempo/1ª parte\" + \"marcar/gol\"\n")
    if coincidencias:
        lineas_md.append("| partido | mercado | casa | valores |")
        lineas_md.append("|---|---|---|---|")
        for c in coincidencias:
            lineas_md.append(f"| {c['local']} vs {c['visitante']} | {c['mercado']} | "
                             f"{c['casa']} | {c['valores']} |")
        print(f"\n{len(coincidencias)} coincidencias encontradas")
    else:
        lineas_md.append("Ninguna.\n")
        print("\nNinguna coincidencia.")

    with open(RUTA_INFORME, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas_md) + "\n")
    print(f"\nEscrito {RUTA_INFORME}")


if __name__ == "__main__":
    main()
