"""
COMPARADOR DEL DESCANSO: modelo contra mercado en vivo.

Junta las tres piezas comprobadas:
  1. Las tarjetas mostradas llegan EN DIRECTO con su minuto.
  2. El modelo condicional del descanso (modelo_descanso.py), validado
     fuera de muestra: Brier 0.2169 vs 0.2523 de la tasa base.
  3. Las cuotas en vivo (oddsType=live) traen hasta 11 líneas de Total
     Cards cotizadas por 24 casas -- muchas más que el previo, donde solo
     cotiza una.

SOLO SE CALCULA EN EL DESCANSO
------------------------------
lambda(k) está ajustado sobre lo que cae DESDE EL MINUTO 45. Aplicarlo en
el minuto 22, con 68 minutos por delante, subestima lo que queda y produce
números sin sentido. Una prueba en vivo lo dejó claro, así que el script
solo evalúa partidos cuyo estado es de descanso; el resto se listan como
"esperando" para saber que están vigilados.

LAS CUOTAS LLEGAN CON HASTA 10 MINUTOS DE RETRASO
-------------------------------------------------
La documentación declara "Live odds refresh interval: Once every 10 minutes",
y la respuesta no trae marca de tiempo, así que de una cuota solo sabemos que
tiene diez minutos o menos. Esto hay que tenerlo delante al leer el "valor":

  - El precio que vemos en el descanso pudo fijarse en el minuto 40, antes de
    las últimas tarjetas del primer tiempo. Parte de la discrepancia que
    medimos puede ser eso, y no un error del mercado.
  - La casa sí tiene el precio actualizado en su web. O sea que una cuota que
    aquí parece regalada puede no existir ya cuando se va a apostar.

Por eso la comparación modelo-contra-mercado vale como pregunta de
MODELADO -- ¿es nuestra probabilidad mejor que la que publicó la casa? -- pero
las unidades ganadas que calcula el cierre NO son dinero que se habría podido
coger. Para saber si lo son hace falta comprobar el precio en la casa real.

LO QUE HAY QUE TENER PRESENTE
-----------------------------
El recuento de tarjetas al descanso es información PÚBLICA: las 24 casas
también la ven. Así que la separación de 48 puntos que da el descanso no es
ventaja sobre el mercado, es información compartida.

La ventaja, si existe, es más concreta: que sus modelos en vivo asuman
persistencia (primer tiempo bronco -> segundo bronco) cuando el histórico
dice que la correlación es NEGATIVA. Si es así, sobrevalorarán el Over justo
en los partidos con muchas tarjetas al descanso.

Esto no lo damos por cierto: lo registramos partido a partido para poder
medirlo luego. Por eso el script compara y anota, pero no recomienda apostar.
"""
import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

from modelo_descanso import (preparar_datos, ajustar, prob_over, prob_push,
                              valor_esperado, ya_resuelto, lambda_de, validar)

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_LOG = "data/registro_descanso.csv"
RUTA_INFORME = "descanso_en_vivo.md"

QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ",
           "scheduled", "tbd", "to be")
MINUTO_MAXIMO = 87
# Cuántos partidos se analizan por pasada. Cada uno cuesta tres llamadas
# (detalle, estadísticas y cuotas), así que subirlo acumula descansos más
# deprisa pero acerca el límite de la API.
MAXIMO_POR_PASADA = int(os.environ.get("MAXIMO_POR_PASADA", "12"))
EV_SOSPECHOSO = 0.20

# Ventana de VIGILANCIA: partidos a mirar. Dentro de ella, solo se evalúan
# los que estén de verdad en el descanso.
MINUTO_MIN = int(os.environ.get("MINUTO_MIN", "40"))
MINUTO_MAX = int(os.environ.get("MINUTO_MAX", "55"))
FILTRO_EQUIPO = os.environ.get("EQUIPO", "").strip().lower()
# para probar el circuito fuera del descanso, a sabiendas de que los números
# no son válidos
FORZAR = os.environ.get("FORZAR", "").lower() in ("1", "true", "si", "sí")


# Pasando a mirar cada cuarto de hora, el límite de la API deja de ser
# teórico. Antes un 429 devolvía None igual que "no hay datos", así que una
# tarde entera limitada se habría visto como una tarde sin partidos. Ahora se
# cuenta y se dice.
FALLOS = {}
LLAMADAS = [0]

