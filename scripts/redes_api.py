"""Descargas de Highlightly para los formatos de redes (2yellow XI, 2yellow Index). Usuario 06/10: "descarga de la
API todo lo que necesites" (la cuota aún es amplia; en ~1 semana pasa a 100/día).
  nombres -> vuelve a pedir /box-score de los partidos de la temporada en curso de las 5 grandes para guardar el NOMBRE
             de cada jugador (el backfill de xG lo tiraba) -> data/redes/jugadores_nombres.csv
  ucl     -> Champions League: busca su id, lista los partidos jugados de la temporada y baja su box-score
             -> data/redes/ucl_partidos.csv, data/redes/ucl_jugadores.csv (mismas columnas que historico_xg_jugador + jugador)
  popularidad -> NO usa Highlightly: interés en Google Trends (mundial, ago-2025 a sep-2026) de los nominados al
             Balón de Oro -> data/redes/popularidad_bdo.csv (usuario 07/10: la popularidad también vota; Google Trends,
             no Wikipedia). Trends compara 5 términos por consulta: Lamine Yamal va en todas como ancla y se reescala.
Tope con TOPE_LLAMADAS; reanudable (salta lo ya guardado)."""
import csv, json, os, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import backfill_xg_jugador as B  # noqa: E402  (pedir con tope/reintentos, ESTADISTICAS, COLUMNAS)

B.TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "400"))
SAL = ROOT / "data/redes"
GRANDES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
RN = SAL / "jugadores_nombres.csv"


def get(path, params=None):
    """pedir() de backfill_xg_jugador no admite params: los pego a la ruta."""
    if params:
        import urllib.parse
        path += "?" + urllib.parse.urlencode(params)
    return B.pedir(path)


def cargar_nombres():
    if RN.exists():
        with open(RN, newline="", encoding="utf-8") as f:
            return {r["jugador_id"]: r for r in csv.DictReader(f)}
    return {}


def guardar_nombres(n):
    SAL.mkdir(parents=True, exist_ok=True)
    with open(RN, "w", newline="", encoding="utf-8") as g:
        w = csv.DictWriter(g, fieldnames=["jugador_id", "nombre", "equipo_id", "equipo"])
        w.writeheader(); w.writerows(n.values())


def jugadores_de(j):
    for eq in B.desempaquetar(j) if j else []:
        if not isinstance(eq, dict):
            continue
        team = eq.get("team") or {}
        for p in eq.get("players") or []:
            yield team, p


def nombres():
    h = pd.read_csv(ROOT / "data/historico_partidos.csv", low_memory=False)
    h = h[(h.temporada == h.temporada.max()) & h.liga.isin(GRANDES) & h.goles_l.notna()]
    n = cargar_nombres()
    hechos_f = SAL / "nombres_partidos_hechos.txt"
    hechos = set(hechos_f.read_text().split()) if hechos_f.exists() else set()
    pend = [str(m) for m in h.sort_values("fecha", ascending=False).match_id if str(m) not in hechos]
    print(f"{len(pend)} partidos por repasar; tope {B.TOPE_LLAMADAS}")
    for mid in pend:
        j = B.pedir(f"/box-score/{mid}")
        if j is None:
            if B.CUOTA_AGOTADA[0] or B.llamadas[0] >= B.TOPE_LLAMADAS: break
            continue
        for team, p in jugadores_de(j):
            if p.get("id") is not None and p.get("name"):
                n[str(p["id"])] = {"jugador_id": p["id"], "nombre": p["name"], "equipo_id": team.get("id"), "equipo": team.get("name") or ""}
        hechos.add(mid)
    guardar_nombres(n)
    hechos_f.write_text("\n".join(sorted(hechos)))
    print(f"OK {len(n)} nombres; llamadas {B.llamadas[0]}")


