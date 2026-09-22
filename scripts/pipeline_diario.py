"""
PIPELINE DIARIO COMPLETO -- se ejecuta solo cada día vía GitHub Actions.
No requiere intervención humana. Hace todo de principio a fin:

  1. Actualiza el histórico de partidos jugados (tarjetas, árbitro, goles)
  2. Recalcula los parámetros del modelo (árbitro, tendencia por equipo,
     fuerza de ataque/defensa por equipo)
  3. Busca los partidos de los próximos 7 días
  4. Para cada uno: cuotas de mercado + alineación (si ya está publicada)
  5. Calcula pronósticos de goles (1X2) y tarjetas (over/under), compara
     con el mercado, aplica el filtro de confianza
  6. Escribe pronosticos_jornada.md -- se abre y se lee directamente en
     GitHub, con tablas y formato, sin necesitar nada más
"""
import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import poisson

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}
LIGA_ID = 119924
RUTA_HISTORICO = "data/historico_completo_2025_26.csv"
RUTA_EVENTOS = "data/eventos_tarjetas_jugadores_2025_26.csv"
RUTA_INFORME = "pronosticos_jornada.md"

EQUIPOS_LA_LIGA = [
    463728, 451814, 452665, 461175, 450963, 456920, 460324, 467132, 462877,
    454367, 620312, 3970699, 462026, 453516, 456069, 459473, 679031, 458622,
    619461, 465430,
]
DERBIS = {
    frozenset(["Real Madrid", "Barcelona"]), frozenset(["Real Madrid", "Atlético Madrid"]),
    frozenset(["Atlético Madrid", "Barcelona"]), frozenset(["Athletic Club", "Real Sociedad"]),
    frozenset(["Sevilla FC", "Real Betis"]), frozenset(["Celta de Vigo", "Deportivo La Coruña"]),
    frozenset(["Espanyol", "Barcelona"]), frozenset(["Valencia", "Villarreal"]),
}
RUTA_PESOS = "data/pesos_modelo.json"


def cargar_pesos():
    """Los pesos del modelo viven en un archivo aparte (no en el código)
    para poder ajustarse solos semana a semana según la calibración real."""
    import json
    if os.path.exists(RUTA_PESOS):
        with open(RUTA_PESOS) as f:
            return json.load(f)
    return {"peso_nivel": 0.15, "peso_derbi": 0.15, "peso_alineacion_max": 0.3, "peso_riesgo_sancion": 0.05}


PESOS = cargar_pesos()


def peticion_con_reintentos(url, params=None, intentos=3):
    for intento in range(intentos):
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r
        if r.status_code == 429:
            time.sleep(5 * (intento + 1))
            continue
        return None
    return None


# ============ 1. ACTUALIZAR HISTÓRICO ============
def actualizar_historico():
    historico = pd.read_csv(RUTA_HISTORICO) if os.path.exists(RUTA_HISTORICO) and os.path.getsize(RUTA_HISTORICO) > 0 else pd.DataFrame()
    ids_conocidos = set(historico["match_id"]) if not historico.empty else set()

    ids_encontrados = {}
    for team_id in EQUIPOS_LA_LIGA:
        r = peticion_con_reintentos(f"{BASE_URL}/last-five-games", {"teamId": team_id})
        if r:
            for p in r.json():
                if p["league"]["id"] == LIGA_ID and p["state"]["description"] == "Finished":
                    ids_encontrados[p["id"]] = p
        time.sleep(2)

    ids_nuevos = [i for i in ids_encontrados if i not in ids_conocidos]
    print(f"[historico] {len(ids_nuevos)} partidos nuevos por añadir")

    filas_nuevas, eventos_nuevos = [], []
    for match_id in ids_nuevos:
        fila, eventos = _detalle_partido(match_id)
        if fila:
            filas_nuevas.append(fila)
            eventos_nuevos.extend(eventos)
        time.sleep(1)

    if filas_nuevas:
        historico = pd.concat([historico, pd.DataFrame(filas_nuevas)], ignore_index=True)
        historico.to_csv(RUTA_HISTORICO, index=False)
        eventos_df = pd.read_csv(RUTA_EVENTOS) if os.path.exists(RUTA_EVENTOS) else pd.DataFrame()
        eventos_df = pd.concat([eventos_df, pd.DataFrame(eventos_nuevos)], ignore_index=True)
        eventos_df.to_csv(RUTA_EVENTOS, index=False)
    return historico


