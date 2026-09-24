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
import os
import numpy as np
import pandas as pd

RUTA_H2H_PROFUNDO = "data/historico_h2h_profundo.csv"

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


def forma_reciente(largo, ventana=3):
    """
    La MISMA media móvil que medias_previas, pero con ventana corta (3
    partidos = las últimas jornadas, no la temporada). Prefijo r_ para
    no chocar con m_ (ventana larga, VENTANA=8).

    Lógica de fútbol: el rendimiento de hace 8 meses no debería pesar
    igual que el de los últimos 3 partidos. Forzar ese peso a mano sobre
    TODA la muestra de entrenamiento (sample_weight por antigüedad de la
    fila) se probó y empeoró sigmas y acierto -- ver CLAUDE.md "Peso por
    recencia". Pero eso mezclaba dos cosas distintas: cuánto confiar en
    un PARTIDO DE ENTRENAMIENTO viejo (empeora, con esta muestra tan
    pequeña no sobra dato que tirar) y si la FORMA RECIENTE de un equipo
    es informativa (otra pregunta, no probada todavía). Esto prueba la
    segunda: forma reciente como variable más, junto a la de ventana
    larga que ya existe, dejando que el modelo aprenda cuánto pesa cada
    una en vez de imponerlo.

    MISMA REGLA ANTI-FUGA: shift(1) antes de rolling.
    """
    cols = [c for c in largo.columns if c in MEDIDAS or c.startswith("contra_")]
    g = largo.groupby("equipo", sort=False)
    for c in cols:
        largo[f"r_{c}"] = (g[c].shift(1)
                           .groupby(largo["equipo"], sort=False)
                           .rolling(ventana, min_periods=2)
                           .mean().reset_index(level=0, drop=True))
    pts = np.where(largo.goles > largo.goles_contra, 3,
                   np.where(largo.goles == largo.goles_contra, 1, 0))
    largo["_pts_r"] = pts
    largo["r_puntos"] = (g["_pts_r"].shift(1)
                         .groupby(largo["equipo"], sort=False)
                         .rolling(ventana, min_periods=2)
                         .mean().reset_index(level=0, drop=True))
    return largo.drop(columns=["_pts_r"])


def calcular_btts(largo):
    """
    Tasa de "ambos marcan" reciente de CADA equipo -- proporción de sus
    últimos VENTANA partidos donde él Y el rival marcaron. Petición del
    usuario: ambos_marcan es el mercado más cerca de competir con el
    mercado (-0.77s, el menos negativo de los 5), y no tiene ninguna
    variable pensada específicamente para él -- las 99 de producción son
    genéricas para los 5 mercados a la vez.

    NO es lo mismo que la media de goles que ya existe (m_goles,
    m_contra_goles): un equipo puede atacar mucho y encajar poco (BTTS
    bajo pese a gran ataque) o meter y encajar pocos siempre 1-0 (BTTS
    bajo con ataque mediocre). Esta variable captura directamente el
    patrón conjunto, no la suma de dos medias separadas.

    Prefijo btts_ -- deliberadamente distinto de "ambos_marcan" (el
    nombre de la columna objetivo) para no repetir el tipo de colisión
    de subcadena del bug de "elo"/"duelos" de hoy mismo.

    MISMA REGLA ANTI-FUGA: shift(1) antes de rolling.
    """
    largo = largo.copy()
    largo["_btts"] = ((largo["goles"] > 0) & (largo["goles_contra"] > 0)).astype(float)
    g = largo.groupby("equipo", sort=False)
    largo["btts_tasa"] = (g["_btts"].shift(1)
                          .groupby(largo["equipo"], sort=False)
                          .rolling(VENTANA, min_periods=MINIMO_PARTIDOS)
                          .mean().reset_index(level=0, drop=True))
    return largo.drop(columns=["_btts"])


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


def _clave_par(id1, id2):
    a, b = sorted((int(id1), int(id2)))
    return f"{a}_{b}"


