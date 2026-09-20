"""
CALENDARIO DEL MES: qué partidos hay y cuándo es su descanso.

Las seis ligas que interesan cotizan tarjetas en vivo, así que el trabajo no
es buscarlas: es saber de antemano a qué hora hay que mirar. Un descanso dura
quince minutos y no avisa.

Hasta ahora el comparador barría TODOS los partidos del mundo cada cuarto de
hora: dieciocho llamadas de barrido por pasada para encontrar los cuatro que
importan. Con el calendario hecho se va directo a los partidos del día por su
id, y el barrido sobra.

POR QUÉ LA TEMPORADA ENTERA Y NO TREINTA DÍAS SUELTOS
-----------------------------------------------------
/matches acepta leagueId + season y devuelve el calendario completo paginado.
Son unas pocas llamadas por liga. Pedir día a día serían treinta fechas por
nueve páginas: cientos de llamadas para el mismo dato.

LA HORA DEL DESCANSO ES UNA ESTIMACIÓN
--------------------------------------
Se calcula como el saque inicial más 45 minutos de juego, más el descuento.
El descuento varía, así que la ventana se deja ancha (de +45 a +62) y quien
la use tiene que comprobar el estado de verdad antes de calcular nada: el
modelo solo vale con el partido parado en el intermedio, no "por la hora".
"""
import os
import re
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_LIGAS = "data/ligas.json"
RUTA_CALENDARIO = "data/calendario.csv"
RUTA_INFORME = "calendario.md"

DIAS = int(os.environ.get("DIAS", "30"))
TEMPORADA = int(os.environ.get("TEMPORADA", "2025"))

# Las seis que cotizan tarjetas en vivo. Cada entrada lleva las formas en que
# la API puede nombrarlas y el país, porque "Serie A" y "Segunda División"
# existen en media docena de países y sin filtrar por país se cuela Brasil.
OBJETIVO = {
    "La Liga":          {"patrones": [r"^la ?liga$", r"^primera divisi[oó]n$"],   "pais": ["spain", "españa"]},
    "Segunda División": {"patrones": [r"^segunda divisi[oó]n$", r"^laliga 2$"],   "pais": ["spain", "españa"]},
    "Premier League":   {"patrones": [r"^premier league$"],                       "pais": ["england", "inglaterra"]},
    "Serie A":          {"patrones": [r"^serie a$"],                              "pais": ["italy", "italia"]},
    "Bundesliga":       {"patrones": [r"^bundesliga$"],                           "pais": ["germany", "alemania"]},
    "Ligue 1":          {"patrones": [r"^ligue 1$", r"^ligue 1 mcdonald'?s$"],    "pais": ["france", "francia"]},
}

FALLOS = {}


def pedir(path, params=None, espera=0.3):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
    except Exception as e:
        FALLOS[type(e).__name__] = FALLOS.get(type(e).__name__, 0) + 1
        return None
    time.sleep(espera)
    if r.status_code != 200:
        FALLOS[f"HTTP {r.status_code}"] = FALLOS.get(f"HTTP {r.status_code}", 0) + 1
        return None
    try:
        return r.json()
    except Exception:
        FALLOS["json ilegible"] = FALLOS.get("json ilegible", 0) + 1
        return None


def desempaquetar(datos):
    if isinstance(datos, dict):
        return datos.get("data", []) or []
    return datos or []


def encaja(liga, objetivo):
    """Nombre Y país. Sin el país, 'Serie A' trae Brasil y Ecuador, y
    'Segunda División' trae media Sudamérica."""
    nombre = str(liga.get("name", "")).strip().lower()
    if not any(re.match(p, nombre) for p in objetivo["patrones"]):
        return False
    pais = str((liga.get("country") or {}).get("name", "")).strip().lower()
    if not pais:                      # si la API no dice país, no se descarta
        return True
    return any(c in pais for c in objetivo["pais"])