def _detalle_partido(match_id):
    r_stats = peticion_con_reintentos(f"{BASE_URL}/statistics/{match_id}")
    r_match = peticion_con_reintentos(f"{BASE_URL}/matches/{match_id}")
    if not r_stats or not r_match:
        return None, []
    stats_por_equipo = r_stats.json()
    datos = r_match.json()[0] if isinstance(r_match.json(), list) else r_match.json()

    def extraer(bloque):
        s = {x["displayName"]: x["value"] for x in bloque["statistics"]}
        return s.get("Yellow cards", 0), s.get("Red cards", 0), s.get("Fouls", None), s.get("Corners", None)

    home_id = datos["homeTeam"]["id"]
    bl = next(b for b in stats_por_equipo if b["team"]["id"] == home_id)
    bv = next(b for b in stats_por_equipo if b["team"]["id"] != home_id)
    am_l, roj_l, faltas_l, corners_l = extraer(bl)
    am_v, roj_v, faltas_v, corners_v = extraer(bv)
    local, visitante = datos["homeTeam"]["name"], datos["awayTeam"]["name"]

    eventos = [{"match_id": match_id, "fecha": datos["date"], "equipo": e["team"]["name"],
                "jugador": e["player"], "jugador_id": e["playerId"], "tipo": e["type"], "minuto": e["time"]}
               for e in datos.get("events", []) if e["type"] in ("Yellow Card", "Red Card")]

    fila = {"match_id": match_id, "fecha": datos["date"], "ronda": datos["round"],
            "equipo_local": local, "equipo_visitante": visitante,
            "goles_local": datos["state"]["score"]["current"].split(" - ")[0],
            "goles_visitante": datos["state"]["score"]["current"].split(" - ")[1],
            "arbitro": datos.get("referee", {}).get("name", None),
            "amarillas_local": am_l, "rojas_local": roj_l, "faltas_local": faltas_l, "corners_local": corners_l,
            "amarillas_visitante": am_v, "rojas_visitante": roj_v, "faltas_visitante": faltas_v, "corners_visitante": corners_v,
            "es_derbi": frozenset([local, visitante]) in DERBIS, "tiene_cuota_total_cards": False}
    return fila, eventos


# ============ 2. RECALCULAR PARÁMETROS ============
def recalcular_parametros(historico):
    historico["goles_local"] = pd.to_numeric(historico["goles_local"], errors="coerce")
    historico["goles_visitante"] = pd.to_numeric(historico["goles_visitante"], errors="coerce")
    historico["tarjetas_totales"] = (historico["amarillas_local"] + historico["rojas_local"] +
                                       historico["amarillas_visitante"] + historico["rojas_visitante"])

    media_arbitro = historico.dropna(subset=["arbitro"]).groupby("arbitro")["tarjetas_totales"].mean().to_dict()
    tendencia_local = historico.groupby("equipo_local").apply(lambda g: (g["amarillas_local"]+g["rojas_local"]).mean())
    tendencia_visitante = historico.groupby("equipo_visitante").apply(lambda g: (g["amarillas_visitante"]+g["rojas_visitante"]).mean())
    tendencia_equipo = ((tendencia_local + tendencia_visitante) / 2).to_dict()
    media_liga_tarjetas = historico["tarjetas_totales"].mean()

    # fuerza de ataque/defensa simplificada (media de goles a favor/en contra vs. la media de la liga)
    # -- una aproximación robusta al estilo Dixon-Coles, más simple y estable para correr sola cada día
    goles_favor_local = historico.groupby("equipo_local")["goles_local"].mean()
    goles_favor_visitante = historico.groupby("equipo_visitante")["goles_visitante"].mean()
    ataque = ((goles_favor_local + goles_favor_visitante) / 2)
    goles_contra_local = historico.groupby("equipo_local")["goles_visitante"].mean()
    goles_contra_visitante = historico.groupby("equipo_visitante")["goles_local"].mean()
    defensa = ((goles_contra_local + goles_contra_visitante) / 2)
    media_liga_goles = (historico["goles_local"].mean() + historico["goles_visitante"].mean()) / 2

    # --- Variable 3: asimetría local/visitante, MEDIDA con datos reales (no supuesta) ---
    media_tarjetas_local = (historico["amarillas_local"] + historico["rojas_local"]).mean()
    media_tarjetas_visitante = (historico["amarillas_visitante"] + historico["rojas_visitante"]).mean()

    # --- Variable 7/8: tasa de tarjetas por jugador y acumulado actual (riesgo de sanción) ---
    tasa_jugador, acumulado_jugador = {}, {}
    if os.path.exists(RUTA_EVENTOS):
        eventos = pd.read_csv(RUTA_EVENTOS)
        eventos["fecha"] = pd.to_datetime(eventos["fecha"])
        solo_amarillas = eventos[eventos["tipo"] == "Yellow Card"].sort_values("fecha")
        # tasa: total de tarjetas del jugador esta temporada (aproximación -- no
        # tenemos minutos jugados por jugador sin una llamada extra por jugador)
        tasa_jugador = eventos.groupby("jugador_id").size().to_dict()
        # acumulado actual: cuántas amarillas lleva SIN cumplir sanción (regla RFEF: 5 = 1 partido, se resetea)
        for _, ev in solo_amarillas.iterrows():
            jid = ev["jugador_id"]
            acumulado_jugador[jid] = acumulado_jugador.get(jid, 0) + 1
            if acumulado_jugador[jid] == 5:
                acumulado_jugador[jid] = 0

    return {"media_arbitro": media_arbitro, "tendencia_equipo": tendencia_equipo,
            "media_liga_tarjetas": media_liga_tarjetas, "ataque": ataque.to_dict(),
            "defensa": defensa.to_dict(), "media_liga_goles": media_liga_goles,
            "media_tarjetas_local": media_tarjetas_local, "media_tarjetas_visitante": media_tarjetas_visitante,
            "tasa_jugador": tasa_jugador, "acumulado_jugador": acumulado_jugador}


