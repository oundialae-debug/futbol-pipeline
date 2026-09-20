"""
BACKTEST: ¿ganan de verdad las apuestas que marcamos como valor?

LA IDEA
-------
No hace falta esperar tres semanas de precios. La API sirve cuotas hasta 28
días DESPUÉS de que el partido termine, así que se pueden coger partidos ya
jugados, calcular qué apuestas habrían salido marcadas como valor contra el
consenso, y comprobar si ganaron. La respuesta está hoy, no en septiembre
que viene.

UNA ADVERTENCIA QUE HACE EL RESULTADO MÁS DURO, NO MÁS BLANDO
--------------------------------------------------------------
Las cuotas que sirve la API de un partido terminado son, con toda
probabilidad, las de cierre: las últimas y por tanto las más afinadas. Batir
al consenso de cierre es más difícil que batir al de tres días antes.

Así que si aquí sale ventaja, es ventaja de verdad. Si sale plano, todavía
podría existir contra precios más tempranos, y eso habría que medirlo aparte.
Conviene saber en qué dirección engaña la prueba.

CÓMO SE RESUELVE CADA MERCADO
-----------------------------
Del marcador, de los eventos y de las estadísticas del propio partido:

    Full Time Result     marcador
    Total Goals X        marcador, con empate (push) en líneas enteras
    Both Teams To Score  marcador
    Odd or Even          marcador
    Clean Sheet          marcador
    First Team To Score  primer evento de gol; None si no hubo goles
    Total Cards X        eventos de tarjeta
    Total Corners X      estadísticas del partido

Asian Handicap se queda FUERA a propósito. Sus reglas de empate en líneas de
cuarto (-0.25, +0.75...) devuelven media apuesta, y equivocarse en eso
inventaría beneficios silenciosamente. Mejor un mercado menos que un número
que no es verdad.
"""
import os
import time
import requests
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

RUTA_LIGAS = "data/ligas.json"
RUTA_SALIDA = "data/backtest_valor.csv"
RUTA_INFORME = "backtest_valor.md"

DIAS = int(os.environ.get("DIAS", "25"))       # las cuotas duran 28 días
MAX_PARTIDOS = int(os.environ.get("MAX_PARTIDOS", "150"))
MIN_CASAS = 8
# Por debajo/encima de esto, el VALOR RELATIVO es ruido del consenso (dividir
# entre una probabilidad pequeña amplifica cualquier diferencia mínima). Pero
# esta misma frontera dejaba sin mirar la zona donde clásicamente aparece el
# sesgo favorito-marginado, que se mide en puntos absolutos y no tiene ese
# problema. Configurable para poder ensanchar solo en una pasada de
# calibración sin tocar el comportamiento por defecto de los crons.
PROB_MINIMA = float(os.environ.get("PROB_MINIMA", "0.15"))
PROB_MAXIMA = float(os.environ.get("PROB_MAXIMA", "0.85"))
LLAMADAS = [0]
VERIFICADO = [False]

FAMILIAS = {
    "Full Time Result": {"home", "draw", "away"},
    "Both Teams To Score": {"yes", "no"},
    "Odd or Even": {"odd", "even"},
    "Clean Sheet": {"home", "away"},
    # OJO CON LAS MAYÚSCULAS: la API devuelve "First Team To Score" (T
    # mayúscula en "To"), no "First Team to Score". La comparación es exacta
    # y sensible a mayúsculas, así que con el nombre mal escrito este mercado
    # entraba en el diccionario de clasificación y no aparecía NUNCA en
    # ningún resultado -- ni un error, solo ausencia total y silenciosa.
    # Verificado contra el censo crudo (censo_mercados_crudo.py) antes de
    # corregirlo, no supuesto.
    "First Team To Score": {"home", "away", "none"},
}
FAMILIAS_CON_LINEA = {
    "total goals": {"over", "under"},
    "total cards": {"over", "under"},
    "total corners": {"over", "under"},
    # Hándicap Asiático SOLO en líneas simples (enteras y medias). Ahí viven
    # dos mercados que el usuario pidió y que no existen con nombre propio:
    #
    #   Sin Empate (Draw No Bet)  = Asian Handicap 0
    #   Doble Oportunidad 1X      = Asian Handicap +0.5 para el local
    #
    # Las líneas de CUARTO (±0.25, ±0.75) se siguen excluyendo: parten la
    # apuesta en dos mitades y devuelven media, y equivocarse en esa regla
    # inventaría beneficios en silencio. Lo que se excluye ahora es solo esa
    # parte, no el hándicap entero como antes.
    "asian handicap": {"home", "away"},
}


