"""2yellow · Nations League (ejemplo: Inglaterra). Mismas piezas que el lienzo de LaLiga.
Lee diseno_nl/datos_nl.json (nl_datos.py). Escribe diseno_nl/project/*.dc.html. Sin API."""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "diseno_nuevo" / "generador"))
import common  # noqa: E402
common.OUT = str(AQUI.parent / "project")
import equipaciones  # noqa: E402
import real_ui  # noqa: E402
from real_ui import (BG, CARD, BORDE, SUB, MUT, TXT, SOFT, AZUL, LIMA, NARANJA, ROJO, AMARILLO, DISP,  # noqa: E402
                     tarjeta, chip, fila_stat, tres, franjas, escudo, glow, volver, pestañas, sparkline,
                     confianza, selector, js_selectores, nota_pie)
from logo import icono, palabra  # noqa: E402

N = json.loads((AQUI.parent / "datos_nl.json").read_text())

# ---------------------------------------------------------------- colores de cada selección (primera, segunda)
BLANCO = "#F4F4F4"
SEL = {  # nombre API: (corto, código FIFA, casa (c1, c2), fuera (c1, c2), un color)
    "England": ("England", "ENG", (BLANCO, "#1E2B5C"), ("#CE1124", BLANCO), True),
    "Croatia": ("Croatia", "CRO", ("#E30613", BLANCO), ("#1B2A5C", "#E30613"), False),
    "Czech Republic": ("Czechia", "CZE", ("#D7141A", BLANCO), (BLANCO, "#11457E"), True),
    "Spain": ("Spain", "ESP", ("#C60B1E", "#FFC400"), (BLANCO, "#C60B1E"), True),
    "France": ("France", "FRA", ("#21304D", BLANCO), (BLANCO, "#21304D"), True),
    "Italy": ("Italy", "ITA", ("#1E64C8", BLANCO), (BLANCO, "#1E64C8"), True),
    "Belgium": ("Belgium", "BEL", ("#E30613", "#111111"), (BLANCO, "#E30613"), True),
    "Turkey": ("Türkiye", "TUR", ("#E30A17", BLANCO), (BLANCO, "#E30A17"), True),
    "Germany": ("Germany", "GER", (BLANCO, "#111111"), ("#1C1C1C", BLANCO), True),
    "Netherlands": ("Netherlands", "NED", ("#F36C21", "#1F2D55"), ("#1F2D55", "#F36C21"), True),
    "Serbia": ("Serbia", "SRB", ("#C6363C", "#0C4076"), (BLANCO, "#C6363C"), True),
    "Greece": ("Greece", "GRE", ("#0D5EAF", BLANCO), (BLANCO, "#0D5EAF"), True),
    "Norway": ("Norway", "NOR", ("#BA0C2F", "#00205B"), (BLANCO, "#BA0C2F"), True),
    "Denmark": ("Denmark", "DEN", ("#C8102E", BLANCO), (BLANCO, "#C8102E"), True),
    "Portugal": ("Portugal", "POR", ("#C8102E", "#006600"), (BLANCO, "#C8102E"), False),
    "Wales": ("Wales", "WAL", ("#D30731", BLANCO), (BLANCO, "#D30731"), True),
    "Austria": ("Austria", "AUT", ("#ED2939", BLANCO), (BLANCO, "#ED2939"), True),
    "Republic of Ireland": ("Ireland", "IRL", ("#169B62", BLANCO), (BLANCO, "#169B62"), True),
    "Israel": ("Israel", "ISR", (BLANCO, "#0038B8"), ("#0038B8", BLANCO), True),
    "Kosovo National Team": ("Kosovo", "KVX", ("#244AA5", "#D0A650"), (BLANCO, "#244AA5"), True),
    "Azerbaijan": ("Azerbaijan", "AZE", ("#00B5E2", BLANCO), ("#E00034", BLANCO), True),
    "Liechtenstein": ("Liechtenstein", "LIE", ("#002B7F", "#CE1126"), ("#CE1126", "#002B7F"), True),
    "Malta": ("Malta", "MLT", ("#CF142B", BLANCO), (BLANCO, "#CF142B"), True),
    "Gibraltar": ("Gibraltar", "GIB", (BLANCO, "#DA000C"), ("#DA000C", BLANCO), True),
    "Argentina": ("Argentina", "ARG", ("#75AADB", BLANCO), ("#1B2A5C", "#75AADB"), False),
    "Panama": ("Panama", "PAN", ("#DA121A", "#072357"), (BLANCO, "#DA121A"), True),
    "Ghana": ("Ghana", "GHA", (BLANCO, "#006B3F"), ("#006B3F", "#FCD116"), True),
}
for nombre, (corto, cod, casa, fuera, una) in SEL.items():
    equipaciones.KITS[nombre] = (casa, fuera)
    if una:
        equipaciones.UN_COLOR.add(nombre)
    real_ui.EQ[nombre] = (corto, cod, casa[0], equipaciones.texto_sobre(casa[0]))
    real_ui.CORTO_A_LARGO[corto] = nombre
for f in N["fifa"]:  # el resto: código FIFA y color neutro
    real_ui.EQ.setdefault(f["equipo"], (f["equipo"], f["codigo"], "#3A4256", TXT))
kit, kits, eq = real_ui.kequipo, real_ui.kits, real_ui.eq


def raiz(h, cuerpo, gap=14):
    return (f'<div style="position: relative; width: 390px; height: {h}px; box-sizing: border-box; background: {BG}; '
            f'overflow: hidden; display: flex; flex-direction: column; gap: {gap}px; padding-bottom: 100px">{cuerpo}@@NAV@@</div>')


JS0 = "class Component extends DCLogic {\n  renderVals() { return {}; }\n}"
MESES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fecha(iso):
    return f"{int(iso[8:10])} {MESES[int(iso[5:7]) - 1]}"


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def marca(ok):
    return (f'<span style="width: 22px; height: 22px; border-radius: 50%; background: {"#1F3A16" if ok else "#3A1719"}; color: {LIMA if ok else "#FF8A80"}; '
            f'font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center">{"✓" if ok else "✗"}</span>')


CAB_NL = (f'<div style="display: flex; align-items: center; gap: 10px">'
          f'<span style="width: 30px; height: 30px; border-radius: 10px; background: linear-gradient(135deg, #0B1F5C, #1D4ED8); {DISP}; font-size: 11px; '
          f'display: flex; align-items: center; justify-content: center">NL</span>'
          f'<div style="display: flex; flex-direction: column"><span style="font-size: 15px; font-weight: 700">Nations League</span>'
          f'<span style="font-size: 12px; color: {MUT}">League A</span></div></div>')

# ======================================================================= MATCHES
RES = N["resultados"]


def carta(r_):
    kl, kv = kits(r_["local"], r_["visitante"])
    m = r_["merecido"]
    llamada = ""
    if "acierto" in r_:
        pick = ["home win", "draw", "away win"][max(range(3), key=lambda i: r_["nuestro"][i])]
        llamada = (f'<div style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: {SOFT}">'
                   f'<span>2yellow said {pick} · {int(max(r_["nuestro"]))}%</span>{marca(r_["acierto"])}</div>')
    href = "Report.dc.html" if r_["visitante"] == "England" and r_["fecha"] == "2026-09-29" else "#"
    barra = (f'<div style="display: flex; flex-direction: column; gap: 6px"><div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}">'
             f'<span>xG <b style="color: {kl["barra"]}">{r_["xg"][0]:.2f}</b></span><span>chances say</span><span><b style="color: {kv["barra"]}">{r_["xg"][1]:.2f}</b> xG</span></div>'
             f'<div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; gap: 2px"><span style="width: {m[0]}%; background: {kl["barra"]}"></span>'
             f'<span style="width: {m[1]}%; background: #3A4256"></span><span style="width: {m[2]}%; background: {kv["barra"]}"></span></div></div>') if m else ""
    return f'''<a href="{href}" style="position: relative; flex-shrink: 0; width: 304px; box-sizing: border-box; border-radius: 26px; background: {CARD}; border: 1px solid #262C3B; overflow: hidden; display: block">
{glow(kl["barra"], kv["barra"], 170)}
<div style="position: relative; display: flex; flex-direction: column; gap: 12px; padding: 14px 16px">
<div style="display: flex; justify-content: space-between; align-items: center"><span style="font-size: 12px; font-weight: 600; color: {SOFT}">{r_["ronda"].replace("League A - ", "League A · MD")} · FT</span><span style="font-size: 12px; color: {MUT}">{fecha(r_["fecha"])}</span></div>
<div style="display: flex; align-items: center; justify-content: space-between">
<div style="width: 90px; display: flex; flex-direction: column; align-items: center; gap: 6px">{escudo(r_["local"], 44, kl)}<span style="display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600">{franjas(kl, 14)}{eq(r_["local"])[0]}</span></div>
<span style="{DISP}; font-size: 46px; line-height: 1">{r_["gl"]} – {r_["gv"]}</span>
<div style="width: 90px; display: flex; flex-direction: column; align-items: center; gap: 6px">{escudo(r_["visitante"], 44, kv)}<span style="display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600">{eq(r_["visitante"])[0]}{franjas(kv, 14)}</span></div>
</div>{barra}{llamada}</div></a>'''


dest = [x for x in RES if x["fecha"] == "2026-09-29"] + [x for x in RES if x["fecha"] == "2026-09-28"]