RUTA_CONSUMO = "data/consumo_api.json"
# El plan da 7.500 llamadas al día. Se reserva un margen para el resto de
# workflows (el calendario semanal, el cierre, el pipeline de los martes) y
# para que un día cargado no se coma el tope antes de la franja europea.
TOPE_DIARIO = int(os.environ.get("TOPE_DIARIO", "6000"))


def consumo_de_hoy():
    """Lo que llevamos gastado hoy, medido, no estimado.

    Mis cuentas a ojo ya fallaron una vez: el horario ampliado habría gastado
    un 95% del tope un sábado. Un contador real es la diferencia entre saberlo
    y creerlo."""
    hoy = datetime.now(timezone.utc).date().isoformat()
    if not os.path.exists(RUTA_CONSUMO):
        return {"fecha": hoy, "llamadas": 0, "pasadas": 0}
    try:
        d = json.load(open(RUTA_CONSUMO, encoding="utf-8"))
    except Exception:
        return {"fecha": hoy, "llamadas": 0, "pasadas": 0}
    if d.get("fecha") != hoy:          # día nuevo, cuenta a cero
        return {"fecha": hoy, "llamadas": 0, "pasadas": 0}
    return d


def apuntar_consumo(previo):
    previo["llamadas"] = previo.get("llamadas", 0) + LLAMADAS[0]
    previo["pasadas"] = previo.get("pasadas", 0) + 1
    os.makedirs("data", exist_ok=True)
    json.dump(previo, open(RUTA_CONSUMO, "w", encoding="utf-8"), indent=2)
    print(f"[api] {LLAMADAS[0]} llamadas en esta pasada; "
          f"{previo['llamadas']} hoy en {previo['pasadas']} pasadas "
          f"({previo['llamadas']/TOPE_DIARIO*100:.0f}% del tope de {TOPE_DIARIO})")


def pedir(path, params=None, espera=0.3):
    LLAMADAS[0] += 1
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception as e:
        FALLOS[type(e).__name__] = FALLOS.get(type(e).__name__, 0) + 1
        return None
    time.sleep(espera)
    if r.status_code != 200:
        clave = f"HTTP {r.status_code}"
        FALLOS[clave] = FALLOS.get(clave, 0) + 1
        return None
    try:
        return r.json()
    except Exception:
        FALLOS["json ilegible"] = FALLOS.get("json ilegible", 0) + 1
        return None


def informar_de_fallos():
    if not FALLOS:
        print("Llamadas a la API: todas correctas")
        return
    print("AVISO -- llamadas fallidas:", ", ".join(f"{k} x{v}" for k, v in FALLOS.items()))
    if any(k.startswith("HTTP 429") for k in FALLOS):
        print("  429 es límite de peticiones: hay que espaciar los crons o el "
              "registro se llenará de huecos sin que se note.")


def desempaquetar(datos):
    if isinstance(datos, dict):
        return datos.get("data", []) or []
    return datos or []


def aplanar_cuotas(datos):
    planas = []
    for bloque in desempaquetar(datos):
        if isinstance(bloque, dict):
            planas.extend(bloque.get("odds", []) or [])
    return planas


def minuto_de(p):
    try:
        return int((p.get("state") or {}).get("clock") or 0)
    except (TypeError, ValueError):
        return 0


def estado_de(p):
    return ((p.get("state") or {}).get("description") or "").strip()


def en_juego(p):
    desc = estado_de(p).lower()
    return bool(desc) and not any(desc.startswith(q) for q in QUIETOS)


# Cómo puede llamar la API al intermedio. La lista es ancha a propósito: si
# el nombre no encaja, el partido se cae del único momento en que el modelo
# vale, y no hay segunda oportunidad hasta la semana siguiente.
DESCANSO_EXACTO = {"ht", "break", "interval", "half", "halftime", "half time"}
DESCANSO_CONTIENE = ("half time", "halftime", "half-time", "descanso",
                     "entretiempo", "intervalo", "mi-temps")


def es_descanso(p):
    """El modelo solo es válido aquí: partido detenido en el intermedio."""
    desc = estado_de(p).lower().replace("-", " ").strip()
    # El descanso de la prórroga NO sirve: quedan 15 minutos, no 45, y
    # lambda(k) está ajustada sobre segundas partes completas.
    if "extra" in desc or "prórroga" in desc or "prorroga" in desc:
        return False
    if desc in DESCANSO_EXACTO:
        return True
    return any(x in desc for x in DESCANSO_CONTIENE)


