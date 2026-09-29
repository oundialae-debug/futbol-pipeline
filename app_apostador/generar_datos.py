"""
Datos reales para las maquetas de app_apostador/.

Solo LEE ficheros de data/ (no los modifica) y escribe app_apostador/datos.json.
No llama a ninguna API.

Qué calcula (LaLiga, temporada 2026/27 tras 7 jornadas, y jornada 8):
- Tabla de clasificación y ranking por fuerza (Elo, misma fórmula que
  scripts/rasgos.py: K=20, ventaja de local 60, multiplicador por goles).
- Probabilidad 1-X-2 de cada partido de la jornada 8: logística ordenada sobre
  la diferencia de Elo, ajustada con todos los partidos de LaLiga del histórico.
  Se comprueba la calibración por tramos (dice X%, pasa Y%).
- Cuota justa = 1 / probabilidad.
- Forma (últimos 5), goles: % de partidos con más de 2,5 y con ambos marcan
  (últimos 10 de cada equipo).
- Historial entre Real Madrid y Villarreal (data/historico_h2h_profundo.csv).
- Árbitros de LaLiga: tarjetas por partido y % de partidos con más de 4,5
  tarjetas (temporadas 2025/26 y 2026/27, mínimo 15 partidos).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SALIDA = Path(__file__).resolve().parent / "datos.json"

LIGA = "La Liga"
TEMPORADA = 2026

NOMBRES = {  # nombre de la API -> nombre corto para la app
    "Atlético Madrid": "Atlético", "Celta de Vigo": "Celta",
    "Deportivo La Coruña": "Deportivo", "Malaga": "Málaga",
    "Racing Santander": "Racing", "Real Betis": "Betis",
    "Sevilla FC": "Sevilla", "Rayo Vallecano": "Rayo", "Athletic Club": "Athletic",
}


def corto(n):
    return NOMBRES.get(n, n)


def elo_previo(hist, k=20.0, ventaja_local=60.0):
    """Igual que rasgos.calcular_elo, pero devuelve también los ratings finales."""
    ratings, filas = {}, []
    for _, f in hist.sort_values("fecha").iterrows():
        l, v = f["local_id"], f["visitante_id"]
        rl, rv = ratings.get(l, 1500.0), ratings.get(v, 1500.0)
        filas.append((f["match_id"], rl, rv))
        gl, gv = f["goles_l"], f["goles_v"]
        if pd.isna(gl) or pd.isna(gv):
            continue
        dif = abs(gl - gv)
        g = 1.0 if dif <= 1 else (1.5 if dif == 2 else (11 + dif) / 8.0)
        esp = 1.0 / (1.0 + 10 ** (-(rl + ventaja_local - rv) / 400.0))
        real = 1.0 if gl > gv else (0.5 if gl == gv else 0.0)
        c = k * g * (real - esp)
        ratings[l] = rl + c
        ratings[v] = rv - c
    return pd.DataFrame(filas, columns=["match_id", "elo_l", "elo_v"]), ratings


def ajustar_ordenada(d, y):
    """Logística ordenada: y en {0 visitante, 1 empate, 2 local}."""
    def nll(p):
        b, c1, c2 = p
        if c2 <= c1:
            return 1e9
        s = lambda z: 1 / (1 + np.exp(-z))
        p_v = s(c1 - b * d)
        p_x = s(c2 - b * d) - p_v
        p_l = 1 - s(c2 - b * d)
        pr = np.choose(y, [p_v, p_x, p_l])
        return -np.log(np.clip(pr, 1e-12, 1)).sum()
    return minimize(nll, [0.005, -0.8, 0.4], method="Nelder-Mead",
                    options={"maxiter": 4000, "xatol": 1e-7, "fatol": 1e-7}).x


def probs(params, d):
    b, c1, c2 = params
    s = lambda z: 1 / (1 + np.exp(-z))
    p_v = s(c1 - b * d)
    p_x = s(c2 - b * d) - p_v
    return 1 - p_v - p_x, p_x, p_v


def main():
    h = pd.read_csv(DATA / "historico_partidos.csv")
    ll = h[h.liga == LIGA].copy()
    ll["fecha"] = pd.to_datetime(ll["fecha"], utc=True)
    previo, ratings = elo_previo(ll)
    ll = ll.merge(previo, on="match_id")
    jug = ll.dropna(subset=["goles_l", "goles_v"]).copy()
    jug["y"] = np.where(jug.goles_l > jug.goles_v, 2,
                        np.where(jug.goles_l == jug.goles_v, 1, 0))
    # Sin la primera temporada: ahí todos empiezan en 1500 y el Elo aún no sabe nada.
    ajuste = jug[jug.fecha >= jug.fecha.min() + pd.Timedelta(days=300)]
    d = (ajuste.elo_l - ajuste.elo_v).values
    params = ajustar_ordenada(d, ajuste.y.values)
    pl, px, pv = probs(params, d)
    ajuste = ajuste.assign(pl=pl)
    # Calibración de "gana el local": dice X%, pasa Y%
    tramos = pd.cut(ajuste.pl, [0, .3, .45, .6, .75, 1])
    cal = [{"dice": round(100 * g.pl.mean(), 1),
            "pasa": round(100 * (g.y == 2).mean(), 1), "n": int(len(g))}
           for _, g in ajuste.groupby(tramos, observed=True)]

    # --- Tabla y fuerza tras 7 jornadas
    t = jug[jug.temporada == TEMPORADA]
    equipos = {}
    for _, f in t.iterrows():
        for lado, eq, gf, gc in (("l", f.local, f.goles_l, f.goles_v),
                                 ("v", f.visitante, f.goles_v, f.goles_l)):
            e = equipos.setdefault(eq, {"pj": 0, "pts": 0, "gf": 0, "gc": 0})
            e["pj"] += 1
            e["gf"] += int(gf)
            e["gc"] += int(gc)
            e["pts"] += 3 if gf > gc else (1 if gf == gc else 0)
    ids = dict(zip(ll.local, ll.local_id))
    tabla = sorted(equipos.items(),
                   key=lambda kv: (-kv[1]["pts"], -(kv[1]["gf"] - kv[1]["gc"]), -kv[1]["gf"]))
    por_elo = sorted(equipos, key=lambda e: -ratings[ids[e]])
    filas_tabla = []
    for i, (eq, e) in enumerate(tabla, 1):
        filas_tabla.append({"pos": i, "equipo": corto(eq), "pj": e["pj"], "pts": e["pts"],
                            "dg": e["gf"] - e["gc"], "gf": e["gf"], "gc": e["gc"],
                            "elo": round(ratings[ids[eq]]),
                            "pos_fuerza": por_elo.index(eq) + 1})

    # --- Jornada 8
    cal_df = pd.read_csv(DATA / "calendario.csv")
    j8 = cal_df[(cal_df.liga == LIGA) & (cal_df.fecha <= "2026-10-12")].sort_values(["fecha", "saque_utc"])
    pos = {f["equipo"]: f for f in filas_tabla}
    partidos = []
    for _, f in j8.iterrows():
        dd = ratings[ids[f.local]] - ratings[ids[f.visitante]]
        a, b, c = (float(x[0]) for x in probs(params, np.array([dd])))
        partidos.append({"fecha": f.fecha, "hora_utc": f.saque_utc,
                         "local": corto(f.local), "visitante": corto(f.visitante),
                         "p1": round(100 * a), "px": round(100 * b), "p2": round(100 * c),
                         "justa1": round(1 / a, 2), "justax": round(1 / b, 2), "justa2": round(1 / c, 2),
                         "local_tabla": pos[corto(f.local)]["pos"], "local_fuerza": pos[corto(f.local)]["pos_fuerza"],
                         "vis_tabla": pos[corto(f.visitante)]["pos"], "vis_fuerza": pos[corto(f.visitante)]["pos_fuerza"]})

    # --- Forma y goles por equipo
    def ultimos(eq, n):
        m = jug[(jug.local == eq) | (jug.visitante == eq)].sort_values("fecha").tail(n)
        out = []
        for _, f in m.iterrows():
            casa = f.local == eq
            gf, gc = (f.goles_l, f.goles_v) if casa else (f.goles_v, f.goles_l)
            out.append({"rival": corto(f.visitante if casa else f.local), "casa": bool(casa),
                        "gf": int(gf), "gc": int(gc),
                        "r": "G" if gf > gc else ("E" if gf == gc else "P")})
        return out

    def goles(eq):
        u = ultimos(eq, 10)
        return {"n": len(u),
                "mas25": sum(x["gf"] + x["gc"] > 2 for x in u),
                "ambos": sum(x["gf"] > 0 and x["gc"] > 0 for x in u),
                "gf_media": round(sum(x["gf"] for x in u) / len(u), 2),
                "gc_media": round(sum(x["gc"] for x in u) / len(u), 2)}

    liga_ult = jug[jug.temporada >= TEMPORADA - 1]
    base = {"mas25": round(100 * ((liga_ult.goles_l + liga_ult.goles_v) > 2).mean(), 1),
            "ambos": round(100 * ((liga_ult.goles_l > 0) & (liga_ult.goles_v > 0)).mean(), 1),
            "goles_media": round((liga_ult.goles_l + liga_ult.goles_v).mean(), 2),
            "n": int(len(liga_ult))}

    foco = {}
    for eq in ("Real Madrid", "Villarreal"):
        foco[corto(eq)] = {"forma": ultimos(eq, 5), "goles": goles(eq),
                           "elo_hist": [round(x) for x in _elo_temporada(ll, ids[eq])] + [round(ratings[ids[eq]])]}

    # --- H2H real
    h2h = pd.read_csv(DATA / "historico_h2h_profundo.csv")
    a_id, b_id = ids["Real Madrid"], ids["Villarreal"]
    par = "_".join(str(x) for x in sorted([a_id, b_id]))
    hh = h2h[h2h.par == par].sort_values("fecha").tail(10)
    h2h_lista = []
    for _, f in hh.iterrows():
        rma_casa = f.local_id == a_id
        g_rma, g_vil = (f.goles_l, f.goles_v) if rma_casa else (f.goles_v, f.goles_l)
        h2h_lista.append({"fecha": f.fecha[:10], "rma_casa": bool(rma_casa),
                          "rma": int(g_rma), "vil": int(g_vil)})

    # --- Árbitros
    arb = pd.read_csv(DATA / "historico_arbitro_clima.csv")
    ma = jug.merge(arb, on="match_id")
    ma = ma[ma.temporada >= TEMPORADA - 1].dropna(subset=["arbitro"])
    ma["tarjetas"] = ma[["l_yellow_cards", "l_red_cards", "v_yellow_cards", "v_red_cards"]].fillna(0).sum(axis=1)
    ma = ma[ma[["l_yellow_cards", "v_yellow_cards"]].notna().all(axis=1)]
    media_liga = ma.tarjetas.mean()
    pct_liga = 100 * (ma.tarjetas > 4.5).mean()
    arbitros = []
    for nombre, g in ma.groupby("arbitro"):
        if len(g) < 15:
            continue
        arbitros.append({"nombre": nombre, "n": int(len(g)),
                         "media": round(g.tarjetas.mean(), 2),
                         "pct_mas45": round(100 * (g.tarjetas > 4.5).mean()),
                         # sigmas de la diferencia con la liga: |z| < 2 puede ser azar
                         "sigmas": round((g.tarjetas.mean() - media_liga) / (ma.tarjetas.std() / len(g) ** 0.5), 1)})
    arbitros.sort(key=lambda x: -x["media"])

    salida = {
        "fuente": "data/ del repositorio, sin API. Generado por app_apostador/generar_datos.py",
        "modelo_1x2": {"partidos_ajuste": int(len(ajuste)), "calibracion_local": cal},
        "tabla": filas_tabla, "jornada8": partidos, "foco": foco,
        "goles_liga": base, "h2h_rma_vil": h2h_lista,
        "arbitros": {"partidos": int(len(ma)), "media_liga": round(media_liga, 2),
                     "pct_mas45_liga": round(pct_liga), "lista": arbitros},
    }
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1))
    print(json.dumps(salida, ensure_ascii=False)[:200], "...")


def _elo_temporada(ll, eq_id):
    """Elo del equipo antes de cada partido de la temporada, más el actual."""
    m = ll[(ll.temporada == TEMPORADA) & ((ll.local_id == eq_id) | (ll.visitante_id == eq_id))].sort_values("fecha")
    return [f.elo_l if f.local_id == eq_id else f.elo_v for _, f in m.iterrows()]


if __name__ == "__main__":
    main()