def fila_prox(p):
    loc, vis = p["local"], p["visitante"]
    kl, kv = kits(loc, vis)
    hh = int(p["fecha"][11:13]) + 2
    hora = f"{hh:02d}:{p['fecha'][14:16]}"
    if p["p"]:
        mx = max(p["p"])

        def caja(v, lab, k):
            on = v == mx
            bg = (k["barra"] if k else "#3A4256") if on else SUB
            fg = (k["texto"] if k else TXT) if on else TXT
            return (f'<div style="padding: 5px 0; border-radius: 9px; background: {bg}; color: {fg}"><span style="display: block; {DISP}; font-size: 14px">{int(v)}%</span>'
                    f'<span style="font-size: 9px; opacity: 0.75">{lab}</span></div>')
        der = (f'<div style="display: grid; grid-template-columns: repeat(3, 44px); gap: 4px; text-align: center">'
               f'{caja(p["p"][0], "1", kl)}{caja(p["p"][1], "X", None)}{caja(p["p"][2], "2", kv)}</div>')
    else:
        der = ""
    ing = "England" in (loc, vis)
    tag = (f'<div style="margin-left: 58px; display: flex; gap: 6px">{chip("Your team", "#1E2A66", "#A9B8FF")}'
           f'{chip("2nd v 3rd in the group", "#26301A", LIMA)}</div>') if ing else ""
    return f'''<a href="{"Partido.dc.html" if ing else "#"}" style="display: flex; flex-direction: column; gap: 10px; padding: 13px 14px; border-top: 1px solid #1E2330; background: {"#141A33" if ing else "transparent"}">
<div style="display: flex; align-items: center; gap: 12px"><span style="width: 46px; {DISP}; font-size: 15px">{hora}</span>
<div style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 7px">
<div style="display: flex; align-items: center; gap: 8px">{franjas(kl)}<span style="font-size: 15px; font-weight: 600">{eq(loc)[0]}</span></div>
<div style="display: flex; align-items: center; gap: 8px">{franjas(kv)}<span style="font-size: 15px; font-weight: 600">{eq(vis)[0]}</span></div></div>{der}</div>{tag}</a>'''


bloques = ""
for dia in sorted({p["fecha"][:10] for p in N["proximos"]}):
    ps = [p for p in N["proximos"] if p["fecha"][:10] == dia]
    nombre = {"2026-10-01": "THURSDAY 1 OCT", "2026-10-02": "FRIDAY 2 OCT", "2026-10-03": "SATURDAY 3 OCT"}[dia]
    bloques += (f'<div style="display: flex; align-items: center; padding: 10px 14px 4px 14px; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; color: {MUT}">'
                f'<span style="flex-grow: 1">{nombre}</span><span style="width: 140px; text-align: center; letter-spacing: 0.4px">WIN CHANCE · 1 X 2</span></div>'
                + "".join(fila_prox(p) for p in ps))
ACI = N["acierto"]
res1 = ACI["mercados"][0]
cuerpo = f'''
<header style="display: flex; align-items: center; gap: 10px; padding: 18px 12px 0 16px">
<a href="Main.dc.html" aria-label="2yellow home" style="flex-grow: 1; display: flex; align-items: center; gap: 6px">{icono(38, "hdr")}{palabra(27)}</a>
{chip("Nations League", "#12204F", "#A9B8FF")}</header>
<div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px 0 16px"><span style="font-size: 18px; font-weight: 700">Latest results</span><span style="font-size: 12px; color: {MUT}">League A · matchday 2</span></div>
<div style="display: flex; gap: 12px; padding: 0 16px; overflow: hidden">{"".join(carta(r_) for r_ in dest[:3])}</div>
<section style="margin: 0 12px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">
<div style="padding: 14px 14px 6px 14px">{CAB_NL.replace("League A", "League A · Matchday 3")}</div>{bloques}</section>
<a href="Tips.dc.html" style="margin: 0 12px; padding: 14px 16px; border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; display: flex; align-items: center; gap: 12px">
{icono(34, "acc")}<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 700">Our favourite won {int(res1["nuestro"])}% of the time</span>
<span style="font-size: 12px; color: {MUT}">{ACI["n"]} Nations League games · bookies {int(res1["casa"])}%</span></div><span style="color: #8FA2FF; font-size: 13px; font-weight: 700">See</span></a>
'''
H_MAIN = 1340
common.page("Main.dc.html", "Nations League", 390, H_MAIN, raiz(H_MAIN, cuerpo), JS0, nav_active="m")

# ======================================================================= MINUTO A MINUTO (sondeo del 01/10)
MM = N["minuto"]


def pct(m, extra=0):
    return min(m + min(extra, 3) * 0.3, 93) / 93 * 100


def icono_ev(e, k, tam=14):
    t = e["tipo"]
    if t in ("gol", "gol_pp"):
        return (f'<span style="width: {tam}px; height: {tam}px; border-radius: 50%; background: {LIMA}; box-shadow: 0 0 0 2px {k["barra"]}; '
                f'display: inline-flex; align-items: center; justify-content: center; color: {BG}; font-size: {tam - 5}px; font-weight: 900">G</span>')
    if t == "roja":
        return f'<span style="width: {tam - 4}px; height: {tam}px; border-radius: 2px; background: {ROJO}"></span>'
    if t == "amarilla":
        return f'<span style="width: {tam - 5}px; height: {tam - 2}px; border-radius: 2px; background: {AMARILLO}"></span>'
    return (f'<span style="width: {tam}px; height: {tam}px; border-radius: 50%; background: #2A3040; color: {SOFT}; font-size: {tam - 4}px; font-weight: 800; '
            f'display: inline-flex; align-items: center; justify-content: center">⇄</span>')


