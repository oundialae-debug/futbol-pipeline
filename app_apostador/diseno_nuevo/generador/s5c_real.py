"""Equipo (Real Madrid), jugador (Mbappé), tabla Elo de la liga y tips, con datos reales."""
from common import page
from real_ui import *
from s5a_real import raiz, JS0

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
<div style="display: flex; flex-direction: column"><span style="{DISP}; font-size: 48px; line-height: 1">{int(RM["elo"])}</span><span style="font-size: 12px; color: {MUT}">2nd strongest in LaLiga</span></div>
<div style="margin-left: auto">{sparkline(RM["elo_hist"], 150, 60)}</div></div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Table</span><span style="{DISP}; font-size: 20px">4th · {RM["pts"]} pts</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Elo points</span><span style="{DISP}; font-size: 20px">{RM["xpts"]}</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">Luck</span><span style="{DISP}; font-size: 20px">{signo(RM["suerte"])}</span></div></div>
<span style="font-size: 12px; color: {MUT}">Elo points: what a team this strong would expect from these fixtures. Madrid are right where their level says.</span>''', "strength, not points")

cs = D["con_sin"]["Real Madrid"]["lista"]
top_cs = [c for c in cs if c["sin_n"] >= 8][:3] + [c for c in cs if c["sin_n"] >= 8][-2:]


def cs_fila(c):
    col = LIMA if c["efecto"] >= 0 else "#FFB27A"
    return (f'<div style="display: flex; align-items: center; gap: 10px"><div style="flex-grow: 1; display: flex; flex-direction: column">'
            f'<span style="font-size: 14px; font-weight: 700">{c["jugador"]}</span>'
            f'<span style="font-size: 12px; color: {MUT}">With {c["con_pts"]:.2f} pts ({c["con_n"]}) · without {c["sin_pts"]:.2f} ({c["sin_n"]})</span></div>'
            f'<span style="{DISP}; font-size: 20px; color: {col}">{signo(c["efecto"], 2)}</span></div>')


CONSIN = tarjeta("With him / without him", lista([cs_fila(c) for c in top_cs])
                 + f'<span style="font-size: 12px; color: {MUT}">Points per game above what Elo expected, when he starts vs when he does not. {D["con_sin"]["Real Madrid"]["partidos"]} league games since Aug 2024. Under ~20 games either side it can be chance.</span>', "vs Elo expectation")

sp = {x["equipo"]: x for x in D["segundas_partes"]["2025_26"]}["Real Madrid"]
SEGUNDAS = tarjeta("After half-time", f'''<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="{DISP}; font-size: 24px; color: {LIMA}">+{int(sp["pts_tras_descanso"])}</span><span style="display: block; font-size: 11px; color: {MUT}">pts won after HT</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="{DISP}; font-size: 24px">{sp["remontadas"]}</span><span style="display: block; font-size: 11px; color: {MUT}">comebacks</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="{DISP}; font-size: 24px">{sp["caidas"]}</span><span style="display: block; font-size: 11px; color: {MUT}">leads lost</span></div></div>
<span style="font-size: 12px; color: {MUT}">2025/26: 2nd best in LaLiga at turning half-time scores into more points. Strong sides do this more; it is mostly quality, not a separate trait.</span>''', "2025/26")

eqr = {x["equipo"]: x for x in D["rachas"]["equipos_2026_27"]}["Real Madrid"]
gk = [g for g in D["porteros"]["ranking"] if g["equipo"] == "Real Madrid"][0]
FINAL = tarjeta("Finishing &amp; keeper", f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">Goals vs xG</span><span style="{DISP}; font-size: 24px">{eqr["goles"]} <span style="font-size: 15px; color: {MUT}">from {eqr["xg"]}</span></span><span style="font-size: 12px; color: {SOFT}">Scoring what the chances are worth</span></div>
<div style="padding: 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column; gap: 4px"><span style="font-size: 11px; color: {MUT}">Courtois · goals saved</span><span style="{DISP}; font-size: 24px">{signo(gk["evitados"])}</span><span style="font-size: 12px; color: {SOFT}">since 2025/26, about average</span></div></div>''', "2026/27")

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
<span style="font-size: 13px; color: {SOFT}">LaLiga · 4th · Elo 2nd</span>
<button style="height: 40px; padding: 0 20px; border: none; border-radius: 20px; background: {LIMA}; color: {BG}; font-size: 14px; font-weight: 800">Following</button>
</div></div>'''
cuerpo = HERO + pestañas("Overview", [("Overview", "Equipo.dc.html"), ("Squad", "Jugador.dc.html"), ("Elo", "Elo.dc.html"), ("Fixtures", "#")]) + ELO_T + FORMA + CONSIN + SEGUNDAS + FINAL + AMAR
page("Equipo.dc.html", "Real Madrid", 390, 2660, raiz(2660, cuerpo), JS0, nav_active="f")

# ======================================================================= PLAYER · Mbappé
J = D["jugador"]
t6, t5 = J["t2026"], J["t2025"]
PCT = J["percentiles_delanteros"]
PCT_EN = {"Goles": "Goals", "xG": "xG", "xA": "xA", "Tiros": "Shots", "Regates": "Dribbles", "Pases clave": "Key passes", "Nota": "Rating"}
res = [("Apps", t6["pj"]), ("Goals", t6["goles"]), ("xG", t6["xg"]), ("Assists", t6["asist"]), ("Shots", t6["tiros"]), ("Rating", f'{t6["nota"]:.2f}')]
RESUMEN = tarjeta("This season", '<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">' + "".join(
    f'<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="display: block; {DISP}; font-size: 26px; line-height: 1.1; color: {LIMA if k in ("Goals", "Rating") else TXT}">{v}</span><span style="font-size: 12px; color: {MUT}">{k}</span></div>'
    for k, v in res) + "</div>", "LaLiga 2026/27")
notas = J["notas_ult"]
NOTAS = tarjeta("Match ratings", '<div style="display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: 4px; align-items: end; height: 132px">' + "".join(
    f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 4px; height: 100%"><span style="font-size: 10px; font-weight: 700; color: {LIMA if n >= 7.5 else (MUT if n >= 6.5 else NARANJA)}">{n:.1f}</span>'
    f'<span style="width: 100%; height: {max(8, round((min(n, 10) - 4) / 6 * 90))}px; border-radius: 5px; background: {LIMA if n >= 7.5 else ("#3A4256" if n >= 6.5 else NARANJA)}"></span></div>' for n in notas)
    + f'</div><div style="display: flex; justify-content: space-between; font-size: 11px; color: {MUT}"><span>oldest</span><span>latest</span></div>', "last 10")
FIN = tarjeta("Finishing", f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="font-size: 11px; color: {MUT}">2026/27</span><div style="{DISP}; font-size: 26px">{t6["goles"]} <span style="font-size: 15px; color: {MUT}">goals from {t6["xg"]} xG</span></div></div>
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="font-size: 11px; color: {MUT}">2025/26</span><div style="{DISP}; font-size: 26px">{t5["goles"]} <span style="font-size: 15px; color: {MUT}">goals from {t5["xg"]} xG</span></div></div></div>
<span style="font-size: 12px; color: {MUT}">He scores what his chances are worth, season after season: no lucky streak to fade.</span>''', "goals vs xG")
PERC = tarjeta("Compared with forwards", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px"><span style="width: 90px; font-size: 13px; color: {SOFT}">{PCT_EN[k]}</span>'
    f'<div style="flex-grow: 1; height: 10px; border-radius: 5px; background: #1E2330"><div style="width: {int(v)}%; height: 10px; border-radius: 5px; background: {LIMA if v >= 75 else (AZUL if v >= 40 else NARANJA)}"></div></div>'
    f'<span style="width: 30px; text-align: right; {DISP}; font-size: 15px">{int(v)}</span></div>' for k, v in PCT.items() if v is not None)
    + f'<span style="font-size: 12px; color: {MUT}">Percentile per 90 among {J["n_delanteros"]} LaLiga forwards with 900+ minutes since 2025/26.</span>', "percentile")
