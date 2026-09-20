"""
LOS RASGOS: qué sabe el modelo de un partido ANTES de que se juegue

LA REGLA QUE MANDA AQUÍ
-----------------------
Un rasgo solo puede usar información existente ANTES del pitido inicial de ESE
partido. Suena obvio y es el fallo número uno de todo modelo deportivo: se
cuela el dato del propio partido, el modelo acierta el 78%, y no vale nada.

Aquí se construye por orden cronológico estricto: para el partido del día D
solo se miran partidos con fecha < D. Nunca se calcula una media de temporada
y se aplica hacia atrás.

LA COMPROBACIÓN QUE LO PILLA
----------------------------
`comprobar_sin_fuga` verifica que ningún rasgo de una fila usa datos de esa
fila. Se hace cambiando el resultado del propio partido y viendo que los
rasgos NO se mueven. Si se movieran, hay fuga.

QUÉ SE MIRA DE CADA EQUIPO
--------------------------
Medias móviles de sus últimos N partidos, separando casa y fuera, porque un
equipo puede ser muy distinto en cada sitio. Y la media de la liga como
referencia, para que el modelo pueda situar a un equipo respecto a su entorno.
"""
import numpy as np
import pandas as pd

VENTANA = 8            # partidos hacia atrás por equipo
MINIMO_PARTIDOS = 4    # por debajo de esto, el equipo no tiene historia fiable

# Lo que se mide de cada equipo. Nombres de columna del histórico.
MEDIDAS = ["goles", "corners", "fouls", "yellow_cards", "expected_goals",
           "possession", "shots_on_target", "shots_off_target", "crosses",
           "total_passes"]


def a_largo(hist):
    """
    De una fila por partido a DOS filas por partido, una por equipo.

    Así cada equipo tiene su propia serie temporal y las medias móviles salen
    solas. `contra_` es lo que le hizo el rival, que es tan informativo como
    lo propio: un equipo que concede muchos córners es tan explotable como uno
    que los gana.
    """
    filas = []
    for lado, rival in (("l", "v"), ("v", "l")):
        d = pd.DataFrame({
            "match_id": hist["match_id"],
            "fecha": pd.to_datetime(hist["fecha"], format="mixed", utc=True),
            "liga_id": hist["liga_id"],
            "equipo": hist[f"{'local' if lado=='l' else 'visitante'}_id"],
            "rival": hist[f"{'visitante' if lado=='l' else 'local'}_id"],
            "en_casa": 1 if lado == "l" else 0,
            "goles": hist[f"goles_{lado}"],
            "goles_contra": hist[f"goles_{rival}"],
        })
        for m in MEDIDAS:
            if m == "goles":
                continue
            propia, ajena = f"{lado}_{m}", f"{rival}_{m}"
            d[m] = pd.to_numeric(hist.get(propia), errors="coerce")
            d[f"contra_{m}"] = pd.to_numeric(hist.get(ajena), errors="coerce")
        filas.append(d)
    return pd.concat(filas, ignore_index=True).sort_values(["equipo", "fecha"])


def medias_previas(largo, ventana=VENTANA):
    """
    Media de los `ventana` partidos ANTERIORES de cada equipo.

    `shift(1)` antes de `rolling` es la línea que evita la fuga: sin ella, la
    media incluiría el partido que estamos intentando predecir.
    """
    cols = ([c for c in largo.columns
             if c in MEDIDAS or c.startswith("contra_")] + ["goles_contra"])
    g = largo.groupby("equipo", sort=False)
    for c in cols:
        largo[f"m_{c}"] = (g[c].shift(1)
                           .groupby(largo["equipo"], sort=False)
                           .rolling(ventana, min_periods=MINIMO_PARTIDOS)
                           .mean().reset_index(level=0, drop=True))
    # forma reciente: puntos por partido en los últimos `ventana`
    pts = np.where(largo.goles > largo.goles_contra, 3,
                   np.where(largo.goles == largo.goles_contra, 1, 0))
    largo["_pts"] = pts
    largo["m_puntos"] = (g["_pts"].shift(1)
                         .groupby(largo["equipo"], sort=False)
                         .rolling(ventana, min_periods=MINIMO_PARTIDOS)
                         .mean().reset_index(level=0, drop=True))
    largo["partidos_previos"] = g.cumcount()
    # días desde el partido anterior: el descanso importa y es gratis
    largo["descanso"] = (g["fecha"].diff().dt.total_seconds() / 86400)
    return largo.drop(columns=["_pts"])


def construir(hist):
    """Una fila por partido, con los rasgos de los dos equipos enfrentados."""
    largo = medias_previas(a_largo(hist))
    rasgos = [c for c in largo.columns
              if c.startswith("m_") or c in ("partidos_previos", "descanso")]
    loc = largo[largo.en_casa == 1].set_index("match_id")
    vis = largo[largo.en_casa == 0].set_index("match_id")
    base = pd.DataFrame(index=loc.index)
    for c in rasgos:
        base[f"loc_{c}"] = loc[c]
        base[f"vis_{c}"] = vis[c]
        base[f"dif_{c}"] = loc[c] - vis[c]      # la diferencia suele mandar
    base["liga_id"] = loc["liga_id"]
    base["fecha"] = loc["fecha"]
    base["goles_l"] = loc["goles"]
    base["goles_v"] = loc["goles_contra"]
    base["corners_total"] = loc["corners"] + loc["contra_corners"]
    base["tarjetas_total"] = loc["yellow_cards"] + loc["contra_yellow_cards"]
    # objetivos
    base["resultado"] = np.select(
        [base.goles_l > base.goles_v, base.goles_l == base.goles_v],
        [0, 1], default=2)          # 0 local, 1 empate, 2 visitante
    base["mas_2_5"] = ((base.goles_l + base.goles_v) > 2.5).astype(int)
    base["ambos_marcan"] = ((base.goles_l > 0) & (base.goles_v > 0)).astype(int)
    return base.reset_index()


def columnas_rasgo(base):
    return [c for c in base.columns
            if c.startswith(("loc_", "vis_", "dif_")) or c == "liga_id"]


def comprobar_sin_fuga(hist):
    """
    ¿Usa algún rasgo el resultado del propio partido?

    Se cambia el marcador de UN partido y se comprueba que sus rasgos no se
    mueven. Si se movieran, el modelo estaría viendo el futuro y cualquier
    acierto que diera seria mentira.
    """
    base = construir(hist)
    if base.empty:
        return False, "sin filas"
    objetivo = base.iloc[len(base) // 2]["match_id"]
    trucado = hist.copy()
    fila = trucado.match_id == objetivo
    if not fila.any():
        return False, "no se encontro el partido"
    for col in ("goles_l", "goles_v", "l_corners", "v_corners"):
        if col in trucado.columns:
            trucado.loc[fila, col] = 99
    base2 = construir(trucado)
    cols = columnas_rasgo(base)
    a = base[base.match_id == objetivo][cols].reset_index(drop=True)
    b = base2[base2.match_id == objetivo][cols].reset_index(drop=True)
    if a.empty or b.empty:
        return False, "el partido desaparecio al reconstruir"
    dif = (a.fillna(-999) != b.fillna(-999)).any()
    culpables = list(dif[dif].index)
    if culpables:
        return False, f"FUGA en {len(culpables)} rasgos: {culpables[:6]}"
    return True, f"{len(cols)} rasgos, ninguno usa el propio partido"