def linea_partido(m, kl, kv, nl, nv, alto_barras=34):
    """Línea 0-90': tiros cada 5 minutos (local arriba, visitante abajo) y los eventos encima."""
    bins = {"l": [0] * 19, "v": [0] * 19}
    goles = {"l": set(), "v": set()}
    for t in m["tiros"]:
        i = min(t["min"] // 5, 18)
        bins[t["lado"]][i] += 1
        if t["res"] == "Goal":
            goles[t["lado"]].add(i)
    mx = max(max(bins["l"]), max(bins["v"]), 1)
    barras = ""
    for i in range(19):
        for l_, k in (("l", kl), ("v", kv)):
            h = bins[l_][i] / mx * alto_barras
            if not h:
                continue
            col = LIMA if i in goles[l_] else k["barra"]
            top = (alto_barras + 26 - h) if l_ == "l" else (alto_barras + 34)
            barras += (f'<span style="position: absolute; left: {i / 19 * 100 + 0.6:.1f}%; width: {100 / 19 - 1.2:.1f}%; top: {top:.0f}px; height: {h:.0f}px; '
                       f'border-radius: 3px; background: {col}; opacity: {1 if i in goles[l_] else 0.85}"></span>')
    marcas = ""
    for e in m["eventos"]:
        if e["tipo"] == "cambio":
            continue
        k = kl if e["lado"] == "l" else kv
        y = 4 if e["lado"] == "l" else alto_barras * 2 + 44
        marcas += (f'<span style="position: absolute; left: {pct(e["min"], e["extra"]):.1f}%; top: {y}px; margin-left: -7px; display: flex">{icono_ev(e, k)}</span>')
    eje = alto_barras + 29
    return (f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span style="display: flex; align-items: center; gap: 6px">{franjas(kl, 14)}{nl}</span>'
            f'<span>shots every 5 minutes</span></div>'
            f'<div style="position: relative; height: {alto_barras * 2 + 64}px">'
            f'<span style="position: absolute; left: 0; right: 0; top: {eje}px; height: 2px; background: #2A3040"></span>'
            f'<span style="position: absolute; left: 50%; top: 16px; bottom: 16px; width: 1px; background: #2A3040"></span>'
            f'{barras}{marcas}</div>'
            f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: {MUT}"><span>0\'</span><span>HT</span><span>90\'</span></div>'
            f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span style="display: flex; align-items: center; gap: 6px">{franjas(kv, 14)}{nv}</span>'
            f'<span style="display: flex; align-items: center; gap: 5px"><span style="width: 10px; height: 10px; border-radius: 3px; background: {LIMA}"></span>scored in that spell</span></div>')


def ap(n):
    t = (n or "?").split(" ")
    return n if len(t) < 2 else f"{t[0][0]}. {' '.join(t[1:])}"


def momentos(m, kl, kv, con_cambios=False):
    filas = ""
    for e in m["eventos"]:
        if e["tipo"] == "amarilla" or (e["tipo"] == "cambio" and not con_cambios):
            continue
        k = kl if e["lado"] == "l" else kv
        minuto_txt = f'{e["min"]}\'' + (f'+{e["extra"]}' if e["extra"] else "")
        if e["tipo"] in ("gol", "gol_pp"):
            txt = f'<b>{ap(e["jugador"])}</b>' + (" (pen.)" if e["penalti"] else "") + (f'<span style="color: {MUT}"> · assist {ap(e["asist"])}</span>' if e.get("asist") else "")
        elif e["tipo"] == "roja":
            txt = f'<b>{ap(e["jugador"])}</b> <span style="color: #FF8A80">sent off</span>'
        else:
            txt = f'{ap(e["entra"])} <span style="color: {MUT}">for {ap(e["sale"])}</span>'
        filas += (f'<div style="display: flex; align-items: center; gap: 10px; padding: 7px 0; border-top: 1px solid #1E2330">'
                  f'<span style="width: 34px; {DISP}; font-size: 14px; color: {SOFT}">{minuto_txt}</span>{franjas(k, 16)}{icono_ev(e, k, 16)}'
                  f'<span style="flex-grow: 1; font-size: 13px">{txt}</span></div>')
    return f'<div style="display: flex; flex-direction: column">{filas}</div>'


# ---- informe Chequia - Inglaterra
KA, KB = kits("Czech Republic", "England")
MC = MM["Czech Republic-England"]
roja = next(e for e in MC["eventos"] if e["tipo"] == "roja")
STORY = tarjeta("Match story", linea_partido(MC, KA, KB, "Czechia", "England") + momentos(MC, KA, KB)
                + f'<div style="padding: 12px; border-radius: 16px; background: #2A1416; display: flex; gap: 10px; align-items: center">'
                  f'<span style="width: 12px; height: 16px; border-radius: 2px; background: {ROJO}; flex-shrink: 0"></span>'
                  f'<span style="font-size: 13px"><b>Turning point · {roja["min"]}\'</b> {ap(roja["jugador"])} sent off at 0–0. Czechia played {90 - roja["min"]} minutes with ten; both goals came after.</span></div>',
                "minute by minute")

RES_ORD = [("Goal", "Goals", LIMA), ("Saved", "Saved", "#8FA2FF"), ("Post", "Woodwork", NARANJA), ("Blocked", "Blocked", "#5B6378"), ("Missed", "Off target", "#2E3546")]


def barra_tiros(m, l_, k, nombre):
    ts = [t for t in m["tiros"] if t["lado"] == l_]
    seg = "".join(f'<span style="flex: {sum(t["res"] == r_ for t in ts)} 1 0; background: {c}"></span>' for r_, _, c in RES_ORD if any(t["res"] == r_ for t in ts))
    return (f'<div style="display: flex; flex-direction: column; gap: 6px"><div style="display: flex; align-items: center; gap: 8px">{franjas(k, 16)}'
            f'<span style="flex-grow: 1; font-size: 13px; font-weight: 700">{nombre}</span><span style="{DISP}; font-size: 22px; color: {k["barra"]}">{len(ts)}</span></div>'
            f'<div style="display: flex; height: 12px; border-radius: 6px; overflow: hidden; gap: 2px">{seg}</div></div>')


def porteria(m, l_):
    ts = [t for t in m["tiros"] if t["lado"] == l_ and t["zona"]]
    c = {}
    for t in ts:
        c[t["zona"]] = c.get(t["zona"], 0) + 1
    g = {}
    for t in ts:
        if t["res"] == "Goal":
            g[t["zona"]] = g.get(t["zona"], 0) + 1

    def celda(z):
        n = c.get(z, 0)
        gg = g.get(z, 0)
        alpha = min(0.15 + n * 0.18, 0.95)
        return (f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(200,255,61,{alpha if n else 0.04:.2f}); '
                f'color: {BG if n >= 3 else TXT}; border-radius: 4px"><span style="{DISP}; font-size: 20px">{n or ""}</span>'
                f'{"<span style=" + chr(34) + "font-size: 10px; font-weight: 800" + chr(34) + ">" + str(gg) + " goal" + ("s" if gg > 1 else "") + "</span>" if gg else ""}</div>')
    lado_txt = lambda z: f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; color: {MUT}; font-size: 10px"><span style="{DISP}; font-size: 16px; color: {SOFT}">{c.get(z, 0) or "–"}</span>just wide</div>'
    return (f'<div style="display: grid; grid-template-columns: 54px minmax(0, 1fr) 54px; gap: 6px; align-items: stretch">{lado_txt("Close Left")}'
            f'<div style="height: 120px; padding: 6px; border: 4px solid {TXT}; border-bottom: none; border-radius: 4px 4px 0 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-template-rows: repeat(2, minmax(0, 1fr)); gap: 4px">'
            f'{celda("High Left")}{celda("High Centre")}{celda("High Right")}{celda("Low Left")}{celda("Low Centre")}{celda("Low Right")}</div>'
            f'{lado_txt("Close Right")}</div>')


ley = "".join(f'<span style="display: flex; align-items: center; gap: 5px"><span style="width: 10px; height: 10px; border-radius: 3px; background: {c}"></span>{n_}</span>' for _, n_, c in RES_ORD)
TIROS = tarjeta("Shots", barra_tiros(MC, "l", KA, "Czechia") + barra_tiros(MC, "v", KB, "England")
                + f'<div style="display: flex; flex-wrap: wrap; gap: 10px; font-size: 11px; color: {MUT}">{ley}</div>'
                + f'<span style="padding-top: 6px; font-size: 13px; font-weight: 700">Where England aimed</span>' + porteria(MC, "v")
                + f'<span style="font-size: 11px; color: {MUT}">Shots with a target zone.</span>', "every attempt")


def fila_cambio(e, k):
    n = e["nota_entra"]
    bg, fg = (LIMA, BG) if n and n >= 7.5 else (("#3A4256", TXT) if n and n >= 6.5 else ((NARANJA, BG) if n else ("#2A3040", MUT)))
    return (f'<div style="display: flex; align-items: center; gap: 10px; padding: 7px 0; border-top: 1px solid #1E2330">'
            f'<span style="width: 30px; {DISP}; font-size: 14px; color: {SOFT}">{e["min"]}\'</span>{franjas(k, 16)}'
            f'<div style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column"><span style="font-size: 13px; font-weight: 700">{ap(e["entra"])}</span>'
            f'<span style="font-size: 11px; color: {MUT}">for {ap(e["sale"])}</span></div>'
            f'<span style="padding: 2px 8px; border-radius: 8px; background: {bg}; color: {fg}; {DISP}; font-size: 14px">{f"{n:.1f}" if n else "–"}</span></div>')


CAMBIOS = tarjeta("From the bench", "".join(fila_cambio(e, KA if e["lado"] == "l" else KB) for e in MC["eventos"] if e["tipo"] == "cambio")
                  + f'<span style="font-size: 11px; color: {MUT}">Rating of the player coming on.</span>', "substitutions")
NEWS = tarjeta("In the news", "".join(
    f'<div style="display: flex; flex-direction: column; gap: 3px; padding: 9px 0; border-top: 1px solid #1E2330"><span style="font-size: 14px; font-weight: 600; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden">{n_["titulo"]}</span>'
    f'<span style="font-size: 11px; color: {MUT}">{n_["fuente"]} · {fecha(n_["fecha"])}</span></div>' for n_ in MC["news"]), "after the match")
v_, ar_, ti_ = MC["venue"], MC["arbitro"], MC["tiempo"]
SEDE = (f'<div style="margin: 0 12px; padding: 12px 14px; border-radius: 18px; background: {CARD}; border: 1px solid {BORDE}; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">'
        f'<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 11px; color: {MUT}">Stadium</span><span style="font-size: 13px; font-weight: 700">{v_["name"]}</span><span style="font-size: 11px; color: {SOFT}">{v_["city"]} · {int(v_["capacity"]):,}</span></div>'
        f'<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 11px; color: {MUT}">Referee</span><span style="font-size: 13px; font-weight: 700">{ar_["name"].split(",")[1].strip()} {ar_["name"].split(",")[0]}</span><span style="font-size: 11px; color: {SOFT}">{ar_["nationality"].replace("Turkiye", "Türkiye")}</span></div>'
        f'<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 11px; color: {MUT}">Weather</span><span style="font-size: 13px; font-weight: 700">{round(float(ti_["temperature"].replace("°C", "")))}°C</span><span style="font-size: 11px; color: {SOFT}">{ti_["status"].capitalize()}</span></div></div>')

# ---- previa: el último partido de cada uno
MS = MM["Spain-Croatia"]
KS, KCR = kits("Spain", "Croatia")


def ultimo(m, kl, kv, nl, nv, titulo, nota_txt):
    gl, gv = m["marcador"].split(" - ")
    return (f'<div style="display: flex; flex-direction: column; gap: 10px">'
            f'<div style="display: flex; align-items: center; justify-content: space-between"><span style="font-size: 12px; font-weight: 800; letter-spacing: 0.6px; color: {MUT}">{titulo}</span>'
            f'<span style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; white-space: nowrap">{franjas(kl, 14)}{nl} <span style="{DISP}; font-size: 18px">{gl}–{gv}</span> {nv}{franjas(kv, 14)}</span></div>'
            + linea_partido(m, kl, kv, nl, nv, 24) + momentos(m, kl, kv)
            + f'<span style="font-size: 12px; color: {SOFT}">{nota_txt}</span></div>')


n_tiros_es = sum(t["lado"] == "l" for t in MS["tiros"])
n_tiros_cr = sum(t["lado"] == "v" for t in MS["tiros"])
ULTIMO = tarjeta("Last time out",
                 ultimo(MS, KS, KCR, "Spain", "Croatia", "CROATIA",
                        f"Croatia level at 1–1 after 28', then conceded three. Shots {n_tiros_cr} to Spain's {n_tiros_es}.")
                 + '<div style="height: 1px; background: #232838"></div>'
                 + ultimo(MC, KA, KB, "Czechia", "England", "ENGLAND",
                          f"England had {sum(t['lado'] == 'v' for t in MC['tiros'])} shots to {sum(t['lado'] == 'l' for t in MC['tiros'])}; Czechia were down to ten from the {roja['min']}th minute."),
                 "minute by minute")


# ======================================================================= PREVIEW Croatia – England
PV = N["previa"]
KC, KE = kits("Croatia", "England")
p1, px, p2 = [int(v) for v in PV["p1x2"]]


def corto(n):
    """Inicial y apellido: «J. Šutalo»; los que ya vienen así, igual."""
    t = n.split(" ")
    return n if len(t) < 2 or t[0].endswith(".") else f"{t[0][0]}. {' '.join(t[1:])}"


def forma_html(e, k):
    celdas = ""
    for f in PV["forma"][e]:
        gana = f["gf"] > f["gc"]
        emp = f["gf"] == f["gc"]
        celdas += (f'<div style="display: flex; flex-direction: column; align-items: center; gap: 4px">'
                   f'<span style="width: 100%; height: 36px; border-radius: 10px; background: {LIMA if gana else ("#3A4256" if emp else NARANJA)}; '
                   f'color: {BG if not emp else TXT}; {DISP}; font-size: 15px; display: flex; align-items: center; justify-content: center">{f["gf"]}-{f["gc"]}</span>'
                   f'<span style="font-size: 9px; font-weight: 700; color: {SOFT}">{"" if f["casa"] else "@"}{eq(f["riv"])[1]}</span>'
                   f'<span style="font-size: 9px; color: {MUT}">{"WC" if f["comp"] == "World Cup" else ("NL" if "Nations" in f["comp"] else "F")}</span></div>')
    return (f'<div style="display: flex; flex-direction: column; gap: 8px"><div style="display: flex; align-items: center; gap: 8px">{franjas(k, 18)}'
            f'<span style="font-size: 13px; font-weight: 700">{eq(e)[0]}</span></div>'
            f'<div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 5px">{celdas}</div></div>')


def once_html(e, k):
    filas = ""
    for j in sorted(PV["once"][e], key=lambda j: ["Goalkeeper", "Defender", "Midfielder", "Forward"].index(j["posicion"])):
        n = j["nota"]
        filas += (f'<div style="display: flex; align-items: center; gap: 8px; padding: 5px 0">'
                  f'<span style="width: 30px; font-size: 10px; font-weight: 700; color: {MUT}">{ {"Goalkeeper": "GK", "Defender": "DEF", "Midfielder": "MID", "Forward": "FWD"}[j["posicion"]] }</span>'
                  f'<span style="flex-grow: 1; font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{corto(j["jugador"])}</span>'
                  f'<span style="padding: 1px 7px; border-radius: 8px; background: {LIMA if n >= 7.2 else "#3A4256"}; color: {BG if n >= 7.2 else TXT}; {DISP}; font-size: 13px">{n:.2f}</span></div>')
    media = sum(j["nota"] for j in PV["once"][e]) / len(PV["once"][e])
    return (f'<div style="flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; gap: 2px">'
            f'<div style="display: flex; align-items: center; gap: 6px; padding-bottom: 6px">{franjas(k, 16)}<span style="font-size: 13px; font-weight: 700">{eq(e)[0]}</span>'
            f'<span style="margin-left: auto; {DISP}; font-size: 16px; color: {k["barra"]}">{media:.2f}</span></div>{filas}</div>')


h2h = PV["h2h"]
H2H = "".join(
    f'<div style="display: flex; align-items: center; gap: 10px; padding: 8px 0; border-top: 1px solid #1E2330"><span style="width: 56px; font-size: 12px; color: {MUT}">{h["fecha"][:4]}</span>'
    f'<span style="flex-grow: 1; font-size: 13px; font-weight: 600">{eq(h["local"])[0]} <span style="{DISP}; font-size: 15px">{h["gl"]}–{h["gv"]}</span> {eq(h["visitante"])[0]}</span>'
    f'<span style="font-size: 11px; color: {MUT}">{h["comp"].replace("UEFA ", "")}</span></div>' for h in h2h[-4:]) or f'<span style="font-size: 13px; color: {MUT}">No meetings since 2025.</span>'
FP = PV["fifa_pts"]
GOLES_T = tarjeta("Goals", f'''<div style="display: flex; align-items: center; justify-content: space-between">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 12px; color: {MUT}">Expected goals</span><span style="{DISP}; font-size: 34px; line-height: 1"><span style="color: {KC["barra"]}">{PV["lam"][0]:.2f}</span> <span style="font-size: 20px; color: {MUT}">–</span> <span style="color: {KE["barra"]}">{PV["lam"][1]:.2f}</span></span></div>
<div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px"><span style="font-size: 12px; color: {MUT}">Most likely</span><span style="{DISP}; font-size: 30px; line-height: 1">{PV["marcador"][0]}–{PV["marcador"][1]}</span></div></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
{"".join(f'<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">{t}</span><span style="{DISP}; font-size: 22px; color: {LIMA if v >= 60 else TXT}">{int(v)}%</span></div>' for t, v in (("Over 1.5", PV["mas15"]), ("Over 2.5", PV["mas25"]), ("Both score", PV["btts"])))}</div>
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span>Croatia score first <b style="color: {KC["barra"]}">{int(PV["primero"][0])}%</b></span><span>England first <b style="color: {KE["barra"]}">{int(PV["primero"][1])}%</b></span></div>''', "2yellow model")
CC_T = tarjeta("Corners &amp; cards", f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 16px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">Corners expected</span><span style="{DISP}; font-size: 26px">{PV["corners"]}</span><span style="font-size: 12px; color: {SOFT}">Over 8.5: <b style="color: {TXT}">{int(PV["corners_85"])}%</b></span></div>
<div style="padding: 12px; border-radius: 16px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">Yellow cards expected</span><span style="{DISP}; font-size: 26px; color: {AMARILLO}">{PV["tarjetas"]}</span><span style="font-size: 12px; color: {SOFT}">Over 3.5: <b style="color: {TXT}">{int(PV["tarjetas_35"])}%</b></span></div></div>''', "2yellow model")
cuerpo = f'''
<div style="position: relative; display: flex; flex-direction: column; padding-bottom: 14px">
{glow(KC["barra"], KE["barra"], 230)}
{volver("Main.dc.html", "Nations League · League A · MD3", "Sat 3 Oct · 18:00 · Zagreb")}
<div style="position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px 0 16px">
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("Croatia", 62, KC)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">{franjas(KC, 16)}Croatia</span><span style="font-size: 12px; color: {SOFT}">FIFA {ordinal(PV["fifa_puesto"][0])}</span></div>
<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; padding-top: 8px"><span style="{DISP}; font-size: 44px; line-height: 1">18:00</span>{chip("Preview", "#1E2A66", "#A9B8FF")}</div>
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("England", 62, KE)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">England{franjas(KE, 16)}</span><span style="font-size: 12px; color: {SOFT}">FIFA {ordinal(PV["fifa_puesto"][1])}</span></div>
</div></div>
{pestañas("Preview", [("Preview", "Partido.dc.html"), ("Tips", "Tips.dc.html"), ("H2H", "#"), ("Group", "Elo.dc.html")])}
{tarjeta("Win chance", tres(p1, px, p2, (KC["barra"], KC["texto"]), (KE["barra"], KE["texto"])) +
 '<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">' +
 "".join(f'<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Fair odds · {k}</span><span style="{DISP}; font-size: 20px">{100 / v:.2f}</span></div>' for k, v in (("1", p1), ("X", px), ("2", p2))) + '</div>'
 + f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span>FIFA <b style="color: {KC["barra"]}">{int(FP[0])}</b> pts</span><span>strength + form</span><span><b style="color: {KE["barra"]}">{int(FP[1])}</b> pts</span></div>', "2yellow model")}
{GOLES_T}
{CC_T}
{tarjeta("Form", forma_html("Croatia", KC) + forma_html("England", KE), "last 5 · latest on the right")}
{tarjeta("Likely XIs", '<div style="display: flex; gap: 14px">' + once_html("Croatia", KC) + once_html("England", KE) + '</div>' + f'<span style="font-size: 11px; color: {MUT}">Last XI · fair rating (club form + country)</span>', "fair rating")}
{ULTIMO}
{tarjeta("Head to head", H2H, "since 2025")}
'''
H_PV = 2760
common.page("Partido.dc.html", "Croatia – England preview", 390, H_PV, raiz(H_PV, cuerpo), JS0, nav_active="m")

# ======================================================================= REPORT Czechia 0–2 England
I = N["informe"]
KA, KB = kits("Czech Republic", "England")
CA, CB = (KA["barra"], KA["texto"]), (KB["barra"], KB["texto"])
TABS = [("Report", "Report.dc.html"), ("Lineups", "Alineacion.dc.html")]


def cabecera(activa, compacta=False):
    if compacta:
        top = (f'<div style="position: relative; display: flex; align-items: center; justify-content: center; gap: 12px; padding: 0 0 12px 0">'
               f'{franjas(KA, 26)}{escudo("Czech Republic", 32, KA)}<span style="{DISP}; font-size: 30px">{I["gl"]} – {I["gv"]}</span>{escudo("England", 32, KB)}{franjas(KB, 26)}</div>')
    else:
        top = f'''<div style="position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px 0 16px">
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("Czech Republic", 62, KA)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">{franjas(KA, 16)}Czechia</span></div>
<div style="display: flex; flex-direction: column; align-items: center; gap: 6px"><span style="{DISP}; font-size: 64px; line-height: 1">{I["gl"]} – {I["gv"]}</span>{chip("Full time", "#1E2330", SOFT)}</div>
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("England", 62, KB)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">England{franjas(KB, 16)}</span></div>
</div><div style="position: relative; display: flex; justify-content: space-between; padding: 12px 16px 16px 16px; font-size: 12px; color: {SOFT}"><span>Tue 29 Sep</span><span>League A · Matchday 2</span></div>'''
    return (f'<div style="position: relative; display: flex; flex-direction: column">{glow(KA["barra"], KB["barra"], 230)}'
            f'{volver("Main.dc.html", "Nations League · League A", "Match report")}{top}</div>{pestañas(activa, TABS)}')


s = I["stats"]


def cara(nombre, par, fmt=lambda v: f"{v:.0f}"):
    return (f'<div style="display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-top: 1px solid #1E2330">'
            f'<span style="{DISP}; font-size: 17px; width: 60px; color: {CA[0]}">{fmt(par[0])}</span>'
            f'<span style="font-size: 12px; font-weight: 600; color: {SOFT}">{nombre}</span>'
            f'<span style="{DISP}; font-size: 17px; width: 60px; text-align: right; color: {CB[0]}">{fmt(par[1])}</span></div>')


m_ = I["merecido"]
MERECIDO = tarjeta("Deserved?", f'''
<div style="display: flex; align-items: center; justify-content: space-between">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 12px; color: {MUT}">Expected goals</span><span style="{DISP}; font-size: 36px; line-height: 1"><span style="color: {CA[0]}">{s["Expected Goals"][0]:.2f}</span> <span style="color: {MUT}; font-size: 22px">vs</span> <span style="color: {CB[0]}">{s["Expected Goals"][1]:.2f}</span></span></div>
{chip("Deserved", "#1F3A16", LIMA)}</div>
<span style="font-size: 13px; color: {SOFT}">Replaying these chances 100 times:</span>
{tres(int(m_[0]), int(m_[1]), int(m_[2]), CA, CB, 40, 20)}
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {MUT}"><span>Czechia win</span><span>draw</span><span>England win</span></div>
<div style="display: flex; flex-direction: column">
{cara("Shots on target", s["Shots on target"])}{cara("Shots off target", s["Shots off target"])}{cara("Shots inside the box", s["Shots within penalty area"])}
{cara("Big chances", s["Big Chances Created"])}{cara("Passes into final third", s["Passes Into Final Third"])}{cara("Key passes", s["Key Passes"])}{cara("Keeper saves", s["Goalkeeper saves"])}</div>''', "by xG")

STATS = tarjeta("Key stats", "".join([
    fila_stat("Possession", s["Possession"][0] * (100 if s["Possession"][0] <= 1 else 1), s["Possession"][1] * (100 if s["Possession"][1] <= 1 else 1), lambda v: f"{v:.0f}%", CA[0], CB[0]),
    fila_stat("Passes", s["Total passes"][0], s["Total passes"][1], ch=CA[0], ca=CB[0]),
    fila_stat("Corners", s["Corners"][0], s["Corners"][1], ch=CA[0], ca=CB[0]),
    fila_stat("Tackles", s["Tackles"][0], s["Tackles"][1], ch=CA[0], ca=CB[0]),
    fila_stat("Fouls", s["Fouls"][0], s["Fouls"][1], ch=CA[0], ca=CB[0]),
    fila_stat("Yellow cards", s["Yellow cards"][0], s["Yellow cards"][1], ch=CA[0], ca=CB[0])]))

jug = [j for j in I["jugadores"] if j["nota"]][:5]
NOTAS = tarjeta("Best players", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px">{franjas(KA if j["equipo"] == "Czech Republic" else KB, 26)}<div style="flex-grow: 1; display: flex; flex-direction: column">'
    f'<span style="font-size: 14px; font-weight: 700">{j["jugador"]}</span><span style="font-size: 12px; color: {MUT}">{j["pos"]} · {j["min"]}\'{" · " + str(j["goles"]) + " goal" if j["goles"] else ""}{" · " + str(j["asist"]) + " assist" if j["asist"] else ""}</span></div>'
    f'<span style="padding: 3px 9px; border-radius: 9px; background: {LIMA if j["nota"] >= 7.5 else "#3A4256"}; color: {BG if j["nota"] >= 7.5 else TXT}; {DISP}; font-size: 15px">{j["nota"]:.1f}</span></div>'
    for j in jug), "rating")

NU, CS, RE = I["nuestro"], I["casa"], I["real"]
NOM = ["Czechia", "Draw", "England"]


def celda(txt, ok):
    return f'<div style="display: flex; align-items: center; justify-content: flex-end; gap: 6px"><span style="{DISP}; font-size: 15px">{txt}</span>{marca(ok)}</div>'


def fila_m(nombre, a, b):
    return (f'<div style="display: grid; grid-template-columns: minmax(0, 1fr) 92px 92px; align-items: center; gap: 8px; padding: 9px 0; border-top: 1px solid #1E2330">'
            f'<span style="font-size: 13px; font-weight: 600">{nombre}</span>{a}{b}</div>')


i_n, i_c = max(range(3), key=lambda i: NU["1x2"][i]), max(range(3), key=lambda i: CS["1x2"][i])
filas_m = fila_m(f"Result · {NOM[RE['1x2']]} won", celda(f"{NOM[i_n]} {int(NU['1x2'][i_n])}%", i_n == RE["1x2"]), celda(f"{NOM[i_c]} {int(CS['1x2'][i_c])}%", i_c == RE["1x2"]))
an, ac = int(i_n == RE["1x2"]), int(i_c == RE["1x2"])
txt = lambda p_: f"{'Yes' if p_ >= 50 else 'No'} {int(max(p_, 100 - p_))}%"
for k, nombre in (("mas15", "Over 1.5 goals"), ("mas25", "Over 2.5 goals"), ("btts", "Both teams score")):
    ok_n, ok_c = (NU[k] >= 50) == RE[k], (CS[k] >= 50) == RE[k]
    an += ok_n
    ac += ok_c
    filas_m += fila_m(nombre, celda(txt(NU[k]), ok_n), celda(txt(CS[k]), ok_c))
MERCADO = tarjeta("Our call vs the bookies", f'''
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}; display: flex; align-items: center; gap: 10px">{icono(28, "rep")}<div style="display: flex; flex-direction: column"><span style="{DISP}; font-size: 22px; line-height: 1">{an} / 4</span><span style="font-size: 11px; color: {MUT}">2yellow right</span></div></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column"><span style="{DISP}; font-size: 22px; line-height: 1">{ac} / 4</span><span style="font-size: 11px; color: {MUT}">bookies right</span></div></div>
<div style="display: grid; grid-template-columns: minmax(0, 1fr) 92px 92px; gap: 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; color: {MUT}"><span>MARKET</span><span style="text-align: right">2YELLOW</span><span style="text-align: right">BOOKIES</span></div>
<div style="display: flex; flex-direction: column">{filas_m}</div>
<span style="font-size: 11px; color: {MUT}">Both {int(round(I["horas_antes"]))} h before kick-off, margin removed.</span>''', "pre-match")

gk = I["porteros"]


def chip_gk(ev):
    txt = ("+" if ev >= 0 else "−") + f"{abs(ev):.2f} goals saved"
    return chip(txt, "#1F3A16" if ev >= 0 else "#3A2412", LIMA if ev >= 0 else "#FFB27A")


PORTERO = tarjeta("Goalkeepers", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px">{franjas(KA if g["equipo"] == "Czech Republic" else KB, 26)}<span style="flex-grow: 1; font-size: 14px; font-weight: 700">{g["jugador"]}</span>'
    f'<span style="font-size: 12px; color: {MUT}">{g["paradas"]} saves</span>'
    f'{chip_gk(g["evitados"]) if g["evitados"] is not None else ""}</div>'
    for g in gk), "shot-stopping")
cuerpo = cabecera("Report") + SEDE + STORY + MERECIDO + TIROS + MERCADO + STATS + NOTAS + CAMBIOS + PORTERO + NEWS
H_REP = 4170
common.page("Report.dc.html", "Czechia 0-2 England report", 390, H_REP, raiz(H_REP, cuerpo), JS0, nav_active="m")

# ---------------------------------------------------------------- alineaciones
FORMAS = {
    "4-4-2": [[(50, .05)], [(12, .30), (37, .20), (63, .20), (88, .30)], [(13, .58), (38, .50), (62, .50), (87, .58)], [(36, .86), (64, .82)]],
    "4-2-3-1": [[(50, .05)], [(12, .30), (37, .20), (63, .20), (88, .30)], [(36, .45), (64, .45)], [(14, .72), (50, .68), (86, .72)], [(50, .90)]],
    "4-3-3": [[(50, .05)], [(12, .30), (37, .20), (63, .20), (88, .30)], [(30, .50), (50, .44), (70, .50)], [(16, .82), (50, .88), (84, .82)]],
    "3-4-2-1": [[(50, .05)], [(25, .20), (50, .18), (75, .20)], [(10, .50), (38, .44), (62, .44), (90, .50)], [(35, .72), (65, .72)], [(50, .90)]],
    "3-4-3": [[(50, .05)], [(25, .20), (50, .18), (75, .20)], [(10, .50), (38, .44), (62, .44), (90, .50)], [(18, .82), (50, .88), (82, .82)]],
    "4-1-4-1": [[(50, .05)], [(12, .30), (37, .20), (63, .20), (88, .30)], [(50, .40)], [(13, .62), (38, .58), (62, .58), (87, .62)], [(50, .90)]],
    "5-3-2": [[(50, .05)], [(8, .34), (30, .20), (50, .18), (70, .20), (92, .34)], [(30, .52), (50, .46), (70, .52)], [(36, .86), (64, .82)]],
    "3-5-2": [[(50, .05)], [(25, .20), (50, .18), (75, .20)], [(8, .54), (30, .48), (50, .42), (70, .48), (92, .54)], [(36, .86), (64, .82)]],
}


def apellido(n):
    t = n.split(" ")
    return t[0] if t[-1] in ("Júnior", "Junior") else t[-1]


def rc(n):
    if n is None:
        return ("#3A4256", TXT, "–")
    return (LIMA, BG, f"{n:.1f}") if n >= 7.5 else (("#3A4256", TXT, f"{n:.1f}") if n >= 6.5 else (NARANJA, BG, f"{n:.1f}"))


def dibuja(info, arriba, color):
    out = ""
    lineas = info["lineas"]
    forma = FORMAS.get(info["formacion"])
    for i, linea in enumerate(lineas):
        for j, p in enumerate(linea):
            if forma and i < len(forma) and j < len(forma[i]):
                x, d = forma[i][j]
            else:
                x, d = (50 if len(linea) == 1 else 12 + j * 76 / (len(linea) - 1)), 0.05 + i * 0.85 / (len(lineas) - 1)
            sx = 100 - x if arriba else x
            sy = 3 + d * 44 if arriba else 97 - d * 44
            bg, fg, t = rc(p["nota"])
            out += (f'<div style="position: absolute; left: {sx:.1f}%; top: {sy:.1f}%; width: 92px; margin-left: -46px; margin-top: -18px; display: flex; flex-direction: column; align-items: center; gap: 2px">'
                    f'<div style="position: relative; width: 28px; height: 28px"><span style="width: 28px; height: 28px; border-radius: 50%; background: {color["c1"] if color.get("una") else "linear-gradient(90deg, " + color["c1"] + " 0 50%, " + color["c2"] + " 50% 100%)"}; display: block; box-shadow: 0 0 0 2px {color["c2"] if color.get("una") else color["c1"]}, 0 0 0 3px rgba(0,0,0,0.6)"></span>'
                    f'<span style="position: absolute; right: -18px; top: -7px; padding: 1px 5px; border-radius: 7px; background: {bg}; color: {fg}; font-size: 10px; font-weight: 800">{t}</span></div>'
                    f'<span style="max-width: 92px; overflow: hidden; text-overflow: ellipsis; font-size: 10.5px; font-weight: 700; white-space: nowrap; text-shadow: 0 1px 2px #000">{apellido(p["jugador"])}</span></div>')
    return out


LI = I["lineas"]


def media_eq(n, k, lado):
    ns = [p["nota"] for l_ in LI[n]["lineas"] for p in l_ if p["nota"]]
    dir_ = "row" if lado == "i" else "row-reverse"
    return (f'<div style="flex: 1 1 0; min-width: 0; padding: 10px 12px; border-radius: 16px; background: {CARD}; border: 1px solid {BORDE}; display: flex; flex-direction: column; gap: 4px; align-items: {"flex-start" if lado == "i" else "flex-end"}">'
            f'<div style="display: flex; align-items: center; gap: 8px; flex-direction: {dir_}">{franjas(k)}<span style="font-size: 14px; font-weight: 700">{eq(n)[0]}</span></div>'
            f'<div style="display: flex; align-items: baseline; gap: 6px; flex-direction: {dir_}"><span style="{DISP}; font-size: 28px; line-height: 1; color: {k["barra"]}">{sum(ns) / len(ns):.2f}</span>'
            f'<span style="font-size: 11px; color: {MUT}">avg · {LI[n]["formacion"]}</span></div></div>')


CAMPO = f'''<section style="margin: 0 12px; position: relative; height: 620px; border-radius: 26px; background: #0F1B15; border: 1px solid #1F3026; overflow: hidden" aria-label="Both starting elevens">
<div style="position: absolute; left: 14px; right: 14px; top: 14px; bottom: 14px; border: 2px solid #25392E; border-radius: 6px"></div>
<div style="position: absolute; left: 14px; right: 14px; top: 309px; height: 2px; background: #25392E"></div>
<div style="position: absolute; left: 50%; top: 310px; width: 88px; height: 88px; margin: -44px 0 0 -44px; border: 2px solid #25392E; border-radius: 50%"></div>
<div style="position: absolute; left: 50%; top: 14px; width: 156px; height: 66px; margin-left: -78px; border: 2px solid #25392E; border-top: none"></div>
<div style="position: absolute; left: 50%; bottom: 14px; width: 156px; height: 66px; margin-left: -78px; border: 2px solid #25392E; border-bottom: none"></div>
{dibuja(LI["Czech Republic"], True, KA)}{dibuja(LI["England"], False, KB)}</section>'''
FORM = '<div style="display: flex; gap: 8px; padding: 0 12px">' + media_eq("Czech Republic", KA, "i") + media_eq("England", KB, "d") + '</div>'
H_AL = 1030
common.page("Alineacion.dc.html", "Lineups", 390, H_AL, raiz(H_AL, cabecera("Lineups", True) + FORM + CAMPO), JS0, nav_active="m")

# ======================================================================= TEAM · England
TABS_EQ = [("Overview", "Equipo.dc.html"), ("Record", "Historial.dc.html"), ("Group", "Elo.dc.html"), ("Fixtures", "#")]
EQ_ = N["equipo"]
KEN = kit("England")
P = EQ_["partidos"]
nl = [x for x in P if x["fecha"] >= "2025-01-01"]
g_ = sum(x["gf"] > x["gc"] for x in nl)
e_ = sum(x["gf"] == x["gc"] for x in nl)
l_ = sum(x["gf"] < x["gc"] for x in nl)
fifa_ing = EQ_["fifa"]
GI = next(g for g in N["grupos"] if "England" in g["equipos"])
POS_G = [t["equipo"] for t in GI["tabla"]].index("England") + 1
PTS_G = next(t["pts"] for t in GI["tabla"] if t["equipo"] == "England")


def forma_eq_html(lista):
    return '<div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px">' + "".join(
        f'<div style="display: flex; flex-direction: column; align-items: center; gap: 5px">'
        f'<span style="width: 100%; height: 44px; border-radius: 12px; background: {LIMA if f["gf"] > f["gc"] else ("#3A4256" if f["gf"] == f["gc"] else NARANJA)}; '
        f'color: {BG if f["gf"] != f["gc"] else TXT}; {DISP}; font-size: 17px; display: flex; align-items: center; justify-content: center">{f["gf"]}-{f["gc"]}</span>'
        f'<span style="font-size: 10px; font-weight: 700; color: {SOFT}">{"" if f["casa"] else "@"}{eq(f["riv"])[1]}</span>'
        f'<span style="font-size: 9px; color: {MUT}">{"World Cup" if f["comp"] == "World Cup" else ("Nations L." if "Nations" in f["comp"] else ("Qualifier" if "Qualif" in f["comp"] else "Friendly"))}</span></div>'
        for f in lista) + "</div>"


def rango(n):
    x = [f for f in P if f["xg"] is not None][-n:] if n else [f for f in P if f["xg"] is not None]
    gf, xg = sum(f["gf"] for f in x), sum(f["xg"] for f in x)
    gc, xga = sum(f["gc"] for f in x), sum(f["xga"] for f in x)
    return {"gf": gf, "xg": f"{xg:.1f}", "gc": gc, "xga": f"{xga:.1f}", "n": f"{len(x)} games with xG",
            "dif": ("+" if gf - xg >= 0 else "−") + f"{abs(gf - xg):.1f}", "difc": LIMA if gf - xg >= 0 else "#FFB27A"}


SEL_EQ = {"fin": {"opts": [["l5", "Last 5"], ["l10", "Last 10"], ["all", "Since 2025"]], "ini": "l10",
                  "vals": {"l5": rango(5), "l10": rango(10), "all": rango(None)}}}
FIN = tarjeta("Goals vs chances", selector("fin") + f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">Scored vs xG</span><span style="{DISP}; font-size: 24px; color: {KEN["barra"]}">{{{{fin.gf}}}} <span style="font-size: 15px; color: {MUT}">from {{{{fin.xg}}}}</span></span><span style="font-size: 12px; font-weight: 700; color: {{{{fin.difc}}}}">{{{{fin.dif}}}}</span></div>
<div style="padding: 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">Conceded vs xG against</span><span style="{DISP}; font-size: 24px">{{{{fin.gc}}}} <span style="font-size: 15px; color: {MUT}">from {{{{fin.xga}}}}</span></span><span style="font-size: 12px; color: {SOFT}">{{{{fin.n}}}}</span></div></div>''', "all competitions")
FIFA_T = tarjeta("FIFA ranking", f'''<div style="display: flex; align-items: center; gap: 16px">
<div style="display: flex; flex-direction: column"><span style="{DISP}; font-size: 48px; line-height: 1">{ordinal(fifa_ing[-1]["puesto"])}</span><span style="font-size: 12px; color: {MUT}">{int(fifa_ing[-1]["puntos"])} pts · Jul 2026</span></div>
<div style="margin-left: auto">{sparkline([f["puntos"] for f in fifa_ing], 150, 60)}</div></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Since 2025</span><span style="{DISP}; font-size: 20px"><span style="color: {LIMA}">{g_}W</span> {e_}D <span style="color: #FFB27A">{l_}L</span></span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Group</span><span style="{DISP}; font-size: 20px">{ordinal(POS_G)} · {PTS_G} pts</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Best rank</span><span style="{DISP}; font-size: 20px">{ordinal(min(f["puesto"] for f in fifa_ing))}</span></div></div>''', "strength")
GOL = tarjeta("Top scorers", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px"><span style="width: 18px; {DISP}; font-size: 14px; color: {MUT}">{i + 1}</span>'
    f'<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 700">{g["jugador"]}</span>'
    f'<span style="font-size: 12px; color: {MUT}">{g["pj"]} games · {g["asist"]} assists</span></div>'
    f'<span style="{DISP}; font-size: 22px; color: {LIMA}">{g["goles"]}</span></div>' for i, g in enumerate(EQ_["goleadores"])), "since 2025")
MEJ = tarjeta("Best rated", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px"><span style="flex-grow: 1; font-size: 14px; font-weight: 600">{b["jugador"]}</span>'
    f'<span style="font-size: 12px; color: {MUT}">{b["pj"]} games</span><span style="padding: 3px 9px; border-radius: 9px; background: {LIMA if b["nota"] >= 7.5 else "#3A4256"}; color: {BG if b["nota"] >= 7.5 else TXT}; {DISP}; font-size: 15px">{b["nota"]:.2f}</span></div>'
    for b in EQ_["mejores"]), "avg rating since 2025")
