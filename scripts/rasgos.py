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
# Backfill resumible: la columna puede EXISTIR (el merge ya la trajo) con
# casi todo NaN mientras el backfill avanza. El notna() de mas adelante
# exige TODAS las columnas sin excepcion, asi que una columna casi vacia
# tira TODAS las filas a cero -- igual que si no existiera, solo que sin
# el "if not in hist.columns" que ya la atajaba. 21/09: 1 fila de
# historico_boxscore.csv fusionada sobre 2540 partidos convirtio "0
# partidos evaluables" un pipeline que un dia antes daba 296.
COBERTURA_MINIMA = 0.3

# Lo que se mide de cada equipo. Nombres de columna del histórico.
MEDIDAS = ["goles", "corners", "fouls", "yellow_cards", "expected_goals",
           "possession", "shots_on_target", "shots_off_target", "crosses",
           "total_passes",
           # De /box-score (21/09), ninguna duplica /statistics: ver
           # backfill_boxscore.py para el porqué de cada una.
           "faltas_recibidas", "segundas_amarillas", "duelos_totales",
           "duelos_ganados_pct", "falta_max_jugador",
           "jugadores_2mas_faltas", "xg_evitado_portero"]


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
            # Si la fuente de esta variable AUN no se ha fusionado en hist
            # (p.ej. el box-score todavia no ha llegado), la columna ni
            # siquiera existe. Rellenarla de NaN aqui contaminaria TODAS las
            # filas cuando algo mas adelante exige notna() en todos los
            # rasgos -- 2.539 partidos utilizables se convirtieron en CERO la
            # primera vez que paso esto. Se omite la variable entera en vez
            # de fingir que existe; en cuanto la columna aparezca, entra sola
            # sin tocar el resto del pipeline.
            if propia not in hist.columns or ajena not in hist.columns:
                continue
            propia_n = pd.to_numeric(hist[propia], errors="coerce")
            ajena_n = pd.to_numeric(hist[ajena], errors="coerce")
            cobertura = min(propia_n.notna().mean(), ajena_n.notna().mean())
            if cobertura < COBERTURA_MINIMA:
                continue
            d[m] = propia_n
            d[f"contra_{m}"] = ajena_n
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


def calcular_elo(hist, k=20.0, ventaja_local=60.0):
    """
    Fuerza de equipo estilo Elo, cronológica, usando solo los goles que ya
    tenemos -- sin dato nuevo, sin API adicional.

    Es de las variables más predictivas que existen en fútbol (lo demuestra
    el propio sistema mundial de Elo de selecciones) y aquí sale gratis: solo
    hace falta el marcador con fecha, que ya está en el histórico.

    LA MISMA REGLA ANTI-FUGA QUE TODO LO DEMÁS: el Elo que se le asigna al
    partido X es el que tenían los equipos justo ANTES de jugarlo. Se lee
    `ratings[...]` y se guarda ANTES de actualizarlo con el marcador de X, así
    que cambiar el resultado de X no puede mover el Elo que ve el propio X
    -- solo el de partidos posteriores. `comprobar_sin_fuga` lo verifica igual
    que al resto.

    K y la ventaja de local son los valores estándar de los sistemas Elo de
    fútbol de club (K=20; la ventaja de jugar en casa ronda 60-100 puntos).
    El multiplicador por diferencia de goles (`g`) es el de World Football
    Elo: una goleada mueve más el rating que un 1-0 ajustado.
    """
    orden = hist.sort_values("fecha")
    ratings = {}
    antes_l, antes_v = [], []
    for _, fila in orden.iterrows():
        l, v = fila["local_id"], fila["visitante_id"]
        rl, rv = ratings.get(l, 1500.0), ratings.get(v, 1500.0)
        antes_l.append(rl)
        antes_v.append(rv)
        gl, gv = fila["goles_l"], fila["goles_v"]
        if pd.isna(gl) or pd.isna(gv):
            continue
        dif = abs(gl - gv)
        g = 1.0 if dif <= 1 else (1.5 if dif == 2 else (11 + dif) / 8.0)
        esperado_local = 1.0 / (1.0 + 10 ** (-(rl + ventaja_local - rv) / 400.0))
        real_local = 1.0 if gl > gv else (0.5 if gl == gv else 0.0)
        cambio = k * g * (real_local - esperado_local)
        ratings[l] = rl + cambio
        ratings[v] = rv - cambio
    return pd.DataFrame({"match_id": orden["match_id"].values,
                         "elo_local_previo": antes_l,
                         "elo_visitante_previo": antes_v})


