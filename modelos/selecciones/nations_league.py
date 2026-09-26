"""
Ciclo de datos de la Nations League, TODAS las selecciones (26/09/2026).
Tema aparte del proyecto de ambos marcan. Lo lanza nations_league_ciclo.yml
(varias veces al día); después, en local o en la misma Action,
pronostico_selecciones.py y evaluar_selecciones.py.

Pasos (todos reanudables: lo que está en data/selecciones/raw/ no se repide):
  1. calendario   la temporada entera de la liga 5039 (se refresca SIEMPRE:
                  así entran los resultados nuevos). -> nl_calendario.csv
  2. historial    por cada selección del calendario, todos sus partidos desde
                  2025 en cualquier competición (temporadas 2024-2026: la API
                  mete la clasificación del Mundial en 2024). Una vez por
                  selección; REFRESCAR_EQUIPOS=1 vuelve a pedir la temporada
                  en curso (amistosos nuevos).
  3. detalles     /statistics, /lineups y /box-score de cada partido terminado.
  4. previa       partidos de la Nations League que empiezan en las próximas
                  HORIZONTE_HORAS: cuotas (todas), /matches/{id} (árbitro) y
                  /lineups (el once, si ya está). Escribe equipos.json (cruces
                  de la jornada), cuotas_hoy.csv y alineaciones_hoy.csv.
  5. aplanar      reconstruye partidos.csv, estadisticas_partido.csv,
                  alineaciones.csv y jugadores_partido.csv desde raw/.
Orden de prioridad con el tope de llamadas: calendario, previa, detalles de
partidos recientes, historial. Lo que no quepa sigue en la siguiente pasada.
"""
import os
import json
import glob
import time
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd

HEADERS = {"x-rapidapi-key": os.environ.get("HIGHLIGHTLY_API_KEY", "")}   # nunca se imprime
BASE_URL = "https://soccer.highlightly.net"
LIGA = int(os.environ.get("LIGA", "5039"))
TEMPORADA = 2026   # temporada en curso de la API (se vuelve a pedir con REFRESCAR_EQUIPOS)
# SOLO se descarga el historial de las selecciones que juegan en los próximos
# VENTANA_DIAS (petición del usuario, 26/09: no las ~55 de golpe). Cada ventana
# internacional nueva entra sola cuando se acerca.
VENTANA_DIAS = int(os.environ.get("VENTANA_DIAS", "7"))
DIAS_ATRAS = int(os.environ.get("DIAS_ATRAS", "3"))
TEMPORADAS_HIST = (2024, 2025, 2026)
DESDE = "2025-01-01"
TOPE = int(os.environ.get("TOPE_LLAMADAS", "600"))
HORIZONTE_HORAS = int(os.environ.get("HORIZONTE_HORAS", "36"))
REFRESCAR_EQUIPOS = os.environ.get("REFRESCAR_EQUIPOS") == "1"
CARPETA = "data/selecciones"
RAW = f"{CARPETA}/raw"
llamadas = [0]