HERO = f'''<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: 50%; top: -70px; width: 300px; height: 260px; margin-left: -150px; border-radius: 50%; background: #F1F3F8; opacity: 0.16; filter: blur(70px)"></span>
{volver("Main.dc.html", "", "")}
<div style="position: relative; display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 0 16px 16px 16px">
{escudo("England", 84)}<span style="{DISP}; font-size: 34px; line-height: 1">England</span>
<span style="font-size: 13px; color: {SOFT}">FIFA {ordinal(fifa_ing[-1]["puesto"])} · Nations League A</span>
<button style="height: 40px; padding: 0 20px; border: none; border-radius: 20px; background: {LIMA}; color: {BG}; font-size: 14px; font-weight: 800">Following</button></div></div>'''
proximo = f'''<a href="Partido.dc.html" style="margin: 0 12px; padding: 14px 16px; border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; display: flex; align-items: center; gap: 12px">
<div style="display: flex; flex-direction: column; gap: 4px; flex-grow: 1"><span style="font-size: 11px; font-weight: 700; letter-spacing: 0.6px; color: {MUT}">NEXT · SAT 3 OCT · 18:00</span>
<span style="display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700">{franjas(KC, 16)}Croatia <span style="color: {MUT}">vs</span> England{franjas(KE, 16)}</span></div>
<span style="{DISP}; font-size: 26px; color: {KE["barra"]}">{p2}%</span></a>'''
cuerpo = HERO + pestañas("Overview", TABS_EQ) + proximo + FIFA_T \
    + tarjeta("Form", forma_eq_html(P[-5:]), "latest on the right") + FIN + GOL + MEJ
