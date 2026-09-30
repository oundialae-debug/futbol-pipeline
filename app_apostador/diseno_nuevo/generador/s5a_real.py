"""Partidos (portada) y previa Real Madrid – Villarreal, con datos reales."""
from common import page
from real_ui import *


def raiz(h, cuerpo, gap=14):
    return (f'<div style="position: relative; width: 390px; height: {h}px; box-sizing: border-box; background: {BG}; '
            f'overflow: hidden; display: flex; flex-direction: column; gap: {gap}px; padding-bottom: 100px">{cuerpo}@@NAV@@</div>')


JS0 = "class Component extends DCLogic {\n  renderVals() { return {}; }\n}"

# ======================================================================= MATCHES
res = D["resultados"]
dest = [r_ for r_ in res if r_["local"] == "Atlético Madrid"] + [r_ for r_ in res if r_["local"] in ("Athletic Club", "Espanyol")]


def veredicto(r_):
    m = r_["merecido"]
    gana = "l" if r_["gl"] > r_["gv"] else ("v" if r_["gv"] > r_["gl"] else "x")
    top = max(range(3), key=lambda i: m[i])
    quien = ["l", "x", "v"][top]
    if quien == gana:
        return ("Deserved", "#1F3A16", LIMA)
    return ("Robbery" if gana != "x" else "Should have won", "#3A2412", "#FFB27A")


def carta_resultado(r_):
    cl, cv = eq(r_["local"])[0], eq(r_["visitante"])[0]
    kl, kv = kits(r_["local"], r_["visitante"])
    txt, cb, cf = veredicto(r_)
    href = "Report.dc.html" if r_["local"] == "Atlético Madrid" else "#"
    m = r_["merecido"]
    return f'''<a href="{href}" style="position: relative; flex-shrink: 0; width: 304px; height: 226px; box-sizing: border-box; border-radius: 26px; background: {CARD}; border: 1px solid #262C3B; overflow: hidden; display: block">
{glow(kl["barra"], kv["barra"], 170)}
<div style="position: relative; display: flex; flex-direction: column; gap: 12px; padding: 14px 16px">
<div style="display: flex; justify-content: space-between; align-items: center"><span style="font-size: 12px; font-weight: 600; color: {SOFT}">LaLiga · FT</span>{chip(txt, cb, cf)}</div>
<div style="display: flex; align-items: center; justify-content: space-between">
<div style="width: 86px; display: flex; flex-direction: column; align-items: center; gap: 6px">{escudo(r_["local"], 44, kl)}<span style="display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600">{franjas(kl, 14)}{cl}</span></div>
<span style="{DISP}; font-size: 46px; line-height: 1">{r_["gl"]} – {r_["gv"]}</span>
<div style="width: 86px; display: flex; flex-direction: column; align-items: center; gap: 6px">{escudo(r_["visitante"], 44, kv)}<span style="display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600">{cv}{franjas(kv, 14)}</span></div>
</div>
<div style="display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span>xG <b style="color: {TXT}">{num(r_["xg"][0])}</b></span><span>chances say</span><span><b style="color: {TXT}">{num(r_["xg"][1])}</b> xG</span></div>
<div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; gap: 2px"><span style="width: {m[0]}%; background: {kl["barra"]}"></span><span style="width: {m[1]}%; background: #3A4256"></span><span style="width: {m[2]}%; background: {kv["barra"]}"></span></div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span>Elo <b style="color: {kl["barra"]}">{'+' if r_["elo_cambio"] >= 0 else ''}{int(r_["elo_cambio"])}</b></span><span>Before: {int(r_["prev"][0])}% · {int(r_["prev"][1])}% · {int(r_["prev"][2])}%</span><span><b style="color: {kv["barra"]}">{'+' if -r_["elo_cambio"] >= 0 else ''}{int(-r_["elo_cambio"])}</b> Elo</span></div>
</div></a>'''


