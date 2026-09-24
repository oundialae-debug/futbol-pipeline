"""
Rasgos propios de mas_2_5 (Más de 2.5 goles), diseñados por el usuario el
24/09/2026. Se SUMAN a los de rasgos.py (Elo y tabla se reutilizan tal cual);
aquí solo está lo nuevo:

1. BASE CASA / FUERA (`casa_`, `fuera_`, `dif_cf_`)
   Medias de los últimos 8 partidos, pero del local SOLO en casa y del
   visitante SOLO fuera. Medidas: goles a favor y en contra, xG a favor y en
   contra, tiros a puerta y fuera (propios y del rival), córners, faltas,
   posesión, pases, centros y puntos. Sin amarillas (el usuario no las pidió).
   Además partidos previos EN ESE ESCENARIO, días de descanso (desde el último
   partido, sea donde sea) y la liga.

2. CALIDAD POR POSICIÓN (`cp_`)
   La posición sale de la formación de /lineups: el backfill guarda los 11
   IDs aplanando `initialLineup` línea a línea (portero, defensas, ..., delanteros).
   Comprobado con datos el 24/09: goles+asistencias por 90 min de la
   temporada anterior = 0.003 (1er ID), 0.10 (1ª línea), 0.28 (medias),
   0.53 (última línea). El orden es el esperado.
   - delanteros: g+a por 90 de su temporada ANTERIOR (hecho cerrado, sin fuga)
   - medios: g+a por 90 (temporada anterior) Y porterías a cero (el "mix")
   - defensas y portero: porterías a cero
   - minutos medios de la temporada anterior de los 11, y cuántos se conocen
   Porterías a cero POR JUGADOR: proporción de sus titularidades ANTERIORES
   en nuestro histórico en que su equipo no encajó. Contraída hacia la tasa
   global con K=5 titularidades ficticias, para que 1 partido no dé 0% o 100%.
   Por qué no el `cleanSheets` de /players/{id}/statistics: el backfill no lo
   guardó (solo goles/asistencias/minutos), y ese dato estilo Transfermarkt
   suele registrarse solo para porteros. Calcularlo del histórico lo da para
   cualquier posición y sin gastar cuota.

3. H2H RECIENTE CON GOLES (`h2hr_`)
   Enfrentamientos reales (/head-2-head) de los 2 años anteriores al partido,
   con peso doble a los del último año. Además de puntos y diferencia de
   goles, goles totales medios y tasa de Más de 2.5 -- lo que importa aquí.

Regla de siempre: solo información anterior al pitido. Cada función se
recorre en orden cronológico y actualiza su estado DESPUÉS de leerlo.
"""
from collections import defaultdict
import numpy as np
import pandas as pd

import rasgos

VENTANA = 8
MIN_PARTIDOS_ESCENARIO = 3
K_CONTRACCION = 5.0

MEDIDAS_CF = [
    ("goles", True), ("expected_goals", True), ("shots_on_target", True),
    ("shots_off_target", True), ("corners", True), ("fouls", True),
    ("possession", False), ("total_passes", True), ("crosses", True),
]