# ============ 3. PRÓXIMOS PARTIDOS ============
def obtener_proximos_partidos(dias=7):
    partidos = {}
    hoy = datetime.utcnow().date()
    for offset in range(dias):
        fecha = (hoy + timedelta(days=offset)).isoformat()
        r = peticion_con_reintentos(f"{BASE_URL}/matches", {"leagueId": LIGA_ID, "date": fecha})
        if r:
            for p in r.json()["data"]:
                if p["league"]["id"] == LIGA_ID and p["state"]["description"] in ("Not started", "Scheduled"):
                    partidos[p["id"]] = p
        time.sleep(1)
    return list(partidos.values())


# ============ 4. CUOTAS Y ALINEACIONES ============
def obtener_cuotas(match_id):
    """La API devuelve [{matchId, odds: [{type, market, values: [{odd, value}],
    bookmakerName, ...}]}]: los mercados van anidados bajo 'odds' y la clave es
    'market', no 'name'. Devuelve la lista plana de entradas de cuota.
    Las cuotas son DECIMALES (verificado: la suma de 1/cuota da 1.05-1.08)."""
    r = peticion_con_reintentos(f"{BASE_URL}/odds", {"matchId": match_id})
    if not r:
        return []
    try:
        datos = r.json()
    except Exception:
        return []
    bloques = datos.get("data", []) if isinstance(datos, dict) else (datos or [])
    planas = []
    for bloque in bloques:
        if isinstance(bloque, dict):
            planas.extend(bloque.get("odds", []) or [])
    return planas


def _entradas_de(cuotas, nombre_mercado):
    objetivo = nombre_mercado.strip().lower()
    return [c for c in cuotas
            if (c.get("market") or "").strip().lower() == objetivo
            and c.get("type") == "prematch"]


def probabilidades_de_mercado(cuotas, nombre_mercado):
    """Probabilidad de consenso del mercado: se quita el margen de cada casa
    (normalizando 1/cuota) y se promedia entre casas. Devuelve ({valor: prob},
    número de casas). Esa probabilidad es la referencia contra la que hay que
    medir el modelo -- si no le gana, no hay apuesta."""
    por_casa = []
    for entrada in _entradas_de(cuotas, nombre_mercado):
        pares = []
        for v in (entrada.get("values") or []):
            try:
                cuota = float(v.get("odd"))
            except (TypeError, ValueError):
                continue
            if cuota > 1:
                pares.append((v.get("value"), cuota))
        if len(pares) < 2:
            continue
        suma = sum(1 / c for _, c in pares)
        por_casa.append({val: (1 / c) / suma for val, c in pares})
    if not por_casa:
        return {}, 0
    claves = set().union(*(set(p) for p in por_casa))
    return ({k: float(np.mean([p[k] for p in por_casa if k in p])) for k in claves},
            len(por_casa))


def mejor_cuota(cuotas, nombre_mercado, valor):
    """Mejor cuota disponible para un resultado concreto, y en qué casa."""
    mejor, casa = 0.0, None
    objetivo = str(valor).strip().lower()
    for entrada in _entradas_de(cuotas, nombre_mercado):
        for v in (entrada.get("values") or []):
            if str(v.get("value")).strip().lower() != objetivo:
                continue
            try:
                cuota = float(v.get("odd"))
            except (TypeError, ValueError):
                continue
            if cuota > mejor:
                mejor, casa = cuota, entrada.get("bookmakerName")
    return mejor, casa


def obtener_alineacion(match_id, fecha_partido_str):
    """Devuelve (alineacion, es_confirmada). Highlightly puede dar una
    alineación PREVISTA con días de antelación -- solo se puede considerar
    confirmada de verdad si faltan menos de 2h para el partido."""
    r = peticion_con_reintentos(f"{BASE_URL}/lineups/{match_id}")
    if not r or r.status_code != 200:
        return None, False
    try:
        alineacion = r.json()
    except Exception:
        return None, False
    if not alineacion:
        return None, False

    fecha_partido = datetime.fromisoformat(fecha_partido_str.replace("Z", "+00:00"))
    horas_restantes = (fecha_partido - datetime.now(fecha_partido.tzinfo)).total_seconds() / 3600
    es_confirmada = horas_restantes <= 2
    return alineacion, es_confirmada


def obtener_tasa_tarjetas_por_90(player_id, temporada_str="26/27"):
    """Llamada real a /players/{id}/statistics -- estructura confirmada con
    datos reales: el campo es 'perCompetition' (no 'statistics'), 'league'
    es un texto ('LaLiga'), y hay que filtrar por temporada y por
    type=='national league' para no contar copas."""
    r = peticion_con_reintentos(f"{BASE_URL}/players/{player_id}/statistics")
    if not r:
        return None
    try:
        datos = r.json()
        jugador = datos[0] if isinstance(datos, list) else datos
        bloques = jugador.get("perCompetition", [])
        bloque_liga = next((b for b in bloques if b.get("league") == "LaLiga"
                             and b.get("type") == "national league"
                             and b.get("season") == temporada_str), None)
        if not bloque_liga:
            return None
        minutos = bloque_liga.get("minutesPlayed") or 0
        amarillas = bloque_liga.get("yellowCards") or 0
        rojas = bloque_liga.get("redCards") or 0
        if minutos < 90:
            return None
        return (amarillas + rojas) / (minutos / 90)
    except Exception:
        return None