def pedir(path, params=None, espera=0.25):
    LLAMADAS[0] += 1
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
    except Exception:
        return None
    time.sleep(espera)
    if r.status_code != 200:
        if r.status_code == 429:
            print("  [429] límite de peticiones -- se para aquí")
            raise SystemExit(0)
        return None
    try:
        return r.json()
    except Exception:
        return None


def desempaquetar(d):
    return (d.get("data", []) or []) if isinstance(d, dict) else (d or [])


def handicap_local(mercado):
    """El hándicap que lleva el LOCAL, o None si la línea no es simple.

    La API nombra estas líneas como "Asian Handicap -1/+1", donde el PRIMER
    número es el del local y el segundo el del visitante. Se verifica contra
    las cuotas antes de usarlo (ver verificar_orientacion): si se invirtiera,
    todos los resultados saldrían al revés sin que nada fallara.

    "Asian Handicap 0" es el caso de un solo número: cero para los dos.
    """
    bajo = (mercado or "").lower().replace("asian handicap", "").strip()
    if not bajo:
        return None
    primero = bajo.split("/")[0].strip()
    try:
        h = float(primero)
    except ValueError:
        return None
    # Solo enteras y medias. Los cuartos (.25, .75) parten la apuesta.
    if abs(h * 2 - round(h * 2)) > 1e-9:
        return None
    return h


def familia_de(mercado):
    nombre = (mercado or "").strip()
    if nombre in FAMILIAS:
        return nombre, FAMILIAS[nombre], None
    bajo = nombre.lower()
    if bajo.startswith("asian handicap"):
        h = handicap_local(nombre)
        return ("Asian Handicap", FAMILIAS_CON_LINEA["asian handicap"], h) if h is not None else (None, None, None)
    for prefijo, lados in FAMILIAS_CON_LINEA.items():
        if prefijo == "asian handicap":
            continue
        if bajo.startswith(prefijo):
            for trozo in bajo.replace("/", " ").split():
                try:
                    return prefijo.title(), lados, float(trozo)
                except ValueError:
                    continue
            return None, None, None
    return None, None, None


def desmarginar(cuotas):
    inv = {k: 1 / v for k, v in cuotas.items()}
    total = sum(inv.values())
    return {k: v / total for k, v in inv.items()} if total else None


def hechos_del_partido(match_id):
    """Todo lo que hace falta para resolver, de una sola llamada de detalle
    más una de estadísticas. Devuelve None si falta algo esencial: resolver a
    medias inventa resultados."""
    datos = pedir(f"/matches/{match_id}")
    if not datos:
        return None
    m = datos[0] if isinstance(datos, list) else datos
    estado = m.get("state") or {}
    if not str(estado.get("description", "")).lower().startswith("finish"):
        return None
    try:
        gl, gv = [int(x) for x in str(estado.get("score", {}).get("current")).split(" - ")]
    except (ValueError, AttributeError, TypeError):
        return None

    eventos = m.get("events") or []
    tarjetas = len([e for e in eventos if e.get("type") in ("Yellow Card", "Red Card")])

    # primer gol: el evento de gol con el minuto más bajo
    local_id = (m.get("homeTeam") or {}).get("id")
    goles = [e for e in eventos if e.get("type") in ("Goal", "Penalty", "Own Goal")]
    primero = "none"
    if goles:
        def minuto(e):
            try:
                return int(str(e.get("time", "0")).split("+")[0])
            except ValueError:
                return 999
        g = min(goles, key=minuto)
        equipo = (g.get("team") or {}).get("id")
        # un gol en propia puerta lo marca el equipo CONTRARIO al que anota
        if g.get("type") == "Own Goal":
            primero = "away" if equipo == local_id else "home"
        else:
            primero = "home" if equipo == local_id else "away"

    corners = None
    stats = pedir(f"/statistics/{match_id}")
    if stats:
        total = 0
        visto = False
        for bloque in stats:
            for s in (bloque.get("statistics") or []):
                if str(s.get("displayName", "")).lower() == "corners":
                    try:
                        total += float(s.get("value") or 0)
                        visto = True
                    except (TypeError, ValueError):
                        pass
        corners = total if visto else None

    return {"goles_local": gl, "goles_visitante": gv, "tarjetas": tarjetas,
            "corners": corners, "primer_gol": primero,
            "goles": gl + gv, "eventos_con_gol": bool(goles)}