def base_casa_fuera(hist):
    largo = rasgos.a_largo(hist)
    cols = []
    for m, con_contra in MEDIDAS_CF:
        if m == "goles":
            cols += ["goles", "goles_contra"]
            continue
        if m in largo.columns:
            cols.append(m)
            if con_contra and f"contra_{m}" in largo.columns:
                cols.append(f"contra_{m}")
    largo["_pts"] = np.where(largo.goles > largo.goles_contra, 3,
                             np.where(largo.goles == largo.goles_contra, 1, 0)).astype(float)
    largo.loc[largo.goles.isna() | largo.goles_contra.isna(), "_pts"] = np.nan
    cols.append("_pts")
    largo = largo.sort_values(["equipo", "fecha"])
    # descanso: desde el último partido del equipo, sea en casa o fuera
    largo["descanso"] = largo.groupby("equipo")["fecha"].diff().dt.total_seconds() / 86400
    g = largo.groupby(["equipo", "en_casa"], sort=False)
    salida = {}
    for c in cols:
        salida[f"m_{c.lstrip('_')}"] = (g[c].shift(1)
                                        .groupby([largo["equipo"], largo["en_casa"]], sort=False)
                                        .rolling(VENTANA, min_periods=MIN_PARTIDOS_ESCENARIO)
                                        .mean().reset_index(level=[0, 1], drop=True))
    largo = largo.assign(**salida)
    largo["partidos_previos_esc"] = g.cumcount()
    feats = list(salida) + ["partidos_previos_esc", "descanso"]
    loc = largo[largo.en_casa == 1].set_index("match_id")
    vis = largo[largo.en_casa == 0].set_index("match_id")
    out = pd.DataFrame(index=loc.index)
    for c in feats:
        out[f"casa_{c}"] = loc[c]
        out[f"fuera_{c}"] = vis[c]
        out[f"dif_cf_{c}"] = loc[c] - vis[c]
    return out.reset_index()


def _posiciones(formacion, ids_str):
    """Lista [(jugador_id, 'POR'|'DEF'|'MED'|'DEL')] o None si no cuadra."""
    if pd.isna(formacion) or pd.isna(ids_str):
        return None
    ids = str(ids_str).split("|")
    try:
        lineas = [int(x) for x in str(formacion).split("-")]
    except ValueError:
        return None
    if len(ids) != 11 or sum(lineas) != 10 or len(lineas) < 2:
        return None
    pos = ["POR"]
    for k, n in enumerate(lineas):
        pos += ["DEF" if k == 0 else ("DEL" if k == len(lineas) - 1 else "MED")] * n
    return list(zip((int(i) for i in ids), pos))


def calidad_posicion(hist, jugador_stats):
    # temporada anterior: (jugador, "24/25") -> [minutos, g+a]
    prev = defaultdict(lambda: [0.0, 0.0])
    for r in jugador_stats.dropna(subset=["temporada"]).itertuples(index=False):
        v = prev[(int(r.jugador_id), r.temporada)]
        v[0] += 0 if pd.isna(r.minutos) else float(r.minutos)
        v[1] += (0 if pd.isna(r.goles) else float(r.goles)) + \
                (0 if pd.isna(r.asistencias) else float(r.asistencias))

    orden = hist.copy()
    orden["_f"] = pd.to_datetime(orden["fecha"], format="mixed", utc=True)
    orden = orden.sort_values("_f")
    cs_n = defaultdict(float)     # titularidades previas
    cs_k = defaultdict(float)     # porterías a cero en ellas
    glob_n, glob_k = 0, 0

    def lado(formacion, ids_str, temporada_prev, p0):
        pl = _posiciones(formacion, ids_str)
        vacio = {k: np.nan for k in ("del_ga90", "med_ga90", "med_cs", "def_cs",
                                     "por_cs", "minutos")}
        if pl is None:
            return {**vacio, "conocidos": 0}, None
        ga = {"DEL": [0.0, 0.0], "MED": [0.0, 0.0]}
        cs = {"MED": [], "DEF": [], "POR": []}
        minutos = []
        for jid, p in pl:
            st = prev.get((jid, temporada_prev))
            if st and st[0] > 0:
                minutos.append(st[0])
                if p in ga:
                    ga[p][0] += st[0]; ga[p][1] += st[1]
            if p in cs:
                cs[p].append((cs_k[jid] + K_CONTRACCION * p0) / (cs_n[jid] + K_CONTRACCION))
        r = {
            "del_ga90": ga["DEL"][1] / ga["DEL"][0] * 90 if ga["DEL"][0] > 0 else np.nan,
            "med_ga90": ga["MED"][1] / ga["MED"][0] * 90 if ga["MED"][0] > 0 else np.nan,
            "med_cs": float(np.mean(cs["MED"])) if cs["MED"] else np.nan,
            "def_cs": float(np.mean(cs["DEF"])) if cs["DEF"] else np.nan,
            "por_cs": float(np.mean(cs["POR"])) if cs["POR"] else np.nan,
            "minutos": float(np.mean(minutos)) if minutos else np.nan,
            "conocidos": len(minutos),
        }
        return r, [j for j, _ in pl]

    filas = []
    tiene_lineups = "local_ids" in orden.columns
    for f in orden.itertuples(index=False):
        p0 = glob_k / glob_n if glob_n else 0.28
        tprev = rasgos._temporada_anterior_str(f.temporada)
        if tiene_lineups:
            rl, ids_l = lado(f.local_formacion, f.local_ids, tprev, p0)
            rv, ids_v = lado(f.visitante_formacion, f.visitante_ids, tprev, p0)
        else:
            rl, ids_l = lado(np.nan, np.nan, tprev, p0)
            rv, ids_v = rl, None
        fila = {"match_id": f.match_id}
        for k in rl:
            fila[f"loc_cp_{k}"] = rl[k]
            fila[f"vis_cp_{k}"] = rv[k]
            fila[f"dif_cp_{k}"] = rl[k] - rv[k]
        filas.append(fila)
        # actualizar DESPUÉS de leer: el propio partido solo cuenta para los siguientes
        gl, gv = f.goles_l, f.goles_v
        if pd.notna(gl) and pd.notna(gv):
            for ids, encajados in ((ids_l, gv), (ids_v, gl)):
                if ids is None:
                    continue
                cero = 1.0 if encajados == 0 else 0.0
                for j in ids:
                    cs_n[j] += 1; cs_k[j] += cero
                glob_n += 1; glob_k += cero
    return pd.DataFrame(filas)