j8 = DJ["jornada8"]
DIAS = {"2026-10-09": "FRIDAY 9 OCT", "2026-10-10": "SATURDAY 10 OCT", "2026-10-11": "SUNDAY 11 OCT", "2026-10-12": "MONDAY 12 OCT"}


def hora(utc):
    hh, mm = utc.split(":")
    return f"{int(hh) + 2:02d}:{mm}"


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def fila_j8(p):
    loc, vis = p["local"], p["visitante"]
    kl, kv = kits(loc, vis)
    tag = ""
    for eqn, tab, fz in ((loc, p["local_tabla"], p["local_fuerza"]), (vis, p["vis_tabla"], p["vis_fuerza"])):
        if fz - tab >= 5:
            tag = chip(f"{eq(eqn)[0]} worse than table: Elo {ordinal(fz)}", "#3A2412", "#FFB27A")
        elif tab - fz >= 5 and not tag:
            tag = chip(f"{eq(eqn)[0]} better than table: Elo {ordinal(fz)}", "#1E2A66", "#A9B8FF")
    if max(p["p1"], p["px"], p["p2"]) <= 36:
        tag = chip("Coin flip", "#1E2330", SOFT)
    if kv["segunda"]:
        tag += " " + chip(f"{eq(vis)[0]} in away kit", "#1E2330", SOFT)
    href = "Partido.dc.html" if loc == "Real Madrid" else "#"
    if loc == "Real Madrid":
        tag = chip("Over 2.5 · 70%", "#26301A", LIMA) + " " + chip("4.4 cards expected", "#3A2412", "#FFB27A")
    mx = max(p["p1"], p["px"], p["p2"])

    def caja(v, lab, k):
        on = v == mx
        bg = (k["barra"] if k else "#3A4256") if on else SUB
        fg = (k["texto"] if k else TXT) if on else TXT
        return (f'<div style="padding: 5px 0; border-radius: 9px; background: {bg}; color: {fg}"><span style="display: block; {DISP}; font-size: 14px">{v}%</span>'
                f'<span style="font-size: 9px; opacity: 0.75">{lab}</span></div>')
    return f'''<a href="{href}" style="display: flex; flex-direction: column; gap: 10px; padding: 13px 14px; border-top: 1px solid #1E2330">
<div style="display: flex; align-items: center; gap: 12px">
<span style="width: 46px; {DISP}; font-size: 15px">{hora(p["hora_utc"])}</span>
<div style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 7px">
<div style="display: flex; align-items: center; gap: 8px">{franjas(kl)}<span style="font-size: 15px; font-weight: 600">{eq(loc)[0]}</span></div>
<div style="display: flex; align-items: center; gap: 8px">{franjas(kv)}<span style="font-size: 15px; font-weight: 600">{eq(vis)[0]}</span></div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, 44px); gap: 4px; text-align: center">{caja(p["p1"], "1", kl)}{caja(p["px"], "X", None)}{caja(p["p2"], "2", kv)}</div></div>
{f'<div style="margin-left: 58px; display: flex; gap: 6px; flex-wrap: wrap">{tag}</div>' if tag else ''}
</a>'''


bloques = []
for dia, nombre in DIAS.items():
    ps = [p for p in j8 if p["fecha"] == dia]
    bloques.append(f'<div style="display: flex; align-items: center; padding: 10px 14px 4px 14px; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; color: {MUT}">'
                   f'<span style="flex-grow: 1">{nombre}</span><span style="width: 140px; text-align: center; letter-spacing: 0.4px">WIN CHANCE · 1 X 2</span></div>' + "".join(fila_j8(p) for p in ps))

pr = DJ["pronosticos"]["real_madrid_villarreal"]
casa = DJ["pronosticos"]["acierto_casa"]
tips_home = [("Real Madrid – Villarreal", "Over 1.5 goals", round(pr["mas15"])),
             ("Real Madrid – Villarreal", "Madrid or draw", 87),
             ("Real Madrid – Villarreal", "Over 2.5 goals", round(pr["mas25"]))]

