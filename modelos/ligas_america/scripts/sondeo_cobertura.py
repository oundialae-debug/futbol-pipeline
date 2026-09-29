"""
SONDEO: ¿trae la API lo que necesita el modelo en Brasil, Japón y México?

Carpeta aislada (modelos/ligas_america/): no escribe nada en data/ ni toca
los modelos oficiales. Pedido el 29/09/2026: antes de entrenar ambos marcan
y más/menos 2.5 en estas ligas, comprobar la cobertura.

Reglas del CLAUDE.md raíz que este sondeo respeta:
  - Ligas por ID, buscadas por PAÍS (hay Serie A en Italia y en Brasil). Se
    imprimen todas las ligas de cada país con su ID para revisarlas a mano.
  - La cobertura NO se mide con un partido: 6 partidos terminados repartidos
    por toda la temporada, en cada temporada (2023/24 engañó por mirar uno).
  - Las cuotas previas se rellenan durante días: se miran en partidos YA
    jugados de los últimos días, no en futuros.

Parte A (API, ~200 llamadas): ligas por país, partidos por temporada, y por
cada muestra /statistics, /matches/{id} (árbitro) y /lineups; cuotas de un
par de partidos recientes (casas, ambos marcan, más/menos 2.5).
Parte B (sin API): cabeceras de football-data.co.uk/new/{BRA,JPN,MEX}.csv
(el precio previo es la variable que más pesa en ambos marcan).
"""
import io
import os
import time
import requests
import pandas as pd

API_KEY = os.environ.get("HIGHLIGHTLY_API_KEY", "")
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
SALIDA = "modelos/ligas_america/sondeo_cobertura.md"

# País -> nombre exacto de la primera división que se busca DENTRO de ese país.
PAISES = {"Brazil": "Serie A", "Japan": "J1 League", "Mexico": "Liga MX"}
TEMPORADAS = (2026, 2025, 2024, 2023)
MUESTRA = 6
FD = {"BRA": "Brasil", "JPN": "Japón", "MEX": "México"}

llamadas = [0]


def pedir(path, params=None):
    for intento in range(3):
        try:
            llamadas[0] += 1
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1))
            continue
        if r.status_code == 429:
            time.sleep(5)
            continue
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except Exception:
            return None
    return None


def lista(j):
    if isinstance(j, dict):
        for k in ("data", "records", "results"):
            if isinstance(j.get(k), list):
                return j[k]
        return [j]
    return j or []


def terminado(p):
    e = p.get("state")
    d = (e.get("description") if isinstance(e, dict) else e) or ""
    return "finish" in str(d).lower()


def ids_titulares(bloque):
    return [j["id"] for linea in (bloque.get("initialLineup") or [])
            for j in linea if j.get("id") is not None]


def ligas_del_pais(pais):
    todas, offset = [], 0
    while True:
        lote = lista(pedir("/leagues", {"countryName": pais, "limit": 100, "offset": offset}))
        todas += [x for x in lote if isinstance(x, dict) and x.get("id")]
        if len(lote) < 100:
            return todas
        offset += 100


def partidos(liga_id, temporada):
    todos, offset = [], 0
    while offset < 1000:
        j = pedir("/matches", {"leagueId": liga_id, "season": temporada,
                               "limit": 100, "offset": offset})
        lote = [p for p in lista(j) if isinstance(p, dict) and p.get("id")]
        todos += lote
        if len(lote) < 100:
            break
        offset += 100
    return todos


def cobertura(p):
    mid = p["id"]
    est = lista(pedir(f"/statistics/{mid}"))
    nombres = set()
    for eq in est:
        if isinstance(eq, dict):
            nombres |= {s.get("displayName") for s in (eq.get("statistics") or [])
                        if s.get("value") is not None}
    det = pedir(f"/matches/{mid}")
    d = lista(det)[0] if det else {}
    arbitro = bool((d.get("referee") or {}).get("name")) if isinstance(d, dict) else False
    lu = pedir(f"/lineups/{mid}")
    lu = lista(lu)[0] if lu else {}
    once = (isinstance(lu, dict) and len(ids_titulares(lu.get("homeTeam") or {})) >= 5
            and len(ids_titulares(lu.get("awayTeam") or {})) >= 5)
    return {"stats": len(nombres), "corners": "Corners" in nombres,
            "xg": "Expected Goals" in nombres, "arbitro": arbitro, "once": once}


def cuotas(p):
    j = pedir("/odds", {"matchId": p["id"], "oddsType": "prematch"})
    casas, btts, ou25 = set(), set(), set()
    for c in lista(j):
        if not isinstance(c, dict):
            continue
        for o in (c.get("odds") or [c]):
            casa, mercado = o.get("bookmakerName"), str(o.get("market") or "")
            if not casa:
                continue
            casas.add(casa)
            if mercado == "Both Teams To Score":
                btts.add(casa)
            # en lo cosechado se llama "Total Goals 2.5" (lado Over/Under)
            if mercado == "Total Goals 2.5" or ("over/under" in mercado.lower() and any(
                    "2.5" in str(v.get("value")) for v in (o.get("values") or []))):
                ou25.add(casa)
    return len(casas), len(btts), len(ou25)