def h2h_reciente_goles(hist, h2h_crudo, anios=2, anios_peso=1, peso_extra=2.0):
    crudo = h2h_crudo.dropna(subset=["fecha"]).copy()
    crudo["fecha"] = pd.to_datetime(crudo["fecha"], utc=True)
    for c in ("local_id", "goles_l", "goles_v"):
        crudo[c] = pd.to_numeric(crudo[c], errors="coerce")
    crudo = crudo.dropna(subset=["goles_l", "goles_v"])
    por_par = {par: g.sort_values("fecha") for par, g in crudo.groupby("par")}
    filas = []
    for f in hist.itertuples(index=False):
        fecha = pd.to_datetime(f.fecha, format="mixed", utc=True)
        g = por_par.get(rasgos._clave_par(f.local_id, f.visitante_id))
        fila = {"match_id": f.match_id, "h2hr_partidos": 0, "h2hr_pts_local_norm": np.nan,
                "h2hr_gd_local": np.nan, "h2hr_goles_media": np.nan, "h2hr_mas25_tasa": np.nan}
        if g is not None:
            # filtro explícito por fecha: la API da "las últimas 10 A DÍA DE HOY"
            p = g[(g.fecha < fecha) & (g.fecha >= fecha - pd.Timedelta(days=365 * anios))]
            if len(p):
                mio = np.where(p.local_id == f.local_id, p.goles_l, p.goles_v)
                suyo = np.where(p.local_id == f.local_id, p.goles_v, p.goles_l)
                w = np.where((fecha - p.fecha).dt.days <= 365 * anios_peso, peso_extra, 1.0)
                pts = np.where(mio > suyo, 3, np.where(mio == suyo, 1, 0))
                tot = mio + suyo
                fila.update(h2hr_partidos=len(p),
                            h2hr_pts_local_norm=np.average(pts, weights=w) / 3,
                            h2hr_gd_local=np.average(mio - suyo, weights=w),
                            h2hr_goles_media=np.average(tot, weights=w),
                            h2hr_mas25_tasa=np.average(tot > 2.5, weights=w))
        filas.append(fila)
    return pd.DataFrame(filas)


