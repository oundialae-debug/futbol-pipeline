"""
Modelo de puntos jerárquico con incertidumbre (30/09/2026).

Cada jugador tiene fuerza al saque (s) y al resto (r), más una desviación
por superficie (s_sup, r_sup), en escala logit, cada una con su varianza.
Prob. de que A gane un punto sacando contra B, en la superficie σ:
    θ = μ_σ + s_A + s_A,σ − r_B − r_B,σ ,   V = suma de las 4 varianzas
    p = logística(θ / sqrt(1 + π·V/8))        (la incertidumbre acerca p a la media)
Antes de cada partido las varianzas CRECEN con el tiempo sin jugar (general)
y sin pisar esa superficie (superficie), con tope en la varianza inicial:
es el "óxido" como parte del rating, no como indicador suelto.
Después, se actualiza con los puntos al saque de cada jugador (binomial,
aproximación de Laplace, como un filtro de Kalman): cada componente se mueve
en proporción a su varianza. Jugador nuevo = media, varianza inicial (encoge
hacia la media). Partidos sin estadísticas: no mueven la fuerza (sí pasa el
tiempo). μ_σ: media móvil del logit de puntos al saque por superficie.

Mismo orden sin fuga que elo_tenis (inicio del torneo y ronda).
Parámetros (v0, crecimiento diario, v0 de superficie) elegidos con la
verosimilitud de los PUNTOS en 2015-2019, sin mirar ninguna cuota.
"""
import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import elo_tenis as E  # noqa: E402

# Elegidos el 30/09/2026 con la verosimilitud de puntos 2015-2019 (rejilla ampliada al salir en
# el borde; la curva es plana en v0 y v0s, y tau queda en el INTERIOR: el óxido lo piden los datos).
PARAMS = {"atp": (0.01, 5e-6, 0.001), "wta": (0.01, 5e-6, 0.001)}
REJILLA = [(v0, tau, v0s) for v0 in (0.01, 0.02, 0.03) for tau in (0.0, 5e-6, 2e-5) for v0s in (0.001, 0.0025, 0.005)]


def logistica(x):
    return 1 / (1 + math.exp(-x))


