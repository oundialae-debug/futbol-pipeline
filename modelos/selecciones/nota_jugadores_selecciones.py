"""
Nota "justa" por jugador para Inglaterra-España y Chequia-Croacia
(26/09/2026). Tema APARTE del proyecto de ambos marcan.

Idea del usuario: cruzar a los jugadores de las selecciones con nuestros
datos de club y darles una nota que mezcle, con prioridad al INICIO DE
TEMPORADA de su club, lo que rinden con su selección (quien rinde en el
club pero no con la selección baja; quien rinde en los dos sube).

Métrica común: la nota de partido de la API (matchRating, misma escala en
club y selección), ponderada por minutos.

  1. club_ahora   = nota media en su club desde el 01/07/2026, encogida
                    hacia la media de su posición con 270 minutos de peso
                    (pocos minutos -> cerca de la media; muchos -> su nota).
  2. seleccion    = nota media con la selección desde 2025, pesando más lo
                    reciente (vida media 180 días), encogida hacia su
                    club_ahora con 180 minutos de peso (sin partidos con la
                    selección, se queda en su nivel de club).
  3. nota         = 0.6 * club_ahora + 0.4 * seleccion
Sin datos de club (p. ej. liga checa): club_ahora = media de su posición,
y se marca.

Once de cada selección: el REAL si ya está en data/selecciones/alineaciones_hoy.csv
(modelos/selecciones/alineaciones_hoy.py); si no, el probable = los 11 con más minutos en
sus últimos 4 partidos. Un titular sin partidos con la selección entra con su
nota de club.
Salida: data/selecciones/notas_jugadores.csv y el once de cada equipo.
"""
import os
import numpy as np
import pandas as pd

HOY = pd.Timestamp.today().normalize()
INICIO_TEMPORADA = "2026-07-01"
K_CLUB, K_SEL = 270.0, 180.0
VIDA_MEDIA_SEL = 180.0
PESO_CLUB, PESO_SEL = 0.6, 0.4
import json
EQUIPOS = json.load(open("data/selecciones/equipos.json"))["equipos"]   # lo escribe descargar_selecciones.py


def num(s):
    return pd.to_numeric(s, errors="coerce")