def plantilla_nueva(hist, jugador_stats):
    """
    Cuántos titulares son NUEVOS en el equipo respecto a la temporada anterior
    (petición del usuario, 24/09: al empezar temporada cambian jugadores).

    El equipo se identifica por el club mayoritario del once en la temporada
    EN CURSO según /players/{id}/statistics (el club es identidad, no
    rendimiento: no hay fuga). Un titular es nuevo si ninguno de sus clubes de
    la temporada anterior es ese club (se acepta el filial: "Chelsea FC U21"
    contiene "Chelsea FC"). Sin datos de la temporada anterior -> desconocido.
    """
    from collections import Counter
    clubes = defaultdict(set)
    for r in jugador_stats.dropna(subset=["temporada", "club"]).itertuples(index=False):
        clubes[(int(r.jugador_id), r.temporada)].add(str(r.club))

    def lado(ids_str, t_act, t_prev):
        if pd.isna(ids_str):
            return np.nan, np.nan
        ids = [int(x) for x in str(ids_str).split("|")]
        cuenta = Counter(c for i in ids for c in clubes.get((i, t_act), ()))
        if not cuenta:
            return np.nan, np.nan
        club = cuenta.most_common(1)[0][0]
        nuevos = conocidos = 0
        for i in ids:
            previos = clubes.get((i, t_prev))
            if not previos:
                continue
            conocidos += 1
            if not any(club in c or c in club for c in previos):
                nuevos += 1
        return (nuevos / conocidos if conocidos else np.nan), float(nuevos)

    filas = []
    for f in hist.itertuples(index=False):
        t = int(f.temporada)
        t_act, t_prev = f"{t % 100:02d}/{(t + 1) % 100:02d}", rasgos._temporada_anterior_str(t)
        fl, nl = lado(getattr(f, "local_ids", np.nan), t_act, t_prev)
        fv, nv = lado(getattr(f, "visitante_ids", np.nan), t_act, t_prev)
        filas.append({"match_id": f.match_id,
                      "loc_pn_frac": fl, "vis_pn_frac": fv, "dif_pn_frac": fl - fv,
                      "loc_pn_n": nl, "vis_pn_n": nv, "dif_pn_n": nl - nv})
    return pd.DataFrame(filas)


def construir(hist, jugador_stats, h2h_crudo):
    """rasgos.construir() + los tres bloques nuevos, una fila por partido."""
    base = rasgos.construir(hist)
    for extra in (base_casa_fuera(hist), calidad_posicion(hist, jugador_stats),
                  h2h_reciente_goles(hist, h2h_crudo), plantilla_nueva(hist, jugador_stats)):
        base = base.merge(extra, on="match_id", how="left")
    return base.sort_values("fecha").reset_index(drop=True)


def grupos(base):
    """Grupos para la selección. `base_cf` es el núcleo pedido por el usuario."""
    cf = [c for c in base.columns if c.startswith(("casa_", "fuera_", "dif_cf_"))]
    cp = lambda *ks: [f"{p}_cp_{k}" for k in ks for p in ("loc", "vis", "dif")]
    g = rasgos.grupos_rasgo(base)
    # rasgos.grupos_rasgo() mete en "base" todo lo que empiece por loc_/vis_/dif_,
    # y eso incluye dif_cf_* y *_cp_* de este módulo. Sin este filtro la base
    # clásica llevaba dentro la calidad por posición y medio casa/fuera (bug
    # encontrado el 24/09: añadir cp_ataque no cambiaba NI UNA predicción).
    base_clasica = [c for c in g["base"] if "yellow_cards" not in c and c != "liga_id"
                    and not c.startswith("dif_cf_") and "_cp_" not in c and "_pn_" not in c]
    return {
        "base_cf": cf + ["liga_id"],
        "base_clasica": base_clasica + ["liga_id"],
        "elo": g["elo"],
        "tabla": g["tabla"],
        "cp_ataque": cp("del_ga90", "med_ga90"),
        "cp_defensa": cp("med_cs", "def_cs", "por_cs"),
        "cp_minutos": cp("minutos", "conocidos"),
        "plantilla_nueva": [f"{p}_pn_{k}" for k in ("frac", "n") for p in ("loc", "vis", "dif")],
        "h2h_reciente": ["h2hr_partidos", "h2hr_pts_local_norm", "h2hr_gd_local",
                         "h2hr_goles_media", "h2hr_mas25_tasa"],
        # referencias
        "calidad_plantilla_vieja": g["calidad_plantilla"],
        "produccion_padre": [c for c in rasgos.columnas_rasgo_default(base)
                             if not c.startswith("dif_cf_") and "_cp_" not in c
                             and "_pn_" not in c],
        "arbitro": g["arbitro"], "h2h": g["h2h"], "h2h_profundo": g["h2h_profundo"],
    }


