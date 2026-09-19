"""
COMPARADOR DEL DESCANSO: modelo contra mercado en vivo.

Junta las tres piezas comprobadas hoy:
  1. Las tarjetas mostradas llegan EN DIRECTO con su minuto.
  2. El modelo condicional del descanso (modelo_descanso.py), validado
     fuera de muestra: Brier 0.2169 vs 0.2523 de la tasa base.
  3. Las cuotas en vivo (oddsType=live) traen hasta 11 líneas de Total
     Cards cotizadas por 24 casas -- muchas más que el previo, donde solo
     cotiza una.

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
from collections import Counter
from datetime import datetime, timedelta, timezone

from modelo_descanso import (preparar_datos, ajustar, prob_over, ya_resuelto,
                              lambda_de, validar)

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_LOG = "data/registro_descanso.csv"
RUTA_INFORME = "descanso_en_vivo.md"

QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ",
           "scheduled", "tbd", "to be")
MINUTO_MAXIMO = 87      # por encima, probable registro ya terminado
EV_SOSPECHOSO = 0.20    # divergencia que delata modelo mal calibrado

# ventana en la que tiene sentido mirar: desde poco antes del descanso hasta
# poco después de reanudar. Fuera de ahí el recuento todavía cambia mucho.
MINUTO_MIN = int(os.environ.get("MINUTO_MIN", "40"))
MINUTO_MAX = int(os.environ.get("MINUTO_MAX", "55"))
FILTRO_EQUIPO = os.environ.get("EQUIPO", "").strip().lower()


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


def en_juego(p):
    desc = ((p.get("state") or {}).get("description") or "").strip().lower()
    return bool(desc) and not any(desc.startswith(q) for q in QUIETOS)


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
    """{linea: {'prob_over': consenso sin margen, 'casas': n,
                'mejor_cuota': x, 'mejor_casa': nombre}}"""
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


def analizar(p, a, b, phi):
    """Devuelve (datos_partido, filas) o (None, []) si no hay nada útil."""
    mid = p["id"]
    datos = pedir(f"/matches/{mid}")
    if datos is None:
        return None, []
    m = datos[0] if isinstance(datos, list) else datos
    estado = m.get("state") or {}
    eventos = m.get("events") or []
    tarjetas = [e for e in eventos if e.get("type") in ("Yellow Card", "Red Card")]
    k = len(tarjetas)

    mercado = mercado_de_tarjetas(
        aplanar_cuotas(pedir("/odds", {"matchId": mid, "oddsType": "live"})))

    info = {
        "match_id": mid, "partido": nombre_de(p),
        "liga": str((p.get("league") or {}).get("name", "?")),
        "minuto": minuto_de(p), "estado": estado.get("description"),
        "marcador": (estado.get("score") or {}).get("current"),
        "tarjetas_ht": k,
        "minutos_tarjetas": [e.get("time") for e in tarjetas],
        "lambda_2a_parte": round(lambda_de(k, a, b), 2),
    }

    filas = []
    for linea in sorted(mercado):
        d = mercado[linea]
        resuelto = ya_resuelto(k, linea)
        p_modelo = prob_over(k, linea, a, b, phi)
        cuota = d["mejor_cuota"]
        ev = (p_modelo * cuota - 1) if (cuota and not resuelto) else None
        filas.append({
            **{x: info[x] for x in ("match_id", "partido", "liga", "minuto", "tarjetas_ht")},
            "linea": linea, "prob_modelo": round(p_modelo, 4),
            "prob_mercado": round(d["prob_over"], 4),
            "casas": d["casas"], "mejor_cuota": cuota, "mejor_casa": d["mejor_casa"],
            "ev": round(ev, 4) if ev is not None else None,
            "resuelto": resuelto,
            "momento": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    return info, filas


def escribir_informe(bloques, a, b, phi, base):
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    bm, bb, mejora = validar(base)
    lineas = [
        f"# Tarjetas al descanso -- {ahora}\n",
        f"Modelo: lambda(k) = max(0.8, {a:.3f} {b:+.3f}*k), phi={phi:.2f}, "
        f"ajustado sobre {len(base)} partidos.",
        f"Validación fuera de muestra (línea 4.5): Brier {bm:.4f} frente a "
        f"{bb:.4f} de la tasa base ({mejora:+.1f}%).\n",
        "> El recuento de tarjetas al descanso es **información pública**: las casas",
        "> también lo ven. Esto no es una ventaja por sí solo. La hipótesis a medir es",
        "> que sus modelos supongan persistencia cuando la correlación real es negativa.\n",
    ]
    if not bloques:
        lineas.append("*Ningún partido en la ventana del descanso ahora mismo.*")
    for info, filas in bloques:
        lineas.append(f"\n## {info['partido']}  ({info['liga']})")
        lineas.append(f"*minuto {info['minuto']} · {info['estado']} · {info['marcador']}*\n")
        lineas.append(f"**{info['tarjetas_ht']} tarjetas** hasta ahora"
                      + (f" (minutos {info['minutos_tarjetas']})" if info["minutos_tarjetas"] else "")
                      + f". Esperadas de aquí al final: **{info['lambda_2a_parte']}**.\n")
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
            elif ev > 0.02:
                juicio = f"{ev*100:+.1f}%"
            else:
                juicio = f"{ev*100:+.1f}%"
            lineas.append(
                f"| {f['linea']} | {f['prob_modelo']*100:.0f}% | {f['prob_mercado']*100:.0f}% | "
                f"{f['casas']} | {f['mejor_cuota']} ({f['mejor_casa']}) | {juicio} |")
    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n".join(lineas))


def guardar_log(todas):
    if not todas:
        return
    nuevo = pd.DataFrame(todas)
    previo = pd.read_csv(RUTA_LOG) if os.path.exists(RUTA_LOG) else pd.DataFrame()
    final = pd.concat([previo, nuevo], ignore_index=True)
    # una observación por partido, línea y minuto: evita duplicar si se relanza
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

    candidatos = [p for p in vivos
                  if MINUTO_MIN <= minuto_de(p) <= min(MINUTO_MAX, MINUTO_MAXIMO)]
    if FILTRO_EQUIPO:
        candidatos = [p for p in vivos
                      if FILTRO_EQUIPO in nombre_de(p).lower() and minuto_de(p) <= MINUTO_MAXIMO]
        print(f"Filtrando por equipo '{FILTRO_EQUIPO}': {len(candidatos)} partido(s)")
    else:
        print(f"En la ventana del descanso (min {MINUTO_MIN}-{MINUTO_MAX}): {len(candidatos)}")

    bloques, todas = [], []
    for p in candidatos[:8]:
        info, filas = analizar(p, a, b, phi)
        if info is None:
            continue
        bloques.append((info, filas))
        todas.extend(filas)

    escribir_informe(bloques, a, b, phi, base)
    guardar_log(todas)


if __name__ == "__main__":
    main()