def pasar(d, v0, tau, v0s, alfa_mu=0.002):
    """Recorre el historial. Devuelve arrays con, para cada partido: θ y V de cada saque
    (antes del partido), puntos jugados y ganados al saque por ganador y perdedor."""
    n = len(d)
    num = lambda c: pd.to_numeric(d[c], errors="coerce").values  # noqa: E731
    sw, sl = num("w_svpt"), num("l_svpt")
    ww = num("w_1stWon") + num("w_2ndWon")
    wl = num("l_1stWon") + num("l_2ndWon")
    ini = d["inicio"].values.astype("datetime64[D]").astype(np.int64)
    sup = d["sup"].values
    W, L = d["w"].values, d["l"].values
    act = d["actualiza"].values
    est = {}                       # jugador -> [s, vs, r, vr, último día]
    est_s = {}                     # (jugador, sup) -> [s, vs, r, vr, último día]
    mu = {"Hard": 0.62, "Clay": 0.52, "Grass": 0.72}
    th_w, v_w, th_l, v_l = (np.full(n, np.nan) for _ in range(4))

    def leer(j, dia, s):
        e = est.get(j)
        if e is None:
            e = est[j] = [0.0, v0, 0.0, v0, dia]
        es = est_s.get((j, s))
        if es is None:
            es = est_s[(j, s)] = [0.0, v0s, 0.0, v0s, dia]
        dt, dts = max(0, dia - e[4]), max(0, dia - es[4])
        e[1], e[3] = min(v0, e[1] + tau * dt), min(v0, e[3] + tau * dt)
        es[1], es[3] = min(v0s, es[1] + tau * dts), min(v0s, es[3] + tau * dts)
        e[4], es[4] = dia, dia
        return e, es

    def actualizar(servidor, servidor_s, restador, restador_s, m, puntos, ganados):
        if not (puntos > 0) or ganados != ganados:
            return
        th = m + servidor[0] + servidor_s[0] - restador[2] - restador_s[2]
        V = servidor[1] + servidor_s[1] + restador[3] + restador_s[3]
        p = logistica(th)
        info = puntos * p * (1 - p)
        dth = (ganados - puntos * p) / (info + 1 / V)
        for obj, i_m, i_v, signo in ((servidor, 0, 1, 1), (servidor_s, 0, 1, 1),
                                     (restador, 2, 3, -1), (restador_s, 2, 3, -1)):
            v = obj[i_v]
            obj[i_m] += signo * v / V * dth
            obj[i_v] = max(1e-5, v - v * v * info / (1 + info * V))

    for i in range(n):
        s = sup[i]
        m = mu.get(s, 0.6)
        ew, esw = leer(W[i], ini[i], s)
        el, esl = leer(L[i], ini[i], s)
        th_w[i] = m + ew[0] + esw[0] - el[2] - esl[2]
        v_w[i] = ew[1] + esw[1] + el[3] + esl[3]
        th_l[i] = m + el[0] + esl[0] - ew[2] - esw[2]
        v_l[i] = el[1] + esl[1] + ew[3] + esw[3]
        if not act[i]:
            continue
        actualizar(ew, esw, el, esl, m, sw[i], ww[i])
        actualizar(el, esl, ew, esw, m, sl[i], wl[i])
        for puntos, ganados in ((sw[i], ww[i]), (sl[i], wl[i])):
            if puntos > 0 and ganados == ganados and 0 < ganados < puntos:
                mu[s] = (1 - alfa_mu) * m + alfa_mu * math.log(ganados / (puntos - ganados))
                m = mu[s]
    return {"th_w": th_w, "v_w": v_w, "th_l": th_l, "v_l": v_l, "sw": sw, "ww": ww, "sl": sl, "wl": wl}


def prob_punto(th, v):
    return 1 / (1 + np.exp(-th / np.sqrt(1 + np.pi * v / 8)))


def verosimilitud(r, mascara):
    """Log-verosimilitud media por punto al saque (binomial), en las filas de la máscara."""
    tot, pts = 0.0, 0.0
    for th, v, n, k in ((r["th_w"], r["v_w"], r["sw"], r["ww"]), (r["th_l"], r["v_l"], r["sl"], r["wl"])):
        p = prob_punto(th, v)
        ok = mascara & (n > 0) & ~np.isnan(k) & ~np.isnan(p)
        tot += np.sum(k[ok] * np.log(p[ok]) + (n[ok] - k[ok]) * np.log(1 - p[ok]))
        pts += np.sum(n[ok])
    return tot / pts


def elegir(circuito):
    d = E.historial(circuito)
    m = ((d["inicio"] >= "2015-01-01") & (d["inicio"] < "2020-01-01")).values
    res = []
    for v0, tau, v0s in REJILLA:
        res.append((verosimilitud(pasar(d, v0, tau, v0s), m), v0, tau, v0s))
        print(f"  {circuito} v0={v0} tau={tau} v0s={v0s}: {res[-1][0]:.5f}", flush=True)
    return max(res), d


def calcular(circuito, params=None):
    """Historial con p_w (punto al saque del ganador) y p_l (del perdedor), antes del partido."""
    if params is None:
        (_, v0, tau, v0s), d = elegir(circuito)
    else:
        v0, tau, v0s = params
        d = E.historial(circuito)
    r = pasar(d, v0, tau, v0s)
    d["p_w"] = prob_punto(r["th_w"], r["v_w"])
    d["p_l"] = prob_punto(r["th_l"], r["v_l"])
    d["v_w"], d["v_l"] = r["v_w"], r["v_l"]
    return d, (v0, tau, v0s)


if __name__ == "__main__":
    for c in ("atp", "wta"):
        mejor, _ = elegir(c)
        print(c, "ELEGIDO", mejor)