def pedir(path, params=None, nombre=None, forzar=False):
    """Lee raw/<nombre>.json si existe (salvo forzar); si no, pide y lo guarda."""
    ruta = f"{RAW}/{nombre}.json" if nombre else None
    if ruta and not forzar and os.path.exists(ruta):
        return json.load(open(ruta, encoding="utf-8"))
    if llamadas[0] >= TOPE or not HEADERS["x-rapidapi-key"]:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
        except Exception as e:
            print(f"  [sin respuesta: {type(e).__name__}] {path}")
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            print(f"  [429: límite de la API] {path}")   # antes callaba: 6 minutos sin decir nada
            time.sleep(5); continue
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] {path} {params or ''}")
            return None
        try:
            j = r.json()
        except Exception:
            return None
        if ruta:
            json.dump(j, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
        return j
    return None


def lista(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def terminado(p):
    e = p.get("state")
    d = (e.get("description") if isinstance(e, dict) else e) or ""
    return "finish" in str(d).lower()


def marcador(p):
    s = ((p.get("state") or {}).get("score") or {}).get("current") if isinstance(p.get("state"), dict) else None
    try:
        a, b = str(s).split("-")
        return int(a), int(b)
    except Exception:
        return None, None


def clave(nombre):
    return nombre.replace(" ", "_").lower()


def paginas(path, params, prefijo, forzar):
    out, offset = [], 0
    while True:
        j = pedir(path, {**params, "limit": 100, "offset": offset}, f"{prefijo}_{offset}", forzar=forzar)
        lote = [p for p in lista(j) if isinstance(p, dict) and p.get("id")] if j else []
        out += lote
        if len(lote) < 100:
            return out
        offset += 100


def calendario():
    """Partidos de la Nations League día a día, de DIAS_ATRAS días atrás a VENTANA_DIAS
    por delante (una llamada por día, siempre refrescada: así entran los resultados).
    La consulta por temporada (leagueId+season) devolvió 0 partidos el 26/09/2026;
    por día sí funciona (es como se encontraron los partidos de esa noche)."""
    hoy = datetime.now(timezone.utc).date()
    ps = []
    for d in range(-DIAS_ATRAS, VENTANA_DIAS + 1):
        dia = (hoy + timedelta(days=d)).isoformat()
        j = pedir("/matches", {"leagueId": LIGA, "date": dia, "timezone": "UTC"}, f"nl_dia_{dia}", forzar=True)
        if j is None:   # sin API: lo último que se bajó de ese día
            j = pedir("/matches", None, f"nl_dia_{dia}")
        ps += [p for p in lista(j) if isinstance(p, dict) and p.get("id")] if j else []
    filas = [{"match_id": p["id"], "fecha": p.get("date"), "ronda": p.get("round"),
              "local_id": (p.get("homeTeam") or {}).get("id"), "local": (p.get("homeTeam") or {}).get("name"),
              "visitante_id": (p.get("awayTeam") or {}).get("id"),
              "visitante": (p.get("awayTeam") or {}).get("name"),
              "goles_l": marcador(p)[0], "goles_v": marcador(p)[1], "terminado": terminado(p)} for p in ps]
    d = pd.DataFrame(filas, columns=["match_id", "fecha", "ronda", "local_id", "local", "visitante_id",
                                     "visitante", "goles_l", "goles_v", "terminado"]).drop_duplicates("match_id")
    if len(d):
        ruta = f"{CARPETA}/nl_calendario.csv"
        viejo = pd.read_csv(ruta) if os.path.exists(ruta) else d.iloc[:0]
        pd.concat([viejo[~viejo.match_id.isin(d.match_id)], d]).sort_values("fecha").to_csv(ruta, index=False)
    return d


def historial(nombre, tid):
    k = clave(nombre)
    if not os.path.exists(f"{RAW}/equipo_{k}.json"):
        pedir(f"/teams/{tid}", nombre=f"equipo_{k}")
    for temp in TEMPORADAS_HIST:
        for lado in ("homeTeamId", "awayTeamId"):
            paginas("/matches", {lado: tid, "season": temp}, f"partidos_{k}_{temp}_{lado}",
                    forzar=REFRESCAR_EQUIPOS and temp == TEMPORADA)


def detalles(mid):
    for ruta, nombre in ((f"/statistics/{mid}", f"statistics_{mid}"), (f"/lineups/{mid}", f"lineups_{mid}"),
                         (f"/box-score/{mid}", f"boxscore_{mid}")):
        pedir(ruta, nombre=nombre)


def todos_los_partidos():
    """Todos los partidos vistos en raw (listas de equipos y calendario), el más nuevo gana."""
    ps = {}
    rutas = sorted(glob.glob(f"{RAW}/partidos_*.json")) + sorted(glob.glob(f"{RAW}/nl_*.json"))
    for ruta in rutas:
        for p in lista(json.load(open(ruta, encoding="utf-8"))):
            if isinstance(p, dict) and p.get("id") and str(p.get("date", ""))[:10] >= DESDE:
                ps[p["id"]] = p
    return ps


def previa(cal):
    ahora = datetime.now(timezone.utc)
    cal = cal.assign(dt=pd.to_datetime(cal.fecha, utc=True, errors="coerce"))
    prox = cal[~cal.terminado & (cal.dt >= ahora - timedelta(hours=2))
               & (cal.dt <= ahora + timedelta(hours=HORIZONTE_HORAS))]
    cruces, equipos, cuotas, onces = [], {}, [], []
    for _, p in prox.sort_values("dt").iterrows():
        mid = int(p.match_id)
        cruces.append([p.local, p.visitante, mid, str(p.fecha)])
        equipos[p.local], equipos[p.visitante] = int(p.local_id), int(p.visitante_id)
        pedir(f"/matches/{mid}", nombre=f"partido_hoy_{mid}", forzar=True)
        o = pedir("/odds", {"matchId": mid, "oddsType": "prematch"}, f"cuotas_hoy_{mid}", forzar=True)
        for b in lista(o) if o else []:
            for c in (b.get("odds") or []) if isinstance(b, dict) else []:
                for v in c.get("values") or []:
                    try:
                        cuotas.append({"partido": f"{p.local} - {p.visitante}", "match_id": mid,
                                       "mercado": c.get("market"), "casa": c.get("bookmakerName"),
                                       "lado": str(v.get("value")), "cuota": float(v.get("odd"))})
                    except (TypeError, ValueError):
                        pass
        lu = pedir(f"/lineups/{mid}", nombre=f"lineups_hoy_{mid}", forzar=True)
        lu = lu[0] if isinstance(lu, list) and lu else lu
        for lado in ("homeTeam", "awayTeam"):
            t = (lu or {}).get(lado) or {} if isinstance(lu, dict) else {}
            for linea in t.get("initialLineup") or []:
                for j in (linea if isinstance(linea, list) else [linea]):
                    if isinstance(j, dict):
                        onces.append({"match_id": mid, "equipo": t.get("name"), "equipo_id": t.get("id"),
                                      "formacion": t.get("formation"), "jugador_id": j.get("id"),
                                      "jugador": j.get("name"), "posicion": j.get("position")})
    json.dump({"equipos": equipos, "cruces": cruces, "generado": ahora.isoformat()},
              open(f"{CARPETA}/equipos.json", "w"), ensure_ascii=False, indent=1)
    if cuotas:
        pd.DataFrame(cuotas).to_csv(f"{CARPETA}/cuotas_hoy.csv", index=False)
    # alineaciones_hoy.csv: se conservan onces escritos a mano para estos partidos
    # (la API no los tuvo el 26/09) salvo que la API ya traiga los suyos
    ruta = f"{CARPETA}/alineaciones_hoy.csv"
    previos = pd.read_csv(ruta) if os.path.exists(ruta) and os.path.getsize(ruta) > 5 else pd.DataFrame()
    nuevos = pd.DataFrame(onces)
    ids = {c[2] for c in cruces}
    if len(previos):
        previos = previos[previos.match_id.isin(ids)]
        if len(nuevos):
            previos = previos[~previos.match_id.isin(nuevos.match_id)]
    pd.concat([previos, nuevos]).to_csv(ruta, index=False)
    print(f"Previa: {len(cruces)} partidos en las próximas {HORIZONTE_HORAS} h, {len(cuotas)} cuotas, "
          f"onces de la API: {nuevos.match_id.nunique() if len(nuevos) else 0} partidos")
    return cruces


def aplanar(partidos):
    filas_p, filas_est, filas_lu, filas_box = [], [], [], []
    leer = lambda n: json.load(open(f"{RAW}/{n}.json", encoding="utf-8")) if os.path.exists(f"{RAW}/{n}.json") else None
    for mid, p in sorted(partidos.items(), key=lambda kv: str(kv[1].get("date"))):
        gl, gv = marcador(p)
        filas_p.append({"match_id": mid, "fecha": str(p.get("date"))[:10],
                        "competicion": (p.get("league") or {}).get("name"),
                        "local_id": (p.get("homeTeam") or {}).get("id"), "local": (p.get("homeTeam") or {}).get("name"),
                        "visitante_id": (p.get("awayTeam") or {}).get("id"),
                        "visitante": (p.get("awayTeam") or {}).get("name"),
                        "goles_l": gl, "goles_v": gv, "terminado": terminado(p)})
        if not terminado(p):
            continue
        for eq in lista(leer(f"statistics_{mid}")):
            if isinstance(eq, dict):
                for s in eq.get("statistics") or []:
                    filas_est.append({"match_id": mid, "equipo_id": (eq.get("team") or {}).get("id"),
                                      "estadistica": s.get("displayName"), "valor": s.get("value")})
        lu = leer(f"lineups_{mid}")
        lu = lu[0] if isinstance(lu, list) and lu else lu
        if isinstance(lu, dict):
            for lado in ("homeTeam", "awayTeam"):
                t = lu.get(lado) or {}
                for linea in t.get("initialLineup") or []:
                    for j in (linea if isinstance(linea, list) else [linea]):
                        if isinstance(j, dict):
                            filas_lu.append({"match_id": mid, "equipo_id": t.get("id"), "formacion": t.get("formation"),
                                             "jugador_id": j.get("id"), "jugador": j.get("name"),
                                             "posicion": j.get("position")})
        for eq in lista(leer(f"boxscore_{mid}")):
            if not isinstance(eq, dict):
                continue
            tid = (eq.get("team") or {}).get("id")
            for j in eq.get("players") or []:
                st = j.get("statistics") or {}
                st = (st[0] if st else {}) if isinstance(st, list) else st
                filas_box.append({"match_id": mid, "equipo_id": tid, "jugador_id": j.get("id"),
                                  "jugador": j.get("name"), "posicion": j.get("position"),
                                  "minutos": j.get("minutesPlayed"), "suplente": j.get("isSubstitute"),
                                  "nota": j.get("matchRating"), **st})
    pd.DataFrame(filas_p).to_csv(f"{CARPETA}/partidos.csv", index=False)
    pd.DataFrame(filas_est).to_csv(f"{CARPETA}/estadisticas_partido.csv", index=False)
    pd.DataFrame(filas_lu).to_csv(f"{CARPETA}/alineaciones.csv", index=False)
    pd.DataFrame(filas_box).to_csv(f"{CARPETA}/jugadores_partido.csv", index=False)
    return pd.DataFrame(filas_p), len(filas_box)


def main():
    os.makedirs(RAW, exist_ok=True)
    cal = calendario()
    equipos = {}
    hoy = datetime.now(timezone.utc).date().isoformat()
    for _, p in cal[cal.fecha.astype(str).str[:10] >= hoy].sort_values("fecha").iterrows():
        equipos[p.local], equipos[p.visitante] = int(p.local_id), int(p.visitante_id)
    print(f"Nations League (liga {LIGA}), de {DIAS_ATRAS} días atrás a {VENTANA_DIAS} por delante: "
          f"{len(cal)} partidos ({int(cal.terminado.sum()) if len(cal) else 0} terminados). "
          f"Selecciones que juegan desde hoy: {len(equipos)}: {', '.join(sorted(equipos))}")
    if len(cal):
        previa(cal)
    else:
        print("[!] Sin calendario (ni de la API ni guardado): no se toca la previa ni equipos.json")
    # selecciones seguidas: las de la ventana de ahora y todas las de antes (su
    # historial ya está bajado). Solo sus partidos piden detalles.
    ruta_seg = f"{CARPETA}/selecciones_seguidas.json"
    seguidas = json.load(open(ruta_seg)) if os.path.exists(ruta_seg) else {}
    seguidas.update({"England": 9294, "Spain": 8443, "Czech Republic": 656054, "Croatia": 3337})
    seguidas.update(equipos)
    json.dump(seguidas, open(ruta_seg, "w"), ensure_ascii=False, indent=1)
    ids = set(seguidas.values())
    de_seguidas = lambda p: ((p.get("homeTeam") or {}).get("id") in ids or (p.get("awayTeam") or {}).get("id") in ids)
    # detalles: primero los partidos más recientes (los de la Nations League de ayer)
    for mid, p in sorted(todos_los_partidos().items(), key=lambda kv: str(kv[1].get("date")), reverse=True):
        if terminado(p) and de_seguidas(p):
            detalles(mid)
    # por orden de pitido: historial Y detalles de cada selección antes de pasar a
    # la siguiente. Antes se bajaba el historial de todas y después los detalles:
    # con ~50 selecciones y el tope por pasada, las que juegan mañana se habrían
    # pronosticado sin estadísticas (y sin avisar: el modelo da números igual).
    for nombre in equipos:
        historial(nombre, equipos[nombre])
        tid = equipos[nombre]
        propios = {}
        for ruta in glob.glob(f"{RAW}/partidos_{clave(nombre)}_*.json"):
            for p in lista(json.load(open(ruta, encoding="utf-8"))):
                if isinstance(p, dict) and p.get("id") and str(p.get("date", ""))[:10] >= DESDE:
                    propios[p["id"]] = p
        for mid, p in sorted(propios.items(), key=lambda kv: str(kv[1].get("date")), reverse=True):
            if terminado(p):
                detalles(mid)
    # los partidos de los historiales recién bajados también necesitan detalles
    ps = todos_los_partidos()
    for mid, p in sorted(ps.items(), key=lambda kv: str(kv[1].get("date")), reverse=True):
        if terminado(p) and de_seguidas(p):
            detalles(mid)
    d, n_box = aplanar(ps)
    faltan_hist = [n for n in equipos if not os.path.exists(f"{RAW}/partidos_{clave(n)}_2026_awayTeamId_0.json")]
    fin = d[d.terminado] if len(d) else d
    sin_det = [m for m in fin.match_id if not os.path.exists(f"{RAW}/boxscore_{m}.json")] if len(fin) else []
    print(f"Partidos desde {DESDE}: {len(d)} ({len(fin)} terminados), filas de jugador {n_box}. "
          f"Selecciones sin historial: {len(faltan_hist)}. Terminados sin detalles: {len(sin_det)}. "
          f"Llamadas {llamadas[0]} de {TOPE}.")
    if llamadas[0] >= TOPE:
        print("[!] Tope alcanzado: la siguiente pasada sigue donde lo dejó.")


if __name__ == "__main__":
    main()
