"""Datos de los formatos propios de 2yellow (usuario 06/10): 2yellow XI (once de la jornada por nota) y 2yellow Index
(top 5 de la semana). Solo NUESTROS datos (box-score de Highlightly), sin API.
    python3 redes/plantillas/datos_formatos.py xi <desde> <hasta> [selecciones|clubes] "<título>"
    python3 redes/plantillas/datos_formatos.py indice <desde> <hasta> [selecciones|clubes] "<título>"
2yellow Index = nota media x10 + 3 por gol o asistencia por partido (mín. 120' en el periodo), tope 100.
Clubes: solo jugadores con nombre en nuestros datos (todos desde el 9/10 con jugadores_redes.yml)."""
import json, subprocess, sys
from datetime import date
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import datos_rankings as R  # noqa: E402

TOP_FIFA = 40
SUMAS = ["goalsScored", "assists", "expectedGoals", "expectedAssists", "shotsOnTarget", "passesKey", "dribblesSuccessful",
         "passesSuccessful", "passesTotal", "tacklesTotal", "interceptionsTotal", "duelsWon", "duelsTotal", "cardsYellow",
         "cardsRed", "goalsSaved", "goalsConceded", "expectedGoalsPrevented"]

# 2yellow Index POR ROL (usuario 06/10: "si usas G+A somos lo mismo que los demás"). Cada métrica se pasa a percentil
# dentro de su rol y periodo (0-1); el índice es la media ponderada x100. Métrica sin datos (p. ej. xG en selecciones):
# se quita y se reparte su peso. (nombre visible, función por fila, peso, menos_es_mejor)
p90 = lambda c: (lambda r: (r[c] / r.minutos * 90) if pd.notna(r[c]) else None)
ROLES = {
    "ATT": [("G+A/90", lambda r: r.ga / r.minutos * 90, .22, False), ("dribbles/90", p90("dribblesSuccessful"), .20, False),
            ("key passes/90", p90("passesKey"), .18, False), ("xG+xA/90", lambda r: ((r.expectedGoals or 0) + (r.expectedAssists or 0)) / r.minutos * 90
                                                               if pd.notna(r.expectedGoals) else None, .15, False),
            ("shots on target/90", p90("shotsOnTarget"), .10, False), ("rating", lambda r: r.nota, .15, False)],
    # Usuario 07/10 (Kane salía 6º en el Balón de Oro): el perfil de ATT premia regate y pase clave, que es lo de un
    # extremo; un 9 se mide sobre todo por gol, ocasiones y tiro. Los delanteros centro se puntúan con su propio perfil
    # (solo entre ellos), pero siguen en la línea ATT para el XI y el top 5.
    "ST": [("G+A/90", lambda r: r.ga / r.minutos * 90, .30, False), ("xG+xA/90", lambda r: ((r.expectedGoals or 0) + (r.expectedAssists or 0)) / r.minutos * 90
                                                               if pd.notna(r.expectedGoals) else None, .22, False),
           ("shots on target/90", p90("shotsOnTarget"), .15, False), ("key passes/90", p90("passesKey"), .10, False),
           ("dribbles/90", p90("dribblesSuccessful"), .05, False), ("rating", lambda r: r.nota, .18, False)],
    "MID": [("key passes/90", p90("passesKey"), .18, False), ("passes/90", p90("passesSuccessful"), .12, False),
            ("pass %", lambda r: r.passesSuccessful / r.passesTotal * 100 if r.passesTotal else None, .10, False),
            ("tackles+int/90", lambda r: ((r.tacklesTotal or 0) + (r.interceptionsTotal or 0)) / r.minutos * 90, .18, False),
            ("duels won/90", p90("duelsWon"), .12, False), ("dribbles/90", p90("dribblesSuccessful"), .10, False),
            ("G+A/90", lambda r: r.ga / r.minutos * 90, .08, False), ("rating", lambda r: r.nota, .12, False)],
    "DEF": [("tackles+int/90", lambda r: ((r.tacklesTotal or 0) + (r.interceptionsTotal or 0)) / r.minutos * 90, .28, False),
            ("duels won/90", p90("duelsWon"), .18, False),
            ("duel %", lambda r: r.duelsWon / r.duelsTotal * 100 if r.duelsTotal else None, .14, False),
            ("pass %", lambda r: r.passesSuccessful / r.passesTotal * 100 if r.passesTotal else None, .10, False),
            ("passes/90", p90("passesSuccessful"), .08, False),
            ("cards/90", lambda r: ((r.cardsYellow or 0) + 3 * (r.cardsRed or 0)) / r.minutos * 90, .07, True),
            ("rating", lambda r: r.nota, .15, False)],
    "GK": [("saves/90", p90("goalsSaved"), .35, False), ("goals prevented", lambda r: r.expectedGoalsPrevented, .30, False),
           ("conceded/90", p90("goalsConceded"), .20, True), ("rating", lambda r: r.nota, .15, False)],
}
ROL_DE = {"Left Winger": "ATT", "Right Winger": "ATT", "Centre-Forward": "ATT", "Second Striker": "ATT",
          "Left Midfield": "ATT", "Right Midfield": "ATT", "Central Midfield": "MID", "Defensive Midfield": "MID",
          "Attacking Midfield": "MID", "Centre-Back": "DEF", "Left-Back": "DEF", "Right-Back": "DEF", "Goalkeeper": "GK"}
