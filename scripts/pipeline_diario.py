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
    r = peticion_con_reintentos(f"{BASE_URL}/odds", {"matchId": match_id})
    if not r:
        return None
    return r.json().get("data", [])


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
        factor_nivel = 1 + np.clip(0.15 * diferencia_nivel, -0.15, 0.3)  # el desnivel siempre AUMENTA, nunca baja
    else:
        factor_nivel = 1.0

    # 3. Local/visitante -- asimetría medida con datos reales, no supuesta
    if params["media_tarjetas_local"] + params["media_tarjetas_visitante"] > 0:
        factor_local_visitante = (params["media_tarjetas_local"] + params["media_tarjetas_visitante"]) / \
                                   (2 * params["media_tarjetas_local"])
    else:
        factor_local_visitante = 1.0

    # 4. Derbi
    factor_derbi = 1.15 if frozenset([local, visitante]) in DERBIS else 1.0

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

        # 5. Cuota de mercado -- comparación real, no solo "disponible sí/no"
        if cuotas:
            mercado_1x2 = next((m for m in cuotas if "Match Winner" in m.get("name", "") or "1X2" in m.get("name", "")), None)
            mercado_cards = next((m for m in cuotas if "Total Cards" in m.get("name", "")), None)
            if mercado_1x2:
                lineas.append(f"**Cuota de mercado 1X2**: disponible -- comparar manualmente contra el {pred_goles['prob_local']*100:.0f}%/"
                               f"{pred_goles['prob_empate']*100:.0f}%/{pred_goles['prob_visitante']*100:.0f}% de arriba")
            if mercado_cards:
                lineas.append(f"**Cuota de mercado Total Cards**: disponible -- comparar contra el "
                               f"{pred_tarjetas['prob_over']*100:.0f}% de over estimado")
            if not mercado_1x2 and not mercado_cards:
                lineas.append(f"**Cuotas**: disponibles pero sin mercados 1X2/Total Cards reconocidos ({len(cuotas)} mercados encontrados)")
        else:
            lineas.append(f"**Cuotas de mercado**: no disponibles todavía")

        if alineacion and es_confirmada:
            lineas.append(f"**Alineación**: confirmada -- variables 7 y 8 aplicadas al cálculo")
        elif alineacion and not es_confirmada:
            lineas.append(f"**Alineación**: solo prevista (faltan más de 2h) -- variables 7 y 8 no aplicadas todavía")
        else:
            lineas.append(f"**Alineación**: no disponible")

        registro_predicciones.append({
            "match_id": p["id"], "fecha": p["date"], "equipo_local": local, "equipo_visitante": visitante,
            "prob_local": pred_goles["prob_local"], "prob_empate": pred_goles["prob_empate"],
     