def calcular_h2h(hist):
    """
    Historial cruzado entre los DOS equipos concretos que se enfrentan --
    no la forma general de cada uno, que ya cubren m_puntos y el Elo. Un
    equipo puede ser fuerte en general y flojo especificamente contra otro
    rival por motivos tacticos o historicos; ninguna otra variable del
    proyecto mira eso.

    MISMA REGLA ANTI-FUGA que el resto: solo cuentan enfrentamientos con
    fecha ANTERIOR al partido evaluado -- se lee el historial del par ANTES
    de anadir el resultado del partido actual.

    La mayoria de pares de equipos no se han enfrentado nunca dentro de la
    ventana del historico (ligas grandes, pocas temporadas). Eso no es el
    mismo problema que el backfill incompleto de box-score: alli la
    cobertura crecia con el tiempo y rellenar de NaN escondia un fallo; aqui
    la escasez es estructural y no va a cambiar sola. Se rellena con un
    valor NEUTRO (0.5 puntos normalizados, 0 de diferencia de goles) y se
    guarda ademas cuantos enfrentamientos previos hay, para que el propio
    modelo pueda aprender a ignorar el valor neutro cuando ese numero es 0.
    """
    orden = hist.sort_values("fecha").reset_index(drop=True)
    historial = {}
    n_prev, pts_local, gd_local = [], [], []
    for _, fila in orden.iterrows():
        l, v = fila["local_id"], fila["visitante_id"]
        clave = frozenset((l, v))
        previos = historial.get(clave, [])
        if previos:
            pts, gd = [], []
            for (loc_prev, gl_prev, gv_prev) in previos:
                mi_g, su_g = (gl_prev, gv_prev) if loc_prev == l else (gv_prev, gl_prev)
                pts.append(3.0 if mi_g > su_g else (1.0 if mi_g == su_g else 0.0))
                gd.append(mi_g - su_g)
            n_prev.append(len(previos))
            pts_local.append(float(np.mean(pts)) / 3.0)
            gd_local.append(float(np.mean(gd)))
        else:
            n_prev.append(0)
            pts_local.append(0.5)
            gd_local.append(0.0)
        gl, gv = fila["goles_l"], fila["goles_v"]
        if pd.notna(gl) and pd.notna(gv):
            historial.setdefault(clave, []).append((l, gl, gv))
    return pd.DataFrame({"match_id": orden["match_id"].values,
                         "h2h_partidos_previos": n_prev,
                         "h2h_pts_local_norm": pts_local,
                         "h2h_gd_local": gd_local})