cuerpo = f'''
<header style="display: flex; align-items: center; gap: 10px; padding: 18px 12px 0 16px">
<a href="Main.dc.html" aria-label="2yellow home" style="flex-grow: 1; display: flex; align-items: center; gap: 6px">{icono(38, "hdr")}{palabra(27)}</a>
<button aria-label="Search" style="width: 44px; height: 44px; border: none; border-radius: 22px; background: #161A23; color: {TXT}; display: flex; align-items: center; justify-content: center"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.5-3.5"></path></svg></button>
</header>
<div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px 0 16px"><span style="font-size: 18px; font-weight: 700">Latest results</span><span style="font-size: 12px; color: {MUT}">LaLiga · matchday 7</span></div>
<div style="display: flex; gap: 12px; padding: 0 16px; overflow: hidden">{"".join(carta_resultado(r_) for r_ in dest)}</div>
<section style="margin: 0 12px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">
<div style="display: flex; align-items: center; gap: 10px; padding: 14px 14px 6px 14px">
<span style="width: 30px; height: 30px; border-radius: 10px; background: {AZUL}; {DISP}; font-size: 12px; display: flex; align-items: center; justify-content: center">LL</span>
<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 15px; font-weight: 700">LaLiga</span><span style="font-size: 12px; color: {MUT}">Matchday 8</span></div>
</div>
{"".join(bloques)}
</section>
<div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 16px 0 16px"><span style="font-size: 18px; font-weight: 700">Top tips</span><a href="Tips.dc.html" style="font-size: 13px; font-weight: 600; color: #8FA2FF">All tips</a></div>
<div style="display: flex; gap: 10px; padding: 0 16px; overflow: hidden">
{"".join(f'<a href="Tips.dc.html" style="flex-shrink: 0; width: 176px; box-sizing: border-box; padding: 14px; border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; display: flex; flex-direction: column; gap: 6px"><span style="font-size: 12px; color: {MUT}">{a}</span><span style="font-size: 15px; font-weight: 700">{b}</span><span style="{DISP}; font-size: 40px; line-height: 1; color: {LIMA}">{c}<span style="font-size: 22px">%</span></span><span style="display: flex">{confianza(c)}</span></a>' for a, b, c in tips_home)}
</div>
'''
page("Main.dc.html", "Matches", 390, 1880, raiz(1880, cuerpo), JS0, nav_active="m")

# ======================================================================= PREVIEW RMA – VIL
p8 = [p for p in j8 if p["local"] == "Real Madrid"][0]
KL, KV = kits("Real Madrid", "Villarreal")
baj = D["bajas"]
term = D["termometro"]
rot = D["rotacion"]
est = D["estilos"]
tab = {f["equipo"]: f for f in D["tabla_elo"]["filas"]}
am = D["amarillas"]["equipos"]


B2 = DX["bajas2"]
MESES = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
         "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}


def fecha_corta(iso):
    return f"{int(iso[8:])} {MESES[iso[5:7]]}" if iso else ""


def baja_fila(x, k):
    motivo = {"Red card": "Red card · suspended", "5 yellows": "5 yellows · suspended"}.get(x["motivo"], x["motivo"])
    cuando = f" · back {fecha_corta(x['vuelve'])}" if x["vuelve"] else ""
    return (f'<div style="display: flex; align-items: center; gap: 10px">{franjas(k, 22)}'
            f'<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 600">{x["jugador"]}</span>'
            f'<span style="font-size: 12px; color: {MUT}">{motivo}{cuando}</span></div>'
            f'<span style="{DISP}; font-size: 16px; color: {k["barra"]}">{int(x["pct_ga"] or 0)}%</span></div>')


