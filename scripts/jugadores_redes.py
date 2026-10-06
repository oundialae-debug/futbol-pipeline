"""Estadísticas de jugadores de las 5 grandes para las plantillas de redes (jugador vs jugador, rankings). 06/10/2026.

Usuario (06/10): "actívalo", recordando el límite de ~100 llamadas/día de Highlightly y que haya respaldo.
Por eso hay DOS fuentes y la principal NO gasta cuota de Highlightly:
  understat   -> totales de temporada por jugador (goles, xG, asistencias, xA, tiros, pases clave, minutos):
                 5 peticiones a understat.com (una por liga), web pública, sin clave. -> data/redes/jugadores_temporada.csv
  highlightly -> /box-score de los partidos de AYER de las 5 grandes que falten (nota y 37 estadísticas por jugador),
                 con TOPE_LLAMADAS bajo (20 por defecto) para no comerse la cuota de ambos_marcan_diario (~80/día).
                 Añade a data/historico_xg_jugador.csv (mismo formato) y guarda los nombres en data/redes/jugadores_nombres.csv.
Si understat falla, las plantillas tiran de lo acumulado de Highlightly (más lento pero suyo); si Highlightly no
llega, se queda con understat. Uso: python3 scripts/jugadores_redes.py understat|highlightly
"""
import csv, json, os, re, sys, time
from datetime import date, timedelta
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
SAL = ROOT / "data/redes"
LIGAS_US = {"EPL": "Premier League", "La_liga": "La Liga", "Bundesliga": "Bundesliga",
            "Serie_A": "Serie A", "Ligue_1": "Ligue 1"}
GRANDES = set(LIGAS_US.values())
UA = {"User-Agent": "Mozilla/5.0 (2yellow data; contact via GitHub oundialae-debug)"}


def temporada_us(hoy=None):
    hoy = hoy or date.today()
    return hoy.year if hoy.month >= 7 else hoy.year - 1


def understat():
    t = temporada_us()
    filas = []
    for code, liga in LIGAS_US.items():
        jug = None
        try:  # formato nuevo (JSON por AJAX)
            r = requests.get(f"https://understat.com/getLeagueData/{code}/{t}",
                             headers={**UA, "X-Requested-With": "XMLHttpRequest", "Referer": f"https://understat.com/league/{code}/{t}"}, timeout=30)
            if r.ok and r.text.strip().startswith("{"):
                jug = r.json().get("players")
        except Exception as ex:
            print("getLeagueData", code, ex)
        if jug is None:  # formato antiguo: JSON escapado dentro del HTML
            try:
                r = requests.get(f"https://understat.com/league/{code}/{t}", headers=UA, timeout=30)
                m = re.search(r"playersData\s*=\s*JSON\.parse\('(.+?)'\)", r.text)
                if m:
                    jug = json.loads(m.group(1).encode().decode("unicode_escape").encode("latin1").decode("utf-8"))
            except Exception as ex:
                print("html", code, ex)
        if not jug:
            print(f"[!] understat sin datos para {liga}"); continue
        for p in jug:
            filas.append({"jugador": p.get("player_name"), "equipo": p.get("team_title"), "liga": liga, "temporada": t,
                          "partidos": p.get("games"), "minutos": p.get("time"), "goles": p.get("goals"),
                          "xg": p.get("xG"), "asistencias": p.get("assists"), "xa": p.get("xA"), "tiros": p.get("shots"),
                          "pases_clave": p.get("key_passes"), "npg": p.get("npg"), "npxg": p.get("npxG"),
                          "amarillas": p.get("yellow_cards"), "posicion": p.get("position"), "fuente": "understat"})
        print(f"{liga}: {len(jug)} jugadores")
        time.sleep(2)
    if not filas:
        sys.exit("[!] understat no devolvió nada: se mantiene el archivo anterior")
    SAL.mkdir(parents=True, exist_ok=True)
    with open(SAL / "jugadores_temporada.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader(); w.writerows(filas)
    print(f"OK {len(filas)} filas -> data/redes/jugadores_temporada.csv")


def highlightly():
    sys.path.insert(0, str(ROOT / "scripts"))
    os.environ.setdefault("TOPE_LLAMADAS", "20")
    import backfill_xg_jugador as B  # reutiliza pedir() con tope, reintentos y corte por cuota agotada
    import pandas as pd
    B.TOPE_LLAMADAS = int(os.environ["TOPE_LLAMADAS"])
    h = pd.read_csv(ROOT / "data/historico_partidos.csv", low_memory=False)
    desde = str(date.today() - timedelta(days=int(os.environ.get("DIAS", "3"))))
    h = h[h.liga.isin(GRANDES) & (h.fecha.astype(str).str[:10] >= desde) & h.goles_l.notna()]
    vistos = B.ya_tengo()
    pend = [str(m) for m in h.sort_values("fecha", ascending=False).match_id if str(m) not in vistos]
    print(f"{len(pend)} partidos de las 5 grandes sin box-score desde {desde}; tope {B.TOPE_LLAMADAS} llamadas")
    rn = SAL / "jugadores_nombres.csv"
    nombres = {}
    if rn.exists():
        with open(rn, newline="", encoding="utf-8") as f:
            nombres = {r["jugador_id"]: r for r in csv.DictReader(f)}
    f = open(ROOT / B.RUTA_SALIDA, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=B.COLUMNAS)
    n = 0
    try:
        for mid in pend:
            j = B.pedir(f"/box-score/{mid}")
            if j is None:
                if B.CUOTA_AGOTADA[0] or B.llamadas[0] >= B.TOPE_LLAMADAS: break
                continue
            for eq in B.desempaquetar(j):
                if not isinstance(eq, dict): continue
                team = eq.get("team") or {}
                for p in eq.get("players") or []:
                    s = B.estadisticas_de(p)
                    fila = {"match_id": mid, "equipo_id": team.get("id"), "jugador_id": p.get("id"), "posicion": p.get("position"),
                            "minutos": p.get("minutesPlayed"), "suplente": p.get("isSubstitute"), "nota": p.get("matchRating"),
                            "fueras_de_juego": p.get("offsides"), **{k: s.get(k) for k in B.ESTADISTICAS}}
                    w.writerow(fila)
                    if p.get("id") is not None:
                        nombres[str(p["id"])] = {"jugador_id": p["id"], "nombre": p.get("name") or p.get("fullName") or "",
                                                 "equipo_id": team.get("id"), "equipo": team.get("name") or ""}
            n += 1
    finally:
        f.close()
    SAL.mkdir(parents=True, exist_ok=True)
    with open(rn, "w", newline="", encoding="utf-8") as g:
        ww = csv.DictWriter(g, fieldnames=["jugador_id", "nombre", "equipo_id", "equipo"])
        ww.writeheader(); ww.writerows(nombres.values())
    print(f"OK {n} partidos con box-score; llamadas {B.llamadas[0]}/{B.TOPE_LLAMADAS}; {len(nombres)} nombres")


if __name__ == "__main__":
    {"understat": understat, "highlightly": highlightly}[sys.argv[1]]()