ROL_LINEA = {"FW": "ATT", "MF": "MID", "DF": "DEF", "GK": "GK"}


# Desempate futbolístico por rol (usuario 06/10: "si dos empatan en la misma posición, usa un dato extra con criterio"):
# atacantes = ocasiones creadas y generadas (xG+xA/90; sin xG, pases clave+tiros a puerta/90); medios = pases clave/90;
# defensas = entradas+intercepciones/90; porteros = paradas/90. Si aún empatan, más minutos.
def desempate(r):
    m = r.minutos or 1
    if r.rol == "ATT":
        if pd.notna(r.expectedGoals):
            return ((r.expectedGoals or 0) + (r.expectedAssists or 0)) / m * 90
        return ((r.passesKey or 0) + (r.shotsOnTarget or 0)) / m * 90
    if r.rol == "MID":
        return (r.passesKey or 0) / m * 90
    if r.rol == "DEF":
        return ((r.tacklesTotal or 0) + (r.interceptionsTotal or 0)) / m * 90
    return (r.goalsSaved or 0) / m * 90


# Banda contraria: nunca (antes Lamine, extremo derecho, salía de extremo izquierdo por empatar con Olise).
CONTRARIA = {"LW": {"Right Winger", "Right Midfield"}, "RW": {"Left Winger", "Left Midfield"},
             "LB": {"Right-Back"}, "RB": {"Left-Back"}}


def puntuar(t):
    """Añade rol, índice por rol (0-99) y las 2 métricas que más le suben (para el desglose)."""
    pos = posiciones()
    t = t.copy()
    t["rol"] = [ROL_DE.get(next(iter(pos.get(int(i), ({None}, set()))[0]), None), ROL_LINEA[l]) for i, l in zip(t.jugador_id, t.pos)]
    nueve = {int(i) for i, (prin, _) in pos.items() if prin & {"Centre-Forward", "Second Striker"}}
    t["perfil"] = ["ST" if r == "ATT" and int(i) in nueve else r for r, i in zip(t.rol, t.jugador_id)]
    t["indice"], t["detalle"] = 0.0, ""
    for rol, mets in ROLES.items():
        g = t[t.perfil == rol]
        if g.empty:
            continue
        vals = pd.DataFrame({m[0]: [m[1](r) for _, r in g.iterrows()] for m in mets}, index=g.index).astype(float)
        pct = pd.DataFrame({m[0]: vals[m[0]].rank(pct=True, ascending=not m[3]) for m in mets if vals[m[0]].notna().any()})
        pesos = pd.Series({m[0]: m[2] for m in mets if m[0] in pct})
        t.loc[g.index, "indice"] = ((pct * pesos).sum(axis=1) / pesos.sum() * 100).clip(upper=99).round(0)
        mejores = pct.drop(columns=["rating"], errors="ignore").apply(lambda r: r.nlargest(2).index.tolist(), axis=1)
        fmt = lambda v, m: f"{v:.0f}{'%' if '%' in m else ''} {m.replace(' %', '')}" if "%" in m else f"{v:.1f} {m}"
        t.loc[g.index, "detalle"] = [" · ".join(fmt(vals.at[i, m], m) for m in mejores[i]) for i in g.index]
    return t
POS = {"Goalkeeper": "GK", "Defender": "DF", "Midfielder": "MF", "Forward": "FW", "Attacker": "FW"}
FORMACION = {"GK": 1, "DF": 4, "MF": 3, "FW": 3}