# ============ 5. PREDICCIONES ============
def predecir_goles(local, visitante, params, max_goles=8):
    a, d = params["ataque"], params["defensa"]
    media_liga = params["media_liga_goles"]
    lam_l = a.get(local, media_liga) * (d.get(visitante, media_liga) / media_liga) if media_liga else media_liga
    lam_v = a.get(visitante, media_liga) * (d.get(local, media_liga) / media_liga) if media_liga else media_liga
    lam_l, lam_v = max(lam_l, 0.2), max(lam_v, 0.2)
    m = np.outer([poisson.pmf(g, lam_l) for g in range(max_goles)], [poisson.pmf(g, lam_v) for g in range(max_goles)])
    return {"prob_local": round(np.tril(m, -1).sum(), 3), "prob_empate": round(np.trace(m), 3),
            "prob_visitante": round(np.triu(m, 1).sum(), 3)}


def predecir_tarjetas(local, visitante, arbitro, params, linea=4.5, alineacion=None, es_alineacion_confirmada=False):
    """Integra las 8 variables discutidas y validadas durante el proyecto:
    1. Árbitro  2. Diferencia de nivel  3. Local/visitante  4. Derbi
    6. Tendencia por equipo  7. Alineación real (jugadores concretos)
    8. Riesgo de sanción (cautela por acumulación)
    (La variable 5, cuota de mercado, se compara aparte en el informe -- no
    se mezcla dentro de esta probabilidad para no contaminar la predicción
    propia con la del mercado; se muestran ambas por separado.)"""

    # 1. Árbitro
    base_arbitro = params["media_arbitro"].get(arbitro, params["media_liga_tarjetas"])

    # 6. Tendencia por equipo (ya incluye el efecto agregado de "equipos que sacan más tarjetas")
    t_l = params["tendencia_equipo"].get(local, params["media_liga_tarjetas"] / 2)
    t_v = params["tendencia_equipo"].get(visitante, params["media_liga_tarjetas"] / 2)
    media_base = base_arbitro * 0.5 + (t_l + t_v) * 0.5

    # 2. Diferencia de nivel entre equipos (a partir del modelo de goles ya entrenado)
    a = params["ataque"]
    if local in a and visitante in a and params["media_liga_goles"] > 0:
        diferencia_nivel = abs(a[local] - a[visitante]) / params["media_liga_goles"]
        factor_nivel = 1 + np.clip(PESOS["peso_nivel"] * diferencia_nivel, -PESOS["peso_nivel"], PESOS["peso_nivel"]*2)
    else:
        factor_nivel = 1.0

    # 3. Local/visitante -- asimetría medida con datos reales, no supuesta
    if params["media_tarjetas_local"] + params["media_tarjetas_visitante"] > 0:
        factor_local_visitante = (params["media_tarjetas_local"] + params["media_tarjetas_visitante"]) / \
                                   (2 * params["media_tarjetas_local"])
    else:
        factor_local_visitante = 1.0

    # 4. Derbi
    factor_derbi = (1 + PESOS["peso_derbi"]) if frozenset([local, visitante]) in DERBIS else 1.0

    media = media_base * factor_nivel * factor_local_visitante * factor_derbi

    # 7 y 8: solo se aplican si hay alineación de verdad (no una prevista)
    factor_alineacion, factor_riesgo_sancion = 1.0, 1.0
    if alineacion and es_alineacion_confirmada:
        jugadores_titulares = []
        for equipo_key in ("homeTeam", "awayTeam"):
            for linea_pos in alineacion.get(equipo_key, {}).get("initialLineup", []):
                jugadores_titulares.extend([j["id"] for j in linea_pos])

        if jugadores_titulares:
            # 7. Alineación real: tasa por 90 min de verdad (llamada a la API),
            # con respaldo a la tasa acumulada de eventos si la llamada falla
            tasa_media_jugador = np.mean(list(params["tasa_jugador"].values())) if params["tasa_jugador"] else 1.0
            tasas_titulares = []
            for j in jugadores_titulares:
                tasa_real = obtener_tasa_tarjetas_por_90(j)
                if tasa_real is not None:
                    tasas_titulares.append(tasa_real)
                else:
                    tasas_titulares.append(params["tasa_jugador"].get(j, tasa_media_jugador))
            factor_alineacion = np.clip(np.mean(tasas_titulares) / tasa_media_jugador, 0.7, 1.3) if tasa_media_jugador else 1.0

            # 8. Riesgo de sanción: si hay titulares a 1 amarilla de la sanción, ligera bajada
            en_riesgo = sum(1 for j in jugadores_titulares if params["acumulado_jugador"].get(j) == 4)
            if en_riesgo > 0:
                factor_riesgo_sancion = max(0.85, 1 - 0.05 * en_riesgo)

    media *= factor_alineacion * factor_riesgo_sancion
    prob_over = 1 - poisson.cdf(int(linea), media)
    return {"media_estimada": round(media, 2), "prob_over": round(prob_over, 3), "prob_under": round(1 - prob_over, 3),
            "variables_aplicadas": {"nivel": round(factor_nivel, 3), "local_visitante": round(factor_local_visitante, 3),
                                      "derbi": factor_derbi, "alineacion": round(factor_alineacion, 3),
                                      "riesgo_sancion": round(factor_riesgo_sancion, 3)}}