def ucl():
    cfg = SAL / "ucl.json"
    info = json.loads(cfg.read_text()) if cfg.exists() else {}
    if not info.get("id"):
        for q in ({"leagueName": "UEFA Champions League"}, {"leagueName": "Champions League"}):
            for l in B.desempaquetar(get("/leagues", {**q, "limit": 50})):
                if isinstance(l, dict) and l.get("name") == "UEFA Champions League":
                    info = {"id": l["id"], "name": l["name"]}; break
            if info.get("id"): break
        if not info.get("id"):
            sys.exit("[!] no encuentro la Champions en /leagues")
        SAL.mkdir(parents=True, exist_ok=True); cfg.write_text(json.dumps(info))
    temporada = int(os.environ.get("TEMPORADA", "2026"))
    rp, rj = SAL / "ucl_partidos.csv", SAL / "ucl_jugadores.csv"
    partidos = pd.read_csv(rp) if rp.exists() else pd.DataFrame()
    filas, off = [], 0
    while True:
        lote = B.desempaquetar(get("/matches", {"leagueId": info["id"], "season": temporada, "limit": 100, "offset": off}))
        for m in lote:
            if not isinstance(m, dict): continue
            st = str((m.get("state") or {}).get("description", "")).lower()
            sc = (m.get("state") or {}).get("score") or {}
            ft = sc.get("current") or ""
            if "finished" not in st or "-" not in str(ft): continue
            gl, gv = [int(x) for x in str(ft).replace(" ", "").split("-")[:2]]
            filas.append({"match_id": m["id"], "fecha": m.get("date"), "ronda": m.get("round"),
                          "local_id": (m.get("homeTeam") or {}).get("id"), "local": (m.get("homeTeam") or {}).get("name"),
                          "visitante_id": (m.get("awayTeam") or {}).get("id"), "visitante": (m.get("awayTeam") or {}).get("name"),
                          "goles_l": gl, "goles_v": gv, "temporada": temporada})
        if len(lote) < 100: break
        off += 100
    nuevos = pd.DataFrame(filas)
    partidos = pd.concat([partidos, nuevos]).drop_duplicates("match_id", keep="last") if len(nuevos) else partidos
    partidos.to_csv(rp, index=False)
    print(f"Champions {temporada}: {len(partidos)} partidos jugados")
    ya = set(pd.read_csv(rj, usecols=["match_id"]).match_id.astype(str)) if rj.exists() else set()
    n = cargar_nombres()
    nuevo = not rj.exists()
    f = open(rj, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=B.COLUMNAS + ["jugador"])
    if nuevo: w.writeheader()
    try:
        for mid in partidos.sort_values("fecha", ascending=False).match_id.astype(str):  # lo más reciente primero
            if mid in ya: continue
            j = B.pedir(f"/box-score/{mid}")
            if j is None:
                if B.CUOTA_AGOTADA[0] or B.llamadas[0] >= B.TOPE_LLAMADAS: break
                continue
            for team, p in jugadores_de(j):
                s = B.estadisticas_de(p)
                w.writerow({"match_id": mid, "equipo_id": team.get("id"), "jugador_id": p.get("id"), "posicion": p.get("position"),
                            "minutos": p.get("minutesPlayed"), "suplente": p.get("isSubstitute"), "nota": p.get("matchRating"),
                            "fueras_de_juego": p.get("offsides"), "jugador": p.get("name"), **{k: s.get(k) for k in B.ESTADISTICAS}})
                if p.get("id") is not None and p.get("name"):
                    n[str(p["id"])] = {"jugador_id": p["id"], "nombre": p["name"], "equipo_id": team.get("id"), "equipo": team.get("name") or ""}
    finally:
        f.close()
    guardar_nombres(n)
    print(f"OK llamadas {B.llamadas[0]}")


def popularidad():
    """Google Trends (pytrends, no oficial): media de interés de cada nominado, reescalada con un ancla común."""
    import time
    from pytrends.request import TrendReq
    sys.path.insert(0, str(ROOT / "redes/plantillas"))
    from datos_rankings import NOMINADOS_BDO
    ancla = "Lamine Yamal"
    otros = [n for n in NOMINADOS_BDO if n != ancla]
    pt = TrendReq(hl="en-GB", tz=0, retries=3, backoff_factor=2)
    res = {ancla: 100.0}
    for k in range(0, len(otros), 4):
        grupo = otros[k:k + 4]
        for intento in range(4):
            try:
                pt.build_payload([ancla] + grupo, timeframe="2025-08-01 2026-09-30", geo="")
                d = pt.interest_over_time()
                break
            except Exception as ex:
                print(f"[!] {grupo}: {ex}"); time.sleep(30 * (intento + 1)); d = None
        if d is None or d.empty:
            continue
        a = d[ancla].mean() or 1
        for n in grupo:
            res[n] = round(d[n].mean() / a * 100, 2)   # interés relativo a Yamal (= 100)
        print(grupo, [res.get(n) for n in grupo])
        time.sleep(8)
    SAL.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"jugador": n, "trends": v} for n, v in res.items()]).to_csv(SAL / "popularidad_bdo.csv", index=False)


if __name__ == "__main__":
    {"nombres": nombres, "ucl": ucl, "popularidad": popularidad}[sys.argv[1]]()
