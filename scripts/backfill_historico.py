"""
TRAER LA HISTORIA HACIA ATRÁS: la base de entrenamiento

POR QUÉ ESTO SE PUEDE HACER HOY
-------------------------------
Había dicho que para usar el inventario nuevo tocaba esperar meses
recolectando. Eso solo vale para alineación, árbitro y tiempo, que la API sirve
en una ventana de 40 minutos antes a 120 después y no se pueden recuperar.

Todo lo demás -- resultado, córners, tarjetas, faltas, xG, posesión, tiros --
sale de `/statistics/{matchId}`, que funciona sobre partidos YA JUGADOS sin
límite de ventana. O sea que la base de entrenamiento se puede construir hoy,
temporadas enteras, y no hay que esperar a nada.

QUÉ GUARDA
----------
Una fila por partido terminado de las seis ligas, con las estadísticas de los
dos equipos. Los nombres de las estadísticas son los EXACTOS que devuelve la
API, comprobados contra datos reales en el censo del 20/09:

    Corners, Fouls, Yellow cards, Red cards, Expected Goals, Possession,
    Shots on target, Shots off target, Crosses, Offsides, Total passes...

Nada de adivinar el nombre: este repo ya perdió una semana buscando "to" en
un mercado que se llamaba "First Team To Score".

REANUDABLE Y CON TOPE
---------------------
Guarda cada N partidos y no vuelve a pedir lo que ya está en el CSV, así que
se puede lanzar muchas veces y va completando. El tope de llamadas evita
comerse la cuota del día de una sentada.

CUENTA LO QUE FALTA, EN VOZ ALTA
--------------------------------
Un partido sin estadísticas no se descarta en silencio: se cuenta y se
informa. Si de pronto media liga viene sin datos hay que enterarse, no
descubrirlo como un hueco raro tres pasos más adelante.
"""
import os
import csv
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

# Por ID, nunca por nombre: hay Serie A en Italia y en Brasil
LIGAS = {
    33973: "Premier League", 119924: "La Liga", 115669: "Serie A",
    67162: "Bundesliga", 52695: "Ligue 1", 121085: "Segunda",
}

RUTA = "data/historico_partidos.csv"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "5500"))
TEMPORADAS = [int(x) for x in os.environ.get("TEMPORADAS", "2026,2025").split(",")]

# Los nombres EXACTOS que devuelve /statistics, del censo del 20/09/2026.
# Si la API cambiara alguno, `sin_estadistica` lo cantaría.
ESTADISTICAS = [
    "Corners", "Fouls", "Yellow cards", "Red cards", "Expected Goals",
    "Expected Assists", "Possession", "Shots on target", "Shots off target",
    "Blocked shots", "Shots within penalty area", "Shots outside penalty area",
    "Shots accuracy", "Crosses", "Successful Crosses", "Offsides",
    "Total passes", "Successful passes", "Passes Into Final Third",
    "Key Passes", "Big Chances Created", "Aerial Duels",
    "Successful Aerial Duels", "Tackles", "Successful Tackles",
    "Interceptions", "Clearances", "Dribbles", "Successful Dribbles",
    "Goalkeeper saves", "Free Kicks", "Throw-Ins", "Goal Kicks",
]

llamadas = [0]
sin_estadistica = []
ligas_vacias = []      # una liga que no devuelve NADA es un ID malo, no un hueco


def pedir(path, params=None):
    if llamadas[0] >= TOPE_LLAMADAS:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS,
                             params=params, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1))
            continue
        if r.status_code == 429:          # demasiadas por minuto
            time.sleep(5)
            continue
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except Exception:
            return None
    return None


def desempaquetar(d):
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


def goles(p):
    """El marcador viene como cadena '1 - 3' dentro de state.score.current."""
    e = p.get("state") or {}
    s = (e.get("score") or {}).get("current") if isinstance(e, dict) else None
    if not s or "-" not in str(s):
        return None, None
    try:
        a, b = str(s).split("-")
        return int(a.strip()), int(b.strip())
    except Exception:
        return None, None


def estadisticas_de(match_id):
    """{id_equipo: {nombre: valor}}. Vacío si la API no las tiene."""
    j = pedir(f"/statistics/{match_id}")
    fuera = {}
    for eq in desempaquetar(j) if j else []:
        tid = (eq.get("team") or {}).get("id")
        if tid is None:
            continue
        fuera[tid] = {s.get("displayName"): s.get("value")
                      for s in (eq.get("statistics") or [])}
    return fuera


