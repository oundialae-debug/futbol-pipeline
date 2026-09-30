"""Equipo (Real Madrid), jugador (Mbappé), tabla Elo de la liga y tips, con datos reales."""
from common import page
from real_ui import *
from s5a_real import raiz, JS0

RANGOS = [["l5", "Last 5"], ["l10", "Last 10"], ["season", "Season"]]
KRM = kequipo("Real Madrid")
TAB = {f["equipo"]: f for f in D["tabla_elo"]["filas"]}
RM = TAB["Real Madrid"]


def signo(x, dec=1):
    return ("+" if x >= 0 else "−") + f"{abs(x):.{dec}f}"


def cinco(n):
    return "".join(f'<span style="width: 10px; height: 14px; border-radius: 2px; background: {AMARILLO if i < n else "#2A3040"}"></span>' for i in range(5))


def lista(filas):
    return '<div style="display: flex; flex-direction: column; gap: 10px">' + "".join(filas) + "</div>"


# ======================================================================= TEAM · Real Madrid
forma = D["equipo"]["forma"][-5:]
FORMA = tarjeta("Form", '<div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px">' + "".join(
    f'<div style="display: flex; flex-direction: column; align-items: center; gap: 5px">'
    f'<span style="width: 100%; height: 44px; border-radius: 12px; background: {LIMA if f["gf"] > f["gc"] else ("#3A4256" if f["gf"] == f["gc"] else NARANJA)}; '
    f'color: {BG if f["gf"] != f["gc"] else TXT}; {DISP}; font-size: 17px; display: flex; align-items: center; justify-content: center">{f["gf"]}-{f["gc"]}</span>'
    f'<span style="font-size: 10px; color: {MUT}">{eq(f["riv"])[1]}{"" if f["casa"] else " (a)"}</span>'
    f'<span style="font-size: 11px; font-weight: 700; color: {LIMA if f["elo_cambio"] >= 0 else "#FFB27A"}">Elo {signo(f["elo_cambio"], 0)}</span></div>' for f in forma) + "</div>",
    "latest on the right")

ELO_T = tarjeta("Elo rating", f'''<div style="display: flex; align-items: center; gap: 16px">
<div style="display: flex; flex-direction: column"><span style="{DISP}; font-size: 48px; line-height: 1; color: {KRM["barra"]}">{int(RM["elo"])}</span><span style="font-size: 12px; color: {MUT}">2nd in the 2yellow Ranking</span></div>
<div style="margin-left: auto">{sparkline(RM["elo_hist"], 150, 60)}</div></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Table</span><span style="{DISP}; font-size: 20px">4th · {RM["pts"]} pts</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Elo points</span><span style="{DISP}; font-size: 20px">{RM["xpts"]}</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Luck</span><span style="{DISP}; font-size: 20px">{signo(RM["suerte"])}</span></div></div>
''', "strength, not points")

cs = D["con_sin"]["Real Madrid"]["lista"]
top_cs = [c for c in cs if c["sin_n"] >= 8][:3] + [c for c in cs if c["sin_n"] >= 8][-2:]


def cs_fila(c):
    col = LIMA if c["efecto"] >= 0 else "#FFB27A"
    return (f'<div style="display: flex; align-items: center; gap: 10px"><div style="flex-grow: 1; display: flex; flex-direction: column">'
            f'<span style="font-size: 14px; font-weight: 700">{c["jugador"]}</span>'
            f'<span style="font-size: 12px; color: {MUT}">With {c["con_pts"]:.2f} pts ({c["con_n"]}) · without {c["sin_pts"]:.2f} ({c["sin_n"]})</span></div>'
            f'{pocos() if min(c["con_n"], c["sin_n"]) < 20 else ""}<span style="{DISP}; font-size: 20px; color: {col}">{signo(c["efecto"], 2)}</span></div>')


CONSIN = tarjeta("With him / without him", lista([cs_fila(c) for c in top_cs])
                 + f'<span style="font-size: 12px; color: {MUT}">Points per game vs Elo, with / without him.</span>', "since 2024/25")

sp = DX["segundas2"]["Real Madrid"]