def bajas_bloque(titulo, clave, color):
    filas = [baja_fila(x, KL) for x in B2["Real Madrid"][clave]] + [baja_fila(x, KV) for x in B2["Villarreal"][clave]]
    if not filas:
        filas = [f'<span style="font-size: 13px; color: {MUT}">None</span>']
    return (f'<div style="display: flex; flex-direction: column; gap: 10px"><div style="display: flex; align-items: center; gap: 8px">'
            f'<span style="width: 8px; height: 8px; border-radius: 50%; background: {color}"></span><span style="font-size: 13px; font-weight: 800; letter-spacing: 0.6px">{titulo}</span>'
            f'<span style="margin-left: auto; font-size: 11px; color: {MUT}">share of G+A</span></div>' + "".join(filas) + '</div>')


BAJAS_HTML = tarjeta("Missing players", bajas_bloque("OUT", "fuera", ROJO) + '<div style="height: 1px; background: #1E2330"></div>'
                     + bajas_bloque("DOUBTFUL", "duda", AMARILLO), "Sat 10 Oct")

E2 = DX["estilos2"]
ESTILO_4 = [("Possession", "%"), ("Passes", ""), ("Long shots", ""), ("Interceptions", "")]


def estilo_html():
    tags = ""
    for n, k in (("Real Madrid", KL), ("Villarreal", KV)):
        tags += (f'<div style="display: flex; flex-direction: column; gap: 6px"><div style="display: flex; align-items: center; gap: 8px">{franjas(k, 18)}<span style="font-size: 13px; font-weight: 700">{eq(n)[0]}</span></div>'
                 f'<div style="display: flex; gap: 6px; flex-wrap: wrap">' + "".join(chip(t, "#1E2330", TXT) for t in E2["equipos"][n]["tags"]) + '</div></div>')
    filas = ""
    for m, u in ESTILO_4:
        a, b, lg = E2["equipos"]["Real Madrid"][m], E2["equipos"]["Villarreal"][m], E2["media"][m]
        fmt = (lambda v: f"{v:.0f}%") if u else ((lambda v: f"{v:.0f}") if m == "Passes" else (lambda v: f"{v:.1f}"))
        filas += (fila_stat(m + " per game" if m != "Possession" else m, a, b, fmt, KL["barra"], KV["barra"])
                  + f'<span style="margin-top: -4px; text-align: center; font-size: 11px; color: {MUT}">LaLiga average {fmt(lg)}</span>')
    return tags + '<div style="height: 1px; background: #1E2330"></div>' + filas


T_ESP, T_P45, T_LIGA, T_EST, T_SUA = term["esperadas"], int(term["p_mas45"]), term["media_liga"], term["con_arbitro_estricto"], term["con_arbitro_suave"]
T_DASH = round(T_ESP / 8 * 302)
TERM_HTML = tarjeta("Cards thermometer", (
    f'<div style="display: flex; align-items: center; gap: 16px">'
    f'<div style="position: relative; width: 120px; height: 120px; flex-shrink: 0">'
    f'<svg width="120" height="120" viewBox="0 0 120 120" role="img" aria-label="{T_ESP} cards expected"><circle cx="60" cy="60" r="48" fill="none" stroke="#232838" stroke-width="12"></circle><circle cx="60" cy="60" r="48" fill="none" stroke="{AMARILLO}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{T_DASH} 302" transform="rotate(-90 60 60)"></circle></svg>'
    f'<div style="position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center"><span style="{DISP}; font-size: 32px; line-height: 1">{T_ESP}</span><span style="font-size: 11px; color: {MUT}">cards</span></div></div>'
    f'<div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: {SOFT}">'
    f'<span>Over 4.5 cards: <b style="color: {TXT}">{T_P45}%</b></span>'
    f'<span>League average: <b style="color: {TXT}">{T_LIGA:.1f}</b></span>'
    f'<span>Referee not named yet. Strict one: <b style="color: {TXT}">{T_EST}</b> · lenient: <b style="color: {TXT}">{T_SUA}</b></span>'
    f'</div></div>'
    f'<div style="display: flex; gap: 6px; flex-wrap: wrap">{chip("Konaté 3 yellows", "#3A2F0A", AMARILLO)}{chip("Vinícius, Camavinga 2", "#1E2330", SOFT)}{chip("Foyth, Veiga, Mouriño, Buchanan 2", "#1E2330", SOFT)}</div>'), "teams + referee")