H_EQ = 1680
common.page("Equipo.dc.html", "England", 390, H_EQ, raiz(H_EQ, cuerpo), js_selectores(SEL_EQ), nav_active="f")

# ======================================================================= RECORD · England en el pasado
HI = N["historial"]
COMP = {"World Cup - Qualification Europe": "WC qualifying", "World Cup": "World Cup 2026", "UEFA Nations League": "Nations League",
        "Friendlies": "Friendlies"}
ORDEN_C = ["World Cup - Qualification Europe", "World Cup", "UEFA Nations League", "Friendlies"]


def res_col(gf, gc):
    return (LIMA, BG) if gf > gc else (("#3A4256", TXT) if gf == gc else (NARANJA, BG))


def fila_bal(b):
    return (f'<div style="display: flex; align-items: center; gap: 8px; padding: 10px 0; border-top: 1px solid #1E2330">'
            f'<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{COMP[b["comp"]]}</span>'
            f'<span style="width: 26px; text-align: right; font-size: 13px; color: {SOFT}">{b["pj"]}</span>'
            f'<span style="width: 26px; text-align: right; font-size: 13px; font-weight: 700; color: {LIMA}">{b["g"]}</span>'
            f'<span style="width: 26px; text-align: right; font-size: 13px; color: {SOFT}">{b["e"]}</span>'
            f'<span style="width: 26px; text-align: right; font-size: 13px; font-weight: 700; color: #FFB27A">{b["p"]}</span>'
            f'<span style="width: 58px; text-align: right; {DISP}; font-size: 16px">{b["gf"]}–{b["gc"]}</span></div>')