MINUTO_TOLERADO = 47


def momento_valido(estado):
    """Entre el escaneo de partidos y la llamada de detalle pasan segundos, y
    a veces la segunda parte ya ha arrancado. Eso sigue valiendo mientras el
    reloj no se haya ido: lambda(k) supone 45 minutos por delante, así que el
    minuto 45-47 es el mismo momento. El minuto 60 ya no."""
    if es_descanso({"state": estado}):
        return True
    try:
        reloj = int(estado.get("clock") or 0)
    except (TypeError, ValueError):
        return False
    return 45 <= reloj <= MINUTO_TOLERADO


def nombre_de(p):
    try:
        return f"{p['homeTeam']['name']} vs {p['awayTeam']['name']}"
    except (KeyError, TypeError):
        return f"partido {p.get('id')}"


RUTA_AGENDA = "data/agenda_hoy.csv"

# Margen alrededor de la ventana estimada del descanso. La estimación es
# saque+45 a saque+62; con media hora por cada lado se absorben el descuento
# largo, un retraso en el saque y el desfase del cron.
MARGEN_MINUTOS = 30


def partidos_de_la_agenda():
    """Los partidos de hoy que PODRÍAN estar en el descanso ahora mismo.

    La primera versión preguntaba por los 25-40 partidos del día en cada
    pasada, también a las tres de la mañana con el saque a las dos de la
    tarde. A 76 pasadas diarias eso eran unas 2.500 llamadas al día tiradas,
    de un tope de 7.500.

    La agenda ya trae la hora de cada partido, así que el filtro se hace en
    local, que no cuesta nada, y solo se pregunta por los que caen dentro de
    la ventana. Lo normal es que no sea ninguno.

    Devuelve None si no hay agenda utilizable -- entonces se barre como antes.
    """
    if not os.path.exists(RUTA_AGENDA):
        return None
    try:
        agenda = pd.read_csv(RUTA_AGENDA)
    except Exception:
        return None
    if agenda.empty or "match_id" not in agenda.columns:
        return None

    ahora = datetime.now(timezone.utc)
    minutos_ahora = ahora.hour * 60 + ahora.minute

    candidatos = []
    for _, f in agenda.iterrows():
        try:
            h, m = str(f["descanso_desde"]).split(":")
            desde = int(h) * 60 + int(m) - MARGEN_MINUTOS
            h, m = str(f["descanso_hasta"]).split(":")
            hasta = int(h) * 60 + int(m) + MARGEN_MINUTOS
        except (ValueError, KeyError):
            continue
        if desde <= minutos_ahora <= hasta:
            candidatos.append(int(f["match_id"]))

    if not candidatos:
        print(f"Agenda: {len(agenda)} partidos hoy, ninguno en ventana de "
              f"descanso ahora ({ahora.strftime('%H:%M')} UTC)")
        return []

    encontrados = []
    for mid in candidatos[:15]:
        datos = pedir(f"/matches/{mid}", espera=0.2)
        if not datos:
            continue
        m = datos[0] if isinstance(datos, list) else datos
        if en_juego(m):
            encontrados.append(m)
    print(f"Agenda: {len(candidatos)} partidos en ventana, "
          f"{len(encontrados)} en juego")
    return encontrados


def buscar_en_juego():
    ahora = datetime.now(timezone.utc)
    vivos = []
    for desplazamiento in (0, -1):
        fecha = (ahora.date() + timedelta(days=desplazamiento)).isoformat()
        for offset in range(0, 900, 100):
            datos = pedir("/matches", {"date": fecha, "limit": 100, "offset": offset}, espera=0.25)
            lote = desempaquetar(datos)
            if not lote:
                break
            vivos.extend(p for p in lote if en_juego(p))
            if len(lote) < 100:
                break
    return vivos


def linea_de_mercado(nombre):
    """'Total Cards 4.5' -> 4.5, y None si no es un mercado de tarjetas."""
    bajo = (nombre or "").strip().lower()
    if "card" not in bajo and "tarjeta" not in bajo:
        return None
    for trozo in bajo.replace("/", " ").split():
        try:
            return float(trozo)
        except ValueError:
            continue
    return None


