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
EV_SOSPECHOSO = 0.20

# Ventana de VIGILANCIA: partidos a mirar. Dentro de ella, solo se evalúan
# los que estén de verdad en el descanso.
MINUTO_MIN = int(os.environ.get("MINUTO_MIN", "40"))
MINUTO_MAX = int(os.environ.get("MINUTO_MAX", "55"))
FILTRO_EQUIPO = os.environ.get("EQUIPO", "").strip().lower()
# para probar el circuito fuera del descanso, a sabiendas de que los números
# no son válidos
FORZAR = os.environ.get("FORZAR", "").lower() in ("1", "true", "si", "sí")


def pedir(path, params=None, espera=0.3):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception:
        return None
    time.sleep(espera)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


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

    base = preparar_datos()
    a, b, phi = ajustar(base)
    print(f"Modelo sobre {len(base)} partidos: lambda(k)=max(0.8, {a:.3f}{b:+.3f}*k), phi={phi:.2f}")

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
    for p in en_descanso[:8]:
        info, filas = analizar(p, a, b, phi)
        if info is None:
            continue
        bloques.append((info, filas))
        todas.extend(filas)

    escribir_informe(bloques, esperando, a, b, phi, base)
    if not FORZAR:
        guardar_log(todas)
    else:
        print("\n[log] omitido: ejecución forzada fuera del descanso")


if __name__ == "__main__":
    main()