bal = sorted(HI["balance"], key=lambda b: ORDEN_C.index(b["comp"]))
CAB_BAL = (f'<div style="display: flex; gap: 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; color: {MUT}">'
           f'<span style="flex-grow: 1">COMPETITION</span><span style="width: 26px; text-align: right">P</span><span style="width: 26px; text-align: right">W</span>'
           f'<span style="width: 26px; text-align: right">D</span><span style="width: 26px; text-align: right">L</span><span style="width: 58px; text-align: right">GOALS</span></div>')
RESUMEN_HI = f'''<section style="position: relative; margin: 0 12px; padding: 18px 16px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden; display: flex; flex-direction: column; gap: 14px">
<span style="position: absolute; right: -60px; top: -80px; width: 240px; height: 240px; border-radius: 50%; background: #F1F3F8; opacity: 0.10; filter: blur(60px)"></span>
<div style="position: relative; display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 16px; font-weight: 700">Since March 2025</span><span style="font-size: 12px; color: {MUT}">{HI["pj"]} games</span></div>
<div style="position: relative; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="display: block; {DISP}; font-size: 32px; line-height: 1; color: {LIMA}">{HI["g"]}</span><span style="font-size: 12px; color: {MUT}">wins</span></div>
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="display: block; {DISP}; font-size: 32px; line-height: 1">{HI["e"]}</span><span style="font-size: 12px; color: {MUT}">draws</span></div>
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="display: block; {DISP}; font-size: 32px; line-height: 1; color: #FFB27A">{HI["p"]}</span><span style="font-size: 12px; color: {MUT}">defeats</span></div></div>
<div style="position: relative; display: flex; flex-direction: column">{CAB_BAL}{"".join(fila_bal(b) for b in bal)}</div></section>'''