def barra_pts(txt, v, top, color, fg):
    return (f'<div style="display: flex; flex-direction: column; gap: 5px"><div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}">'
            f'<span>{txt}</span><span style="{DISP}; font-size: 17px; color: {fg}">{v} pts</span></div>'
            f'<div style="height: 12px; border-radius: 6px; background: #1E2330"><div style="width: {v / top * 100:.0f}%; height: 12px; border-radius: 6px; background: {color}"></div></div></div>')


SEGUNDAS = tarjeta("Second halves", barra_pts("If every game had ended at half-time", sp["pts_ht"], sp["pts_ft"], "#3A4256", SOFT)
                   + barra_pts("What they really got", sp["pts_ft"], sp["pts_ft"], KRM["barra"], KRM["barra"])
                   + f'''<div style="display: flex; align-items: center; gap: 10px"><span style="{DISP}; font-size: 30px; color: {LIMA}">+{sp["dif"]}</span>
<span style="font-size: 13px; color: {SOFT}">points after the break · <b style="color: {TXT}">{sp["rank"]}nd in LaLiga</b></span></div>
<div style="display: flex; gap: 6px">{chip(f"{sp['remontadas']} games turned around", "#1F3A16", LIMA)}{chip(f"{sp['caidas']} lead lost", "#3A2412", "#FFB27A")}</div>''', "2025/26")

GX, PR = DX["rangos"]["goles_xg"]["Real Madrid"], DX["rangos"]["portero"]["Real Madrid"]
SEL_EQ = {"fin": {"opts": RANGOS, "ini": "l10", "vals": {
    k: {"goles": GX[k]["goles"], "xg": GX[k]["xg"], "dif": signo(GX[k]["dif"]),
        "gk": PR[k]["jugador"].split(" ")[-1], "ev": signo(PR[k]["evitados"]), "pj": f'{PR[k]["pj"]} of {PR[k]["de"]} games' if PR[k]["pj"] < PR[k]["de"] else f'{PR[k]["de"]} games',
        "evc": LIMA if PR[k]["evitados"] >= 0 else "#FFB27A", "difc": LIMA if GX[k]["dif"] >= 0 else "#FFB27A"} for k, _ in RANGOS}}}
