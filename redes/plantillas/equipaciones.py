"""Colores de club para 2yellow: dos equipaciones de dos colores por equipo.
COPIA de app_apostador/diseno_nuevo/generador/equipaciones.py (rama ccr-302c299f-kdpgwl), la paleta corregida de la
app (usuario 06/10: "úsala de ahora en adelante"); aquí lee redes/plantillas/colores/equipaciones.json, ampliado a las
5 grandes y la Champions con el mismo método (workflow colores_redes.yml).

En un partido el local viste la primera. El visitante también, salvo que su
color principal choque con el del local (distancia de color CIE76 < 30, o los
dos casi blancos): entonces viste la segunda, como en los marcadores de TV.

Los colores de la primera son los tradicionales del club; los de la segunda
son aproximados (cambian cada temporada) y conviene revisarlos.

Clubes de un solo color (Madrid blanco, Villarreal amarillo...): una sola
franja. Rayas o dos colores de verdad (Barça, Atlético, Athletic...): dos.
La segunda equipación va siempre con una franja.
"""
BG = "#0A0C11"

KITS = {  # equipo: ((principal, secundario) casa, (principal, secundario) fuera)
    "Barcelona": (("#A50044", "#004D98"), ("#F5C518", "#A50044")),
    "Real Madrid": (("#F4F4F4", "#1E2B5C"), ("#8E7CC3", "#F4F4F4")),
    "Atlético Madrid": (("#CB3524", "#F4F4F4"), ("#27408B", "#CB3524")),
    "Villarreal": (("#FFE11F", "#005187"), ("#0B3A6E", "#FFE11F")),
    "Real Betis": (("#0BB363", "#F4F4F4"), ("#E8C547", "#0BB363")),
    "Sevilla FC": (("#F4F4F4", "#D8262F"), ("#D8262F", "#F4F4F4")),
    "Real Sociedad": (("#0067B1", "#F4F4F4"), ("#F07A2A", "#0067B1")),
    "Alavés": (("#1F4E9E", "#F4F4F4"), ("#E03A3E", "#F4F4F4")),
    "Deportivo La Coruña": (("#2B67C2", "#F4F4F4"), ("#E9B44C", "#1B3A6B")),
    "Athletic Club": (("#EE2523", "#F4F4F4"), ("#10924A", "#111111")),
    "Getafe": (("#005CA9", "#F4F4F4"), ("#D7263D", "#F4F4F4")),
    "Rayo Vallecano": (("#F4F4F4", "#D0202E"), ("#D0202E", "#F4F4F4")),
    "Osasuna": (("#D91A21", "#0A346F"), ("#F4F4F4", "#D91A21")),
    "Celta de Vigo": (("#8AC3EE", "#F4F4F4"), ("#E53945", "#8AC3EE")),
    "Espanyol": (("#1E6FC8", "#F4F4F4"), ("#E8C547", "#1E6FC8")),
    "Racing Santander": (("#1E9E57", "#F4F4F4"), ("#F4F4F4", "#1E9E57")),
    "Levante": (("#A6192E", "#1C3F94"), ("#F4F4F4", "#A6192E")),
    "Elche": (("#F4F4F4", "#1E8C4E"), ("#1E8C4E", "#F4F4F4")),
    "Valencia": (("#F4F4F4", "#1B1B1B"), ("#F28C28", "#1B1B1B")),
    "Malaga": (("#5AA0D8", "#F4F4F4"), ("#F4F4F4", "#5AA0D8")),
    "Oviedo": (("#0B4A9C", "#F4F4F4"), ("#F4F4F4", "#0B4A9C")),
    "Mallorca": (("#C8102E", "#111111"), ("#F4F4F4", "#C8102E")),
    "Girona": (("#D7182A", "#F4F4F4"), ("#1F2F5C", "#D7182A")),
}
UN_COLOR = {"Real Madrid", "Villarreal", "Getafe", "Celta de Vigo", "Valencia", "Sevilla FC", "Osasuna",
            "Mallorca", "Oviedo"}


# Equipaciones reales 2026/27 (1ª, 2ª y 3ª) medidas en Wikipedia: app_apostador/colores/
# (petición del usuario, 01/10/2026). Mandan sobre la tabla de arriba.
import json as _json  # noqa: E402
from pathlib import Path as _Path  # noqa: E402
_REALES = _Path(__file__).resolve().parent / "colores" / "equipaciones.json"  # copia ampliada de app_apostador/colores
if _REALES.exists():
    for _e, _ks in _json.loads(_REALES.read_text()).items():
        KITS[_e] = tuple(tuple(k) for k in _ks)
REALES = set(_json.loads(_REALES.read_text())) if _REALES.exists() else set()

