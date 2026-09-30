"""
Variables de cada jugador ANTES de cada partido del historial (sin fuga):
se recorre el historial en el mismo orden que el Elo (inicio del torneo y
ronda) y cada partido lee lo acumulado hasta el anterior.

Grupos:
- saque: medias de los últimos N partidos con estadísticas (puntos ganados
  al saque y al resto, aces, dobles faltas, 1º dentro, breaks salvados).
- fatiga: partidos, sets y minutos ya jugados EN ESTE torneo, minutos del
  partido anterior, partidos en los 30 días anteriores al inicio del torneo,
  días entre el inicio del torneo anterior y este.
- perfil: ranking, puntos, edad, altura, mano (del propio partido: son datos
  de antes de jugarlo).
- h2h: victorias previas de cada uno contra el otro.

Los datos de estadísticas son texto a veces (TennisMyLife 2026: '4y',
'-35.9%'): se pasan a número y lo que no lo es queda vacío. Edad y altura
fuera de rango (14-50 años, 150-215 cm) quedan vacías.
"""
from collections import defaultdict, deque

import numpy as np
import pandas as pd

N_SAQUE = 20
MIN_SAQUE = 5
STATS = ["ace", "df", "svpt", "1stIn", "1stWon", "2ndWon", "bpSaved", "bpFaced"]


def num(d, c):
    return pd.to_numeric(d[c], errors="coerce") if c in d else pd.Series(np.nan, index=d.index)


def sets_jugados(score):
    return len([x for x in str(score).split() if "-" in x and x[0].isdigit()])


def calcular(d):
    """d: historial ordenado (elo_tenis.historial). Devuelve DataFrame de variables por fila,
    con sufijo _w (ganador) y _l (perdedor)."""
    s = {f"{p}_{c}": num(d, f"{p}_{c}").values for p in "wl" for c in STATS}
    minutos = num(d, "minutes").values
    sets = d["score"].map(sets_jugados).values
    ini = d["inicio"].values.astype("datetime64[D]").astype(np.int64)
    tid = d["tourney_id"].astype(str).values
    hist_saque = defaultdict(lambda: deque(maxlen=N_SAQUE))   # jugador -> (spw, rpw, ace, df, in1, bps)
    en_torneo = {}                                            # jugador -> (tid, partidos, sets, minutos)
    ult_min = {}
    fechas = defaultdict(lambda: deque(maxlen=60))            # inicios de torneo por partido
    ult_torneo = {}                                           # jugador -> (tid, inicio)
    h2h = defaultdict(int)
    nombres = ["spw", "rpw", "ace", "df", "in1", "bps", "n_saque", "t_partidos", "t_sets", "t_min",
               "min_ant", "p30", "descanso", "h2h"]
    out = {f"{n}_{lado}": np.full(len(d), np.nan) for n in nombres for lado in "wl"}
    W, L = d["w"].values, d["l"].values
    for i in range(len(d)):
        for lado, j, o in (("w", W[i], L[i]), ("l", L[i], W[i])):
            h = hist_saque[j]
            out[f"n_saque_{lado}"][i] = len(h)
            if len(h) >= MIN_SAQUE:
                a = np.nanmean(np.array(h), axis=0)
                for k, n in enumerate(["spw", "rpw", "ace", "df", "in1", "bps"]):
                    out[f"{n}_{lado}"][i] = a[k]
            t = en_torneo.get(j)
            if t and t[0] == tid[i]:
                out[f"t_partidos_{lado}"][i], out[f"t_sets_{lado}"][i], out[f"t_min_{lado}"][i] = t[1], t[2], t[3]
            else:
                out[f"t_partidos_{lado}"][i] = out[f"t_sets_{lado}"][i] = out[f"t_min_{lado}"][i] = 0
            out[f"min_ant_{lado}"][i] = ult_min.get(j, np.nan)
            f = fechas[j]
            out[f"p30_{lado}"][i] = sum(1 for x in f if 0 < ini[i] - x <= 30)
            u = ult_torneo.get(j)
            if u and u[0] != tid[i]:
                out[f"descanso_{lado}"][i] = ini[i] - u[1]
            elif u and u[0] == tid[i]:
                out[f"descanso_{lado}"][i] = u[2] if len(u) > 2 else np.nan
            out[f"h2h_{lado}"][i] = h2h[(j, o)]
        # actualizar DESPUÉS de leer
        if not d["actualiza"].values[i]:
            continue
        w, l = W[i], L[i]
        sw, sl = s["w_svpt"][i], s["l_svpt"][i]
        if sw > 0 and sl > 0:
            spw_w = (s["w_1stWon"][i] + s["w_2ndWon"][i]) / sw
            spw_l = (s["l_1stWon"][i] + s["l_2ndWon"][i]) / sl
            for j, sp, so, p in ((w, spw_w, spw_l, "w"), (l, spw_l, spw_w, "l")):
                bpf = s[f"{p}_bpFaced"][i]
                hist_saque[j].append((sp, 1 - so, s[f"{p}_ace"][i] / s[f"{p}_svpt"][i],
                                      s[f"{p}_df"][i] / s[f"{p}_svpt"][i], s[f"{p}_1stIn"][i] / s[f"{p}_svpt"][i],
                                      s[f"{p}_bpSaved"][i] / bpf if bpf > 0 else np.nan))
        for j in (w, l):
            t = en_torneo.get(j)
            base = (t[1], t[2], t[3]) if t and t[0] == tid[i] else (0, 0, 0)
            m = minutos[i] if minutos[i] == minutos[i] else 0
            en_torneo[j] = (tid[i], base[0] + 1, base[1] + sets[i], base[2] + m)
            ult_min[j] = minutos[i]
            fechas[j].append(ini[i])
            u = ult_torneo.get(j)
            if u is None or u[0] != tid[i]:
                ult_torneo[j] = (tid[i], ini[i], ini[i] - u[1] if u else np.nan)
        h2h[(w, l)] += 1
    r = pd.DataFrame(out, index=d.index)
    for lado, p in (("w", "winner"), ("l", "loser")):
        r[f"rank_{lado}"] = np.log(num(d, f"{p}_rank").values)
        r[f"pts_{lado}"] = np.log1p(num(d, f"{p}_rank_points").values)
        edad, alt = num(d, f"{p}_age"), num(d, f"{p}_ht")
        # TennisMyLife WTA 2026 trae columnas desplazadas (edad 3387, altura 20011008 = fecha
        # de nacimiento) y hay alturas 0 sueltas: fuera de rango = desconocido.
        r[f"edad_{lado}"] = edad.where(edad.between(14, 50)).values
        r[f"alt_{lado}"] = alt.where(alt.between(150, 215)).values
        r[f"zurdo_{lado}"] = (d[f"{p}_hand"] == "L").astype(float).values
    return r