c = J["con_sin"]
CS = tarjeta("With him / without him", f'''<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="{DISP}; font-size: 26px">{c["con_pts"]:.2f}</span><span style="display: block; font-size: 12px; color: {MUT}">pts per game with him · {c["con_n"]} games</span></div>
<div style="padding: 12px; border-radius: 16px; background: {SUB}"><span style="{DISP}; font-size: 26px">{c["sin_pts"]:.2f}</span><span style="display: block; font-size: 12px; color: {MUT}">without him · {c["sin_n"]} games</span></div></div>
<span style="font-size: 12px; color: {MUT}">Madrid collect the same points either way: the squad covers him well.</span>''', "since 2024/25")
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
page("Jugador.dc.html", "Kylian Mbappé", 390, 2520, raiz(2520, cuerpo), JS0, nav_active="f")

# ======================================================================= ELO · la tabla de verdad
filas = ""
for f in D["tabla_elo"]["filas"]:
    s_ = f["suerte"]
    col = LIMA if s_ >= 2 else ("#FFB27A" if s_ <= -2 else SOFT)
    filas += (f'<div style="display: flex; align-items: center; gap: 8px; min-height: 48px; padding: 0 14px; border-top: 1px solid #1E2330; background: {"#182042" if f["equipo"] == "Real Madrid" else "transparent"}">'
              f'<span style="width: 20px; {DISP}; font-size: 14px">{f["pos"]}</span>{escudo(f["equipo"], 22)}'
              f'<span style="flex-grow: 1; font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{eq(f["equipo"])[0]}</span>'
              f'<span style="width: 26px; text-align: right; {DISP}; font-size: 15px">{f["pts"]}</span>'
              f'<span style="width: 40px; text-align: right; font-size: 13px; color: {SOFT}">{f["xpts"]:.1f}</span>'
              f'<span style="width: 40px; text-align: right; font-size: 12px; font-weight: 700; color: {col}">{signo(s_)}</span>'
              f'<span style="width: 30px; text-align: center; font-size: 12px; font-weight: 800; color: {BG}; background: {AZUL if f["elo_rank"] <= 4 else "#3A4256"}; border-radius: 8px; padding: 2px 0">{f["elo_rank"]}</span>'
              f'<span style="width: 44px; display: flex; justify-content: flex-end">{sparkline(f["elo_hist"], 44, 18, LIMA if f["elo_cambio"] >= 0 else NARANJA)}</span></div>')