COD_FIFA = {"Latvia": "LVA", "Congo DR": "COD", "Albania": "ALB", "Andorra": "AND", "Ghana": "GHA", "Panama": "PAN",
            "Mexico": "MEX", "Norway": "NOR", "Argentina": "ARG", "France": "FRA", "Croatia": "CRO", "Serbia": "SRB"}


def ficha(x, neutral=False):
    bg, fg = res_col(x["gf"], x["gc"])
    riv = COD_FIFA.get(x["riv"]) or (eq(x["riv"])[1] if x["riv"] in real_ui.EQ else x["riv"][:3].upper())
    pre = "" if neutral or x.get("casa", True) else "@"
    return (f'<div style="display: flex; flex-direction: column; align-items: center; gap: 5px">'
            f'<span style="width: 100%; height: 40px; border-radius: 11px; background: {bg}; color: {fg}; {DISP}; font-size: 16px; display: flex; align-items: center; justify-content: center">{x["gf"]}-{x["gc"]}</span>'
            f'<span style="font-size: 10px; font-weight: 700; color: {SOFT}">{pre}{riv}</span></div>')


CLAS = tarjeta("World Cup qualifying", f'''<div style="display: flex; align-items: center; gap: 14px">
<span style="{DISP}; font-size: 44px; line-height: 1; color: {LIMA}">8/8</span>
<span style="font-size: 14px; color: {SOFT}">Perfect: <b style="color: {TXT}">8 wins</b>, <b style="color: {TXT}">22 scored</b>, <b style="color: {TXT}">0 conceded</b></span></div>
<div style="display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 4px">{"".join(ficha(x) for x in HI["clasificacion"])}</div>''', "2025")

MUN = HI["mundial"]
g_m = sum(x["gf"] for x in MUN)
MUNDIAL = tarjeta("World Cup 2026", f'''<div style="display: flex; align-items: center; gap: 14px">
<span style="{DISP}; font-size: 44px; line-height: 1">{len(MUN)}</span>
<span style="font-size: 14px; color: {SOFT}">games · <b style="color: {TXT}">{g_m} goals</b> · beaten only by <b style="color: {TXT}">Argentina</b></span></div>
<div style="display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 4px">{"".join(ficha(x, True) for x in MUN)}</div>
<div style="display: flex; justify-content: space-between; font-size: 11px; color: {MUT}"><span>17 Jun</span><span>18 Jul</span></div>''', "Jun – Jul 2026")

DOM = HI["dominio"]
dom_filas = "".join(fila_stat(n_, DOM[k][0] * (100 if k == "Possession" else 1), DOM[k][1] * (100 if k == "Possession" else 1),
                              (lambda v: f"{v:.0f}%") if k == "Possession" else (lambda v: f"{v:.1f}"), KEN["barra"], "#5B6378")
                    for k, n_ in (("Possession", "Possession"), ("Shots on target", "Shots on target"),
                                  ("Big Chances Created", "Big chances"), ("Corners", "Corners")))