def mercado_de_tarjetas(planas):
    por_linea = {}
    for c in planas:
        linea = linea_de_mercado(c.get("market"))
        if linea is None:
            continue
        pares = []
        for v in (c.get("values") or []):
            try:
                cuota = float(v.get("odd"))
            except (TypeError, ValueError):
                continue
            if cuota > 1:
                pares.append((str(v.get("value")).strip().lower(), cuota))
        if len(pares) < 2:
            continue
        suma = sum(1 / q for _, q in pares)
        probs = {val: (1 / q) / suma for val, q in pares}
        entrada = por_linea.setdefault(linea, {"probs": [], "cuotas_over": []})
        if "over" in probs:
            entrada["probs"].append(probs["over"])
        for val, q in pares:
            if val == "over":
                entrada["cuotas_over"].append((q, c.get("bookmakerName")))

    salida = {}
    for linea, d in por_linea.items():
        if not d["probs"]:
            continue
        mejor = max(d["cuotas_over"], default=(0.0, None))
        salida[linea] = {
            "prob_over": sum(d["probs"]) / len(d["probs"]),
            "casas": len(d["probs"]),
            "mejor_cuota": mejor[0],
            "mejor_casa": mejor[1],
        }
    return salida


def estadisticas_del_primer_tiempo(match_id):
    """Faltas y corners acumulados hasta el descanso.

    /statistics no da desglose por tiempos, pero en un partido EN JUEGO
    devuelve los acumulados hasta ese minuto -- comprobado en el descanso del
    DC United-Charlotte (11 faltas) y del San Jose-LAFC (9), contra las 25 de
    media de un partido entero. Llamándolo en el intermedio, eso ES el primer
    tiempo.

    Se apunta aunque el modelo todavía no lo use. En el histórico las faltas
    del partido completo correlacionan +0.406 con las tarjetas, frente al
    -0.171 de las tarjetas al descanso contra la segunda parte: es la señal
    más fuerte que tenemos y no la estamos usando. No se puede ajustar hoy
    porque el histórico solo guarda faltas del partido entero, así que hay que
    ir acumulando descansos hasta tener con qué ajustar el coeficiente."""
    datos = pedir(f"/statistics/{match_id}")
    if not datos:
        return None, None
    faltas = corners = 0
    visto = False
    for bloque in datos:
        for s in (bloque.get("statistics") or []):
            nombre = str(s.get("displayName", "")).lower()
            try:
                valor = float(s.get("value") or 0)
            except (TypeError, ValueError):
                continue
            if nombre == "fouls":
                faltas += valor
                visto = True
            elif nombre == "corners":
                corners += valor
    return (faltas if visto else None), corners


