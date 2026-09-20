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


def temporada_actual(hoy=None):
    """La temporada europea se nombra por el año en que empieza, y empieza en
    verano: en septiembre de 2026 la temporada en curso es la 2026-27, o sea
    2026. Poner el número a mano es pedir el calendario del año pasado y no
    enterarse -- que es exactamente lo que pasó la primera vez."""
    hoy = hoy or datetime.now(timezone.utc).date()
    return hoy.year if hoy.month >= 7 else hoy.year - 1


TEMPORADA = int(os.environ.get("TEMPORADA", "0")) or temporada_actual()

# Las seis que cotizan tarjetas en vivo.
#
# Identificarlas por NOMBRE no funciona, y no es una precaución teórica: la
# primera versión filtraba por nombre y país, y trajo la Premier de Jamaica,
# la Serie A de Brasil, la Segunda de Uruguay y una "La Liga" de El Salvador.
# El filtro de país no sirvió porque la API no siempre trae el país dentro del
# partido, y la rama de "si no lo dice, le doy el beneficio de la duda" se lo
# tragaba todo.
#
# Así que cada liga se identifica por sus EQUIPOS, que no admiten confusión:
# solo hay un Bayern Munich. Se exige encontrar al menos dos de la lista, para
# que un nombre parecido suelto no baste -- "Inter" está en El Salvador y
# "River Plate" en media Sudamérica.
OBJETIVO = {
    "La Liga": {
        "patrones": [r"^la ?liga$", r"^primera divisi[oó]n$", r"^laliga"],
        "anclas": ["real madrid", "barcelona", "atletico madrid", "sevilla",
                    "villarreal", "athletic", "real sociedad", "valencia",
                    "betis", "celta"],
    },
    "Segunda División": {
        "patrones": [r"^segunda divisi[oó]n$", r"^laliga ?2", r"^la ?liga ?2"],
        "anclas": ["sporting gijon", "racing santander", "zaragoza", "eibar",
                    "huesca", "albacete", "mirandes", "burgos", "almeria",
                    "granada", "malaga", "cadiz", "leganes", "castellon",
                    "cordoba", "las palmas"],
    },
    "Premier League": {
        "patrones": [r"^premier league$", r"^english premier league$"],
        "anclas": ["arsenal", "liverpool", "manchester", "chelsea",
                    "tottenham", "everton", "newcastle", "aston villa",
                    "west ham", "brighton"],
    },
    "Serie A": {
        "patrones": [r"^serie a$", r"^serie a tim$"],
        "anclas": ["juventus", "napoli", "atalanta", "fiorentina", "lazio",
                    "udinese", "bologna", "torino", "verona", "milan",
                    "roma", "cagliari"],
    },
    "Bundesliga": {
        "patrones": [r"^bundesliga$", r"^1\.? bundesliga$"],
        "anclas": ["bayern", "dortmund", "leipzig", "leverkusen", "wolfsburg",
                    "frankfurt", "stuttgart", "werder", "freiburg", "mainz"],
    },
    "Ligue 1": {
        "patrones": [r"^ligue 1", r"^ligue1$"],
        "anclas": ["paris saint", "marseille", "lyon", "monaco", "lille",
                    "rennes", "nice", "lens", "nantes", "strasbourg"],
    },
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


def nombre_encaja(liga, objetivo):
    nombre = str(liga.get("name", "")).strip().lower()
    return any(re.match(p, nombre) for p in objetivo["patrones"])


def equipos_de(partidos):
    equipos = set()
    for p in partidos:
        for lado in ("homeTeam", "awayTeam"):
            nombre = str((p.get(lado) or {}).get("name", "")).strip().lower()
            if nombre:
                equipos.add(nombre)
    return equipos


def anclas_encontradas(equipos, objetivo):
    return {a for a in objetivo["anclas"] if any(a in e for e in equipos)}


def descubrir_ligas():
    """Los ids no están documentados aquí, pero vienen dentro de cada partido.

    El nombre NO basta para elegir: hay una Premier League en Jamaica y una
    Serie A en Brasil, y la API devuelve las dos. Así que se recogen TODAS las
    candidatas cuyo nombre encaje, se mira qué equipos tiene cada una, y se
    queda la que contenga al menos dos equipos que solo pueden ser de esa liga.
    Si ninguna los tiene, se dice y se deja fuera: mejor una liga menos que
    treinta días de calendario de otro país."""
    if os.path.exists(RUTA_LIGAS):
        guardadas = json.load(open(RUTA_LIGAS, encoding="utf-8"))
        if guardadas.get("_verificado") and len(guardadas) == len(OBJETIVO) + 1:
            print(f"Ligas ya verificadas: "
                  f"{', '.join(k for k in guardadas if not k.startswith('_'))}")
            return {k: v for k, v in guardadas.items() if not k.startswith("_")}
        print("El fichero de ligas no está verificado por equipos -- se rehace")

    print("Descubriendo ids de liga (y comprobándolos por sus equipos)...")
    candidatas = {}
    hoy = datetime.now(timezone.utc).date()
    for salto in range(0, 12):
        fecha = (hoy + timedelta(days=salto)).isoformat()
        for offset in range(0, 900, 100):
            lote = desempaquetar(pedir("/matches", {"date": fecha, "limit": 100,
                                                     "offset": offset}, espera=0.2))
            if not lote:
                break
            for p in lote:
                liga = p.get("league") or {}
                if liga.get("id"):
                    candidatas[liga["id"]] = liga
            if len(lote) < 100:
                break

    encontradas = {}
    for nombre, obj in OBJETIVO.items():
        posibles = [lid for lid, liga in candidatas.items() if nombre_encaja(liga, obj)]
        if not posibles:
            print(f"  {nombre}: ninguna candidata por nombre")
            continue
        mejor, mejor_anclas = None, set()
        for lid in posibles:
            partidos, _ = partidos_de_liga(lid)
            if not partidos:
                continue
            aciertos = anclas_encontradas(equipos_de(partidos), obj)
            etiqueta = candidatas[lid].get("name")
            print(f"    id {lid} ({etiqueta!r}): {len(aciertos)} equipos reconocidos"
                  + (f" -> {', '.join(sorted(aciertos)[:4])}" if aciertos else ""))
            if len(aciertos) > len(mejor_anclas):
                mejor, mejor_anclas = lid, aciertos
        if mejor is not None and len(mejor_anclas) >= 2:
            encontradas[nombre] = mejor
            print(f"  {nombre}: id {mejor}  ({len(mejor_anclas)} equipos reconocidos)")
        else:
            print(f"  {nombre}: NINGUNA candidata contiene sus equipos "
                  f"-- queda fuera. Candidatas miradas: {posibles}")

    if encontradas:
        os.makedirs("data", exist_ok=True)
        json.dump({**encontradas, "_verificado": True},
                  open(RUTA_LIGAS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return encontradas


def partidos_de_una_temporada(liga_id, temporada):
    todos = []
    for offset in range(0, 1200, 100):
        lote = desempaquetar(pedir("/matches", {"leagueId": liga_id, "season": temporada,
                                                 "limit": 100, "offset": offset}))
        if not lote:
            break
        todos.extend(lote)
        if len(lote) < 100:
            break
    return todos


def partidos_de_liga(liga_id):
    """Prueba la temporada deducida y, si vuelve vacía, las de al lado.

    No todas las ligas numeran igual ni arrancan el mismo mes, y una liga que
    devuelve cero partidos es indistinguible de una temporada mal pedida. En
    vez de dar por buena la deducción, se prueba y se dice cuál funcionó."""
    for temporada in (TEMPORADA, TEMPORADA - 1, TEMPORADA + 1):
        partidos = partidos_de_una_temporada(liga_id, temporada)
        if partidos:
            return partidos, temporada
    return [], None


# Lo que cubre el cron de descanso_en_vivo.yml, en horas UTC del descanso.
# Está escrito aquí a mano a propósito: si alguien cambia el cron y no toca
# esto, el aviso deja de cuadrar y se nota. Lo que NO puede pasar es que
# aparezca una jornada entre semana y no la cubra nadie sin decirlo.
# Todos los días, de 09:00 a 23:59 y de 00:00 a 03:59 UTC. Queda descubierto
# 04:00-08:59, que es la franja de Asia y Oceanía: de ahí no ha salido todavía
# ninguna observación con mercado, pero si el calendario mete partidos ahí,
# el aviso de abajo lo dirá en vez de dejarlos caer.
COBERTURA = {d: (0, 23) for d in range(7)}
HORAS_MUERTAS = range(0, 0)   # ya no queda ninguna: se cubre el día entero


def avisar_de_cobertura(cal, lineas):
    """El cron es fijo y el calendario cambia. Si sale una jornada entre
    semana -- una ronda de mitad de semana, un aplazamiento -- el comparador
    no la mirará, y sin este aviso no se sabría: no hay error, simplemente no
    aparecerían observaciones de ese día."""
    fuera = []
    for _, f in cal.iterrows():
        dia = datetime.fromisoformat(f["fecha"]).weekday()
        hora = int(str(f["descanso_desde"])[:2])
        ventana = COBERTURA.get(dia)
        if ventana is None or not (ventana[0] <= hora <= ventana[1]) or hora in HORAS_MUERTAS:
            fuera.append(f)

    if not fuera:
        print("Cobertura: el cron cubre todos los descansos del calendario")
        return

    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    print(f"\nAVISO -- {len(fuera)} partidos con el descanso FUERA de lo que mira el cron:")
    lineas += ["\n## Partidos que el cron no cubre\n",
               f"**{len(fuera)} partidos** tienen el descanso fuera de las horas "
               "que vigila el comparador. No darán observaciones salvo que se "
               "amplíe el cron de `descanso_en_vivo.yml`.\n",
               "| Día | Liga | Partido | Descanso |", "|---|---|---|---|"]
    for f in fuera:
        dia = dias[datetime.fromisoformat(f["fecha"]).weekday()]
        print(f"   {f['fecha']} ({dia}) {f['descanso_desde']} "
              f"{f['local']} vs {f['visitante']} ({f['liga']})")
        lineas.append(f"| {f['fecha']} ({dia}) | {f['liga']} | "
                      f"{f['local']} vs {f['visitante']} | {f['descanso_desde']} |")


def main():
    print("CALENDARIO DEL MES")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print(f"Temporada deducida: {TEMPORADA}")

    ligas = descubrir_ligas()
    if not ligas:
        print("Sin ninguna liga identificada -- no se puede montar el calendario")
        return

    ahora = datetime.now(timezone.utc)
    hasta = ahora + timedelta(days=DIAS)
    filas = []

    for nombre, lid in ligas.items():
        partidos, temporada = partidos_de_liga(lid)
        if not partidos:
            print(f"  {nombre}: la API no devuelve partidos en ninguna temporada "
                  f"probada ({TEMPORADA-1}, {TEMPORADA}, {TEMPORADA+1}) -- queda fuera")
            continue
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
        aviso = "" if temporada == TEMPORADA else f"  [temporada {temporada}, no la deducida]"
        print(f"  {nombre}: {len(partidos)} en la temporada {temporada}, "
              f"{dentro} en los próximos {DIAS} días{aviso}")

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

    avisar_de_cobertura(cal, lineas)

    print(f"\n{len(cal)} partidos escritos en {RUTA_CALENDARIO}")
    print(cal.groupby("liga").size().to_string())
    if FALLOS:
        print("AVISO -- llamadas fallidas:", ", ".join(f"{k} x{v}" for k, v in FALLOS.items()))


if __name__ == "__main__":
    main()