TABLA = (f'<section style="margin: 0 12px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">'
         f'<div style="display: flex; align-items: center; gap: 8px; padding: 12px 14px 8px 14px; font-size: 10px; letter-spacing: 0.4px; color: {MUT}">'
         f'<span style="width: 20px">#</span><span style="width: 22px"></span><span style="flex-grow: 1">TEAM</span><span style="width: 26px; text-align: right">PTS</span>'
         f'<span style="width: 40px; text-align: right">ELO PTS</span><span style="width: 40px; text-align: right">LUCK</span><span style="width: 30px; text-align: center">RANK</span><span style="width: 44px; text-align: right">TREND</span></div>{filas}</section>')
v5 = D["tabla_elo"]["comprobacion"]
HONESTO = tarjeta("How good is Elo this early?", f'''<span style="font-size: 13px; color: {SOFT}">After 7 matchdays, how well each ranking matched the final table:</span>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">{"".join(f'<div style="padding: 10px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">{2000 + v["temporada"] % 100}/{(v["temporada"] + 1) % 100:02d}</span><span style="display: block; font-size: 13px">Elo <b>{v["spearman_elo_j7"]:.2f}</b></span><span style="display: block; font-size: 13px; color: {SOFT}">Table {v["spearman_tabla_j7"]:.2f}</span></div>' for v in v5)}</div>
<span style="font-size: 12px; color: {MUT}">Elo wins 2 of 3 seasons, by a little. Its edge is context: it knows who you played.</span>''', "checked")

rq = D["rachas"]["equipos_2026_27"]
RACHAS = tarjeta("Finishing streaks", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px">{escudo(x["equipo"], 24)}<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{eq(x["equipo"])[0]}</span>'
     f'<span style="font-size: 12px; color: {MUT}">{x["goles"]} goals · {x["xg"]} xG</span>{chip(signo(x["dif"]), "#1F3A16" if x["dif"] > 0 else "#3A2412", LIMA if x["dif"] > 0 else "#FFB27A")}</div>'
     for x in rq[:3] + rq[-3:]])
    + f'<span style="font-size: 12px; color: {MUT}">Over- or under-finishing only partly carries on (correlation 0.34 across 2025/26); most of it fades.</span>', "goals vs xG")

gks = D["porteros"]["ranking"][:5]
PORT = tarjeta("Goalkeepers who save points", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px"><span style="width: 18px; {DISP}; font-size: 14px; color: {MUT}">{i + 1}</span>{escudo(g["equipo"], 24)}'
     f'<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{g["jugador"]}</span><span style="{DISP}; font-size: 18px; color: {LIMA}">{signo(g["evitados"])}</span></div>'
     for i, g in enumerate(gks)])
    + f'<span style="font-size: 12px; color: {MUT}">Goals saved since 2025/26. It only partly repeats from one half-season to the next (correlation 0.31): a hint, not a law.</span>', "goals saved")

