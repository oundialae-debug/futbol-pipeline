"""
Datos para pronosticar UN partido de una liga que no está en el proyecto
(27/09/2026: Gimnasia y Tiro - Atlético de Rafaela, Primera Nacional de
Argentina). Tema aparte de ambos marcan y de selecciones.

Llamadas (unas 20, el usuario dio permiso):
  1. /leagues?countryName=PAIS -> id de la liga (por nombre EXACTO; si no, avisa)
  2. /matches?leagueId&season (paginado) -> resultados de la temporada
  3. el partido pedido (por nombre de equipo, contiene LOCAL / VISITANTE)
  4. /odds del partido, /matches/{id} (árbitro), /lineups/{id} (once, si ya está)
  5. /box-score de los últimos N_BOX partidos terminados de cada equipo
     (nota, minutos y estadísticas de cada jugador)
Guarda la respuesta ENTERA en data/sueltos/<carpeta>/raw y tablas planas.
"""
import os
import json
import time
import requests
import pandas as pd

HEADERS = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}   # nunca se imprime
BASE = "https://soccer.highlightly.net"
PAIS = os.environ.get("PAIS", "Argentina")
LIGA_NOMBRE = os.environ.get("LIGA_NOMBRE", "Primera Nacional")
TEMPORADA = int(os.environ.get("TEMPORADA", "2026"))
LOCAL = os.environ.get("LOCAL", "Gimnasia")
VISITANTE = os.environ.get("VISITANTE", "Rafaela")
N_BOX = int(os.environ.get("N_BOX", "6"))
TOPE = int(os.environ.get("TOPE_LLAMADAS", "40"))
CARPETA = f"data/sueltos/{os.environ.get('CARPETA', 'gimnasia_tiro_rafaela')}"
RAW = f"{CARPETA}/raw"
llamadas = [0]


def pedir(path, params=None, nombre=None):
    if llamadas[0] >= TOPE:
        print(f"  [tope {TOPE}] {path}"); return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(BASE + path, headers=HEADERS, params=params, timeout=30)
        except Exception as e:
            print(f"  [sin respuesta: {type(e).__name__}] {path}"); time.sleep(3); continue
        if r.status_code == 429:
            print(f"  [429] {path}"); time.sleep(5); continue
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] {path} {params or ''}"); return None
        j = r.json()
        if nombre:
            json.dump(j, open(f"{RAW}/{nombre}.json", "w"), ensure_ascii=False)
        return j
    return None


def lista(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def estado(p):
    e = p.get("state")
    return str((e.get("description") if isinstance(e, dict) else e) or "")


def marcador(p):
    s = ((p.get("state") or {}).get("score") or {}).get("current") if isinstance(p.get("state"), dict) else None
    try:
        a, b = str(s).split("-")
        return int(a), int(b)
    except Exception:
        return None, None


def main():
    os.makedirs(RAW, exist_ok=True)
    ligas = lista(pedir("/leagues", {"countryName": PAIS, "limit": 100}, "ligas"))
    print(f"Ligas de {PAIS}: " + "; ".join(f"{l.get('name')} ({l.get('id')})" for l in ligas if isinstance(l, dict)))
    cand = [l for l in ligas if isinstance(l, dict) and str(l.get("name", "")).strip().lower() == LIGA_NOMBRE.lower()]
    if not cand:
        cand = [l for l in ligas if isinstance(l, dict) and LIGA_NOMBRE.lower() in str(l.get("name", "")).lower()]
    if len(cand) != 1:
        print(f"[!] {len(cand)} ligas encajan con '{LIGA_NOMBRE}': no sigo a ciegas."); return
    lid = cand[0]["id"]
    print(f"Liga: {cand[0].get('name')} id {lid}")
    ps, off = [], 0
    while True:
        lote = lista(pedir("/matches", {"leagueId": lid, "season": TEMPORADA, "limit": 100, "offset": off}, f"partidos_{off}"))
        lote = [p for p in lote if isinstance(p, dict) and p.get("id")]
        ps += lote
        if len(lote) < 100:
            break
        off += 100
    filas = [{"match_id": p["id"], "fecha": p.get("date"), "ronda": p.get("round"),
              "local_id": (p.get("homeTeam") or {}).get("id"), "local": (p.get("homeTeam") or {}).get("name"),
              "visitante_id": (p.get("awayTeam") or {}).get("id"), "visitante": (p.get("awayTeam") or {}).get("name"),
              "goles_l": marcador(p)[0], "goles_v": marcador(p)[1], "estado": estado(p)} for p in ps]
    d = pd.DataFrame(filas).drop_duplicates("match_id").sort_values("fecha")
    d.to_csv(f"{CARPETA}/temporada.csv", index=False)
    fin = d[d.estado.str.lower().str.contains("finish")]
    print(f"Temporada {TEMPORADA}: {len(d)} partidos, {len(fin)} terminados")
    ok = d[d.local.str.contains(LOCAL, case=False, na=False) & d.visitante.str.contains(VISITANTE, case=False, na=False)
           & ~d.estado.str.lower().str.contains("finish")]
    if ok.empty:
        print(f"[!] No encuentro {LOCAL} - {VISITANTE} sin jugar en la temporada."); return
    m = ok.iloc[0]
    mid = int(m.match_id)
    print(f"Partido: {m.local} - {m.visitante}, {m.fecha}, id {mid}, estado {m.estado}")
    pedir(f"/matches/{mid}", nombre="partido")
    pedir("/odds", {"matchId": mid, "oddsType": "prematch"}, "cuotas")
    pedir(f"/lineups/{mid}", nombre="lineups")
    for tid in (int(m.local_id), int(m.visitante_id)):
        suyos = fin[(fin.local_id == tid) | (fin.visitante_id == tid)].tail(N_BOX)
        for x in suyos.match_id:
            if not os.path.exists(f"{RAW}/boxscore_{x}.json"):
                pedir(f"/box-score/{x}", nombre=f"boxscore_{x}")
    json.dump({"liga_id": lid, "match_id": mid, "local": m.local, "local_id": int(m.local_id),
               "visitante": m.visitante, "visitante_id": int(m.visitante_id), "fecha": m.fecha},
              open(f"{CARPETA}/partido.json", "w"), ensure_ascii=False, indent=1)
    print(f"Llamadas: {llamadas[0]}")


if __name__ == "__main__":
    main()