def columnas():
    base = ["match_id", "fecha", "liga_id", "liga", "temporada", "ronda",
            "local_id", "local", "visitante_id", "visitante", "goles_l",
            "goles_v"]
    for lado in ("l", "v"):
        for s in ESTADISTICAS:
            base.append(f"{lado}_{s.replace(' ', '_').lower()}")
    return base


def ya_guardados():
    if not os.path.exists(RUTA):
        return set()
    with open(RUTA, newline="", encoding="utf-8") as f:
        return {fila["match_id"] for fila in csv.DictReader(f)}


def main():
    os.makedirs("data", exist_ok=True)
    vistos = ya_guardados()
    print(f"Ya había {len(vistos)} partidos guardados. "
          f"Tope de esta pasada: {TOPE_LLAMADAS} llamadas.\n")

    cols = columnas()
    nuevo = not os.path.exists(RUTA)
    f = open(RUTA, "a", newline="", encoding="utf-8")
    escritor = csv.DictWriter(f, fieldnames=cols)
    if nuevo:
        escritor.writeheader()

    añadidos = 0
    try:
        for temporada in TEMPORADAS:
            for liga_id, liga in LIGAS.items():
                if llamadas[0] >= TOPE_LLAMADAS:
                    break
                encontrados = guardados = 0
                offset = 0
                while llamadas[0] < TOPE_LLAMADAS:
                    j = pedir("/matches", {"leagueId": liga_id,
                                           "season": temporada,
                                           "limit": 100, "offset": offset})
                    lote = desempaquetar(j) if j else []
                    if not lote:
                        break
                    for p in lote:
                        encontrados += 1
                        mid = str(p.get("id"))
                        if mid in vistos or not terminado(p):
                            continue
                        gl, gv = goles(p)
                        if gl is None:
                            continue
                        loc = p.get("homeTeam") or {}
                        vis = p.get("awayTeam") or {}
                        est = estadisticas_de(p["id"])
                        if not est:
                            sin_estadistica.append((liga, mid))
                            continue
                        fila = {
                            "match_id": mid, "fecha": p.get("date"),
                            "liga_id": liga_id, "liga": liga,
                            "temporada": temporada, "ronda": p.get("round"),
                            "local_id": loc.get("id"), "local": loc.get("name"),
                            "visitante_id": vis.get("id"),
                            "visitante": vis.get("name"),
                            "goles_l": gl, "goles_v": gv,
                        }
                        for lado, tid in (("l", loc.get("id")),
                                          ("v", vis.get("id"))):
                            d = est.get(tid, {})
                            for s in ESTADISTICAS:
                                fila[f"{lado}_{s.replace(' ', '_').lower()}"] = d.get(s)
                        escritor.writerow(fila)
                        vistos.add(mid)
                        guardados += 1
                        añadidos += 1
                    if len(lote) < 100:
                        break
                    offset += 100
                    f.flush()
                aviso = ""
                if encontrados == 0:
                    ligas_vacias.append((temporada, liga, liga_id))
                    aviso = "   <== VACIA, el ID no devuelve nada"
                print(f"  {temporada} {liga:16s} vistos {encontrados:4d}  "
                      f"nuevos {guardados:4d}  (llamadas {llamadas[0]}){aviso}")
    finally:
        f.close()

    print(f"\n{añadidos} partidos nuevos. Total en {RUTA}: {len(vistos)}.")
    print(f"Llamadas gastadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if sin_estadistica:
        print(f"\n[!] {len(sin_estadistica)} partidos TERMINADOS sin "
              f"estadísticas. No es normal si son muchos:")
        for liga, mid in sin_estadistica[:10]:
            print(f"      {liga} {mid}")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("\n[!] Tope alcanzado: queda historia por traer. "
              "Vuelve a lanzarlo, continúa donde lo dejó.")

    # Una liga que devuelve cero partidos no es un hueco: es un ID equivocado.
    # La primera version solo contaba los partidos sin estadisticas, y la
    # Segunda se quedo fuera entera sin que nadie se enterara.
    if ligas_vacias:
        print("\n" + "!" * 68)
        print("LIGAS QUE NO DEVOLVIERON NI UN PARTIDO:")
        for temporada, liga, lid in ligas_vacias:
            print(f"    {temporada}  {liga} (id {lid})")
        print("\nUn ID que no devuelve nada no da error HTTP: devuelve una")
        print("lista vacia. Corre scripts/buscar_ligas.py para ver los IDs")
        print("buenos por pais.")
        print("!" * 68)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