def calcular_h2h_profundo(hist, h2h_crudo):
    """
    Igual que calcular_h2h() pero con /head-2-head (data/historico_h2h_profundo.csv)
    en vez de solo lo que hay dentro de nuestro propio histórico -- ve hasta
    año y medio más atrás (comprobado con Real Madrid-Barcelona,
    sondeo_h2h.py, 24/09: 7 de sus últimas 10 confrontaciones son de antes
    de nuestra ventana de 13 meses).

    REGLA ANTI-FUGA MÁS ESTRICTA QUE EL RESTO: `h2h_crudo` trae las
    últimas 10 confrontaciones A DÍA DE HOY, no las últimas 10 ANTES de
    cada partido del histórico. Para un partido de hace 13 meses, alguna
    de esas 10 puede ser POSTERIOR a ese partido -- eso SÍ sería fuga. Se
    filtra explícitamente `fecha_confrontacion < fecha_partido` antes de
    usar nada, no se confía en el orden que devuelve la API.
    """
    crudo = h2h_crudo.dropna(subset=["fecha"]).copy()
    crudo["fecha"] = pd.to_datetime(crudo["fecha"], utc=True)
    crudo["local_id"] = pd.to_numeric(crudo["local_id"], errors="coerce")
    crudo["goles_l"] = pd.to_numeric(crudo["goles_l"], errors="coerce")
    crudo["goles_v"] = pd.to_numeric(crudo["goles_v"], errors="coerce")
    por_par = {par: grupo for par, grupo in crudo.groupby("par")}

    orden = hist.copy()
    orden["_fecha_dt"] = pd.to_datetime(orden["fecha"], format="mixed", utc=True)
    orden = orden.sort_values("_fecha_dt").reset_index(drop=True)

    n_prev, pts_local, gd_local = [], [], []
    for _, fila in orden.iterrows():
        l, v = fila["local_id"], fila["visitante_id"]
        grupo = por_par.get(_clave_par(l, v))
        if grupo is None:
            n_prev.append(0); pts_local.append(0.5); gd_local.append(0.0)
            continue
        previos = grupo[grupo["fecha"] < fila["_fecha_dt"]]
        pts, gd = [], []
        for _, m in previos.iterrows():
            if pd.isna(m["goles_l"]) or pd.isna(m["goles_v"]):
                continue
            mi_g, su_g = ((m["goles_l"], m["goles_v"]) if m["local_id"] == l
                         else (m["goles_v"], m["goles_l"]))
            pts.append(3.0 if mi_g > su_g else (1.0 if mi_g == su_g else 0.0))
            gd.append(mi_g - su_g)
        if not pts:
            n_prev.append(0); pts_local.append(0.5); gd_local.append(0.0)
        else:
            n_prev.append(len(pts))
            pts_local.append(float(np.mean(pts)) / 3.0)
            gd_local.append(float(np.mean(gd)))
    return pd.DataFrame({"match_id": orden["match_id"].values,
                         "h2hp_partidos_previos": n_prev,
                         "h2hp_pts_local_norm": pts_local,
                         "h2hp_gd_local": gd_local})


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


def calcular_arbitro(hist):
    """
    Tarjetas medias por partido de CADA árbitro, usando solo sus
    apariciones ANTERIORES -- misma regla anti-fuga que Elo, H2H y tabla.
    Distintos árbitros pitan un número de tarjetas muy distinto de media;
    ninguna otra variable del proyecto lo mira, y es justo el mercado
    donde peor va el modelo (mas_4_5_tarjetas).

    Sin árbitro conocido (~20% de los partidos, comprobado en
    sondeo_matches.py) o sin apariciones previas de ESE árbitro en el
    histórico, se rellena con la media de LIGA acumulada hasta ese momento
    (no un cero, que el modelo leería como "cero tarjetas esperadas").
    `arbitro_partidos_previos` viaja al lado para poder descontar un
    árbitro con muy poca muestra.
    """
    orden = hist.sort_values("fecha").reset_index(drop=True)
    stats_arb = {}
    media_num, media_den = 0.0, 0
    valores, n_prev = [], []
    for _, fila in orden.iterrows():
        arb = fila.get("arbitro")
        media_actual = (media_num / media_den) if media_den else 3.5
        if pd.notna(arb) and arb in stats_arb and stats_arb[arb][1] > 0:
            suma, n = stats_arb[arb]
            valores.append(suma / n)
            n_prev.append(n)
        else:
            valores.append(media_actual)
            n_prev.append(0)
        tarjetas = None
        if all(pd.notna(fila.get(c)) for c in
              ("l_yellow_cards", "l_red_cards", "v_yellow_cards", "v_red_cards")):
            tarjetas = (fila["l_yellow_cards"] + fila["l_red_cards"] +
                       fila["v_yellow_cards"] + fila["v_red_cards"])
        if tarjetas is not None:
            media_num += tarjetas
            media_den += 1
            if pd.notna(arb):
                s, n = stats_arb.get(arb, (0.0, 0))
                stats_arb[arb] = (s + tarjetas, n + 1)
    return pd.DataFrame({"match_id": orden["match_id"].values,
                         "arbitro_tarjetas_media": valores,
                         "arbitro_partidos_previos": n_prev})