FINAL = tarjeta("Finishing &amp; keeper", selector("fin") + f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">Goals vs xG</span><span style="{DISP}; font-size: 24px; color: {KRM["barra"]}">{{{{fin.goles}}}} <span style="font-size: 15px; color: {MUT}">from {{{{fin.xg}}}}</span></span><span style="font-size: 12px; font-weight: 700; color: {{{{fin.difc}}}}">{{{{fin.dif}}}}</span></div>
<div style="padding: 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">{{{{fin.gk}}}} · goals saved</span><span style="{DISP}; font-size: 24px; color: {{{{fin.evc}}}}">{{{{fin.ev}}}}</span><span style="font-size: 12px; color: {SOFT}">{{{{fin.pj}}}}</span></div></div>''', "LaLiga")

am = D["amarillas"]["equipos"]["Real Madrid"]
AMAR = tarjeta("Yellow card watch", lista([
    f'<div style="display: flex; align-items: center; gap: 10px"><span style="flex-grow: 1; font-size: 14px; font-weight: 600">{a["jugador"]}</span>'
    f'<div style="display: flex; gap: 3px">{cinco(a["amarillas"])}</div>'
    f'<span style="width: 70px; text-align: right; font-size: 12px; color: {MUT}">{a["faltan"]} to ban</span></div>' for a in am[:4]])
    + f'<span style="font-size: 12px; color: {MUT}">LaLiga: 5 yellows = 1-match ban.</span>', "2026/27")

HERO = f'''<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: 50%; top: -70px; width: 300px; height: 260px; margin-left: -150px; border-radius: 50%; background: #F1F3F8; opacity: 0.18; filter: blur(70px)"></span>
{volver("Main.dc.html", "", "")}
<div style="position: relative; display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 0 16px 16px 16px">
{escudo("Real Madrid", 84)}
<span style="{DISP}; font-size: 34px; line-height: 1">Real Madrid</span>
<span style="font-size: 13px; color: {SOFT}">LaLiga 4th · Elo 2nd</span>
<button style="height: 40px; padding: 0 20px; border: none; border-radius: 20px; background: {LIMA}; color: {BG}; font-size: 14px; font-weight: 800">Following</button>
</div></div>'''
cuerpo = HERO + pestañas("Overview", [("Overview", "Equipo.dc.html"), ("Squad", "Jugador.dc.html"), ("Elo", "Elo.dc.html"), ("Fixtures", "#")]) + ELO_T + FORMA + CONSIN + SEGUNDAS + FINAL + AMAR
page("Equipo.dc.html", "Real Madrid", 390, 1870, raiz(1870, cuerpo), js_selectores(SEL_EQ), nav_active="f")

# ======================================================================= PLAYER · Mbappé
J = D["jugador"]
t6, t5 = J["t2026"], J["t2025"]
PCT = J["percentiles_delanteros"]
PCT_EN = {"Goles": "Goals", "xG": "xG", "xA": "xA", "Tiros": "Shots", "Regates": "Dribbles", "Pases clave": "Key passes", "Nota": "Rating"}
res = [("Apps", t6["pj"]), ("Goals", t6["goles"]), ("xG", t6["xg"]), ("Assists", t6["asist"]), ("Shots", t6["tiros"]), ("Rating", f'{t6["nota"]:.2f}')]
RESUMEN = tarjeta("This season", '<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">' + "".join(
    f'<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="display: block; {DISP}; font-size: 26px; line-height: 1.1; color: {LIMA if k in ("Goals", "Rating") else TXT}">{v}</span><span style="font-size: 12px; color: {MUT}">{k}</span></div>'
    for k, v in res) + "</div>", "LaLiga 2026/27")
U10 = DX["mbappe"]["ult10"]


def nota_col(n):
    return LIMA if n >= 7.5 else ("#3A4256" if n >= 6.5 else NARANJA)


def barra_nota(u):
    n = u["nota"]
    k = kequipo(u["rival"])
    return (f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 4px; height: 100%">'
            f'<span style="font-size: 10px; font-weight: 700; color: {LIMA if n >= 7.5 else (MUT if n >= 6.5 else NARANJA)}">{n:.1f}</span>'
            f'<span style="width: 100%; height: {max(8, round((min(n, 10) - 4) / 6 * 80))}px; border-radius: 5px; background: {nota_col(n)}; opacity: {0.45 if u["suplente"] else 1}"></span>'
            f'{escudo(u["rival"], 20, k)}'
            f'<span style="font-size: 9px; font-weight: 700; color: {SOFT}">{"" if u["casa"] else "@"}{eq(u["rival"])[1]}</span>'
            f'<span style="font-size: 9px; font-weight: 700; color: {MUT if u["suplente"] else TXT}">{u["min"]}\'</span></div>')


NOTAS = tarjeta("Match ratings", '<div style="display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: 4px; align-items: end; height: 170px">'
                + "".join(barra_nota(u) for u in U10)
                + f'</div><div style="display: flex; justify-content: space-between; font-size: 11px; color: {MUT}"><span>oldest</span><span>faded = off the bench · @ = away</span><span>latest</span></div>', "last 10")
FIN = tarjeta("Finishing", f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="font-size: 11px; color: {MUT}">2026/27</span><div style="{DISP}; font-size: 26px">{t6["goles"]} <span style="font-size: 15px; color: {MUT}">goals from {t6["xg"]} xG</span></div></div>
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="font-size: 11px; color: {MUT}">2025/26</span><div style="{DISP}; font-size: 26px">{t5["goles"]} <span style="font-size: 15px; color: {MUT}">goals from {t5["xg"]} xG</span></div></div></div>
''', "goals vs xG")
PP = DX["mbappe"]["percentiles"]
RANGOS_J = [["l5", "Last 5"], ["l10", "Last 10"], ["season", "Season"], ["last", "2025/26"]]
ORDEN_P = ["Goals", "xG", "xA", "Shots", "Dribbles", "Key passes", "Rating"]
SEL_J = {"perc": {"opts": RANGOS_J, "ini": "l10", "vals": {
    k: {"filas": [{"n": m, "v": int(PP[k]["pct"][m]), "w": f'{int(PP[k]["pct"][m])}%',
                   "c": LIMA if PP[k]["pct"][m] >= 75 else (AZUL if PP[k]["pct"][m] >= 40 else NARANJA)} for m in ORDEN_P],
        "pie": f'Per 90 vs {PP[k]["n"]} LaLiga forwards', "pocos": k == "l5"} for k, _ in RANGOS_J}}}