def filas(desde, hasta, fuente):
    if fuente == "selecciones":
        p = pd.read_csv(ROOT / "data/selecciones/partidos.csv")
        p = p[(p.fecha >= desde) & (p.fecha <= hasta) & p.goles_l.notna()]
        # Nivel (usuario 06/10: el XI se llenaba de Bielorrusia/Estonia con notas altas contra rivales flojos):
        # solo partidos entre dos selecciones del top 40 FIFA.
        rk = pd.read_csv(ROOT / "data/selecciones/ranking_fifa.csv").sort_values("fecha").groupby("equipo").puesto.last()
        top = set(rk[rk <= TOP_FIFA].index)
        torneo = p.competicion.isin(["World Cup", "European Championship", "Euro", "Copa America"])
        p = p[torneo | (p.local.isin(top) & p.visitante.isin(top))]  # en un Mundial/Euro todos los rivales cuentan
        j = pd.read_csv(ROOT / "data/selecciones/jugadores_partido.csv", low_memory=False)
        j = j[j.match_id.isin(p.match_id)].copy()
        eq = pd.concat([p[["local_id", "local"]].set_axis(["id", "n"], axis=1), p[["visitante_id", "visitante"]].set_axis(["id", "n"], axis=1)])
        j["equipo"] = j.equipo_id.map(dict(zip(eq.id, eq.n)))
        comp = ", ".join(sorted(p.competicion.unique()))
    else:
        # clubes = 5 grandes ligas; ucl = Champions; clubes+ucl = las dos (XI del mes, usuario 06/10)
        trozos, comps = [], []
        if "clubes" in fuente:
            h = pd.read_csv(ROOT / "data/historico_partidos.csv", low_memory=False)
            h = h[(h.fecha.astype(str).str[:10] >= desde) & (h.fecha.astype(str).str[:10] <= hasta) & h.liga.isin(R.GRANDES) & h.goles_l.notna()]
            x = pd.read_csv(ROOT / "data/historico_xg_jugador.csv", low_memory=False)
            x = x[x.match_id.isin(h.match_id) & x.jugador_id.notna()].copy()
            x["jugador"] = x.jugador_id.astype(int).map(R.nombres_propios())
            trozos.append((x, h)); comps.append("Top 5 leagues")
        if "ucl" in fuente:
            u = pd.read_csv(ROOT / "data/redes/ucl_partidos.csv")
            u = u[(u.fecha.astype(str).str[:10] >= desde) & (u.fecha.astype(str).str[:10] <= hasta)]
            x = pd.read_csv(ROOT / "data/redes/ucl_jugadores.csv", low_memory=False)
            x = x[x.match_id.isin(u.match_id) & x.jugador_id.notna()].copy()
            nom = R.nombres_propios()
            x["jugador"] = x.jugador.fillna(x.jugador_id.astype(int).map(nom))
            trozos.append((x, u)); comps.append("Champions League")
        j = pd.concat([t[0] for t in trozos])
        h = pd.concat([t[1][["match_id", "local_id", "local", "visitante_id", "visitante"]] for t in trozos])
        eq = pd.concat([h[["local_id", "local"]].set_axis(["id", "n"], axis=1), h[["visitante_id", "visitante"]].set_axis(["id", "n"], axis=1)])
        j["equipo"] = j.equipo_id.map(dict(zip(eq.id, eq.n)))
        sin = j.jugador.isna() & (pd.to_numeric(j.minutos, errors="coerce") > 0)
        if sin.mean() > 0.05:
            print(f"[!] {sin.mean():.0%} de filas sin nombre: lanza redes_api.yml modo nombres antes de publicar")
        j = j.dropna(subset=["jugador"])
        comp = " + ".join(comps)
    for c in ["nota", "minutos"] + SUMAS:
        j[c] = pd.to_numeric(j.get(c), errors="coerce")
    j = j[j.minutos > 0]
    agg = {"jugador": ("jugador", "last"), "equipo": ("equipo", "last"), "posicion": ("posicion", "last"),
           "nota": ("nota", "mean"), "partidos": ("match_id", "nunique"), "minutos": ("minutos", "sum")}
    agg.update({c: (c, lambda v: v.sum(min_count=1)) for c in SUMAS})
    t = j.groupby("jugador_id").agg(**agg).reset_index()
    t["ga"] = t.goalsScored.fillna(0) + t.assists.fillna(0)
    t["pos"] = t.posicion.map(POS)
    # Mínimo de minutos COMÚN al XI y a los top 5 (si no, las cifras no cuadran entre formatos):
    # 60' por partido que jugó SU equipo en el periodo (jornada = 60', parón de 2 = 120'), tope 360' (torneo).
    pj_eq = j.groupby("equipo").match_id.nunique()
    t = t[t.minutos >= (60 * t.equipo.map(pj_eq).fillna(1)).clip(upper=360)]
    if (pd.Timestamp(hasta) - pd.Timestamp(desde)).days > 10:  # mes o torneo: muestra mínima (antes colaba un AEK con 1 partido)
        t = t[t.minutos >= 270]
    return t.dropna(subset=["nota", "pos"]), comp


