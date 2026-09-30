"""
Datos de UN partido de una liga sin fuentes externas, con la API (autorizado
por el usuario el 30/09 para Amatitlán - Santa Lucía, Guatemala 2ª). ~20
llamadas: ligas del país, partido de hoy, resultados de la temporada de esa
liga, h2h y cuotas (1X2, ambos marcan, más/menos 2.5) de todas las casas.
Escribe modelos/ligas_america/api_partido.md.
"""
import os, time, json, requests
from datetime import datetime, timedelta, timezone
H = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}
B = "https://soccer.highlightly.net"
PAIS = os.environ.get("PAIS", "Guatemala"); CLAVE = os.environ.get("CLAVE", "Amatit")
n = [0]; out = []
def pedir(p, q=None):
    for _ in range(3):
        n[0] += 1
        r = requests.get(B + p, headers=H, params=q, timeout=25)
        if r.status_code == 429: time.sleep(4); continue
        if r.status_code != 200: out.append(f"[HTTP {r.status_code}] {p} {q}"); return None
        return r.json()
def lista(j): return (j.get("data") if isinstance(j, dict) else j) or []
hoy = (datetime.now(timezone.utc) - timedelta(hours=6)).date().isoformat()
partido = None
for f in (hoy, (datetime.now(timezone.utc)).date().isoformat()):
    for p in lista(pedir("/matches", {"countryName": PAIS, "date": f, "limit": 100})):
        if CLAVE.lower() in json.dumps(p, ensure_ascii=False).lower():
            partido = p; break
    if partido: break
if not partido:
    out.append("No encontrado el partido"); open("modelos/ligas_america/api_partido.md","w").write("\n".join(out)); raise SystemExit
lg = partido["league"]; loc, vis = partido["homeTeam"], partido["awayTeam"]
out.append(f"# {loc['name']} - {vis['name']} | {lg.get('name')} (id {lg.get('id')}, temporada {lg.get('season')}) | {partido.get('date')}\n")
res = []
for temp in (lg.get("season"), (lg.get("season") or 0) - 1):
    for off in (0, 100, 200, 300):
        l = lista(pedir("/matches", {"leagueId": lg["id"], "season": temp, "limit": 100, "offset": off}))
        for p in l:
            sc = ((p.get("state") or {}).get("score") or {}).get("current")
            if sc and "finish" in str((p.get("state") or {}).get("description", "")).lower():
                a, b = (int(x) for x in sc.replace(" ", "").split("-"))
                res.append((p.get("date", "")[:10], p["homeTeam"]["name"], p["awayTeam"]["name"], a, b))
        if len(l) < 100: break
out.append(f"## Resultados de la liga ({len(res)} partidos)\n")
for r in sorted(res): out.append(f"{r[0]} {r[1]} {r[3]}-{r[4]} {r[2]}")
h2h = lista(pedir("/head-2-head", {"teamIdOne": loc["id"], "teamIdTwo": vis["id"]}))
out.append("\n## H2H\n")
for p in h2h: out.append(f"{p.get('date','')[:10]} {p['homeTeam']['name']} {((p.get('state') or {}).get('score') or {}).get('current')} {p['awayTeam']['name']}")
for eq in (loc, vis):
    ult = lista(pedir("/last-five-games", {"teamId": eq["id"]}))
    out.append(f"\n## Últimos de {eq['name']}\n")
    for p in ult: out.append(f"{p.get('date','')[:10]} {p['homeTeam']['name']} {((p.get('state') or {}).get('score') or {}).get('current')} {p['awayTeam']['name']} ({(p.get('league') or {}).get('name')})")
od = pedir("/odds", {"matchId": partido["id"], "oddsType": "prematch"})
out.append("\n## Cuotas (casa: mercado -> valores)\n")
for blk in lista(od):
    for o in (blk.get("odds") or []):
        m = o.get("market") or ""
        if any(k in m for k in ("Full Time Result", "Both Teams To Score", "Over/Under", "Total Goals", "Match Winner")):
            out.append(f"{o.get('bookmakerName')}: {m} -> " + ", ".join(f"{v.get('value')} {v.get('odd')}" for v in (o.get('values') or [])))
out.append(f"\nLlamadas: {n[0]}")
open("modelos/ligas_america/api_partido.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out[:80]))