PERC = tarjeta("Compared with forwards", selector("perc")
               + f'''<sc-for list="{{{{perc.filas}}}}" as="r" hint-placeholder-count="7"><div style="display: flex; align-items: center; gap: 10px"><span style="width: 90px; font-size: 13px; color: {SOFT}">{{{{r.n}}}}</span>
<div style="flex-grow: 1; height: 10px; border-radius: 5px; background: #1E2330"><div style="width: {{{{r.w}}}}; height: 10px; border-radius: 5px; background: {{{{r.c}}}}"></div></div>
<span style="width: 30px; text-align: right; {DISP}; font-size: 15px">{{{{r.v}}}}</span></div></sc-for>
<div style="display: flex; align-items: center; gap: 8px"><span style="font-size: 12px; color: {MUT}">{{{{perc.pie}}}}</span><sc-if value="{{{{perc.pocos}}}}" hint-placeholder-val="{{{{ false }}}}">{pocos()}</sc-if></div>''', "percentile")
c = J["con_sin"]
CS = tarjeta("With him / without him", f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="{DISP}; font-size: 26px">{c["con_pts"]:.2f}</span><span style="display: block; font-size: 12px; color: {MUT}">pts per game with him · {c["con_n"]} games</span></div>
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="{DISP}; font-size: 26px">{c["sin_pts"]:.2f}</span><span style="display: block; font-size: 12px; color: {MUT}">without him · {c["sin_n"]} games</span></div></div>
''', "since 2024/25")
vh = J["valor_hist"]
VALOR = tarjeta("Market value", f'''<div style="display: flex; align-items: center; gap: 14px"><span style="{DISP}; font-size: 44px; line-height: 1">€{int(J["valor_m"])}M</span>
<div style="margin-left: auto">{sparkline([v["m"] for v in vh], 150, 50, AZUL)}</div></div>
<div style="display: flex; justify-content: space-between; font-size: 11px; color: {MUT}"><span>{vh[0]["fecha"][:7]}</span><span>{vh[-1]["fecha"][:7]}</span></div>''', "history")
pf = J["perfil"]
HERO = f'''<div style="position: relative; display: flex; flex-direction: column">
<span style="position: absolute; left: 50%; top: -70px; width: 300px; height: 260px; margin-left: -150px; border-radius: 50%; background: #F1F3F8; opacity: 0.16; filter: blur(70px)"></span>
{volver("Equipo.dc.html", "", "")}
<div style="position: relative; display: flex; align-items: center; gap: 16px; padding: 6px 16px 16px 16px">
<span style="position: relative; width: 92px; height: 92px; flex-shrink: 0; border-radius: 50%; background: {SUB}; font-weight: 800; font-size: 28px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 4px #F1F3F8">KM<span style="position: absolute; right: -6px; bottom: -2px; padding: 3px 10px; border-radius: 12px; background: {LIMA}; color: {BG}; {DISP}; font-size: 20px">{t6["nota"]:.1f}</span></span>
<div style="display: flex; flex-direction: column; gap: 6px"><span style="{DISP}; font-size: 32px; line-height: 1">Kylian Mbappé</span>
<div style="display: flex; align-items: center; gap: 8px">{escudo("Real Madrid", 22)}<span style="font-size: 13px; color: {SOFT}">Real Madrid · Centre-forward</span></div>
<div style="display: flex; gap: 6px">{chip(f"{pf['edad']} yrs")}{chip(f"{int(pf['altura'])} cm")}{chip("Right foot")}{chip("0 yellows")}</div></div></div></div>'''
cuerpo = HERO + pestañas("Season", [("Season", "Jugador.dc.html"), ("Matches", "#"), ("Career", "#")]) + RESUMEN + FIN + NOTAS + PERC + CS + VALOR
page("Jugador.dc.html", "Kylian Mbappé", 390, 1770, raiz(1770, cuerpo), js_selectores(SEL_J), nav_active="f")

# ======================================================================= ELO · ranking 2yellow y clasificación real
TB = DX["tablas"]


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


filas_r = ""
for f in TB["ranking"]:
    k = kit(f["equipo"])
    yo = f["equipo"] == "Real Madrid"
    filas_r += (f'<div style="display: flex; align-items: center; gap: 10px; min-height: 50px; padding: 0 14px; border-top: 1px solid #1E2330; background: {"#182042" if yo else "transparent"}">'
                f'<span style="width: 22px; {DISP}; font-size: 16px; color: {LIMA if f["rank"] <= 4 else TXT}">{f["rank"]}</span>{franjas(k, 24)}'
                f'<div style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{eq(f["equipo"])[0]}</span>'
                f'<span style="font-size: 11px; color: {MUT}">LaLiga {ordinal(f["pos"])}</span></div>'
                f'<span style="width: 50px; text-align: right; {DISP}; font-size: 18px; color: {k["barra"]}">{int(f["elo"])}</span>'
                f'<span style="width: 34px; text-align: right; font-size: 12px; font-weight: 700; color: {LIMA if f["elo_cambio"] >= 0 else "#FFB27A"}">{signo(f["elo_cambio"], 0)}</span>'
                f'<span style="width: 44px; display: flex; justify-content: flex-end">{sparkline(f["elo_hist"], 44, 18, LIMA if f["elo_cambio"] >= 0 else NARANJA)}</span></div>')
RANKING = (f'<section style="margin: 0 12px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">'
           f'<div style="display: flex; align-items: center; gap: 10px; padding: 12px 14px 8px 14px; font-size: 10px; letter-spacing: 0.4px; color: {MUT}">'
           f'<span style="width: 22px">#</span><span style="width: 8px"></span><span style="flex-grow: 1">TEAM</span><span style="width: 50px; text-align: right">ELO</span>'
           f'<span style="width: 34px; text-align: right">SEASON</span><span style="width: 44px; text-align: right">TREND</span></div>{filas_r}</section>')

C = "text-align: right; font-size: 12px"
filas_l = ""
for f in TB["liga"]:
    k = kit(f["equipo"])
    s_ = f["suerte"]
    col = LIMA if s_ >= 2 else ("#FFB27A" if s_ <= -2 else SOFT)
    rk = next(x["rank"] for x in TB["ranking"] if x["equipo"] == f["equipo"])
    flecha = (f'<span style="color: {LIMA}" title="2yellow {rk}">▲</span>' if rk < f["pos"] - 1 else
              (f'<span style="color: #FFB27A" title="2yellow {rk}">▼</span>' if rk > f["pos"] + 1 else ""))
    filas_l += (f'<div style="display: flex; align-items: center; gap: 4px; min-height: 44px; padding: 0 10px; border-top: 1px solid #1E2330; background: {"#182042" if f["equipo"] == "Real Madrid" else "transparent"}">'
                f'<span style="width: 18px; {DISP}; font-size: 14px">{f["pos"]}</span>{franjas(k, 20)}'
                f'<span style="flex-grow: 1; min-width: 0; padding-left: 4px; font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{eq(f["equipo"])[0]}</span>'
                f'<span style="width: 12px; font-size: 9px; text-align: center">{flecha}</span>'
                + "".join(f'<span style="width: 16px; {C}; color: {SOFT}">{f[c_]}</span>' for c_ in ("pj", "g", "e", "p"))
                + f'<span style="width: 26px; {C}; color: {SOFT}">{"+" if f["dg"] > 0 else ""}{f["dg"]}</span>'
                f'<span style="width: 24px; text-align: right; {DISP}; font-size: 15px">{f["pts"]}</span>'
                f'<span style="width: 30px; {C}; color: {MUT}">{f["xpts"]:.1f}</span>'
                f'<span style="width: 32px; {C}; font-weight: 700; color: {col}">{signo(s_)}</span></div>')
LIGA = (f'<section style="margin: 0 12px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">'
        f'<div style="display: flex; align-items: center; gap: 4px; padding: 12px 10px 8px 10px; font-size: 9.5px; letter-spacing: 0.3px; color: {MUT}">'
        f'<span style="width: 18px">#</span><span style="width: 10px"></span><span style="flex-grow: 1; padding-left: 4px">TEAM</span><span style="width: 12px"></span>'
        + "".join(f'<span style="width: 16px; text-align: right">{h_}</span>' for h_ in ("P", "W", "D", "L"))
        + f'<span style="width: 26px; text-align: right">GD</span><span style="width: 24px; text-align: right">PTS</span>'
        f'<span style="width: 30px; text-align: right">xPTS</span><span style="width: 32px; text-align: right">LUCK</span></div>{filas_l}'
        f'<div style="display: flex; gap: 14px; padding: 10px 14px 12px 14px; border-top: 1px solid #1E2330; font-size: 11px; color: {MUT}"><span><b style="color: {LIMA}">▲</b> higher in 2yellow</span><span><b style="color: #FFB27A">▼</b> lower</span><span>xPTS = deserved points</span></div></section>')
TABS_ELO = f'''<nav aria-label="Tables" style="margin: 0 12px; padding: 4px; border-radius: 22px; background: {SUB}; display: flex; gap: 4px">
<sc-for list="{{{{sel_tabla}}}}" as="o" hint-placeholder-count="2"><button onClick="{{{{o.pick}}}}" style="flex: 1 1 0; height: 38px; border: none; border-radius: 18px; background: {{{{o.bg}}}}; color: {{{{o.fg}}}}; font-size: 13px; font-weight: 800">{{{{o.txt}}}}</button></sc-for></nav>
<sc-if value="{{{{tabla.ranking}}}}" hint-placeholder-val="{{{{ true }}}}">{RANKING}</sc-if>
<sc-if value="{{{{tabla.liga}}}}" hint-placeholder-val="{{{{ false }}}}">{LIGA}</sc-if>'''
v5 = D["tabla_elo"]["comprobacion"]
HONESTO = tarjeta("How good is Elo this early?", f'''<span style="font-size: 13px; color: {SOFT}">After 7 matchdays, how well each ranking matched the final table:</span>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">{"".join(f'<div style="padding: 10px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">{2000 + v["temporada"] % 100}/{(v["temporada"] + 1) % 100:02d}</span><span style="display: block; font-size: 13px">Elo <b>{v["spearman_elo_j7"]:.2f}</b></span><span style="display: block; font-size: 13px; color: {SOFT}">Table {v["spearman_tabla_j7"]:.2f}</span></div>' for v in v5)}</div>
<span style="font-size: 12px; color: {MUT}">Elo wins 2 of 3 seasons.</span>''', "checked")

GXL, PL = DX["rangos"]["goles_xg"], DX["rangos"]["porteros_liga"]


def rachas_vals(k):
    xs = sorted(({"e": e, **v[k]} for e, v in GXL.items()), key=lambda x: -x["dif"])
    sel = xs[:3] + xs[-3:]
    return {"filas": [{"eq": eq(x["e"])[0], "sig": eq(x["e"])[1], "c1": kit(x["e"])["c1"], "tx": kit(x["e"])["texto"],
                       "txt": f'{x["goles"]} goals · {x["xg"]} xG', "dif": signo(x["dif"]),
                       "bg": "#1F3A16" if x["dif"] > 0 else "#3A2412", "fg": LIMA if x["dif"] > 0 else "#FFB27A"} for x in sel]}


def porteros_vals(k):
    return {"filas": [{"i": i + 1, "jug": x["jugador"], "sig": eq(x["equipo"])[1], "c1": kit(x["equipo"])["c1"], "tx": kit(x["equipo"])["texto"],
                       "ev": signo(x["evitados"]), "pj": x["pj"]} for i, x in enumerate(PL[k][:5])]}


ESC = ('<span style="width: 24px; height: 24px; flex-shrink: 0; border-radius: 50%; background: {{{{r.c1}}}}; color: {{{{r.tx}}}}; font-size: 7px; font-weight: 800; '
       'display: flex; align-items: center; justify-content: center">{{{{r.sig}}}}</span>').format()
RACHAS = tarjeta("Finishing streaks", selector("rach") + f'''<div style="display: flex; flex-direction: column; gap: 10px"><sc-for list="{{{{rach.filas}}}}" as="r" hint-placeholder-count="6">
<div style="display: flex; align-items: center; gap: 10px">{ESC}<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{{{{r.eq}}}}</span><span style="font-size: 12px; color: {MUT}">{{{{r.txt}}}}</span>
<span style="padding: 3px 9px; border-radius: 9px; background: {{{{r.bg}}}}; color: {{{{r.fg}}}}; font-size: 11px; font-weight: 700">{{{{r.dif}}}}</span></div></sc-for></div>
<span style="font-size: 12px; color: {MUT}">Goals minus xG. Most of it fades.</span>''', "goals vs xG")

PORT = tarjeta("Goalkeepers who save points", selector("port") + f'''<div style="display: flex; flex-direction: column; gap: 10px"><sc-for list="{{{{port.filas}}}}" as="r" hint-placeholder-count="5">
<div style="display: flex; align-items: center; gap: 10px"><span style="width: 18px; {DISP}; font-size: 14px; color: {MUT}">{{{{r.i}}}}</span>{ESC}
<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{{{{r.jug}}}}</span><span style="font-size: 11px; color: {MUT}">{{{{r.pj}}}} gp</span><span style="{DISP}; font-size: 18px; color: {LIMA}">{{{{r.ev}}}}</span></div></sc-for></div>''', "goals saved")

SEL_ELO = {"tabla": {"opts": [["ranking", "2yellow Ranking"], ["liga", "LaLiga table"]], "ini": "ranking",
                     "vals": {"ranking": {"ranking": True, "liga": False}, "liga": {"ranking": False, "liga": True}}},
           "rach": {"opts": RANGOS, "ini": "l10", "vals": {k: rachas_vals(k) for k, _ in RANGOS}},
           "port": {"opts": RANGOS, "ini": "l10", "vals": {k: porteros_vals(k) for k, _ in RANGOS}}}

POS_EN = {"Defender": "DEF", "Midfielder": "MID", "Forward": "FWD", "Goalkeeper": "GK"}
mb = D["moneyball"]["gangas"][:5]
MONEY = tarjeta("Moneyball", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px">{escudo(x["equipo"], 24)}<div style="flex-grow: 1; display: flex; flex-direction: column">'
     f'<span style="font-size: 14px; font-weight: 700">{x["jugador"]}</span><span style="font-size: 12px; color: {MUT}">{POS_EN.get(x["pos"], x["pos"])} · rating {x["nota"]:.2f} · top {100 - int(x["pct_nota"])}% of his position</span></div>'
     f'{chip("€" + str(int(x["valor_m"])) + "M", "#1E2A66", "#A9B8FF")}</div>' for x in mb])
    + f'<span style="font-size: 12px; color: {MUT}">Top rated for their price.</span>', "value for money")

lim = D["amarillas"]["al_limite"]
LIMITE = tarjeta("One yellow from a ban", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px">{escudo(x["equipo"], 24)}<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{x["jugador"]}</span>'
     f'<div style="display: flex; gap: 3px">{cinco(4)}</div></div>' for x in lim]), "LaLiga")

HEAD = f'''<header style="display: flex; flex-direction: column; gap: 6px; padding: 20px 16px 0 16px">
<span style="font-size: 12px; font-weight: 700; letter-spacing: 1px; color: {LIMA}">ONLY ON 2YELLOW</span>
<span style="{DISP}; font-size: 38px; line-height: 1">2yellow Ranking</span>
<span style="font-size: 13px; color: {SOFT}">Teams ranked by strength, not points.</span></header>'''
cuerpo = HEAD + TABS_ELO + HONESTO + RACHAS + PORT + MONEY + LIMITE
page("Elo.dc.html", "2yellow Ranking", 390, 2720, raiz(2720, cuerpo), js_selectores(SEL_ELO), nav_active="e")

# ======================================================================= TIPS
pr = DJ["pronosticos"]["real_madrid_villarreal"]
ca = DJ["pronosticos"]["acierto_casa"]
cg = DJ["pronosticos"]["calibracion_goles"]
tips = [("Over 1.5 goals", pr["mas15"], ca["mas15"]["acierta"]), ("Madrid or draw", 87, ca["doble"]["acierta"]),
        ("Over 2.5 goals", pr["mas25"], ca["mas25"]["acierta"]), ("Real Madrid to win", 66, ca["1x2"]["acierta"]),
        ("Both teams score", pr["ambos"], ca["ambos"]["acierta"]), ("Over 4.5 cards", D["termometro"]["p_mas45"], None)]
TOP = f'''<section style="position: relative; margin: 0 12px; padding: 18px; border-radius: 28px; background: {CARD}; border: 1px solid #262C3B; overflow: hidden; display: flex; flex-direction: column; gap: 14px">
<span style="position: absolute; right: -50px; top: -60px; width: 200px; height: 200px; border-radius: 50%; background: {LIMA}; opacity: 0.18; filter: blur(50px)"></span>
<div style="position: relative; display: flex; justify-content: space-between; align-items: center">{chip("TOP PICK", LIMA, BG)}<span style="font-size: 12px; color: {SOFT}">Sat 10 Oct · 21:00</span></div>
<div style="position: relative; display: flex; align-items: center; gap: 16px">
<svg width="112" height="112" viewBox="0 0 112 112" role="img" aria-label="{round(pr["mas15"])} percent"><circle cx="56" cy="56" r="46" fill="none" stroke="#232838" stroke-width="12"></circle><circle cx="56" cy="56" r="46" fill="none" stroke="{LIMA}" stroke-width="12" stroke-linecap="round" stroke-dasharray="{pr["mas15"] / 100 * 289:.0f} 289" transform="rotate(-90 56 56)"></circle><text x="56" y="62" text-anchor="middle" fill="{TXT}" font-family="Archivo, sans-serif" font-weight="800" font-size="30">{round(pr["mas15"])}%</text></svg>
<div style="display: flex; flex-direction: column; gap: 6px"><span style="{DISP}; font-size: 28px; line-height: 1.05">Over 1.5 goals</span>
<div style="display: flex; align-items: center; gap: 8px">{escudo("Real Madrid", 22)}<span style="font-size: 13px; font-weight: 600">Real Madrid – Villarreal</span>{escudo("Villarreal", 22)}</div>
<div style="display: flex; align-items: center; gap: 8px"><span style="font-size: 13px; color: {SOFT}">Fair odds <b style="color: {TXT}">{100 / pr["mas15"]:.2f}</b></span>{confianza(pr["mas15"])}</div></div></div>
</section>'''
MAS = "".join(
    f'<div style="margin: 0 12px; padding: 14px 16px; border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; display: flex; align-items: center; gap: 14px">'
    f'<div style="flex-grow: 1; display: flex; flex-direction: column; gap: 6px"><span style="font-size: 12px; color: {MUT}">Real Madrid – Villarreal</span><span style="font-size: 16px; font-weight: 700">{n}</span>'
    f'<div style="display: flex; gap: 6px; flex-wrap: wrap">{confianza(p)}{chip("fair " + f"{100 / p:.2f}")}</div></div>'
    f'<span style="{DISP}; font-size: 36px; line-height: 1; color: {LIMA}">{round(p)}<span style="font-size: 18px">%</span></span></div>' for n, p, c in tips[1:])
cal = cg["mas25"]
COMO = tarjeta("Do our numbers hold up?", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px"><span style="flex-grow: 1; font-size: 13px; color: {SOFT}">We said {x["dice"]:.0f}%</span><span style="font-size: 13px">it happened <b>{x["pasa"]:.0f}%</b></span><span style="width: 60px; text-align: right; font-size: 11px; color: {MUT}">{x["n"]} games</span></div>'
     for x in cal if x["n"] >= 20])
    + f'<span style="font-size: 12px; color: {MUT}">Over 2.5 goals · {cg["partidos"]} LaLiga games.</span>', "checked")
HEAD = f'<header style="display: flex; align-items: center; gap: 10px; padding: 18px 12px 0 16px"><span style="flex-grow: 1; {DISP}; font-size: 34px">Tips</span></header>'
cuerpo = HEAD + TOP + f'<div style="padding: 6px 16px 0 16px; font-size: 18px; font-weight: 700">More for this match</div>' + MAS + COMO
page("Tips.dc.html", "Tips", 390, 1250, raiz(1250, cuerpo), JS0, nav_active="t")
print("s5c ok")
