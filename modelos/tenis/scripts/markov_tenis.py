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


# ---------------------------------------------------------------------------------------------
# En directo (30/09/2026): la misma cadena, pero empezando desde un marcador a medias.
# Marcador: sets ganados (sa, sb), juegos del set en curso (ga, gb), puntos del juego en curso
# (xa, xb: 0,1,2,3 = 0,15,30,40; en tie-break, puntos del tie-break) y quién saca ESE juego.
# Si no se sabe quién saca (ESPN no lo da), se promedian los dos casos.
# ---------------------------------------------------------------------------------------------

def juego_desde(p, a, b):
    """Prob. de que el que saca gane el juego desde a-b puntos (0,1,2,3=40; a partir de 3-3, iguales)."""
    @lru_cache(maxsize=None)
    def f(a, b):
        if a >= 4 and a - b >= 2:
            return 1.0
        if b >= 4 and b - a >= 2:
            return 0.0
        if a >= 3 and b >= 3 and a == b:
            return p * p / (p * p + (1 - p) * (1 - p))
        return p * f(a + 1, b) + (1 - p) * f(a, b + 1)
    return f(a, b)


def tiebreak_desde(pa, pb, a, b, a_saco_primero):
    """Prob. de que A gane el tie-break desde a-b; a_saco_primero: A sacó el 1er punto del tie-break."""
    @lru_cache(maxsize=None)
    def f(a, b):
        if a >= 7 and a - b >= 2:
            return 1.0
        if b >= 7 and b - a >= 2:
            return 0.0
        if a >= 6 and b >= 6 and a == b:
            g, pr = pa * (1 - pb), (1 - pa) * pb
            return g / (g + pr)
        n = a + b
        primero = (n % 4 == 0) or (n % 4 == 3)
        saca_a = primero if a_saco_primero else not primero
        p = pa if saca_a else 1 - pb
        return p * f(a + 1, b) + (1 - p) * f(a, b + 1)
    return f(a, b)


def set_desde(pa, pb, ga, gb, a_saca, xa=0, xb=0):
    """Distribución final del set en curso desde ga-gb, con A sacando el juego en curso si a_saca,
    y xa-xb puntos jugados en ese juego (o en el tie-break si ga == gb == 6)."""
    dist = {}
    if (ga >= 6 or gb >= 6) and abs(ga - gb) >= 2 or ga == 7 or gb == 7:
        return {(ga, gb): 1.0}
    if ga == 6 and gb == 6:
        t = tiebreak_desde(pa, pb, xa, xb, a_saca)
        return {(7, 6): t, (6, 7): 1 - t}
    # juego en curso
    if a_saca:
        h = juego_desde(pa, xa, xb)
        sig = {(ga + 1, gb): h, (ga, gb + 1): 1 - h}
    else:
        h = juego_desde(pb, xb, xa)
        sig = {(ga, gb + 1): h, (ga + 1, gb): 1 - h}
    ga_ = 1 - pb
    for (a, b), pr in sig.items():
        # desde aquí, juegos enteros alternando saque; el siguiente saca el otro
        estados = {(a, b, not a_saca): pr}
        while estados:
            nuevos = {}
            for (x, y, sa_), q in estados.items():
                if (x >= 6 or y >= 6) and abs(x - y) >= 2 or x == 7 or y == 7:
                    dist[(x, y)] = dist.get((x, y), 0) + q
                    continue
                if x == 6 and y == 6:
                    t = tiebreak(pa, pb) if sa_ else 1 - tiebreak(pb, pa)
                    dist[(7, 6)] = dist.get((7, 6), 0) + q * t
                    dist[(6, 7)] = dist.get((6, 7), 0) + q * (1 - t)
                    continue
                pg = juego(pa) if sa_ else 1 - juego(pb)
                for k, v in (((x + 1, y, not sa_), pg), ((x, y + 1, not sa_), 1 - pg)):
                    nuevos[k] = nuevos.get(k, 0) + q * v
            estados = nuevos
    del ga_
    return dist


def partido_desde(pa, pb, mejor_de=3, sa=0, sb=0, ga=0, gb=0, a_saca=None, xa=0, xb=0, previos=(0, 0)):
    """Desde el marcador dado, devuelve {'gana_A', 'total', 'dif', 'sets'} con distribuciones del
    partido COMPLETO (previos = juegos de A y B en los sets ya terminados). a_saca=None: promedio."""
    if a_saca is None:
        r1 = partido_desde(pa, pb, mejor_de, sa, sb, ga, gb, True, xa, xb, previos)
        r2 = partido_desde(pa, pb, mejor_de, sa, sb, ga, gb, False, xa, xb, previos)
        return {k: (0.5 * (r1[k] + r2[k]) if k == "gana_A" else
                    {z: 0.5 * (r1[k].get(z, 0) + r2[k].get(z, 0)) for z in set(r1[k]) | set(r2[k])})
                for k in r1}
    nec = mejor_de // 2 + 1
    total, dif, sets_, gana = {}, {}, {}, 0.0
    estados = {}
    for (a, b), pr in set_desde(pa, pb, ga, gb, a_saca, xa, xb).items():
        # quién saca el primer juego del set siguiente: alterna con cada juego del set
        jugados_desde_ahora = (a + b) - (ga + gb)
        sig_saca = a_saca if jugados_desde_ahora % 2 == 0 else not a_saca
        k = (sa + (a > b), sb + (b > a), sig_saca, previos[0] + a, previos[1] + b)
        estados[k] = estados.get(k, 0) + pr
    while estados:
        nuevos = {}
        for (x, y, sa_, ja, jb), pr in estados.items():
            if x == nec or y == nec:
                total[ja + jb] = total.get(ja + jb, 0) + pr
                dif[ja - jb] = dif.get(ja - jb, 0) + pr
                sets_[(x, y)] = sets_.get((x, y), 0) + pr
                gana += pr if x == nec else 0
                continue
            for (a, b), ps in set_dist(pa, pb, sa_).items():
                s2 = sa_ if (a + b) % 2 == 0 else not sa_
                k = (x + (a > b), y + (b > a), s2, ja + a, jb + b)
                nuevos[k] = nuevos.get(k, 0) + pr * ps
        estados = nuevos
    return {"gana_A": gana, "total": total, "dif": dif, "sets": sets_}