def main():
    # ---- club ----
    h = pd.read_csv("data/historico_partidos.csv").set_index("match_id")
    club = pd.read_csv("data/historico_xg_jugador.csv")
    club = club[club.jugador_id.notna()].copy()
    club["fecha"] = club.match_id.map(h.fecha.astype(str).str[:10])
    # forma de club reciente que mantiene forma_clubes.py (partidos que el
    # histórico principal aún no tiene); si un partido está en los dos, vale uno
    if os.path.exists("data/selecciones/club_reciente.csv"):
        rec = pd.read_csv("data/selecciones/club_reciente.csv")
        club = pd.concat([club, rec[rec.jugador_id.notna()]]).drop_duplicates(["match_id", "jugador_id"])
    club["nota"], club["minutos"] = num(club.nota), num(club.minutos)
    club = club[(club.fecha >= INICIO_TEMPORADA) & (club.minutos > 0) & club.nota.notna()]
    club["jugador_id"] = club.jugador_id.astype(int)
    media_pos = club.groupby("posicion").apply(lambda g: np.average(g.nota, weights=g.minutos)).to_dict()
    media_global = np.average(club.nota, weights=club.minutos)
    agg_club = club.groupby("jugador_id").apply(lambda g: pd.Series({
        "club_min": g.minutos.sum(), "club_partidos": len(g),
        "club_nota_bruta": np.average(g.nota, weights=g.minutos),
        "club_goles": num(g.goalsScored).sum(), "club_asist": num(g.assists).sum()}))

    # temporada pasada (solo informativo): goles+asistencias por 90 en 25/26
    js = pd.read_csv("data/historico_jugador_stats.csv")
    js = js[js.temporada == "25/26"].copy()
    js["ga"] = num(js.goles).fillna(0) + num(js.asistencias).fillna(0)
    js["minutos"] = num(js.minutos)
    prev = js.groupby("jugador_id").agg(prev_min=("minutos", "sum"), prev_ga=("ga", "sum"))
    prev["prev_ga90"] = prev.prev_ga / prev.prev_min.replace(0, np.nan) * 90

    # ---- selección ----
    part = pd.read_csv("data/selecciones/partidos.csv").set_index("match_id")
    sel = pd.read_csv("data/selecciones/jugadores_partido.csv")
    sel["fecha"] = pd.to_datetime(sel.match_id.map(part.fecha))
    sel["nota"], sel["minutos"] = num(sel.nota), num(sel.minutos)
    sel = sel[sel.equipo_id.isin(EQUIPOS.values()) & (sel.minutos > 0)].copy()
    sel["dias"] = (HOY - sel.fecha).dt.days
    sel["w"] = sel.minutos * 0.5 ** (sel.dias / VIDA_MEDIA_SEL)

    ruta = "data/selecciones/alineaciones_hoy.csv"
    # la API devuelve el once vacío hasta ~1h antes: el csv queda vacío (sin cabecera)
    real = (pd.read_csv(ruta) if os.path.exists(ruta) and os.path.getsize(ruta) > 5
            else pd.DataFrame(columns=["match_id", "equipo_id", "jugador_id"]))
    # solo el once de los partidos de ESTA jornada: si la misma selección vuelve a
    # jugar, un alineaciones_hoy.csv viejo colaría el once del partido anterior
    real = real[real.match_id.isin([c[2] for c in json.load(open("data/selecciones/equipos.json"))["cruces"]])]
    POS = {"Goalkeeper": "Goalkeeper", "Defender": "Defender", "Midfielder": "Midfielder",
           "Forward": "Forward", "Attacker": "Forward"}
    filas = []
    for nombre, tid in EQUIPOS.items():
        s = sel[sel.equipo_id == tid]
        r = real[real.equipo_id == tid]
        ultimos = s.drop_duplicates("match_id").sort_values("fecha").match_id.tail(4)
        habitual = (s[s.match_id.isin(ultimos)].groupby(["jugador_id", "jugador"]).minutos.sum()
                    .sort_values(ascending=False).head(11).reset_index())
        if len(r) >= 11:
            once = r.assign(jugador_id=r.jugador_id.astype(int))
            fuente_once = "real"
        else:
            once, fuente_once = habitual, "probable"
        candidatos = pd.concat([s[["jugador_id", "jugador", "posicion"]],
                                once[~once.jugador_id.isin(s.jugador_id)][["jugador_id", "jugador"]]
                                .assign(posicion=[POS.get(str(x), None) for x in
                                                  once[~once.jugador_id.isin(s.jugador_id)].get("posicion", [])]
                                        if "posicion" in once else None)])
        for _, j in candidatos.drop_duplicates("jugador_id").iterrows():
            jid = int(j.jugador_id)
            g = s[(s.jugador_id == jid) & s.nota.notna()]
            ps = s[s.jugador_id == jid].posicion
            pos = ps.mode().iloc[0] if ps.notna().any() else j.posicion
            mu = media_pos.get(pos, media_global)
            tiene_club = jid in agg_club.index
            if tiene_club:
                c = agg_club.loc[jid]
                club_ahora = (c.club_nota_bruta * c.club_min + mu * K_CLUB) / (c.club_min + K_CLUB)
            else:
                club_ahora = mu
            seleccion = ((g.nota * g.w).sum() + club_ahora * K_SEL) / (g.w.sum() + K_SEL) if len(g) else club_ahora
            nota = PESO_CLUB * club_ahora + PESO_SEL * seleccion
            filas.append({
                "seleccion": nombre, "jugador_id": jid, "jugador": j.jugador, "posicion": pos,
                "once_probable": jid in set(once.jugador_id), "fuente_once": fuente_once,
                "once_habitual": jid in set(habitual.jugador_id),
                "club_partidos": int(agg_club.loc[jid].club_partidos) if tiene_club else 0,
                "club_min": int(agg_club.loc[jid].club_min) if tiene_club else 0,
                "club_nota_bruta": round(agg_club.loc[jid].club_nota_bruta, 2) if tiene_club else None,
                "club_goles": int(agg_club.loc[jid].club_goles) if tiene_club else None,
                "club_asist": int(agg_club.loc[jid].club_asist) if tiene_club else None,
                "prev_ga90_25_26": round(prev.prev_ga90.get(jid, np.nan), 2),
                "sel_partidos": len(g), "sel_min": int(s[s.jugador_id == jid].minutos.sum()),
                "sel_nota_bruta": round(np.average(g.nota, weights=g.w), 2) if len(g) and g.w.sum() > 0 else None,
                "club_ahora": round(club_ahora, 2), "seleccion_ajustada": round(seleccion, 2),
                "nota": round(nota, 2), "sin_datos_club": not tiene_club})
    t = pd.DataFrame(filas).sort_values(["seleccion", "once_probable", "nota"], ascending=[True, False, False])
    t.to_csv("data/selecciones/notas_jugadores.csv", index=False)

    print(f"Media de nota en club 2026/27 (todas las posiciones): {media_global:.2f}\n")
    for nombre in EQUIPOS:
        o = t[(t.seleccion == nombre) & t.once_probable]
        if o.empty:
            print(f"== {nombre}: SIN jugadores con datos (ni de selección ni once real) ==\n")
            continue
        print(f"== {nombre}: once {o.fuente_once.iloc[0]}, nota media {o.nota.mean():.2f} "
              f"({o.sin_datos_club.sum()} sin datos de club) ==")
        print(o[["jugador", "posicion", "club_partidos", "club_nota_bruta", "club_goles", "club_asist",
                 "sel_partidos", "sel_nota_bruta", "nota"]].to_string(index=False))
        print()


if __name__ == "__main__":
    main()