def analizar(p, a, b, phi):
    mid = p["id"]
    datos = pedir(f"/matches/{mid}")
    if datos is None:
        return None, []
    m = datos[0] if isinstance(datos, list) else datos
    estado = m.get("state") or {}
    if not FORZAR and not momento_valido(estado):
        print(f"   descartado (ya no es el descanso): {nombre_de(p)} "
              f"-- {estado.get('description')!r} min {estado.get('clock')}")
        return None, []
    eventos = m.get("events") or []
    tarjetas = [e for e in eventos if e.get("type") in ("Yellow Card", "Red Card")]
    k = len(tarjetas)

    faltas_ht, corners_ht = estadisticas_del_primer_tiempo(mid)

    mercado = mercado_de_tarjetas(
        aplanar_cuotas(pedir("/odds", {"matchId": mid, "oddsType": "live"})))

    info = {
        "match_id": mid, "partido": nombre_de(p),
        "liga": str((p.get("league") or {}).get("name", "?")),
        "minuto": minuto_de(p), "estado": estado.get("description"),
        "marcador": (estado.get("score") or {}).get("current"),
        "tarjetas_ht": k,
        "faltas_ht": faltas_ht, "corners_ht": corners_ht,
        "minutos_tarjetas": [e.get("time") for e in tarjetas],
        "lambda_restante": round(lambda_de(k, a, b), 2),
    }

    filas = []
    for linea in sorted(mercado):
        d = mercado[linea]
        resuelto = ya_resuelto(k, linea)
        ev = None if resuelto else valor_esperado(k, linea, d["mejor_cuota"], a, b, phi)
        filas.append({
            **{x: info[x] for x in ("match_id", "partido", "liga", "minuto",
                                     "estado", "tarjetas_ht", "faltas_ht",
                                     "corners_ht")},
            "linea": linea,
            "prob_modelo": round(prob_over(k, linea, a, b, phi), 4),
            "prob_push": round(prob_push(k, linea, a, b, phi), 4),
            "prob_mercado": round(d["prob_over"], 4),
            "casas": d["casas"], "mejor_cuota": d["mejor_cuota"],
            "mejor_casa": d["mejor_casa"],
            "ev": round(ev, 4) if ev is not None else None,
            "resuelto": resuelto,
            "momento": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    return info, filas


def escribir_informe(bloques, esperando, a, b, phi, base):
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    bm, bb, mejora = validar(base)
    lineas = [
        f"# Tarjetas al descanso -- {ahora}\n",
        f"Modelo: lambda(k) = max(0.8, {a:.3f} {b:+.3f}*k), phi={phi:.2f}, "
        f"ajustado sobre {len(base)} partidos.",
        f"Validación fuera de muestra (línea 4.5): Brier {bm:.4f} frente a "
        f"{bb:.4f} de la tasa base ({mejora:+.1f}%).\n",
        "> El recuento del descanso es **información pública**: las casas también lo",
        "> ven. La hipótesis a medir es que sus modelos supongan persistencia cuando",
        "> la correlación real es negativa. Una observación no demuestra nada.\n",
    ]
    if FORZAR:
        lineas.insert(1, "> ⚠ **EJECUCIÓN FORZADA fuera del descanso.** lambda(k) está "
                          "ajustada para los 45 minutos que quedan desde el descanso, "
                          "así que estos números NO son válidos: solo sirven para probar "
                          "que el mercado se lee bien. No se ha registrado nada.\n")
    # Con una pasada cada quince minutos durante diecinueve horas, el límite
    # de la API es el riesgo real. Un 429 no rompe nada: simplemente no hay
    # observaciones, que es indistinguible de "no había partidos". En el log
    # se ve, pero los logs no los lee nadie -- así que sale en el informe.
    # El informe se escribe ANTES de apuntar el consumo, así que hay que
    # sumarle lo que lleva gastado esta pasada. Si no, el número del informe
    # va siempre una pasada por detrás -- y un contador que va por detrás
    # engaña justo el día que importa.
    gasto = consumo_de_hoy()
    llevamos = gasto.get("llamadas", 0) + LLAMADAS[0]
    lineas.append(f"*Consumo de API hoy: {llevamos} llamadas en "
                  f"{gasto.get('pasadas', 0) + 1} pasadas, sobre un tope de "
                  f"{TOPE_DIARIO} ({llevamos/TOPE_DIARIO*100:.0f}%). "
                  f"El plan da 7.500 al día.*\n")
    lineas.append("> ⚠ Las cuotas en vivo se refrescan **cada 10 minutos** "
                  "(documentación de la API) y no traen marca de tiempo. El "
                  "precio de abajo puede ser de antes de las últimas tarjetas "
                  "del primer tiempo, y puede no existir ya en la casa. El "
                  "valor sirve para comparar modelos, no como dinero cogible.\n")
    if FALLOS:
        lineas.append("> ⚠ **Llamadas fallidas:** "
                      + ", ".join(f"{k} x{v}" for k, v in FALLOS.items())
                      + (". Un 429 es límite de peticiones: hay huecos en el "
                         "registro de esta pasada."
                         if any(str(k).startswith("HTTP 429") for k in FALLOS)
                         else ".") + "\n")
    if esperando:
        lineas.append("**En juego, esperando al descanso:** " +
                      ", ".join(f"{n} (min {mn})" for n, mn in esperando) + "\n")
    if not bloques:
        lineas.append("*Ningún partido en el descanso ahora mismo.*")
    for info, filas in bloques:
        lineas.append(f"\n## {info['partido']}  ({info['liga']})")
        lineas.append(f"*{info['estado']} · minuto {info['minuto']} · {info['marcador']}*\n")
        faltas = (f" · **{info['faltas_ht']:.0f} faltas**"
                  if info.get("faltas_ht") is not None else "")
        lineas.append(f"**{info['tarjetas_ht']} tarjetas** al descanso"
                      + (f" (minutos {info['minutos_tarjetas']})" if info["minutos_tarjetas"] else "")
                      + faltas
                      + f". Esperadas en la 2ª parte: **{info['lambda_restante']}**.\n")
        if not filas:
            lineas.append("*Sin mercado de tarjetas en vivo para este partido.*")
            continue
        lineas.append("| Línea | Modelo | Mercado | Casas | Mejor cuota | Valor |")
        lineas.append("|---|---|---|---|---|---|")
        for f in filas:
            if f["resuelto"]:
                lineas.append(f"| {f['linea']} | — | — | {f['casas']} | — | ya resuelto |")
                continue
            ev = f["ev"]
            if ev is None:
                juicio = "—"
            elif ev > EV_SOSPECHOSO:
                juicio = f"{ev*100:+.1f}% ⚠ revisar modelo"
            else:
                juicio = f"{ev*100:+.1f}%"
            empate = f" (push {f['prob_push']*100:.0f}%)" if f["prob_push"] > 0.01 else ""
            lineas.append(
                f"| {f['linea']}{empate} | {f['prob_modelo']*100:.0f}% | "
                f"{f['prob_mercado']*100:.0f}% | {f['casas']} | "
                f"{f['mejor_cuota']} ({f['mejor_casa']}) | {juicio} |")
    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n".join(lineas))


# Cuánto después se toma la segunda foto del precio.
#
# La documentación de la API lo dice con todas las letras: "Live odds refresh
# interval: Once every 10 minutes". Con la ventana anterior (10-35 min) una
# segunda foto tomada a los 10 minutos podía caer en el MISMO ciclo de caché
# que la primera y salir idéntica sin que el mercado estuviera quieto -- que
# es exactamente lo que pasó: 14 líneas iguales hasta el último decimal.
#
# 20 minutos de mínimo garantizan un ciclo distinto.
MINUTOS_SEGUNDA_FOTO = (20, 45)


def segunda_foto():
    """Vuelve a mirar el precio de las líneas que marcamos en el descanso.

    POR QUÉ: para saber si le ganamos al mercado hacen falta unos 420 partidos
    -- la desviación del resultado por partido es de 2.05 unidades, así que
    con menos, un +35% y un -35% son igual de compatibles con "no hay nada".
    Tres semanas de recogida antes de saber si esto sirve.

    El movimiento del precio dice lo mismo con muchas menos observaciones,
    porque tiene mucha menos varianza que el resultado. Si marcamos una línea
    como valor y diez minutos después el mercado se ha movido hacia nosotros,
    eso es ventaja aunque ese partido concreto acabe perdiendo.

    Es lo que en apuestas se llama closing line value, y es la medida que usan
    los que viven de esto para saber si tienen ventaja sin esperar a que la
    suerte se promedie.

    Hay que montarlo ANTES de acumular: esta foto no se puede sacar hacia
    atrás. Dentro de tres semanas tendríamos 400 partidos y ninguna forma de
    calcularla.
    """
    if not os.path.exists(RUTA_LOG):
        return
    try:
        log = pd.read_csv(RUTA_LOG)
    except Exception:
        return
    if log.empty or "momento" not in log.columns:
        return

    for col in ("cuota_despues", "prob_mercado_despues", "momento_despues"):
        if col not in log.columns:
            log[col] = pd.NA

    ahora = datetime.now(timezone.utc)
    momentos = pd.to_datetime(log["momento"], errors="coerce", utc=True)
    edad = (ahora - momentos).dt.total_seconds() / 60

    pendientes = log[(log["cuota_despues"].isna())
                     & (edad >= MINUTOS_SEGUNDA_FOTO[0])
                     & (edad <= MINUTOS_SEGUNDA_FOTO[1])]
    if pendientes.empty:
        return

    partidos = list(pendientes["match_id"].unique())[:8]
    print(f"Segunda foto: {len(partidos)} partidos con líneas por revisar")

    for mid in partidos:
        mercado = mercado_de_tarjetas(
            aplanar_cuotas(pedir("/odds", {"matchId": int(mid), "oddsType": "live"})))
        if not mercado:
            continue
        filas = log[(log["match_id"] == mid) & (log["cuota_despues"].isna())]
        tocadas = 0
        for idx, fila in filas.iterrows():
            d = mercado.get(float(fila["linea"]))
            if not d:
                continue
            log.at[idx, "cuota_despues"] = d["mejor_cuota"]
            log.at[idx, "prob_mercado_despues"] = round(d["prob_over"], 4)
            log.at[idx, "momento_despues"] = ahora.isoformat(timespec="seconds")
            tocadas += 1
        nombre = filas.iloc[0]["partido"] if not filas.empty else mid
        print(f"   {nombre}: {tocadas} líneas actualizadas")

    log.to_csv(RUTA_LOG, index=False)


def guardar_log(todas):
    if not todas:
        print("\n[log] sin observaciones que guardar")
        return
    nuevo = pd.DataFrame(todas)
    previo = pd.read_csv(RUTA_LOG) if os.path.exists(RUTA_LOG) else pd.DataFrame()
    final = pd.concat([previo, nuevo], ignore_index=True)
    if {"match_id", "linea", "minuto"}.issubset(final.columns):
        final = final.drop_duplicates(subset=["match_id", "linea", "minuto"], keep="last")
    final.to_csv(RUTA_LOG, index=False)
    print(f"\n[log] {len(nuevo)} observaciones nuevas, {len(final)} en total -> {RUTA_LOG}")


def main():
    print("TARJETAS AL DESCANSO -- modelo contra mercado en vivo")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    consumo = consumo_de_hoy()
    if consumo["llamadas"] >= TOPE_DIARIO:
        print(f"PARADA -- ya van {consumo['llamadas']} llamadas hoy, por encima "
              f"del tope de {TOPE_DIARIO}. No se pide nada más hasta mañana.")
        print("Si esto salta a menudo, hay que espaciar el cron: el plan da "
              "7.500 al día y quedarse sin ellas a media tarde es perderse la "
              "franja europea entera, que es la que más rinde.")
        return

    base = preparar_datos()
    a, b, phi = ajustar(base)
    print(f"Modelo sobre {len(base)} partidos: lambda(k)=max(0.8, {a:.3f}{b:+.3f}*k), phi={phi:.2f}")

    # La agenda primero: filtra en local y solo pregunta por los partidos que
    # podrían estar en el descanso. Si no da nada se barre, porque la mitad de
    # las observaciones que tenemos vienen de ligas que no están en el
    # calendario -- MLS y Serie A de Brasil, sobre todo.
    vivos = partidos_de_la_agenda()
    if not vivos:
        vivos = buscar_en_juego()
    print(f"Partidos en juego: {len(vivos)}")

    # Qué nombres usa de verdad la API para los estados. Si algún día el
    # descanso se llama de una forma que es_descanso() no reconoce, aquí se
    # ve en vez de desaparecer en silencio.
    estados = {}
    for p in vivos:
        estados[estado_de(p)] = estados.get(estado_de(p), 0) + 1
    print("Estados vistos:", ", ".join(f"{e!r} x{n}" for e, n in
                                        sorted(estados.items(), key=lambda x: -x[1])))

    if FILTRO_EQUIPO:
        vigilados = [p for p in vivos
                     if FILTRO_EQUIPO in nombre_de(p).lower() and minuto_de(p) <= MINUTO_MAXIMO]
        print(f"Filtrando por equipo '{FILTRO_EQUIPO}': {len(vigilados)}")
    else:
        # El descanso entra SIEMPRE, esté donde esté el reloj. Al parar el
        # partido la API puede dejar clock a cero o en blanco, y filtrando
        # solo por minuto se caería de la lista justo el momento que
        # queremos medir.
        vigilados = [p for p in vivos
                     if (MINUTO_MIN <= minuto_de(p) <= min(MINUTO_MAX, MINUTO_MAXIMO)
                         or es_descanso(p))]
        print(f"En la ventana de vigilancia (min {MINUTO_MIN}-{MINUTO_MAX}, "
              f"más cualquiera en el descanso): {len(vigilados)}")

    en_descanso = [p for p in vigilados if es_descanso(p) or FORZAR]
    esperando = [(nombre_de(p), minuto_de(p)) for p in vigilados if p not in en_descanso]
    print(f"De esos, EN EL DESCANSO: {len(en_descanso)}"
          + ("   [FORZADO: números no válidos]" if FORZAR else ""))
    for n, mn in esperando:
        print(f"   esperando: {n} (min {mn})")

    bloques, todas = [], []
    for p in en_descanso[:MAXIMO_POR_PASADA]:
        info, filas = analizar(p, a, b, phi)
        if info is None:
            continue
        bloques.append((info, filas))
        todas.extend(filas)

    escribir_informe(bloques, esperando, a, b, phi, base)
    informar_de_fallos()
    apuntar_consumo(consumo)
    if not FORZAR:
        guardar_log(todas)
        # Después de guardar, para que las líneas de esta pasada entren ya en
        # la cola de la segunda foto.
        segunda_foto()
    else:
        print("\n[log] omitido: ejecución forzada fuera del descanso")


if __name__ == "__main__":
    main()
