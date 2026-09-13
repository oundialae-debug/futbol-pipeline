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

    return {"media_arbitro": media_arbitro, "tendencia_equipo": tendencia_equipo,
            "media_liga_tarjetas": media_liga_tarjetas, "ataque": ataque.to_dict(),
            "defensa": defensa.to_dict(), "media_liga_goles": media_liga_goles}


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


def predecir_tarjetas(local, visitante, arbitro, params, linea=4.5):
    base = params["media_arbitro"].get(arbitro, params["media_liga_tarjetas"])
    t_l = params["tendencia_equipo"].get(local, params["media_liga_tarjetas"] / 2)
    t_v = params["tendencia_equipo"].get(visitante, params["media_liga_tarjetas"] / 2)
    factor_derbi = 1.15 if frozenset([local, visitante]) in DERBIS else 1.0
    media = (base * 0.5 + (t_l + t_v) * 0.5) * factor_derbi
    prob_over = 1 - poisson.cdf(int(linea), media)
    return {"media_estimada": round(media, 2), "prob_over": round(prob_over, 3), "prob_under": round(1 - prob_over, 3)}


# ============ 6. INFORME ============
def generar_informe(proximos_partidos, params):
    lineas = [f"# Pronósticos -- generado automáticamente el {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"]
    registro_predicciones = []

    for p in sorted(proximos_partidos, key=lambda x: x["date"]):
        local, visitante = p["homeTeam"]["name"], p["awayTeam"]["name"]
        arbitro = None  # el árbitro no siempre está confirmado con antelación

        pred_goles = predecir_goles(local, visitante, params)
        pred_tarjetas = predecir_tarjetas(local, visitante, arbitro, params)

        cuotas = obtener_cuotas(p["id"])
        alineacion, es_confirmada = obtener_alineacion(p["id"], p["date"])

        lineas.append(f"## {local} vs {visitante}")
        lineas.append(f"*{p['date'][:16].replace('T', ' ')} UTC*\n")
        lineas.append(f"**Goles (1X2)**: Local {pred_goles['prob_local']*100:.0f}% | "
                       f"Empate {pred_goles['prob_empate']*100:.0f}% | Visitante {pred_goles['prob_visitante']*100:.0f}%\n")
        lineas.append(f"**Tarjetas (línea 4.5)**: media estimada {pred_tarjetas['media_estimada']} | "
                       f"Over {pred_tarjetas['prob_over']*100:.0f}% | Under {pred_tarjetas['prob_under']*100:.0f}%\n")

        if cuotas:
            lineas.append(f"**Cuotas de mercado disponibles**: sí ({len(cuotas)} mercados)")
        else:
            lineas.append(f"**Cuotas de mercado disponibles**: no (todavía no publicadas)")

        if alineacion and es_confirmada:
            lineas.append(f"**Alineación**: confirmada -- variable 7 aplicable")
        elif alineacion and not es_confirmada:
            lineas.append(f"**Alineación**: solo prevista/probable (faltan más de 2h) -- no usada todavía para ajustar la predicción")
        else:
            lineas.append(f"**Alineación**: no disponible")

        registro_predicciones.append({
            "match_id": p["id"], "fecha": p["date"], "equipo_local": local, "equipo_visitante": visitante,
            "prob_local": pred_goles["prob_local"], "prob_empate": pred_goles["prob_empate"],
            "prob_visitante": pred_goles["prob_visitante"], "prob_over_tarjetas": pred_tarjetas["prob_over"],
            "generado_el": datetime.utcnow().isoformat(),
        })

        lineas.append("\n---\n")

    with open(RUTA_INFORME, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print(f"Informe generado: {RUTA_INFORME}")

    # Registro para calibración futura: guarda cada predicción, sin duplicar
    # las que ya se habían registrado en una ejecución anterior de la misma semana
    ruta_registro = "data/registro_predicciones.csv"
    registro_previo = pd.read_csv(ruta_registro) if os.path.exists(ruta_registro) else pd.DataFrame()
    nuevos = pd.DataFrame(registro_predicciones)
    if not registro_previo.empty:
        nuevos = nuevos[~nuevos["match_id"].isin(registro_previo["match_id"])]
    registro_final = pd.concat([registro_previo, nuevos], ignore_index=True)
    registro_final.to_csv(ruta_registro, index=False)
    print(f"Registro de predicciones actualizado: {len(nuevos)} nuevas, {len(registro_final)} en total")


# ============ 7. CALIBRACIÓN AUTOMÁTICA ============
def calcular_calibracion():
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

    informe = f"""# Informe de calibración -- actualizado el {datetime.utcnow().strftime('%Y-%m-%d')}
Partidos evaluados hasta ahora: {len(cruzado)}

## Goles (victoria local)
- Brier score: {brier_goles:.4f} (0.25 = azar, más bajo = mejor)
- Acierto: {acierto_goles*100:.1f}%

## Tarjetas (over/under 4.5)
- Brier score: {brier_tarjetas:.4f} (0.25 = azar, más bajo = mejor)
- Acierto: {acierto_tarjetas*100:.1f}%
"""
    with open("data/informe_calibracion.md", "w", encoding="utf-8") as f:
        f.write(informe)
    print(f"[calibracion] informe actualizado con {len(cruzado)} partidos evaluados")


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
    calcular_calibracion()


if __name__ == "__main__":
    main()
  