def calcular_tabla(hist):
    """
    Posición y puntos-por-partido en la tabla de SU liga y SU temporada en
    curso -- distinto de m_puntos, que es una media móvil de los últimos 8
    partidos y puede mezclar partidos de la temporada anterior justo al
    empezar una nueva (plantilla distinta, objetivos distintos). Un equipo
    en descenso a diez jornadas del final no juega igual que uno de mitad
    de tabla sin nada en juego -- esto es lo más parecido a "presión" que
    se puede calcular sin inventar dónde está el corte de descenso de cada
    liga (varía entre competiciones y no está en los datos que tenemos).

    MISMA REGLA ANTI-FUGA: la posición y los puntos que ve el partido X son
    los de ANTES de jugarse X -- se lee la tabla, se calculan las columnas
    de esa fila, y solo DESPUÉS se actualiza la tabla con el resultado de X.

    Un equipo que aún no ha jugado esta temporada (jornada 1) no tiene
    posición real todavía: se le da el último puesto de los ya vistos + 1,
    neutro y conservador, nunca un puesto intermedio inventado. `tabla_pj`
    (partidos jugados esta temporada) viaja siempre al lado para que el
    modelo pueda descontar una posición basada en muy pocos partidos.
    """
    orden = hist.sort_values("fecha").reset_index(drop=True)
    tablas = {}
    pos_l, pos_v, ppg_l, ppg_v, pj_l, pj_v = [], [], [], [], [], []
    for _, fila in orden.iterrows():
        clave = (fila["liga_id"], fila["temporada"])
        tabla = tablas.setdefault(clave, {})
        l, v = fila["local_id"], fila["visitante_id"]

        equipos_vistos = list(tabla.keys())
        ranking = sorted(equipos_vistos,
                         key=lambda e: (-tabla[e][0], -(tabla[e][1] - tabla[e][2])))
        posiciones = {e: i + 1 for i, e in enumerate(ranking)}
        n_vistos = len(ranking)

        pts_l0, gf_l0, gc_l0, pj_l0 = tabla.get(l, (0, 0, 0, 0))
        pts_v0, gf_v0, gc_v0, pj_v0 = tabla.get(v, (0, 0, 0, 0))

        pos_l.append(posiciones.get(l, n_vistos + 1))
        pos_v.append(posiciones.get(v, n_vistos + 1))
        ppg_l.append(pts_l0 / pj_l0 if pj_l0 else 0.0)
        ppg_v.append(pts_v0 / pj_v0 if pj_v0 else 0.0)
        pj_l.append(pj_l0)
        pj_v.append(pj_v0)

        gl, gv = fila["goles_l"], fila["goles_v"]
        if pd.notna(gl) and pd.notna(gv):
            pl3 = 3 if gl > gv else (1 if gl == gv else 0)
            pv3 = 3 if gv > gl else (1 if gl == gv else 0)
            tabla[l] = (pts_l0 + pl3, gf_l0 + gl, gc_l0 + gv, pj_l0 + 1)
            tabla[v] = (pts_v0 + pv3, gf_v0 + gv, gc_v0 + gl, pj_v0 + 1)
    return pd.DataFrame({"match_id": orden["match_id"].values,
                         "loc_tabla_pos": pos_l, "vis_tabla_pos": pos_v,
                         "loc_tabla_ppg": ppg_l, "vis_tabla_ppg": ppg_v,
                         "loc_tabla_pj": pj_l, "vis_tabla_pj": pj_v})


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
    elo = calcular_elo(hist).set_index("match_id")
    base["loc_elo"] = elo["elo_local_previo"]
    base["vis_elo"] = elo["elo_visitante_previo"]
    base["dif_elo"] = base["loc_elo"] - base["vis_elo"]
    tabla = calcular_tabla(hist).set_index("match_id")
    for c in ("tabla_pos", "tabla_ppg", "tabla_pj"):
        base[f"loc_{c}"] = tabla[f"loc_{c}"]
        base[f"vis_{c}"] = tabla[f"vis_{c}"]
        base[f"dif_{c}"] = tabla[f"loc_{c}"] - tabla[f"vis_{c}"]
    h2h = calcular_h2h(hist).set_index("match_id")
    base["h2h_partidos_previos"] = h2h["h2h_partidos_previos"]
    base["h2h_pts_local_norm"] = h2h["h2h_pts_local_norm"]
    base["h2h_gd_local"] = h2h["h2h_gd_local"]
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
    # Líneas reales del mercado (censo_margenes.md): 9.5 córners, 4.5
    # tarjetas son las que más casas cotizan. Partidos sin ese dato (córners
    # o tarjetas nulos) se descartan solos vía notna() en columnas_rasgo.
    base["mas_9_5_corners"] = (base.corners_total > 9.5).astype(int)
    base["mas_4_5_tarjetas"] = (base.tarjetas_total > 4.5).astype(int)
    return base.reset_index()


def columnas_rasgo(base):
    return [c for c in base.columns
            if c.startswith(("loc_", "vis_", "dif_", "h2h_")) or c == "liga_id"]


MEDIDAS_BOXSCORE = ("faltas_recibidas", "segundas_amarillas", "duelos_totales",
                    "duelos_ganados_pct", "falta_max_jugador",
                    "jugadores_2mas_faltas", "xg_evitado_portero")


def grupos_rasgo(base):
    """
    Los rasgos agrupados por de dónde vienen, para poder probar cada
    variable nueva SOLA contra el mercado antes de sumarlas todas juntas.
    `columnas_rasgo()` las mezcla todas de golpe; esto es lo que permite el
    "una a una, y luego combinaciones" en vez de solo acumular.
    """
    grupos = {"base": [], "elo": [], "h2h": [], "tabla": [], "boxscore": []}
    for c in columnas_rasgo(base):
        if c == "liga_id":
            grupos["base"].append(c)
        elif "elo" in c:
            grupos["elo"].append(c)
        elif c.startswith("h2h_"):
            grupos["h2h"].append(c)
        elif "tabla_" in c:
            grupos["tabla"].append(c)
        elif any(m in c for m in MEDIDAS_BOXSCORE):
            grupos["boxscore"].append(c)
        else:
            grupos["base"].append(c)
    return grupos


def columnas_rasgo_default(base):
    """
    Las columnas que usa el modelo en producción -- columnas_rasgo() menos
    box-score. experimentos_rasgos.py (23/09) confirmó box-score empeora
    las 5 líneas, aislado o combinado con h2h/tabla; seguir entrenando con
    él por defecto sería ignorar el propio experimento. Sigue fusionado en
    `hist` (modelo_xgboost.cargar()) para poder volver a probarlo vía
    grupos_rasgo() si aparece más muestra -- esto solo lo saca del set que
    entrena de verdad.
    """
    boxscore = set(grupos_rasgo(base)["boxscore"])
    return [c for c in columnas_rasgo(base) if c not in boxscore]


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
