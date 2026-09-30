"""
De puntos a partido, exacto (cadena de Markov con puntos independientes).

pa = prob. de que A gane un punto SACANDO A; pb = prob. de que B gane un punto
sacando B. Devuelve la distribución conjunta del partido: prob. de que gane
A, y distribuciones de juegos totales y de diferencia de juegos (A - B).
Sets normales con tie-break a 6-6 (también el 5º set: regla actual de los
Grand Slams, tie-break a 10 en el set decisivo; se aproxima como un tie-break
normal). Quién saca primero: se promedian los dos casos.
"""
from functools import lru_cache


def juego(p):
    """Prob. de ganar un juego al saque con prob. p de ganar cada punto."""
    q = 1 - p
    base = p ** 4 * (1 + 4 * q + 10 * q * q)
    deuce = 20 * p ** 3 * q ** 3 * p * p / (1 - 2 * p * q)
    return base + deuce


@lru_cache(maxsize=None)
def tiebreak(pa, pb, hasta=7):
    """Prob. de que A gane un tie-break en el que A saca el primer punto."""
    @lru_cache(maxsize=None)
    def f(a, b):
        if a >= hasta and a - b >= 2:
            return 1.0
        if b >= hasta and b - a >= 2:
            return 0.0
        if a >= hasta - 1 and b >= hasta - 1 and a == b:
            # empate a partir de 6-6: dos puntos seguidos (uno con cada saque, en promedio)
            ganar2 = pa * (1 - pb)
            perder2 = (1 - pa) * pb
            return ganar2 / (ganar2 + perder2)
        n = a + b
        saca_a = (n % 4 == 0) or (n % 4 == 3)        # A, B, B, A, A, B, B...
        p = pa if saca_a else 1 - pb
        return p * f(a + 1, b) + (1 - p) * f(a, b + 1)
    return f(0, 0)


@lru_cache(maxsize=None)
def set_dist(pa, pb, a_saca):
    """Distribución del set: {(juegos_A, juegos_B): prob}, A saca el primer juego si a_saca."""
    ga, gb = juego(pa), juego(pb)                    # A gana su saque / B gana su saque
    tb = tiebreak(pa, pb) if a_saca else 1 - tiebreak(pb, pa)
    dist = {}
    estados = {(0, 0): 1.0}
    while estados:
        nuevos = {}
        for (a, b), pr in estados.items():
            if (a >= 6 or b >= 6) and abs(a - b) >= 2 or a == 7 or b == 7:
                dist[(a, b)] = dist.get((a, b), 0) + pr
                continue
            if a == 6 and b == 6:
                dist[(7, 6)] = dist.get((7, 6), 0) + pr * tb
                dist[(6, 7)] = dist.get((6, 7), 0) + pr * (1 - tb)
                continue
            saca_a = ((a + b) % 2 == 0) == a_saca
            p = ga if saca_a else 1 - gb
            nuevos[(a + 1, b)] = nuevos.get((a + 1, b), 0) + pr * p
            nuevos[(a, b + 1)] = nuevos.get((a, b + 1), 0) + pr * (1 - p)
        estados = nuevos
    return dist


@lru_cache(maxsize=None)
def partido(pa, pb, mejor_de=3):
    """(prob. gana A, {juegos_totales: prob}, {dif_juegos A-B: prob})."""
    necesarios = mejor_de // 2 + 1
    total, dif, gana = {}, {}, 0.0
    for primero in (True, False):
        estados = {(0, 0, primero, 0, 0): 0.5}       # sets A, sets B, A saca 1º, juegos A, juegos B
        while estados:
            nuevos = {}
            for (sa, sb, a_saca, ja, jb), pr in estados.items():
                if sa == necesarios or sb == necesarios:
                    t, d = ja + jb, ja - jb
                    total[t] = total.get(t, 0) + pr
                    dif[d] = dif.get(d, 0) + pr
                    if sa == necesarios:
                        gana += pr
                    continue
                for (a, b), ps in set_dist(pa, pb, a_saca).items():
                    sig_saca = a_saca if (a + b) % 2 == 0 else not a_saca
                    k = (sa + (a > b), sb + (b > a), sig_saca, ja + a, jb + b)
                    nuevos[k] = nuevos.get(k, 0) + pr * ps
            estados = nuevos
    return gana, total, dif


def redondear(p, paso=0.0025):
    return round(min(max(p, 0.2), 0.9) / paso) * paso