def descubrir_ligas():
    """Los ids no están documentados aquí, pero vienen dentro de cada partido.
    Se barren unos días y se recogen. Se guarda el resultado para no repetirlo
    cada semana."""
    if os.path.exists(RUTA_LIGAS):
        guardadas = json.load(open(RUTA_LIGAS, encoding="utf-8"))
        if len(guardadas) == len(OBJETIVO):
            print(f"Ligas ya conocidas: {', '.join(guardadas)}")
            return guardadas

    print("Descubriendo ids de liga...")
    vistas, encontradas = {}, {}
    hoy = datetime.now(timezone.utc).date()
    # Se mira un rango de días para no depender de que hoy haya fútbol de las
    # seis: un lunes de septiembre puede no haber Bundesliga.
    for salto in range(0, 12):
        fecha = (hoy + timedelta(days=salto)).isoformat()
        for offset in range(0, 900, 100):
            lote = desempaquetar(pedir("/matches", {"date": fecha, "limit": 100, "offset": offset}, espera=0.2))
            if not lote:
                break
            for p in lote:
                liga = p.get("league") or {}
                if liga.get("id"):
                    vistas[liga["id"]] = liga
            if len(lote) < 100:
                break
        if len(encontradas) == len(OBJETIVO):
            break
        for nombre, obj in OBJETIVO.items():
            if nombre in encontradas:
                continue
            for lid, liga in vistas.items():
                if encaja(liga, obj):
                    encontradas[nombre] = lid
                    pais = (liga.get("country") or {}).get("name", "?")
                    print(f"  {nombre}: id {lid}  (API: {liga.get('name')!r}, {pais})")
                    break

    faltan = [n for n in OBJETIVO if n not in encontradas]
    if faltan:
        # No se inventa un id ni se cuela una liga parecida: se dice cuál falta.
        print(f"  AVISO -- sin id para: {', '.join(faltan)}. "
              f"Esas ligas quedan fuera del calendario.")
    if encontradas:
        os.makedirs("data", exist_ok=True)
        json.dump(encontradas, open(RUTA_LIGAS, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    return encontradas


def partidos_de_liga(liga_id):
    todos = []
    for offset in range(0, 1200, 100):
        lote = desempaquetar(pedir("/matches", {"leagueId": liga_id, "season": TEMPORADA,
                                                 "limit": 100, "offset": offset}))
        if not lote:
            break
        todos.extend(lote)
        if len(lote) < 100:
            break
    return todos


def main():
    print("CALENDARIO DEL MES")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    ligas = descubrir_ligas()
    if not ligas:
        print("Sin ninguna liga identificada -- no se puede montar el calendario")
        return

    ahora = datetime.now(timezone.utc)
    hasta = ahora + timedelta(days=DIAS)
    filas = []

    for nombre, lid in ligas.items():
        partidos = partidos_de_liga(lid)
        dentro = 0
        for p in partidos:
            crudo = p.get("date")
            if not crudo:
                continue
            try:
                cuando = datetime.fromisoformat(str(crudo).replace("Z", "+00:00"))
            except ValueError:
                continue
            if cuando.tzinfo is None:
                cuando = cuando.replace(tzinfo=timezone.utc)
            if not (ahora - timedelta(hours=3) <= cuando <= hasta):
                continue
            dentro += 1
            filas.append({
                "match_id": p.get("id"),
                "liga": nombre,
                "liga_id": lid,
                "fecha": cuando.date().isoformat(),
                "saque_utc": cuando.strftime("%H:%M"),
                "local": (p.get("homeTeam") or {}).get("name"),
                "visitante": (p.get("awayTeam") or {}).get("name"),
                # ventana ancha a propósito: el descuento del primer tiempo
                # varía, y quien la use debe confirmar el estado de verdad
                "descanso_desde": (cuando + timedelta(minutes=45)).strftime("%H:%M"),
                "descanso_hasta": (cuando + timedelta(minutes=62)).strftime("%H:%M"),
            })
        print(f"  {nombre}: {len(partidos)} en la temporada, {dentro} en los próximos {DIAS} días")

    if not filas:
        print("Ningún partido en la ventana -- nada que escribir")
        return

    cal = pd.DataFrame(filas).sort_values(["fecha", "saque_utc", "liga"])
    os.makedirs("data", exist_ok=True)
    cal.to_csv(RUTA_CALENDARIO, index=False)

    lineas = [
        f"# Calendario -- próximos {DIAS} días\n",
        f"Generado el {ahora.strftime('%Y-%m-%d %H:%M UTC')}. "
        f"**{len(cal)} partidos** en {cal['liga'].nunique()} ligas.\n",
        "> La hora del descanso es una ESTIMACIÓN: saque inicial más 45 minutos "
        "más descuento, y el descuento varía. Por eso la ventana va de +45 a "
        "+62. Quien la use tiene que comprobar el estado real del partido "
        "antes de calcular nada: el modelo solo vale con el partido parado en "
        "el intermedio, no por la hora que sea.\n",
        "## Partidos por día\n",
        "| Día | Liga | Saque (UTC) | Partido | Ventana del descanso |",
        "|---|---|---|---|---|",
    ]
    for _, f in cal.iterrows():
        lineas.append(f"| {f['fecha']} | {f['liga']} | {f['saque_utc']} | "
                      f"{f['local']} vs {f['visitante']} | "
                      f"{f['descanso_desde']}-{f['descanso_hasta']} |")

    resumen = cal.groupby("fecha").size()
    lineas += ["\n## Carga por día\n", "| Día | Partidos |", "|---|---|"]
    for dia, n in resumen.items():
        lineas.append(f"| {dia} | {n} |")

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")

    print(f"\n{len(cal)} partidos escritos en {RUTA_CALENDARIO}")
    print(cal.groupby("liga").size().to_string())
    if FALLOS:
        print("AVISO -- llamadas fallidas:", ", ".join(f"{k} x{v}" for k, v in FALLOS.items()))


if __name__ == "__main__":
    main()