def render(nombre, datos):
    out = ROOT / "redes/plantillas/salida" / f"{date.today()}_{nombre}"
    out.mkdir(parents=True, exist_ok=True)
    jf = out / f"{nombre}.json"
    jf.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    subprocess.run([sys.executable, str(ROOT / "redes/plantillas/generar.py"), str(jf), "-o", str(out)], check=True)


def corto(n):
    p = str(n).split()
    return n if len(n) <= 13 or len(p) < 2 else " ".join(p[1:])  # quita el nombre de pila: "Kevin De Bruyne" -> "De Bruyne"


# Huecos del 4-3-3 en orden de dibujo (izquierda -> derecha) y qué posiciones de jugador_perfil.csv valen para cada uno.
HUECOS = [("FW", "LW", {"Left Winger", "Left Midfield"}), ("FW", "ST", {"Centre-Forward", "Second Striker"}),
          ("FW", "RW", {"Right Winger", "Right Midfield"}),
          ("MF", "CM", {"Central Midfield", "Attacking Midfield", "Defensive Midfield"}), ("MF", "DM", {"Defensive Midfield", "Central Midfield"}),
          ("MF", "CM", {"Central Midfield", "Attacking Midfield", "Defensive Midfield"}),
          ("DF", "LB", {"Left-Back"}), ("DF", "CB", {"Centre-Back"}), ("DF", "CB", {"Centre-Back"}), ("DF", "RB", {"Right-Back"}),
          ("GK", "GK", {"Goalkeeper"})]


def posiciones():
    pf = pd.read_csv(ROOT / "data/jugador_perfil.csv", usecols=["jugador_id", "posicion", "posicion_2"])
    out = {}
    for r in pf.itertuples():
        prin = {r.posicion} if isinstance(r.posicion, str) else set()
        sec = {x.strip() for x in str(r.posicion_2).split(",")} if isinstance(r.posicion_2, str) else set()
        out[int(r.jugador_id)] = (prin, sec)
    return out


def xi(desde, hasta, fuente="clubes", titulo=None):
    """2yellow XI = los 11 con mejor 2yellow Index, cada uno en un hueco del 4-3-3 que sea SU posición
    (jugador_perfil.csv: principal, o secundaria con -3 puntos). Reparto global: se recorren todas las parejas
    jugador-hueco de mejor a peor (antes Porro salía de central y Kane donde no era). Sin perfil (Messi, fuera de las
    5 grandes) solo puede ir al hueco central de su línea."""
    t, comp = filas(desde, hasta, fuente)
    t = puntuar(t)
    pos = posiciones()
    parejas = []
    t = t.reset_index(drop=True)
    for k, (linea, hueco, valen) in enumerate(HUECOS):
        rol_hueco = ROL_LINEA[linea]
        central = {"ST": "FW", "DM": "MF", "CB": "DF", "GK": "GK"}.get(hueco)
        for r in t.itertuples():
            if r.rol != rol_hueco:  # nunca fuera de su rol (antes Dasilva, lateral, salía de extremo)
                continue
            if int(r.jugador_id) in pos:
                prin, sec = pos[int(r.jugador_id)]
                if prin & CONTRARIA.get(hueco, set()):
                    continue
                if prin & valen:
                    parejas.append((r.indice, k, r))
                elif sec & valen:
                    parejas.append((r.indice - 3, k, r))
            elif central == r.pos:
                parejas.append((r.indice, k, r))
    parejas.sort(key=lambda x: (-x[0], -desempate(x[2]), -x[2].minutos, x[1]))
    ocupado, usados, asign = set(), set(), {}
    for punt, k, r in parejas:
        if k in ocupado or r.jugador_id in usados:
            continue
        ocupado.add(k); usados.add(r.jugador_id); asign[k] = r
    if len(asign) < len(HUECOS):
        sys.exit("[!] faltan huecos por cubrir: no se publica un XI incompleto")
    jug = [{"name": corto(R.visible_nombre(asign[k].jugador)), "team": asign[k].equipo, "pos": linea, "slot": hueco,
            "value": int(asign[k].indice), "rating": round(float(asign[k].nota), 1)} for k, (linea, hueco, _) in enumerate(HUECOS)]
    render(f"xi_{desde}_{hasta}", {"template": "xi", "competition": comp, "kicker": "2yellow XI",
                                   "title": titulo or "Team of the week", "metric": "2yellow Index by role: attack, midfield, defence · 4-3-3", "players": jug,
                                   "question": "Who did we leave out?"})