def calcular_rotacion(hist):
    """
    Cuántos titulares cambian respecto al partido ANTERIOR del mismo
    equipo -- misma regla anti-fuga: se lee la última alineación conocida
    de cada equipo ANTES de actualizarla con la de hoy. La alineación de
    HOY no es un resultado (se conoce antes del pitido), así que no hay
    fuga en usarla; lo que sí filtraría es comparar contra un partido
    posterior por error, que es justo lo que este orden evita.

    Requiere columnas `local_ids`/`visitante_ids` (pipe-joined) fusionadas
    desde historico_lineups.csv -- si no existen, se devuelve un DataFrame
    vacío y construir() se salta la variable entera (mismo patrón que
    box-score cuando aún no hay backfill).
    """
    if "local_ids" not in hist.columns or "visitante_ids" not in hist.columns:
        return pd.DataFrame({"match_id": hist["match_id"].values})
    orden = hist.sort_values("fecha").reset_index(drop=True)
    ultima_alineacion = {}
    rot_l, rot_v, n_prev_l, n_prev_v = [], [], [], []
    for _, fila in orden.iterrows():
        l, v = fila["local_id"], fila["visitante_id"]
        ids_l_str, ids_v_str = fila.get("local_ids"), fila.get("visitante_ids")
        ids_l = set(ids_l_str.split("|")) if pd.notna(ids_l_str) else None
        ids_v = set(ids_v_str.split("|")) if pd.notna(ids_v_str) else None

        previa_l = ultima_alineacion.get(l)
        previa_v = ultima_alineacion.get(v)
        if ids_l is not None and previa_l:
            rot_l.append(len(ids_l - previa_l))
            n_prev_l.append(1)
        else:
            rot_l.append(2.5)  # neutro: rotación media típica observada
            n_prev_l.append(0)
        if ids_v is not None and previa_v:
            rot_v.append(len(ids_v - previa_v))
            n_prev_v.append(1)
        else:
            rot_v.append(2.5)
            n_prev_v.append(0)

        if ids_l is not None:
            ultima_alineacion[l] = ids_l
        if ids_v is not None:
            ultima_alineacion[v] = ids_v
    return pd.DataFrame({"match_id": orden["match_id"].values,
                         "loc_rotacion": rot_l, "vis_rotacion": rot_v,
                         "loc_rotacion_conocida": n_prev_l,
                         "vis_rotacion_conocida": n_prev_v})


RUTA_LINEUPS = "data/historico_lineups.csv"
RUTA_JUGADOR_STATS = "data/historico_jugador_stats.csv"


def _temporada_anterior_str(year):
    """temporada=2025 (liga "25/26") -> temporada anterior "24/25"."""
    y = int(year)
    return f"{(y - 1) % 100:02d}/{y % 100:02d}"


def calcular_calidad_plantilla(hist, jugador_stats_crudo):
    """
    Calidad de la ALINEACIÓN TITULAR, no del equipo en abstracto -- cruza
    quién juega de verdad (`local_ids`/`visitante_ids`, ya fusionados en
    `hist` desde historico_lineups.csv por modelo_xgboost.cargar()) con lo
    que rindió cada jugador en la temporada ANTERIOR ya cerrada (hecho
    histórico fijo, sin fuga posible: la temporada en curso sigue
    acumulando, comprobado en sondeo_jugador_stats.py, 24/09).

    Con solo una fracción de los 3478 jugadores backfilleados, la mayoría
    de partidos tienen cobertura PARCIAL de su once titular. Sumar
    minutos/goles de los conocidos confundiría "equipo bueno" con "equipo
    con más jugadores en nuestra muestra" -- se usa la MEDIA por jugador
    conocido, no la suma, y se guarda cuántos de los 11 son conocidos para
    que el modelo pueda descontar una media con poca base.
    """
    stats_prev = {}  # (jugador_id, temporada) -> (minutos, goles+asist, partidos)
    for _, fila in jugador_stats_crudo.dropna(subset=["temporada"]).iterrows():
        clave = (int(fila["jugador_id"]), fila["temporada"])
        m = pd.to_numeric(fila.get("minutos"), errors="coerce") or 0
        g = pd.to_numeric(fila.get("goles"), errors="coerce") or 0
        a = pd.to_numeric(fila.get("asistencias"), errors="coerce") or 0
        p = pd.to_numeric(fila.get("partidos"), errors="coerce") or 0
        m0, ga0, p0 = stats_prev.get(clave, (0.0, 0.0, 0.0))
        stats_prev[clave] = (m0 + m, ga0 + g + a, p0 + p)

    def calidad_equipo(ids_str, temporada_str):
        if pd.isna(ids_str):
            return 0.0, 0.0, 0
        minutos, ga = [], []
        for jid_s in ids_str.split("|"):
            clave = (int(jid_s), temporada_str)
            if clave in stats_prev:
                m, g_a, _ = stats_prev[clave]
                minutos.append(m)
                ga.append(g_a)
        n = len(minutos)
        if n == 0:
            return 0.0, 0.0, 0
        return float(np.mean(minutos)), float(np.mean(ga)), n

    if "local_ids" not in hist.columns or "visitante_ids" not in hist.columns:
        return pd.DataFrame({"match_id": hist["match_id"].values})

    filas = []
    for _, fila in hist.iterrows():
        temporada_str = _temporada_anterior_str(fila["temporada"])
        m_l, ga_l, n_l = calidad_equipo(fila.get("local_ids"), temporada_str)
        m_v, ga_v, n_v = calidad_equipo(fila.get("visitante_ids"), temporada_str)
        filas.append({
            "match_id": fila["match_id"],
            "loc_calidad_minutos": m_l, "vis_calidad_minutos": m_v,
            "loc_calidad_ga": ga_l, "vis_calidad_ga": ga_v,
            "loc_calidad_conocidos": n_l, "vis_calidad_conocidos": n_v,
        })
    return pd.DataFrame(filas)