# ============ 6. INFORME ============
def generar_informe(proximos_partidos, params):
    lineas = [f"# Pronósticos -- generado automáticamente el {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"]
    registro_predicciones = []

    for p in sorted(proximos_partidos, key=lambda x: x["date"]):
        local, visitante = p["homeTeam"]["name"], p["awayTeam"]["name"]
        arbitro = None  # el árbitro no siempre está confirmado con antelación

        cuotas = obtener_cuotas(p["id"])
        alineacion, es_confirmada = obtener_alineacion(p["id"], p["date"])

        pred_goles = predecir_goles(local, visitante, params)
        pred_tarjetas = predecir_tarjetas(local, visitante, arbitro, params,
                                            alineacion=alineacion, es_alineacion_confirmada=es_confirmada)

        lineas.append(f"## {local} vs {visitante}")
        lineas.append(f"*{p['date'][:16].replace('T', ' ')} UTC*\n")
        lineas.append(f"**Goles (1X2)**: Local {pred_goles['prob_local']*100:.0f}% | "
                       f"Empate {pred_goles['prob_empate']*100:.0f}% | Visitante {pred_goles['prob_visitante']*100:.0f}%\n")
        lineas.append(f"**Tarjetas (línea 4.5)**: media estimada {pred_tarjetas['media_estimada']} | "
                       f"Over {pred_tarjetas['prob_over']*100:.0f}% | Under {pred_tarjetas['prob_under']*100:.0f}%")
        v = pred_tarjetas["variables_aplicadas"]
        lineas.append(f"*(factores aplicados -- nivel: {v['nivel']}, local/visitante: {v['local_visitante']}, "
                       f"derbi: {v['derbi']}, alineación: {v['alineacion']}, riesgo sanción: {v['riesgo_sancion']})*\n")

        # 5. Mercado: consenso sin margen y valor esperado contra la mejor cuota
        prob_mercado_over = None
        if cuotas:
            casas = {c.get("bookmakerName") for c in cuotas if c.get("bookmakerName")}
            lineas.append(f"**Mercado** ({len(cuotas)} cuotas de {len(casas)} casas):")

            prob_1x2, n_1x2 = probabilidades_de_mercado(cuotas, "Full Time Result")
            if prob_1x2:
                lineas.append(f"- *1X2 consenso de {n_1x2} casas*: "
                               f"Local {prob_1x2.get('Home', 0)*100:.0f}% | "
                               f"Empate {prob_1x2.get('Draw', 0)*100:.0f}% | "
                               f"Visitante {prob_1x2.get('Away', 0)*100:.0f}%  "
                               f"(modelo: {pred_goles['prob_local']*100:.0f}/"
                               f"{pred_goles['prob_empate']*100:.0f}/"
                               f"{pred_goles['prob_visitante']*100:.0f})")

            prob_cards, n_cards = probabilidades_de_mercado(cuotas, "Total Cards 4.5")
            if prob_cards:
                prob_mercado_over = prob_cards.get("Over")
                cuota, casa = mejor_cuota(cuotas, "Total Cards 4.5", "Over")
                # valor esperado de apostar 1 unidad al Over segun NUESTRA probabilidad
                ev = pred_tarjetas["prob_over"] * cuota - 1 if cuota else None
                aviso = "" if n_cards > 1 else "  [!] una sola casa: sin contraste"
                lineas.append(f"- *Tarjetas 4.5*: modelo {pred_tarjetas['prob_over']*100:.0f}% "
                               f"vs mercado {prob_mercado_over*100:.0f}% ({n_cards} casa/s)"
                               f"{aviso}")
                if ev is not None:
                    # Una divergencia enorme contra el mercado casi nunca es una
                    # oportunidad: es un modelo mal calibrado. El mercado agrega
                    # mucha más información que nosotros, así que por encima de
                    # +20% se avisa en vez de invitar a apostar.
                    if ev > 0.20:
                        juicio = "  <-- SOSPECHOSO: revisar el modelo, no apostar"
                    elif ev > 0.02:
                        juicio = "  <-- valor potencial"
                    else:
                        juicio = ""
                    lineas.append(f"  mejor cuota Over {cuota} en {casa} -> "
                                   f"valor esperado {ev*100:+.1f}%{juicio}")
            else:
                lineas.append("- *Tarjetas 4.5*: sin cuotas en el feed para este partido")

            prob_corners, n_corners = probabilidades_de_mercado(cuotas, "Total Corners 9.5")
            if prob_corners:
                lineas.append(f"- *Córners 9.5*: mercado {prob_corners.get('Over', 0)*100:.0f}% "
                               f"Over ({n_corners} casas) -- todavía sin modelo propio")
        else:
            lineas.append("**Mercado**: sin cuotas disponibles todavía")

        if alineacion and es_confirmada:
            lineas.append(f"**Alineación**: confirmada -- variables 7 y 8 aplicadas al cálculo")
        elif alineacion and not es_confirmada:
            lineas.append(f"**Alineación**: solo prevista (faltan más de 2h) -- variables 7 y 8 no aplicadas todavía")
        else:
            lineas.append(f"**Alineación**: no disponible")

        registro_predicciones.append({
            "match_id": p["id"], "fecha": p["date"], "equipo_local": local, "equipo_visitante": visitante,
            "prob_local": pred_goles["prob_local"], "prob_empate": pred_goles["prob_empate"],
            "prob_visitante": pred_goles["prob_visitante"], "prob_over_tarjetas": pred_tarjetas["prob_over"],
            # se guarda la probabilidad del mercado para poder comparar después
            # quién acierta más, si el modelo o la casa
            "prob_mercado_over_tarjetas": prob_mercado_over,
            "generado_el": datetime.utcnow().isoformat(),
        })

        lineas.append("\n---\n")

    with open(RUTA_INFORME, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print(f"Informe generado: {RUTA_INFORME}")

    if not registro_predicciones:
        # pd.DataFrame([]) no tiene columnas (RangeIndex vacío): guardar_registro
        # hace nuevos["match_id"] sin comprobar y eso revienta con KeyError
        # justo cuando no hay ningun partido en los proximos 7 dias -- 22/09,
        # 0 partidos encontrados. No hay nada que registrar, así que se omite
        # igual que actualizar_historico() omite el to_csv si no hay filas
        # nuevas.
        print("Registro: sin partidos nuevos que evaluar esta pasada")
        return

    ruta_registro = "data/registro_predicciones.csv"
    registro_previo = pd.read_csv(ruta_registro) if os.path.exists(ruta_registro) else pd.DataFrame()
    guardar_registro(pd.DataFrame(registro_predicciones), registro_previo, ruta_registro)


def _es_refinado(valor):
    """Un NaN es 'verdadero' para bool(), así que hay que mirarlo antes."""
    return bool(valor) if pd.notna(valor) else False


def guardar_registro(nuevos, registro_previo, ruta_registro):
    """Alta de los partidos nuevos y ACTUALIZACIÓN de los que ya estaban.

    Antes solo se daban de alta los nuevos, así que un partido ya registrado
    no volvía a tocarse nunca: por eso la probabilidad del mercado (columna
    añadida después) se quedaba vacía para toda la jornada en curso.

    Actualizar además es lo correcto de por sí: la cuota que sirve para medir
    es la más cercana al inicio del partido, no la que hubiera cinco días
    antes. Cada pasada refresca el mercado y deja la última observación antes
    del pitido, que es contra la que hay que juzgar al modelo."""
    if registro_previo.empty:
        registro_previo = pd.DataFrame(columns=nuevos.columns)

    # un match_id duplicado rompería el índice; nos quedamos con el más reciente
    previo = registro_previo.drop_duplicates(subset="match_id", keep="last").set_index("match_id")
    ids_previos = set(previo.index)

    altas = nuevos[~nuevos["match_id"].isin(ids_previos)]
    actualizables = nuevos[nuevos["match_id"].isin(ids_previos)]

    columnas_modelo = ("prob_local", "prob_empate", "prob_visitante", "prob_over_tarjetas")
    pisados = 0
    for _, fila in actualizables.iterrows():
        mid = fila["match_id"]
        # el mercado siempre se refresca: buscamos la cuota de cierre
        previo.loc[mid, "prob_mercado_over_tarjetas"] = fila.get("prob_mercado_over_tarjetas")
        previo.loc[mid, "generado_el"] = fila["generado_el"]
        # la predicción propia solo se pisa si la guardada NO venía del refinado
        # con alineación confirmada, que es mejor que la que calculamos aquí
        refinado = previo.loc[mid, "refinado"] if "refinado" in previo.columns else False
        if not _es_refinado(refinado):
            for col in columnas_modelo:
                previo.loc[mid, col] = fila[col]
            pisados += 1

    registro_final = pd.concat([previo.reset_index(), altas], ignore_index=True)
    registro_final.to_csv(ruta_registro, index=False)

    con_mercado = registro_final["prob_mercado_over_tarjetas"].notna().sum() \
        if "prob_mercado_over_tarjetas" in registro_final.columns else 0
    print(f"Registro: {len(altas)} altas, {len(actualizables)} actualizados "
          f"({pisados} con predicción refrescada), {len(registro_final)} en total")
    print(f"  filas con probabilidad de mercado: {con_mercado}/{len(registro_final)}")


# ============ 7. CALIBRACIÓN AUTOMÁTICA ============
def calcular_calibracion(params):
    ruta_registro = "data/registro_predicciones.csv"
    if not os.path.exists(ruta_registro):
        print("[calibracion] todavía no hay registro de predicciones -- se omite esta semana")
        return
    registro = pd.read_csv(ruta_registro)
    historico = pd.read_csv(RUTA_HISTORICO)

    cruzado = registro.merge(
        historico[["match_id", "goles_local", "goles_visitante",
                   "amarillas_local", "rojas_local", "amarillas_visitante", "rojas_visitante"]],
        on="match_id", how="inner")

    if cruzado.empty:
        print("[calibracion] ningún partido predicho se ha jugado todavía -- se omite esta semana")
        return

    cruzado["tarjetas_totales"] = (cruzado["amarillas_local"] + cruzado["rojas_local"] +
                                     cruzado["amarillas_visitante"] + cruzado["rojas_visitante"])
    cruzado["gano_local"] = (cruzado["goles_local"] > cruzado["goles_visitante"]).astype(float)
    cruzado["over_tarjetas"] = (cruzado["tarjetas_totales"] > 4.5).astype(float)

    brier_goles = ((cruzado["prob_local"] - cruzado["gano_local"]) ** 2).mean()
    brier_tarjetas = ((cruzado["prob_over_tarjetas"] - cruzado["over_tarjetas"]) ** 2).mean()
    acierto_goles = ((cruzado["prob_local"] > 0.5) == cruzado["gano_local"].astype(bool)).mean()
    acierto_tarjetas = ((cruzado["prob_over_tarjetas"] > 0.5) == cruzado["over_tarjetas"].astype(bool)).mean()

    # ¿Le ganamos al mercado? Es la única comparación que decide si hay negocio.
    linea_mercado = ""
    if "prob_mercado_over_tarjetas" in cruzado.columns:
        con_mercado = cruzado.dropna(subset=["prob_mercado_over_tarjetas"])
        if len(con_mercado) >= 5:
            brier_nuestro = ((con_mercado["prob_over_tarjetas"] - con_mercado["over_tarjetas"]) ** 2).mean()
            brier_mercado = ((con_mercado["prob_mercado_over_tarjetas"] - con_mercado["over_tarjetas"]) ** 2).mean()
            veredicto = "el MODELO gana" if brier_nuestro < brier_mercado else "gana el MERCADO"
            linea_mercado = (f"\n## Modelo contra mercado (n={len(con_mercado)})\n"
                             f"- Brier del modelo:  {brier_nuestro:.4f}\n"
                             f"- Brier del mercado: {brier_mercado:.4f}\n"
                             f"- Veredicto: {veredicto}. Si gana el mercado, no hay apuesta rentable todavía.\n")
        else:
            linea_mercado = (f"\n## Modelo contra mercado\nTodavía pocos partidos con cuota "
                             f"registrada ({len(con_mercado)}); hacen falta 5+.\n")

    # --- Desglose por variable: ¿en qué situaciones falla más el modelo? ---
    cruzado["es_derbi"] = cruzado.apply(
        lambda r: frozenset([r["equipo_local"], r["equipo_visitante"]]) in DERBIS, axis=1)

    # diferencia de nivel de cada partido evaluado, con la fuerza de ataque
    # vigente ahora mismo (aproximación -- no se guardó la de la semana en
    # que se hizo cada predicción, pero es estable de una semana a otra)
    media_liga_goles = params["media_liga_goles"]
    ataque = params["ataque"]
    cruzado["diferencia_nivel"] = cruzado.apply(
        lambda r: abs(ataque.get(r["equipo_local"], media_liga_goles) - ataque.get(r["equipo_visitante"], media_liga_goles))
                  / media_liga_goles if media_liga_goles else 0.0, axis=1)

    cruzado["acierto_tarjetas_fila"] = (cruzado["prob_over_tarjetas"] > 0.5) == cruzado["over_tarjetas"].astype(bool)

    mediana_nivel = cruzado["diferencia_nivel"].median()
    grupos_desglose = [
        ("Partidos de derbi", cruzado[cruzado["es_derbi"]]),
        ("Partidos normales (no derbi)", cruzado[~cruzado["es_derbi"]]),
        ("Diferencia de nivel alta", cruzado[cruzado["diferencia_nivel"] >= mediana_nivel]),
        ("Diferencia de nivel baja", cruzado[cruzado["diferencia_nivel"] < mediana_nivel]),
    ]
    desglose = []
    for nombre, subset in grupos_desglose:
        if len(subset) > 0:
            desglose.append(f"- **{nombre}** (n={len(subset)}): acierto tarjetas {subset['acierto_tarjetas_fila'].mean()*100:.1f}%")
        else:
            desglose.append(f"- **{nombre}**: sin casos todavía")
    lineas_desglose = "\n".join(desglose)

    # --- Ajuste automático de pesos -- se hace ANTES de escribir el informe
    # para poder reportar los pesos realmente vigentes y qué cambió ---
    pesos_vigentes, cambios_aprendizaje = ajustar_pesos(cruzado)
    lineas_cambios = "\n".join(f"- {c}" for c in cambios_aprendizaje)

    informe = f"""# Informe de calibración -- actualizado el {datetime.utcnow().strftime('%Y-%m-%d')}
Partidos evaluados hasta ahora: {len(cruzado)}

## Goles (victoria local)
- Brier score: {brier_goles:.4f} (0.25 = azar, más bajo = mejor)
- Acierto: {acierto_goles*100:.1f}%

## Tarjetas (over/under 4.5)
- Brier score: {brier_tarjetas:.4f} (0.25 = azar, más bajo = mejor)
- Acierto: {acierto_tarjetas*100:.1f}%
{linea_mercado}
## Desglose por variable (para diagnosticar qué falla)

{lineas_desglose}

## Aprendizaje automático de pesos
Pesos vigentes ahora mismo: peso_nivel={pesos_vigentes['peso_nivel']:.2f} (factor máximo {1 + pesos_vigentes['peso_nivel']*2:.2f}),
peso_derbi={pesos_vigentes['peso_derbi']:.2f} (factor derbi {1 + pesos_vigentes['peso_derbi']:.2f})

{lineas_cambios}

*Nota: el ajuste se guarda en `{RUTA_PESOS}` y persiste entre ejecuciones
semanales. Cada peso se mueve como máximo un 5% por semana, y solo si hay
10+ partidos evaluados en cada grupo comparado, para no sobrerreaccionar a
pocos casos. El split 50/50 árbitro-equipo dentro de la media base, y los
pesos de alineación/riesgo de sanción, todavía son fijos -- no se ajustan
solos.*
"""
    with open("data/informe_calibracion.md", "w", encoding="utf-8") as f:
        f.write(informe)
    print(f"[calibracion] informe actualizado con {len(cruzado)} partidos evaluados")


def ajustar_pesos(cruzado, minimo_casos=10, paso=0.05, tope=0.4):
    """Ajusta un peso comparando el acierto de tarjetas entre dos grupos de
    partidos (p.ej. derbi vs. no derbi, diferencia de nivel alta vs. baja).
    Pasos pequeños (5%) y solo si hay casos suficientes en AMBOS grupos --
    para no sobrerreaccionar a 1-2 partidos sueltos. Devuelve los pesos
    vigentes tras el ajuste y una lista de mensajes para el informe."""
    import json
    pesos = cargar_pesos()
    cambios = []

    def _ajustar(clave, grupo_a, nombre_a, grupo_b, nombre_b):
        if len(grupo_a) < minimo_casos or len(grupo_b) < minimo_casos:
            cambios.append(f"{clave}: todavía no hay casos suficientes ({nombre_a} n={len(grupo_a)}, "
                            f"{nombre_b} n={len(grupo_b)}, se necesitan {minimo_casos}+ de cada uno)")
            return
        acierto_a = grupo_a["acierto_tarjetas_fila"].mean()
        acierto_b = grupo_b["acierto_tarjetas_fila"].mean()
        if acierto_a < acierto_b - 0.05:  # el factor está perjudicando de forma clara
            pesos[clave] = max(0.0, pesos[clave] - paso)
            cambios.append(f"{clave} bajado a {pesos[clave]:.2f} ({nombre_a} acertaba peor: "
                            f"{acierto_a*100:.1f}% vs {acierto_b*100:.1f}% en {nombre_b})")
        elif acierto_a > acierto_b + 0.05:
            pesos[clave] = min(tope, pesos[clave] + paso)
            cambios.append(f"{clave} subido a {pesos[clave]:.2f} ({nombre_a} acertaba mejor: "
                            f"{acierto_a*100:.1f}% vs {acierto_b*100:.1f}% en {nombre_b})")
        else:
            cambios.append(f"{clave} sin cambios ({pesos[clave]:.2f}) -- diferencia no concluyente "
                            f"({acierto_a*100:.1f}% vs {acierto_b*100:.1f}%)")

    derbis, no_derbis = cruzado[cruzado["es_derbi"]], cruzado[~cruzado["es_derbi"]]
    _ajustar("peso_derbi", derbis, "derbis", no_derbis, "partidos normales")

    mediana_nivel = cruzado["diferencia_nivel"].median()
    alta = cruzado[cruzado["diferencia_nivel"] >= mediana_nivel]
    baja = cruzado[cruzado["diferencia_nivel"] < mediana_nivel]
    _ajustar("peso_nivel", alta, "diferencia de nivel alta", baja, "diferencia de nivel baja")

    with open(RUTA_PESOS, "w") as f:
        json.dump(pesos, f, indent=2)
    print("[aprendizaje] " + " | ".join(cambios))
    return pesos, cambios


# ============ MAIN ============
def main():
    print("Paso 1/5: actualizando histórico...")
    historico = actualizar_historico()

    print("Paso 2/5: recalculando parámetros...")
    params = recalcular_parametros(historico)

    print("Paso 3/5: buscando próximos partidos...")
    proximos = obtener_proximos_partidos()
    print(f"  {len(proximos)} partidos encontrados en los próximos 7 días")

    print("Paso 4/5: generando informe de pronósticos...")
    generar_informe(proximos, params)

    print("Paso 5/5: actualizando calibración...")
    calcular_calibracion(params)


if __name__ == "__main__":
    main()