NOMBRE_ROL = {"ATT": ("Attackers", "Goals+assists, dribbles, key passes, shots"),
              "MID": ("Midfielders", "Chances created, passing, tackles+interceptions, duels"),
              "DEF": ("Defenders", "Tackles+interceptions, duels won, passing, discipline"),
              "GK": ("Goalkeepers", "Saves, goals prevented, goals conceded")}


def indice(desde, hasta, fuente="clubes", titulo=None, rol="ATT"):
    """2yellow Index de un rol: top 5 de la semana (ATT, MID, DEF o GK). Desglose: las 2 métricas donde más destaca."""
    t, comp = filas(desde, hasta, fuente)
    t = puntuar(t)
    t = t[t.rol == rol].sort_values(["indice", "nota"], ascending=False).head(5)
    nombre, expl = NOMBRE_ROL[rol]
    rows = [{"name": R.visible_nombre(r.jugador), "team": r.equipo, "value": int(r.indice), "detail": r.detalle} for r in t.itertuples()]
    render(f"indice_{rol}_{desde}_{hasta}", {"template": "indice", "competition": comp, "kicker": f"2yellow Index · {nombre}",
                                             "title": titulo or f"Top 5 {nombre.lower()} of the week", "metric": expl,
                                             "rows": rows, "question": "Who's too low?"})


def balon_oro_doble():
    """Usuario 07/10: dos listas juntas. MERECE = rendimiento por posición (índice 2yellow por perfil, liga 25/26 +
    Mundial, ponderado por minutos y encogido hacia la media con 1350' para que pocos minutos no inflen la media) 60%
    + títulos 35% (Mundial 50%, liga 25%, Champions 25%) + juego limpio 5%. GANARÁ = 70% MERECE + 30% popularidad
    (visitas de Wikipedia en 5 idiomas, escala logarítmica; data/redes/popularidad_bdo.csv, redes_api.py popularidad)."""
    import numpy as np
    c, _ = filas("2025-08-01", "2026-06-30", "clubes"); c = puntuar(c)
    w, _ = filas("2026-06-11", "2026-07-20", "selecciones"); w = puntuar(w)
    b = R.indice_bdo(mostrar=False).set_index("jugador")
    t, _ = R.jugadores_propios(temporada=2025)
    rows = []
    for nom in b.index:
        jid = int(R.buscar(t, nom).jugador_id)
        rc, rw = c[c.jugador_id == jid], w[w.jugador_id == jid]
        mc, mw = rc.minutos.sum(), rw.minutos.sum()
        ind = ((rc.indice.iloc[0] if len(rc) else 0) * mc + (rw.indice.iloc[0] if len(rw) else 0) * mw) / max(mc + mw, 1)
        rows.append({"jugador": nom, "equipo": b.at[nom, "equipo"], "nacion": b.at[nom, "nacion"], "min": mc + mw, "ind": ind,
                     "col": .25 * b.at[nom, "liga_t"] + .25 * b.at[nom, "ucl"] + .5 * b.at[nom, "mundial"], "fp": b.at[nom, "fairplay"]})
    x = pd.DataFrame(rows)
    K = 1350
    x["ind_s"] = (x.ind * x["min"] + x.ind.mean() * K) / (x["min"] + K)
    i = (x.ind_s - x.ind_s.min()) / (x.ind_s.max() - x.ind_s.min())
    x["merece"] = (100 * (.6 * i + .35 * x.col / x.col.max() + .05 * x.fp)).round(0)
    pop = pd.read_csv(ROOT / "data/redes/popularidad_bdo.csv").set_index("jugador").visitas
    lp = np.log10(x.jugador.map(pop))
    x["gana"] = (.7 * x.merece + 30 * (lp - lp.min()) / (lp.max() - lp.min())).round(0)
    print(x.sort_values("merece", ascending=False).head(5)[["jugador", "merece"]].to_string(index=False))
    print(x.sort_values("gana", ascending=False).head(5)[["jugador", "gana"]].to_string(index=False))
    return x


if __name__ == "__main__":
    {"xi": xi, "indice": indice, "balon_oro_doble": balon_oro_doble}[sys.argv[1]](*sys.argv[2:])