def construir(hist):
    """Una fila por partido, con los rasgos de los dos equipos enfrentados."""
    largo = calcular_btts(forma_reciente(medias_previas(a_largo(hist))))
    rasgos = [c for c in largo.columns
              if c.startswith(("m_", "r_", "btts_")) or c in ("partidos_previos", "descanso")]
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
    if os.path.exists(RUTA_H2H_PROFUNDO):
        h2h_crudo = pd.read_csv(RUTA_H2H_PROFUNDO)
        h2hp = calcular_h2h_profundo(hist, h2h_crudo).set_index("match_id")
        base["h2hp_partidos_previos"] = h2hp["h2hp_partidos_previos"]
        base["h2hp_pts_local_norm"] = h2hp["h2hp_pts_local_norm"]
        base["h2hp_gd_local"] = h2hp["h2hp_gd_local"]
    if os.path.exists(RUTA_JUGADOR_STATS):
        jug_crudo = pd.read_csv(RUTA_JUGADOR_STATS)
        calidad = calcular_calidad_plantilla(hist, jug_crudo)
        if "loc_calidad_minutos" in calidad.columns:
            calidad = calidad.set_index("match_id")
            for c in ("calidad_minutos", "calidad_ga", "calidad_conocidos"):
                base[f"loc_{c}"] = calidad[f"loc_{c}"]
                base[f"vis_{c}"] = calidad[f"vis_{c}"]
                base[f"dif_{c}"] = calidad[f"loc_{c}"] - calidad[f"vis_{c}"]
    # árbitro y clima: igual que box-score, solo entran si el backfill ya
    # tiene cobertura real -- una columna casi vacía tira todas las filas
    # via notna() aguas abajo (bug ya visto y arreglado el 21/09).
    if "arbitro" in hist.columns and hist["arbitro"].notna().mean() >= COBERTURA_MINIMA:
        arb = calcular_arbitro(hist).set_index("match_id")
        base["arbitro_tarjetas_media"] = arb["arbitro_tarjetas_media"]
        base["arbitro_partidos_previos"] = arb["arbitro_partidos_previos"]
    if "clima_temp" in hist.columns and hist["clima_temp"].notna().mean() >= COBERTURA_MINIMA:
        clima = hist.set_index("match_id")[["clima_temp", "clima_status"]]
        base["clima_temp"] = clima["clima_temp"]
        status = clima["clima_status"].fillna("").str.lower()
        base["clima_lluvia"] = status.str.contains("rain").astype(int)
        base["clima_viento"] = status.str.contains("wind").astype(int)
    rot = calcular_rotacion(hist)
    if "loc_rotacion" in rot.columns:
        rot = rot.set_index("match_id")
        base["loc_rotacion"] = rot["loc_rotacion"]
        base["vis_rotacion"] = rot["vis_rotacion"]
        base["dif_rotacion"] = rot["loc_rotacion"] - rot["vis_rotacion"]
        base["loc_rotacion_conocida"] = rot["loc_rotacion_conocida"]
        base["vis_rotacion_conocida"] = rot["vis_rotacion_conocida"]
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
            if c.startswith(("loc_", "vis_", "dif_", "h2h_", "h2hp_", "arbitro_", "clima_"))
            or c == "liga_id"]


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
    grupos = {"base": [], "elo": [], "h2h": [], "h2h_profundo": [], "tabla": [],
             "boxscore": [], "duelos": [], "arbitro": [], "clima": [],
             "rotacion": [], "calidad_plantilla": [], "forma_reciente": [],
             "btts": []}
    for c in columnas_rasgo(base):
        if c == "liga_id":
            grupos["base"].append(c)
        elif c.endswith("_elo"):
            grupos["elo"].append(c)
        elif c.startswith(("loc_btts_", "vis_btts_", "dif_btts_")):
            grupos["btts"].append(c)
        elif c.startswith(("loc_r_", "vis_r_", "dif_r_")) and "duelos" not in c:
            grupos["forma_reciente"].append(c)
        elif c.startswith("h2hp_"):
            grupos["h2h_profundo"].append(c)
        elif c.startswith("h2h_"):
            grupos["h2h"].append(c)
        elif "tabla_" in c:
            grupos["tabla"].append(c)
        elif c.startswith("arbitro_"):
            grupos["arbitro"].append(c)
        elif c.startswith("clima_"):
            grupos["clima"].append(c)
        elif "rotacion" in c:
            grupos["rotacion"].append(c)
        elif "calidad_" in c:
            grupos["calidad_plantilla"].append(c)
        elif "duelos" in c:
            # duelos_totales/duelos_ganados_pct: hasta hoy se colaban en
            # "elo" por un bug de substring ("elo" dentro de "duelos") --
            # ver CLAUDE.md "Bug en grupos_rasgo". Grupo propio, separado
            # del resto de box-score, para poder probarlo aislado: el
            # bug los tuvo SIEMPRE presentes en cualquier config con
            # "elo" (es decir, en todas), así que nunca se probó "cero
            # box-score" de verdad hasta corregir esto.
            grupos["duelos"].append(c)
        elif any(m in c for m in MEDIDAS_BOXSCORE):
            grupos["boxscore"].append(c)
        else:
            grupos["base"].append(c)
    return grupos