def rot_caja(n):
    x = rot[n]
    return (f'<div style="padding: 12px; border-radius: 16px; background: {SUB}; display: flex; flex-direction: column; gap: 6px">'
            f'<div style="display: flex; align-items: center; gap: 8px">{franjas(KL if n == "Real Madrid" else KV)}<span style="font-size: 13px; font-weight: 700">{eq(n)[0]}</span></div>'
            f'<span style="{DISP}; font-size: 26px; line-height: 1; color: {(KL if n == "Real Madrid" else KV)["barra"]}">{x["media_cambios"]}</span>'
            f'<span style="font-size: 11px; color: {MUT}">changes to the XI per match</span>'
            f'<span style="font-size: 12px; color: {SOFT}">After ≤4 days: <b style="color: {(KL if n == "Real Madrid" else KV)["barra"]}">{x["corto"]}</b></span></div>')


ROT_HTML = tarjeta("Rest &amp; rotation",
    '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">' + rot_caja("Real Madrid") + rot_caja("Villarreal") + '</div>'
    + f'<span style="font-size: 12px; color: {MUT}">Both rested {rot["Real Madrid"]["dias_hasta_previa"]} days.</span>', "league games")

cuerpo = f'''
<div style="position: relative; display: flex; flex-direction: column; padding-bottom: 14px">
{glow(KL["barra"], KV["barra"], 230)}
{volver("Main.dc.html", "LaLiga · Matchday 8", "Sat 10 Oct · 21:00 · Santiago Bernabéu")}
<div style="position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px 0 16px">
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("Real Madrid", 62, KL)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">{franjas(KL, 16)}Real Madrid</span><span style="font-size: 12px; color: {SOFT}">4th · Elo 2nd</span></div>
<div style="display: flex; flex-direction: column; align-items: center; gap: 6px; padding-top: 8px"><span style="{DISP}; font-size: 44px; line-height: 1">21:00</span>{chip("Preview", "#1E2A66", "#A9B8FF")}</div>
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("Villarreal", 62, KV)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">Villarreal{franjas(KV, 16)}</span><span style="font-size: 12px; color: {SOFT}">9th · Elo 4th</span></div>
</div></div>
{pestañas("Preview", [("Preview", "Partido.dc.html"), ("Tips", "Tips.dc.html"), ("H2H", "#"), ("Report", "Report.dc.html")])}
{tarjeta("Win chance", tres(p8["p1"], p8["px"], p8["p2"], (KL["barra"], KL["texto"]), (KV["barra"], KV["texto"])) +
 f'<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">' +
 "".join(f'<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Fair odds · {k}</span><span style="{DISP}; font-size: 20px">{v:.2f}</span></div>' for k, v in (("1", p8["justa1"]), ("X", p8["justax"]), ("2", p8["justa2"]))) + '</div>'
 + f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span>Elo <b style="color: {KL["barra"]}">{int(tab["Real Madrid"]["elo"])}</b></span><span>by strength, not by table</span><span><b style="color: {KV["barra"]}">{int(tab["Villarreal"]["elo"])}</b> Elo</span></div>', "by Elo")}
{BAJAS_HTML}
{TERM_HTML}
{ROT_HTML}
{tarjeta("Style clash", estilo_html(), "since 2025/26")}
'''
page("Partido.dc.html", "Real Madrid – Villarreal preview", 390, 1950, raiz(1950, cuerpo), JS0, nav_active="m")
print("s5a ok")