def resolver(familia, lado, linea, h):
    """Devuelve 1.0 si la apuesta gana, 0.0 si pierde, 0.5 si es empate
    (devuelven la apuesta), o None si no se puede resolver con lo que hay."""
    gl, gv, tot = h["goles_local"], h["goles_visitante"], h["goles"]

    if familia == "Full Time Result":
        gana = "home" if gl > gv else ("away" if gv > gl else "draw")
        return 1.0 if lado == gana else 0.0
    if familia == "Both Teams To Score":
        si = gl > 0 and gv > 0
        return 1.0 if (lado == "yes") == si else 0.0
    if familia == "Odd or Even":
        impar = tot % 2 == 1
        return 1.0 if (lado == "odd") == impar else 0.0
    if familia == "Clean Sheet":
        # el equipo no encaja ningún gol
        limpio = (gv == 0) if lado == "home" else (gl == 0)
        return 1.0 if limpio else 0.0
    if familia == "First Team To Score":
        return 1.0 if lado == h["primer_gol"] else 0.0

    if familia == "Asian Handicap":
        if linea is None:
            return None
        # linea es el hándicap del LOCAL. Se suma al marcador local y se mira
        # el signo del margen resultante.
        margen = (gl + linea) - gv if lado == "home" else (gv - linea) - gl
        if abs(margen) < 1e-9:
            return 0.5                   # empate con hándicap: devuelven
        return 1.0 if margen > 0 else 0.0

    observado = {"Total Goals": tot, "Total Cards": h["tarjetas"],
                 "Total Corners": h["corners"]}.get(familia)
    if observado is None or linea is None:
        return None
    if float(observado) == float(linea):
        return 0.5                       # push: se devuelve la apuesta
    supera = float(observado) > float(linea)
    return 1.0 if (lado == "over") == supera else 0.0


def verificar_orientacion(por_mercado):
    """Comprueba que el PRIMER número del nombre es el hándicap del local.

    Si estuviera al revés, el resolver daría todos los hándicaps invertidos y
    nada fallaría: saldrían números plausibles y equivocados. La comprobación
    no necesita documentación, solo lógica de mercado -- un hándicap más
    negativo es más exigente, así que tiene que pagar MÁS.

    Devuelve (ok, detalle). Si sale que no, hay que parar, no seguir.
    """
    pares = []
    por_h = {}
    for (familia, mercado, linea), por_casa in por_mercado.items():
        if familia != "Asian Handicap" or linea is None:
            continue
        for casa, cuotas in por_casa.items():
            if "home" in cuotas:
                por_h[(casa, linea)] = cuotas["home"]
    for (casa, h), cuota in por_h.items():
        opuesta = por_h.get((casa, -h))
        if opuesta is not None and h < 0:
            # h negativo es más exigente que -h positivo: debe pagar más
            pares.append(cuota > opuesta)
    if not pares:
        return None, "sin pares simétricos para comprobar"
    acierto = sum(pares) / len(pares)
    return acierto > 0.9, f"{sum(pares)}/{len(pares)} pares coherentes ({acierto*100:.0f}%)"