def comprobar_sin_fuga(hist, jugador_stats, h2h_crudo, n=3):
    """Cambia el marcador de varios partidos y exige que SUS rasgos no se muevan."""
    base = construir(hist, jugador_stats, h2h_crudo)
    gr = grupos(base)
    cols = sorted(set(sum((gr[k] for k in ("base_cf", "cp_ataque", "cp_defensa",
                                            "cp_minutos", "h2h_reciente", "plantilla_nueva")), [])))
    con_lu = base[base[[c for c in cols if c.startswith("loc_cp_")]].notna().any(axis=1)]
    objetivos = con_lu.match_id.iloc[np.linspace(len(con_lu) // 4, len(con_lu) - 1, n).astype(int)]
    bi = base.set_index("match_id")
    movido = 0
    # UN partido trucado cada vez: trucar varios a la vez hace que el primero
    # mueva (legítimamente) los rasgos de los siguientes y parece fuga.
    for obj in objetivos:
        trucado = hist.copy()
        fila = trucado.match_id == obj
        for col in ("goles_l", "goles_v", "l_corners", "v_corners",
                    "l_expected_goals", "v_expected_goals"):
            if col in trucado.columns:
                trucado.loc[fila, col] = 0 if col.startswith("goles") else 99
        b2 = construir(trucado, jugador_stats, h2h_crudo).set_index("match_id")
        dif = (bi.loc[[obj], cols].fillna(-999) != b2.loc[[obj], cols].fillna(-999)).any()
        culpables = list(dif[dif].index)
        if culpables:
            return False, f"FUGA en {len(culpables)} rasgos: {culpables[:6]}"
        # control: el cambio SÍ debe mover rasgos de partidos posteriores
        despues = bi.index[bi.fecha > bi.loc[obj, "fecha"]]
        movido = max(movido, int((bi.loc[despues, cols].fillna(-999) !=
                                  b2.loc[despues, cols].fillna(-999)).any().sum()))
    if movido == 0:
        return False, "el marcador trucado no movió nada posterior: la prueba no prueba nada"
    return True, (f"{len(cols)} rasgos nuevos, {n} partidos trucados de uno en uno: ninguno "
                  f"usa el propio partido; hasta {movido} columnas sí cambian en partidos posteriores")


# Elegido por seleccion_combinaciones.py (24/09/2026): el mejor de 128 en el
# tramo de selección (rehecho tras corregir el bug de base_clasica). En la
# prueba final empata con la base clásica (-0.25s) -- ver CLAUDE.md. Se congela como candidato por
# protocolo, junto con base_clasica+elo, para juzgar los dos con partidos
# jugados desde el 25/09/2026, que ninguna prueba ha visto.
PRODUCCION = ["base_cf", "elo", "cp_ataque", "h2h_reciente"]
ALTERNATIVA = ["base_clasica", "elo"]


def columnas_produccion(base, grupos_elegidos=PRODUCCION):
    g = grupos(base)
    return list(dict.fromkeys(sum((g[k] for k in grupos_elegidos), [])))