DOMINIO = tarjeta("How England play", f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span style="display: flex; align-items: center; gap: 6px">{franjas(KEN, 14)}England</span><span>per game</span><span>Opponents</span></div>' + dom_filas, "since 2025")

cs = HI["porterias_cero"]
PORTE = tarjeta("Clean sheets", f'''<div style="display: flex; align-items: center; gap: 18px">
<div style="position: relative; width: 110px; height: 110px; flex-shrink: 0">
<svg width="110" height="110" viewBox="0 0 120 120" role="img" aria-label="{cs} clean sheets in {HI["pj"]}"><circle cx="60" cy="60" r="48" fill="none" stroke="#232838" stroke-width="12"></circle><circle cx="60" cy="60" r="48" fill="none" stroke="{LIMA}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{cs / HI["pj"] * 302:.0f} 302" transform="rotate(-90 60 60)"></circle></svg>
<span style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; {DISP}; font-size: 30px">{cs}/{HI["pj"]}</span></div>
<div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: {SOFT}"><span><b style="color: {TXT}">{round(cs / HI["pj"] * 100)}%</b> of games without conceding</span>
<span>Only <b style="color: {TXT}">{HI["gc"]}</b> goals against in {HI["pj"]} games</span><span>0 conceded in qualifying</span></div></div>''', "since 2025")


def linea_res(x, verde):
    riv = eq(x["riv"])[0] if x["riv"] in real_ui.EQ else x["riv"]
    comp = COMP.get(x["comp"], x["comp"])
    return (f'<div style="display: flex; align-items: center; gap: 10px; padding: 8px 0; border-top: 1px solid #1E2330">'
            f'<span style="width: 52px; {DISP}; font-size: 18px; color: {LIMA if verde else "#FFB27A"}">{x["gf"]}–{x["gc"]}</span>'
            f'<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{"" if x.get("casa", True) else "at "}{riv}</span>'
            f'<span style="font-size: 11px; color: {MUT}">{comp} · {x["fecha"][:4]}</span></div>')


EXTREMOS = tarjeta("Biggest wins", "".join(linea_res(x, True) for x in HI["mayores"]), "since 2025") \
    + tarjeta("The 4 defeats", "".join(linea_res(x, False) for x in HI["derrotas"]), "since 2025")
HERO_HI = f'''<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: 50%; top: -70px; width: 300px; height: 260px; margin-left: -150px; border-radius: 50%; background: #F1F3F8; opacity: 0.16; filter: blur(70px)"></span>
{volver("Equipo.dc.html", "", "")}
<div style="position: relative; display: flex; align-items: center; gap: 14px; padding: 0 16px 14px 16px">{escudo("England", 56)}
<div style="display: flex; flex-direction: column"><span style="{DISP}; font-size: 30px; line-height: 1">England</span><span style="font-size: 13px; color: {SOFT}">FIFA 4th · record</span></div></div></div>'''
cuerpo = HERO_HI + pestañas("Record", TABS_EQ) + RESUMEN_HI + CLAS + MUNDIAL + DOMINIO + PORTE + EXTREMOS
H_HI = 2040
common.page("Historial.dc.html", "England record", 390, H_HI, raiz(H_HI, cuerpo), JS0, nav_active="f")

# ======================================================================= GROUPS + FIFA
def tabla_grupo(g):
    filas = ""
    for i, t in enumerate(g["tabla"]):
        k = kit(t["equipo"])
        yo = t["equipo"] == "England"
        dg = t["gf"] - t["gc"]
        filas += (f'<div style="display: flex; align-items: center; gap: 6px; min-height: 42px; padding: 0 12px; border-top: 1px solid #1E2330; background: {"#141A33" if yo else "transparent"}">'
                  f'<span style="width: 16px; {DISP}; font-size: 14px; color: {LIMA if i == 0 else TXT}">{i + 1}</span>{franjas(k, 20)}'
                  f'<span style="flex-grow: 1; min-width: 0; padding-left: 4px; font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{eq(t["equipo"])[0]}</span>'
                  + "".join(f'<span style="width: 18px; text-align: right; font-size: 12px; color: {SOFT}">{t[c_]}</span>' for c_ in ("pj", "g", "e", "p"))
                  + f'<span style="width: 26px; text-align: right; font-size: 12px; color: {SOFT}">{"+" if dg > 0 else ""}{dg}</span>'
                  f'<span style="width: 26px; text-align: right; {DISP}; font-size: 15px">{t["pts"]}</span>'
                  f'<span style="width: 34px; text-align: right; font-size: 11px; color: {MUT}">{ordinal(t["fifa"])}</span></div>')
    cab = (f'<div style="display: flex; align-items: center; gap: 6px; padding: 12px 12px 8px 12px; font-size: 9.5px; letter-spacing: 0.3px; color: {MUT}">'
           f'<span style="flex-grow: 1; font-size: 14px; font-weight: 700; letter-spacing: 0; color: {TXT}">{g["nombre"]}</span>'
           + "".join(f'<span style="width: 18px; text-align: right">{h_}</span>' for h_ in ("P", "W", "D", "L"))
           + '<span style="width: 26px; text-align: right">GD</span><span style="width: 26px; text-align: right">PTS</span><span style="width: 34px; text-align: right">FIFA</span></div>')
    return f'<section style="margin: 0 12px; border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">{cab}{filas}</section>'


GRUPOS = '<div style="display: flex; flex-direction: column; gap: 12px">' + "".join(tabla_grupo(g) for g in N["grupos"]) \
    + f'<span style="padding: 0 16px; font-size: 11px; color: {MUT}">Matchday 3: 1–3 Oct.</span></div>'
filas_f = ""
for f in N["fifa"]:
    nombre = next((k for k, v in real_ui.EQ.items() if v[1] == f["codigo"]), f["equipo"])
    k = kit(nombre)
    c_ = f["cambio"]
    filas_f += (f'<div style="display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 0 14px; border-top: 1px solid #1E2330; background: {"#141A33" if f["equipo"] == "England" else "transparent"}">'
                f'<span style="width: 22px; {DISP}; font-size: 15px">{f["puesto"]}</span>{franjas(k, 22)}'
                f'<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{f["equipo"]}</span>'
                f'<span style="width: 34px; text-align: right; font-size: 12px; font-weight: 700; color: {LIMA if c_ > 0 else ("#FFB27A" if c_ < 0 else MUT)}">{"▲" + str(c_) if c_ > 0 else ("▼" + str(-c_) if c_ < 0 else "–")}</span>'
                f'<span style="width: 54px; text-align: right; {DISP}; font-size: 16px">{int(f["puntos"])}</span></div>')
FIFA = (f'<section style="margin: 0 12px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">'
        f'<div style="display: flex; align-items: center; gap: 10px; padding: 12px 14px 8px 14px; font-size: 10px; letter-spacing: 0.4px; color: {MUT}">'
        f'<span style="width: 22px">#</span><span style="width: 8px"></span><span style="flex-grow: 1">TEAM</span><span style="width: 34px; text-align: right">MOVE</span><span style="width: 54px; text-align: right">POINTS</span></div>'
        f'{filas_f}<div style="padding: 10px 14px 12px 14px; border-top: 1px solid #1E2330; font-size: 11px; color: {MUT}">Published {fecha(N["fifa_fecha"])} {N["fifa_fecha"][:4]} · next 7 Oct</div></section>')
TABS_G = f'''<nav aria-label="Tables" style="margin: 0 12px; padding: 4px; border-radius: 22px; background: {SUB}; display: flex; gap: 4px">
<sc-for list="{{{{sel_tabla}}}}" as="o" hint-placeholder-count="2"><button onClick="{{{{o.pick}}}}" style="flex: 1 1 0; height: 38px; border: none; border-radius: 18px; background: {{{{o.bg}}}}; color: {{{{o.fg}}}}; font-size: 13px; font-weight: 800">{{{{o.txt}}}}</button></sc-for></nav>
<sc-if value="{{{{tabla.grupos}}}}" hint-placeholder-val="{{{{ true }}}}">{GRUPOS}</sc-if>
<sc-if value="{{{{tabla.fifa}}}}" hint-placeholder-val="{{{{ false }}}}">{FIFA}</sc-if>'''
SEL_G = {"tabla": {"opts": [["grupos", "League A groups"], ["fifa", "FIFA ranking"]], "ini": "grupos",
                   "vals": {"grupos": {"grupos": True, "fifa": False}, "fifa": {"grupos": False, "fifa": True}}}}
HEAD = f'''<header style="display: flex; flex-direction: column; gap: 6px; padding: 20px 16px 0 16px">
<span style="font-size: 12px; font-weight: 700; letter-spacing: 1px; color: {LIMA}">NATIONS LEAGUE</span>
<span style="{DISP}; font-size: 38px; line-height: 1">Standings</span>
<span style="font-size: 13px; color: {SOFT}">League A after matchday 2.</span></header>'''
H_G = 1480
common.page("Elo.dc.html", "Standings", 390, H_G, raiz(H_G, HEAD + TABS_G), js_selectores(SEL_G), nav_active="e")

# ======================================================================= TIPS
TOPI = f'''<section style="position: relative; margin: 0 12px; padding: 18px; border-radius: 28px; background: {CARD}; border: 1px solid #262C3B; overflow: hidden; display: flex; flex-direction: column; gap: 14px">
<span style="position: absolute; right: -50px; top: -60px; width: 200px; height: 200px; border-radius: 50%; background: {KE["barra"]}; opacity: 0.14; filter: blur(50px)"></span>
<div style="position: relative; display: flex; justify-content: space-between; align-items: center">{chip("YOUR TEAM", "#1E2A66", "#A9B8FF")}<span style="font-size: 12px; color: {SOFT}">Sat 3 Oct · 18:00</span></div>
<div style="position: relative; display: flex; align-items: center; gap: 8px">{escudo("Croatia", 26, KC)}<span style="font-size: 15px; font-weight: 700">Croatia – England</span>{escudo("England", 26, KE)}</div>
<div style="position: relative; display: flex; flex-direction: column">
{"".join(f'<div style="display: flex; align-items: center; gap: 10px; padding: 9px 0; border-top: 1px solid #1E2330"><span style="flex-grow: 1; font-size: 14px; font-weight: 600">{t}</span>{confianza(v)}<span style="{DISP}; font-size: 22px; color: {LIMA}; width: 50px; text-align: right">{int(v)}%</span></div>' for t, v in (("England to win", p2), ("Over 1.5 goals", PV["mas15"]), ("Over 2.5 goals", PV["mas25"]), ("Both teams score", PV["btts"])))}</div>
<div style="position: relative; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
{"".join(f'<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Fair odds · {k}</span><span style="{DISP}; font-size: 20px">{100 / v:.2f}</span></div>' for k, v in (("1", p1), ("X", px), ("2", p2)))}</div></section>'''


def chip_odds(o):
    return chip(f"best odds {o:.2f}") if o else ""


def tip(t):
    kl, kv = kits(t["local"], t["visitante"])
    d = t["p"] - t["casa"]
    acuerdo = chip("Bookies agree", "#1E2330", SOFT) if abs(d) < 4 else (chip(f"We see {abs(int(d))} pts more", "#1F3A16", LIMA) if d > 0 else chip(f"We see {abs(int(d))} pts less", "#3A2412", "#FFB27A"))
    return (f'<div style="margin: 0 12px; padding: 14px 16px; border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; display: flex; align-items: center; gap: 14px">'
            f'<div style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px"><span style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: {MUT}">{franjas(kl, 12)}{eq(t["local"])[0]} – {eq(t["visitante"])[0]}{franjas(kv, 12)}</span>'
            f'<span style="font-size: 16px; font-weight: 700">{t["pick"].replace("Kosovo National Team", "Kosovo").replace("Republic of Ireland", "Ireland")}</span>'
            f'<div style="display: flex; gap: 6px; flex-wrap: wrap">{acuerdo}{chip_odds(t["mejor"])}</div></div>'
            f'<span style="{DISP}; font-size: 36px; line-height: 1; color: {LIMA}">{int(t["p"])}<span style="font-size: 18px">%</span></span></div>')


ACI_T = tarjeta("How we did", '<div style="display: grid; grid-template-columns: minmax(0, 1fr) 70px 70px; gap: 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; color: {MUT}"><span>MARKET</span><span style="text-align: right">2YELLOW</span><span style="text-align: right">BOOKIES</span></div>'.replace("{MUT}", MUT)
                + "".join(f'<div style="display: grid; grid-template-columns: minmax(0, 1fr) 70px 70px; gap: 8px; align-items: center; padding: 8px 0; border-top: 1px solid #1E2330">'
                          f'<span style="font-size: 13px; font-weight: 600">{m["mercado"]}</span><span style="text-align: right; {DISP}; font-size: 17px; color: {LIMA if m["nuestro"] >= m["casa"] else TXT}">{int(m["nuestro"])}%</span>'
                          f'<span style="text-align: right; {DISP}; font-size: 17px">{int(m["casa"])}%</span></div>' for m in ACI["mercados"])
                + f'<span style="font-size: 11px; color: {MUT}">Favourite side right · {ACI["n"]} Nations League games.</span>', "so far")
cuerpo = (f'<header style="display: flex; align-items: center; gap: 10px; padding: 18px 12px 0 16px"><span style="flex-grow: 1; {DISP}; font-size: 34px">Tips</span>{chip("Nations League", "#12204F", "#A9B8FF")}</header>'
          + TOPI + f'<div style="padding: 6px 16px 0 16px; font-size: 18px; font-weight: 700">Thursday 1 Oct</div>' + "".join(tip(t) for t in N["tips"]) + ACI_T)
H_T = 1600
common.page("Tips.dc.html", "Tips", 390, H_T, raiz(H_T, cuerpo), JS0, nav_active="t")

# ---------------------------------------------------------------- lienzo
tablero = [("Main.dc.html", "1 · Matches", H_MAIN), ("Partido.dc.html", "2 · Preview · Croatia–England", H_PV),
           ("Report.dc.html", "3 · Report · Czechia 0-2 England", H_REP), ("Alineacion.dc.html", "4 · Report lineups", H_AL),
           ("Equipo.dc.html", "5 · Team · England", H_EQ), ("Historial.dc.html", "6 · England record", H_HI), ("Elo.dc.html", "7 · Standings", H_G), ("Tips.dc.html", "8 · Tips", H_T)]
canvas = {"v": 3, "createdOnFiles": {"v": 1, "at": "2026-09-30T20:00:00Z"}, "title": "2yellow · Nations League",
          "launch": {"view": "canvas"}, "pages": [],
          "boards": {f: {"x": i * 470, "y": 0, "w": 390, "h": h, "title": t, "is_interactive": True, "radius": 36} for i, (f, t, h) in enumerate(tablero)},
          "order": [f for f, _, _ in tablero],
          "notes": {"titulo": {"x": 0, "y": -260, "text": "2yellow · Nations League · England", "kind": "title1", "maxW": 3200}},
          "designSystems": []}
(AQUI.parent / "project" / "canvas.json").write_text(json.dumps(canvas, ensure_ascii=False))
print("nl ok")