def main():
    print("BACKTEST DE VALOR CONTRA EL CONSENSO")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    import json
    if not os.path.exists(RUTA_LIGAS):
        print("Falta data/ligas.json")
        return
    ligas = {k: v for k, v in json.load(open(RUTA_LIGAS, encoding="utf-8")).items()
             if not k.startswith("_")}

    hoy = datetime.now(timezone.utc).date()
    candidatos = []
    for nombre, lid in ligas.items():
        for offset in range(0, 600, 100):
            lote = desempaquetar(pedir("/matches", {"leagueId": lid, "limit": 100,
                                                     "offset": offset}, espera=0.2))
            if not lote:
                break
            for p in lote:
                estado = ((p.get("state") or {}).get("description") or "").lower()
                if not estado.startswith("finish"):
                    continue
                try:
                    cuando = datetime.fromisoformat(str(p["date"]).replace("Z", "+00:00")).date()
                except (ValueError, KeyError, TypeError):
                    continue
                if 0 <= (hoy - cuando).days <= DIAS:
                    candidatos.append((nombre, p))
            if len(lote) < 100:
                break

    candidatos.sort(key=lambda x: str(x[1].get("date")), reverse=True)
    candidatos = candidatos[:MAX_PARTIDOS]
    print(f"{len(candidatos)} partidos terminados en los últimos {DIAS} días")

    filas = []
    for liga, p in candidatos:
        h = hechos_del_partido(p["id"])
        if h is None:
            continue
        datos = pedir("/odds", {"matchId": int(p["id"]), "oddsType": "prematch"})
        planas = []
        for b in desempaquetar(datos):
            if isinstance(b, dict):
                planas.extend(b.get("odds", []) or [])
        if not planas:
            continue

        por_mercado = defaultdict(lambda: defaultdict(dict))
        for c in planas:
            familia, lados, linea = familia_de(c.get("market"))
            if familia is None:
                continue
            for v in (c.get("values") or []):
                lado = str(v.get("value", "")).strip().lower()
                if lado not in lados:
                    continue
                try:
                    cuota = float(v.get("odd"))
                except (TypeError, ValueError):
                    continue
                if cuota > 1:
                    por_mercado[(familia, c.get("market"), linea)][c.get("bookmakerName")][lado] = cuota

        if not VERIFICADO[0] and por_mercado:
            ok, detalle = verificar_orientacion(por_mercado)
            if ok is not None:
                VERIFICADO[0] = True
                print(f"[orientación del hándicap] {detalle}")
                if not ok:
                    print("PARADA: el primer número del nombre NO parece ser el "
                          "del local. Con la orientación invertida todos los "
                          "hándicaps saldrían al revés y los números parecerían "
                          "normales. Hay que revisarlo antes de seguir.")
                    raise SystemExit(1)

        for (familia, mercado, linea), por_casa in por_mercado.items():
            lados = FAMILIAS.get(familia) or FAMILIAS_CON_LINEA.get(familia.lower())
            if lados is None:
                continue
            limpias = {}
            for casa, cuotas in por_casa.items():
                if set(cuotas) != lados:
                    continue
                d = desmarginar(cuotas)
                if d:
                    limpias[casa] = d
            if len(limpias) < MIN_CASAS:
                continue

            for casa, probs in limpias.items():
                for lado in lados:
                    # consenso sin la casa evaluada y sin contar dos veces la
                    # misma cuota (marcas clonadas del mismo operador)
                    vistas = {}
                    for c, q in limpias.items():
                        if c != casa:
                            vistas.setdefault(round(q[lado], 6), c)
                    otras = list(vistas.keys())
                    if len(otras) < MIN_CASAS - 1:
                        continue
                    consenso = float(np.median(otras))
                    if not (PROB_MINIMA <= consenso <= PROB_MAXIMA):
                        continue
                    cuota = por_casa[casa][lado]
                    valor = consenso / (1 / cuota) - 1
                    resultado = resolver(familia, lado, linea, h)
                    if resultado is None:
                        continue
                    # retorno de 1 unidad: gana cuota-1, empate devuelve 0,
                    # pierde -1
                    retorno = (cuota - 1) if resultado == 1.0 else (0.0 if resultado == 0.5 else -1.0)
                    filas.append({
                        "match_id": int(p["id"]), "liga": liga, "casa": casa,
                        "familia": familia, "mercado": mercado, "lado": lado,
                        "cuota": cuota, "consenso": consenso, "valor": valor,
                        "resultado": resultado, "retorno": retorno,
                    })

    if not filas:
        print("Sin datos")
        return

    d = pd.DataFrame(filas)
    os.makedirs("data", exist_ok=True)
    d.to_csv(RUTA_SALIDA, index=False)
    print(f"\n{len(d)} apuestas simuladas sobre {d['match_id'].nunique()} partidos")

    lineas = [
        f"# Backtest de valor -- {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"{len(d)} cotizaciones de {d['match_id'].nunique()} partidos ya "
        f"jugados, de los últimos {DIAS} días.\n",
        "Pregunta: las cuotas que baten al consenso, ¿ganan de verdad?\n",
        "> Las cuotas de un partido terminado son probablemente las de CIERRE, "
        "las más afinadas. Batirlas es más difícil que batir un precio de tres "
        "días antes, así que esta prueba engaña hacia el lado duro: si aquí "
        "sale ventaja, es ventaja.\n",
        "## Por nivel de valor\n",
        "| Valor contra el consenso | Apuestas | Aciertos | Retorno | Por apuesta |",
        "|---|---|---|---|---|",
    ]
    tramos = [(-9, -0.02), (-0.02, 0.0), (0.0, 0.02), (0.02, 0.05), (0.05, 9)]
    etiquetas = ["por debajo de -2%", "-2% a 0%", "0% a +2%", "+2% a +5%", "más de +5%"]
    for (lo, hi), etq in zip(tramos, etiquetas):
        t = d[(d["valor"] > lo) & (d["valor"] <= hi)]
        if t.empty:
            continue
        lineas.append(f"| {etq} | {len(t)} | {(t['resultado']==1.0).mean()*100:.1f}% | "
                      f"{t['retorno'].sum():+.1f} u | **{t['retorno'].mean()*100:+.2f}%** |")

    con_valor = d[d["valor"] > 0.02]
    if len(con_valor) > 10:
        por_partido = con_valor.groupby("match_id")["retorno"].sum()
        err = por_partido.std(ddof=1) * np.sqrt(len(por_partido)) / len(con_valor)
        lineas += [
            "\n## Lo que decide\n",
            f"Apostando solo las cuotas con más de un 2% de valor: "
            f"**{len(con_valor)} apuestas** en {len(por_partido)} partidos.\n",
            f"- Retorno: **{con_valor['retorno'].sum():+.2f} unidades** "
            f"({con_valor['retorno'].mean()*100:+.2f}% por apuesta)",
            f"- Margen de error (1 sigma, agrupando por partido): "
            f"±{err*100:.2f} puntos",
            f"- El resto de cuotas rinde {d[d['valor'] <= 0.02]['retorno'].mean()*100:+.2f}% "
            f"por apuesta\n",
        ]
        t = con_valor["retorno"].mean() / err if err else 0
        if t > 2:
            lineas.append("> Más de 2 sigmas por encima de cero. Es la primera "
                          "señal real que encontramos en todo el proyecto.\n")
        elif con_valor["retorno"].mean() > 0:
            lineas.append(f"> Positivo pero a {t:.1f} sigmas: todavía no se "
                          "distingue de la suerte.\n")
        else:
            lineas.append("> Negativo. El valor contra el consenso no se "
                          "convierte en dinero.\n")

    lineas += ["\n## Por mercado (solo apuestas con más de 2% de valor)\n",
               "| Mercado | Apuestas | Por apuesta |", "|---|---|---|"]
    for fam, g in con_valor.groupby("familia"):
        if len(g) >= 20:
            lineas.append(f"| {fam} | {len(g)} | {g['retorno'].mean()*100:+.2f}% |")

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print("\n".join(lineas))
    print(f"\n[api] {LLAMADAS[0]} llamadas")


if __name__ == "__main__":
    main()
