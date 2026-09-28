"""
Rasgo del portero titular para el modelo oficial de ambos marcan (desde el
28/09/2026, decisión del usuario tras experimento_xg_jugador_v2.py: +1.25s
sobre el oficial anterior, 10 de 14 meses mejor; no llega al listón de +2.4s
pero es lo que mejor ha funcionado).

gk_gp90 = goles evitados por 90 (expectedGoalsPrevented del box-score) del
portero TITULAR en sus 10 apariciones anteriores, encogido hacia 0 con 270'.
Solo hay datos desde abril de 2025 (antes queda vacío; el modelo entrena con
huecos). Misma construcción que la prueba (experimento_xg_jugador_v2.rasgos).
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
COLS = ["loc_gk_gp90", "vis_gk_gp90"]
VENTANA, K_MIN = 10, 270.0


def historico():
    """loc_gk_gp90 / vis_gk_gp90 de cada partido jugado (match_id)."""
    import experimento_xg_jugador_v2 as V
    return V.rasgos()[["match_id"] + COLS]


def para_partido(jugador_ids, equipo_id, fecha):
    """gk_gp90 del portero de un once (ids) antes de `fecha`. Sin once: el último
    portero titular del equipo. Devuelve NaN si no hay datos."""
    x = pd.read_csv("data/historico_xg_jugador.csv",
                    usecols=["match_id", "equipo_id", "jugador_id", "posicion", "minutos", "suplente",
                             "expectedGoalsPrevented"])
    x = x[x.jugador_id.notna() & (pd.to_numeric(x.minutos, errors="coerce") > 0)]
    f = pd.read_csv("data/historico_partidos.csv", usecols=["match_id", "fecha"])
    x = x.merge(f, on="match_id")
    x = x[pd.to_datetime(x.fecha, utc=True) < pd.to_datetime(fecha, utc=True)]
    x["jugador_id"] = x.jugador_id.astype(int)
    porteros = set(x[x.posicion == "Goalkeeper"].jugador_id)
    gk = [int(j) for j in (jugador_ids or []) if int(j) in porteros]
    if not gk:
        tit = x[(x.equipo_id == equipo_id) & (x.posicion == "Goalkeeper")
                & (x.suplente.astype(str).str.lower() == "false")].sort_values("fecha")
        if tit.empty:
            return np.nan
        gk = [int(tit.jugador_id.iloc[-1])]
    r = x[x.jugador_id == gk[0]].sort_values("fecha").tail(VENTANA)
    gp = pd.to_numeric(r.expectedGoalsPrevented, errors="coerce").fillna(0).sum()
    return gp * 90 / (pd.to_numeric(r.minutos).sum() + K_MIN)