def parte_api(out):
    if not API_KEY:
        out.append("\n**Sin clave de API: parte A no ejecutada.**\n")
        return
    for pais, buscada in PAISES.items():
        ligas = ligas_del_pais(pais)
        out.append(f"\n## {pais}\n\nLigas que devuelve `/leagues?countryName={pais}`:\n")
        out.append("| id | nombre | temporadas |\n|---|---|---|")
        for l in ligas:
            temps = [s.get("season") for s in (l.get("seasons") or []) if isinstance(s, dict)]
            out.append(f"| {l['id']} | {l.get('name')} | {', '.join(map(str, temps[-6:]))} |")
        elegidas = [l for l in ligas if l.get("name") == buscada]
        if len(elegidas) != 1:
            out.append(f"\n**'{buscada}' aparece {len(elegidas)} veces: no se elige sola.**")
            continue
        liga_id = elegidas[0]["id"]
        out.append(f"\nSondeada: **{buscada} (id {liga_id})**\n")
        out.append("| temporada | partidos | terminados | muestra | con estadísticas (media nº) "
                   "| córners | xG | árbitro | once |\n|---|---|---|---|---|---|---|---|---|")
        recientes = []
        for t in TEMPORADAS:
            ps = partidos(liga_id, t)
            fin = sorted([p for p in ps if terminado(p)], key=lambda p: str(p.get("date")))
            recientes += fin[-3:]
            if not fin:
                out.append(f"| {t} | {len(ps)} | 0 | - | - | - | - | - | - |")
                continue
            paso = max(1, len(fin) // MUESTRA)
            muestra = fin[::paso][:MUESTRA]
            cs = [cobertura(p) for p in muestra]
            n = len(cs)
            con = [c for c in cs if c["stats"]]
            media = sum(c["stats"] for c in con) / len(con) if con else 0
            f = lambda k: f"{sum(c[k] for c in cs)}/{n}"
            out.append(f"| {t} | {len(ps)} | {len(fin)} | {n} ({muestra[0].get('date','')[:10]} a "
                       f"{muestra[-1].get('date','')[:10]}) | {len(con)}/{n} ({media:.0f}) | "
                       f"{f('corners')} | {f('xg')} | {f('arbitro')} | {f('once')} |")
            print(pais, t, len(ps), len(fin), cs, f"llamadas={llamadas[0]}")
        recientes = sorted(recientes, key=lambda p: str(p.get("date")))[-3:]
        out.append("\nCuotas de los 3 últimos partidos terminados (la API guarda ~28 días):\n")
        out.append("| fecha | partido | casas | con ambos marcan | con más/menos 2.5 |\n|---|---|---|---|---|")
        for p in recientes:
            c, b, o = cuotas(p)
            nom = f"{(p.get('homeTeam') or {}).get('name')} - {(p.get('awayTeam') or {}).get('name')}"
            out.append(f"| {str(p.get('date'))[:10]} | {nom} | {c} | {b} | {o} |")


def parte_fd(out):
    out.append("\n## football-data.co.uk (sin API)\n")
    out.append("| fichero | filas | temporadas | Pinnacle 1X2 | Pinnacle cierre | más/menos 2.5 | ambos marcan |"
               "\n|---|---|---|---|---|---|---|")
    for cod, nombre in FD.items():
        try:
            r = requests.get(f"https://www.football-data.co.uk/new/{cod}.csv", timeout=30)
            df = pd.read_csv(io.StringIO(r.content.decode("utf-8-sig", errors="replace")))
        except Exception as e:
            out.append(f"| {cod}.csv ({nombre}) | error {type(e).__name__} | | | | | |")
            continue
        cols = list(df.columns)
        temps = sorted(df["Season"].astype(str).unique()) if "Season" in cols else []
        ou = [c for c in cols if "2.5" in c]
        bt = [c for c in cols if "BTTS" in c.upper() or "BTS" in c.upper()]
        pin = [c for c in cols if c in ("PH", "PD", "PA", "PSH", "PSD", "PSA")]
        pinc = [c for c in cols if c.startswith("PSC") or c in ("PSCH", "PCH")]
        out.append(f"| {cod}.csv ({nombre}) | {len(df)} | {', '.join(temps[-5:])} | {' '.join(pin) or '-'} "
                   f"| {' '.join(pinc) or '-'} | {' '.join(ou) or 'ninguna'} | {' '.join(bt) or 'ninguna'} |")
        out.append(f"\nColumnas de {cod}: `{' '.join(cols)}`\n")


def main():
    out = ["# Sondeo de cobertura: Brasil, Japón, México\n",
           f"Muestra: {MUESTRA} partidos terminados repartidos por cada temporada.\n"]
    parte_api(out)
    parte_fd(out)
    out.append(f"\nLlamadas a la API: {llamadas[0]}\n")
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    open(SALIDA, "w", encoding="utf-8").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