def columnas_rasgo_default(base):
    """
    Las columnas que usa el modelo en producción.

    CAMBIO 24/09 (barrido_combinatorio.py): la ronda anterior (CLAUDE.md
    "Ronda de variables cerrada") solo probó sumar cada candidata SOLA
    encima de árbitro+calidad_plantilla -- eso descarta interacciones
    entre candidatas que ninguna aporta por sí sola. Un barrido de las
    256 combinaciones posibles de las 8 candidatas (cribado a 2 semillas,
    luego las mejores reverificadas con el protocolo completo de 5) encontró
    que h2h+h2h_profundo+tabla+arbitro+calidad_plantilla JUNTAS baten a
    árbitro+calidad_plantilla en las dos métricas que importan, no solo
    Brier:

                                          suma sigmas   suma acierto-mercado
      base+elo solo                        -8.76           -17.3pp
      +arbitro+calidad_plantilla (viejo)   -8.12           -18.5pp
      +h2h+h2h_profundo+tabla+calidad      -7.94           -14.1pp
      +arbitro+h2h+h2h_profundo+tabla+calidad -7.93        -13.8pp  <- ahora

    Ningún mercado bate al mercado (haría falta +2s), y el acierto sigue
    perdiendo en casi todos los mercados -- esto NO es un hallazgo, es
    la mejor base encontrada hasta ahora, igual que antes. Pero por
    primera vez el ACIERTO (no solo el Brier) mejora de forma clara al
    cambiar de configuración: 45.3%/63.7%/58.0%/54.7%/63.2% vs mercado
    51.4%/65.6%/58.5%/58.5%/64.7% en resultado/mas_2_5/ambos_marcan/
    corners/tarjetas respectivamente -- sigue perdiendo en las 5, pero
    menos que la config anterior en 4 de 5 (empate en ambos_marcan).

    calidad_plantilla sigue siendo la variable individual más fuerte del
    proyecto. Box-score sigue fuera (empeora las 5 líneas en TODAS las
    combinaciones del barrido). Clima y rotación no entran: su cobertura
    parcial reduce la muestra utilizable y no compensan en el barrido.

    Todas siguen fusionadas en `hist` (modelo_xgboost.cargar()) y
    disponibles vía grupos_rasgo() para volver a probarlas si crece la
    muestra -- esto solo decide qué entra al entrenamiento de producción
    HOY, con la evidencia de HOY.
    """
    grupos = grupos_rasgo(base)
    permitidas = (set(grupos["base"]) | set(grupos["elo"]) | set(grupos["arbitro"])
                 | set(grupos["h2h"]) | set(grupos["h2h_profundo"])
                 | set(grupos["tabla"]) | set(grupos["calidad_plantilla"]))
    return [c for c in columnas_rasgo(base) if c in permitidas]


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