POS_EN = {"Defender": "DEF", "Midfielder": "MID", "Forward": "FWD", "Goalkeeper": "GK"}
mb = D["moneyball"]["gangas"][:5]
MONEY = tarjeta("Moneyball", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px">{escudo(x["equipo"], 24)}<div style="flex-grow: 1; display: flex; flex-direction: column">'
     f'<span style="font-size: 14px; font-weight: 700">{x["jugador"]}</span><span style="font-size: 12px; color: {MUT}">{POS_EN.get(x["pos"], x["pos"])} · rating {x["nota"]:.2f} · top {100 - int(x["pct_nota"])}% of his position</span></div>'
     f'{chip("€" + str(int(x["valor_m"])) + "M", "#1E2A66", "#A9B8FF")}</div>' for x in mb])
    + f'<span style="font-size: 12px; color: {MUT}">Best rated for their position against their market value. {D["moneyball"]["n"]} players with 1,500+ minutes.</span>', "value for money")

lim = D["amarillas"]["al_limite"]
LIMITE = tarjeta("One yellow from a ban", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px">{escudo(x["equipo"], 24)}<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{x["jugador"]}</span>'
     f'<div style="display: flex; gap: 3px">{cinco(4)}</div></div>' for x in lim]), "LaLiga")

HEAD = f'''<header style="display: flex; flex-direction: column; gap: 6px; padding: 20px 16px 0 16px">
<span style="font-size: 12px; font-weight: 700; letter-spacing: 1px; color: {LIMA}">ONLY ON 2YELLOW</span>
<span style="{DISP}; font-size: 38px; line-height: 1">The Elo table</span>
<span style="font-size: 13px; color: {SOFT}">Strength, not just points. Elo pts = what a side this strong would expect from its fixtures. Luck = the gap.</span></header>'''
cuerpo = HEAD + TABLA + HONESTO + RACHAS + PORT + MONEY + LIMITE
page("Elo.dc.html", "Elo table", 390, 3120, raiz(3120, cuerpo), JS0, nav_active="e")

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
<span style="font-size: 13px; color: {SOFT}">Fair odds <b style="color: {TXT}">{100 / pr["mas15"]:.2f}</b> · books hit {ca["mas15"]["acierta"]:.0f}% here</span></div></div>
<div style="position: relative; display: flex; align-items: center; gap: 8px; padding: 6px 6px 6px 14px; border-radius: 16px; background: {BG}; border: 1px solid #2A3040">
<label for="odds" style="flex-grow: 1; font-size: 13px; color: {SOFT}">Your bookmaker pays</label>
<input id="odds" type="text" inputmode="decimal" value="1.20" style="width: 72px; height: 40px; box-sizing: border-box; border: none; border-radius: 12px; background: {SUB}; color: {TXT}; text-align: center; font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 18px">
<span style="height: 40px; padding: 0 14px; border-radius: 12px; background: {LIMA}; color: {BG}; font-size: 13px; font-weight: 800; display: flex; align-items: center">Good price +5%</span></div></section>'''
MAS = "".join(
    f'<div style="margin: 0 12px; padding: 14px 16px; border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; display: flex; align-items: center; gap: 14px">'
    f'<div style="flex-grow: 1; display: flex; flex-direction: column; gap: 6px"><span style="font-size: 12px; color: {MUT}">Real Madrid – Villarreal</span><span style="font-size: 16px; font-weight: 700">{n}</span>'
    f'<div style="display: flex; gap: 6px">{chip("fair " + f"{100 / p:.2f}")}{chip("books hit " + f"{c:.0f}%") if c else chip("referee not named", "#3A2412", "#FFB27A")}</div></div>'
    f'<span style="{DISP}; font-size: 36px; line-height: 1; color: {LIMA}">{round(p)}<span style="font-size: 18px">%</span></span></div>' for n, p, c in tips[1:])
cal = cg["mas25"]
COMO = tarjeta("Do our numbers hold up?", lista(
    [f'<div style="display: flex; align-items: center; gap: 10px"><span style="flex-grow: 1; font-size: 13px; color: {SOFT}">We said {x["dice"]:.0f}%</span><span style="font-size: 13px">it happened <b>{x["pasa"]:.0f}%</b></span><span style="width: 60px; text-align: right; font-size: 11px; color: {MUT}">{x["n"]} games</span></div>'
     for x in cal if x["n"] >= 20])
    + f'<span style="font-size: 12px; color: {MUT}">Over 2.5 goals, {cg["partidos"]} LaLiga games since Aug 2024, each predicted with past data only.</span>', "checked")
HEAD = f'<header style="display: flex; align-items: center; gap: 10px; padding: 18px 12px 0 16px"><span style="flex-grow: 1; {DISP}; font-size: 34px">Tips</span></header>'
cuerpo = HEAD + TOP + f'<div style="padding: 6px 16px 0 16px; font-size: 18px; font-weight: 700">More for this match</div>' + MAS + COMO
page("Tips.dc.html", "Tips", 390, 2080, raiz(2080, cuerpo), JS0, nav_active="t")
print("s5c ok")