def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _lum(h):
    def c(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (c(x) for x in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _lab(h):
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(x) for x in _rgb(h))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def distancia(a, b):
    return sum((p - q) ** 2 for p, q in zip(_lab(a), _lab(b))) ** 0.5


def choca(a, b):
    return distancia(a, b) < 30


def _mezcla(h, t):
    r, g, b = _rgb(h)
    return "#%02X%02X%02X" % tuple(round((v + (1 - v) * t) * 255) for v in (r, g, b))


def legible(h, fondo=BG, minimo=3.0):
    """Color para barras sobre fondo oscuro: se aclara hasta contraste 3:1."""
    t = 0.0
    c = h
    while contraste(c, fondo) < minimo and t < 1:
        t += 0.08
        c = _mezcla(h, t)
    return c


def texto_sobre(h):
    return "#0A0C11" if contraste(h, "#0A0C11") >= contraste(h, "#FFFFFF") else "#FFFFFF"


def kit(equipo, cual=0):
    ks = KITS.get(equipo, (("#7C8496", "#F4F4F4"), ("#F4F4F4", "#7C8496")))
    k = ks[min(cual, len(ks) - 1)]
    una = k[2] if len(k) > 2 else (equipo in UN_COLOR if cual == 0 else True)   # 3er campo: camiseta de un color
    return {"c1": k[0], "c2": k[1], "barra": legible(k[0]), "texto": texto_sobre(k[0]), "segunda": cual >= 1, "cual": cual, "una": una}


def n_kits(equipo):
    return len(KITS.get(equipo, ((), ())))


def se_parecen(a, b, estricto=True):
    """¿Se confunden dos equipaciones? En un partido (estricto) basta con que el
    color principal se parezca. En una lista de franjas, una de dos colores
    (Croacia, a cuadros rojos y blancos) se distingue de una lisa del mismo
    color (España, roja): solo se confunden si las dos son lisas o si los dos
    colores se parecen."""
    if distancia(a["barra"], b["barra"]) >= 30:
        return False
    if estricto or (a["una"] and b["una"]):
        return True
    if a["una"] != b["una"]:
        return False
    return distancia(a["c2"], b["c2"]) < 30


def _sin_choque(equipo, ocupados, estricto=True):
    """Primera equipación (1ª, 2ª, 3ª) que no se confunde con ninguna ya puesta;
    si todas se confunden, el color secundario de alguna como principal; si aun
    así, la que más se separa."""
    cands = [kit(equipo, i) for i in range(n_kits(equipo))]
    cands += [{**b, "c1": b["c2"], "c2": b["c1"], "barra": legible(b["c2"]), "texto": texto_sobre(b["c2"]), "una": True} for b in cands]
    for k in cands:
        if not any(se_parecen(k, o, estricto) for o in ocupados):
            return k
    return max(cands, key=lambda k: min((distancia(k["barra"], o["barra"]) for o in ocupados), default=999))


def colores_partido(local, visitante):
    """(kit local, kit visitante) sin choques: el local con la 1ª; el visitante
    con la 1ª, 2ª o 3ª, la primera que no choque (como en la TV)."""
    l = kit(local, 0)
    return l, _sin_choque(visitante, [l])


def colores_grupo(equipos, fijos=None):
    """{equipo: kit} para varios equipos a la vez (un grupo, una tabla corta):
    en el orden dado, cada uno la primera equipación que no choque con las ya
    puestas. Así España (roja) y Chequia no salen las dos en rojo."""
    out = dict(fijos or {})   # p. ej. los dos del partido, ya con sus colores
    ocupados = list(out.values())
    for e in equipos:
        if e in out:
            continue
        k = _sin_choque(e, ocupados, estricto=False)
        out[e] = k
        ocupados.append(k)
    return out


def colores_lista(equipos):
    """Para listas largas (clasificación de 20, ranking FIFA): cada fila sin
    chocar con la de arriba y la de abajo."""
    out, prev = {}, []
    for e in equipos:
        k = _sin_choque(e, prev[-1:], estricto=False)
        out[e] = k
        prev.append(k)
    return out


if __name__ == "__main__":
    # Comprobación: cada pareja de LaLiga sin choque tras la regla
    eqs = list(KITS)
    malos, cambian = [], 0
    for a in eqs:
        for b in eqs:
            if a == b:
                continue
            l, v = colores_partido(a, b)
            cambian += v["segunda"]
            if choca(l["barra"], v["barra"]):
                malos.append((a, b))
    print("parejas:", len(eqs) * (len(eqs) - 1), "visitante con segunda:", cambian, "choques que quedan:", malos)
    for a, b in (("Real Sociedad", "Deportivo La Coruña"), ("Real Madrid", "Valencia"), ("Sevilla FC", "Real Madrid"),
                 ("Atlético Madrid", "Real Madrid"), ("Real Madrid", "Villarreal"), ("Athletic Club", "Atlético Madrid")):
        l, v = colores_partido(a, b)
        print(f"{a} {l['barra']} vs {b} {v['barra']} (segunda: {v['segunda']})")
