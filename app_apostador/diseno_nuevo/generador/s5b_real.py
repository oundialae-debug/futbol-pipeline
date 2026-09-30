"""Informe post-partido Atlético 2-1 Real Madrid: resumen, estadísticas y alineaciones."""
import pandas as pd
from common import page
from real_ui import *
from s5a_real import raiz, JS0

I = D["informe"]
H = pd.read_csv(APP.parent / "data" / "historico_partidos.csv")
M = H[(H.local == "Atlético Madrid") & (H.visitante == "Real Madrid") & (H.temporada == 2026)].iloc[0]
KA, KB = kits("Atlético Madrid", "Real Madrid")
CA, CB = (KA["barra"], KA["texto"]), (KB["barra"], KB["texto"])
TABS = [("Report", "Report.dc.html"), ("Stats", "Stats.dc.html"), ("Lineups", "Alineacion.dc.html")]


def cabecera(activa, compacta=False):
    if compacta:
        top = (f'<div style="position: relative; display: flex; align-items: center; justify-content: center; gap: 12px; padding: 0 0 12px 0">'
               f'{franjas(KA, 26)}{escudo("Atlético Madrid", 32, KA)}<span style="{DISP}; font-size: 30px">2 – 1</span>{escudo("Real Madrid", 32, KB)}{franjas(KB, 26)}</div>')
    else:
        top = f'''<div style="position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px 0 16px">
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("Atlético Madrid", 62, KA)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">{franjas(KA, 16)}Atlético</span></div>
<div style="display: flex; flex-direction: column; align-items: center; gap: 6px"><span style="{DISP}; font-size: 64px; line-height: 1">2 – 1</span>{chip("Full time · HT 0–0", "#1E2330", SOFT)}</div>
<div style="width: 112px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center">{escudo("Real Madrid", 62, KB)}<span style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700">Real Madrid{franjas(KB, 16)}</span></div>
</div><div style="position: relative; display: flex; justify-content: space-between; padding: 12px 16px 16px 16px; font-size: 12px; color: {SOFT}"><span>Atlético at home</span><span>Sun 20 Sep · Matchday 7</span></div>'''
    return (f'<div style="position: relative; display: flex; flex-direction: column">{glow(KA["barra"], KB["barra"], 230)}'
            f'{volver("Main.dc.html", "LaLiga · Matchday 7", "Match report")}{top}</div>{pestañas(activa, TABS)}')


# ---------------------------------------------------------------- historia del partido (momentum a posteriori)
def pos(minuto):
    m = int(str(minuto).split("+")[0])
    return min(m, 90) / 90 * 100


marcas = ""
for t in I["tarjetas"]:
    roja = t["tipo"] == "Red Card"
    arriba = t["equipo"] == "Atlético Madrid"
    top = 6 if arriba else 44
    marcas += (f'<span title="{t["min"]}\' {t["jugador"]}" style="position: absolute; left: {pos(t["min"]):.1f}%; top: {top}px; width: {12 if roja else 9}px; '
               f'height: {16 if roja else 13}px; margin-left: -5px; border-radius: 2px; background: {ROJO if roja else AMARILLO}; box-shadow: 0 0 0 2px {CARD}"></span>')
HISTORIA = tarjeta("Match story", f'''
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span style="display: flex; align-items: center; gap: 6px">{franjas(KA, 14)}Atlético</span><span>goals per half · cards by minute</span></div>
<div style="position: relative; height: 66px">
<div style="position: absolute; left: 0; width: calc(50% - 2px); top: 26px; height: 14px; border-radius: 7px 0 0 7px; background: #1E2330"></div>
<div style="position: absolute; right: 0; width: calc(50% - 2px); top: 26px; height: 14px; border-radius: 0 7px 7px 0; background: linear-gradient(90deg, #1E2330 0%, #1E2330 15.5%, #3A1719 15.5%, #3A1719 100%)"></div>
<span style="position: absolute; left: 25%; top: 24px; margin-left: -18px; width: 36px; text-align: center; {DISP}; font-size: 15px">0–0</span>
<span style="position: absolute; left: 75%; top: 24px; margin-left: -18px; width: 36px; text-align: center; {DISP}; font-size: 15px; color: {LIMA}">2–1</span>
{marcas}
</div>
<div style="display: flex; justify-content: space-between; font-size: 11px; color: {MUT}"><span>0'</span><span>HT</span><span>90'</span></div>
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {SOFT}"><span style="display: flex; align-items: center; gap: 6px">{franjas(KB, 14)}Real Madrid</span><span>shaded: Madrid down to 10</span></div>
<div style="padding: 12px; border-radius: 16px; background: #2A1416; display: flex; gap: 10px; align-items: center">
<span style="width: 12px; height: 16px; border-radius: 2px; background: {ROJO}; flex-shrink: 0"></span>
<span style="font-size: 13px; color: {TXT}"><b>Turning point · 52'</b> Huijsen sent off at 0–0. All three goals came in the second half; Madrid played 38 minutes with ten.</span></div>
<span style="font-size: 11px; color: {MUT}">Goal and substitution minutes are not stored yet, so goals show per half.</span>''', "after the match")

m_ = I["merecido_xg"]
MERECIDO = tarjeta("Deserved?", f'''
<div style="display: flex; align-items: center; justify-content: space-between">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 12px; color: {MUT}">Expected goals</span><span style="{DISP}; font-size: 36px; line-height: 1">{I["xg"][0]:.2f} <span style="color: {MUT}; font-size: 22px">vs</span> {I["xg"][1]:.2f}</span></div>
{chip("Deserved", "#1F3A16", LIMA)}</div>
<span style="font-size: 13px; color: {SOFT}">Replaying these chances 100 times:</span>
{tres(int(m_[0]), int(m_[1]), int(m_[2]), CA, CB, 40, 20)}
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {MUT}"><span>Atlético win</span><span>draw</span><span>Madrid win</span></div>''', "by xG")

p_ = I["prob_previa"]
SORPRESA = tarjeta("How big a surprise?", f'''
<div style="display: flex; align-items: center; gap: 14px">
<span style="{DISP}; font-size: 48px; line-height: 1; color: {NARANJA}">{int(p_[0])}%</span>
<span style="font-size: 13px; color: {SOFT}">Atlético's win chance before kick-off by Elo. Madrid were favourites at {int(p_[2])}%.</span></div>
{tres(int(p_[0]), int(p_[1]), int(p_[2]), CA, CB, 26, 14)}''', "pre-match")

ea, ed = I["elo_antes"], I["elo_despues"]
ELO = tarjeta("Elo after this game", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px">{escudo(n, 30, KA if n == "Atlético Madrid" else KB)}<span style="flex-grow: 1; font-size: 14px; font-weight: 700">{eq(n)[0]}</span>'
    f'<span style="font-size: 13px; color: {MUT}">{int(a)} →</span><span style="{DISP}; font-size: 22px">{int(d)}</span>'
    f'{chip(("+" if d >= a else "") + str(int(d - a)), "#1F3A16" if d >= a else "#3A2412", LIMA if d >= a else "#FFB27A")}</div>'
    for n, a, d in (("Atlético Madrid", ea[0], ed[0]), ("Real Madrid", ea[1], ed[1])))
    + f'<span style="font-size: 12px; color: {MUT}">Winning as the underdog moves Elo more than a routine win.</span>', "strength rating")

s = I["stats"]
STATS = tarjeta("Key stats", "".join([
    fila_stat("Expected goals", I["xg"][0], I["xg"][1], lambda v: f"{v:.2f}", CA[0], CB[0]),
    fila_stat("Possession", s["possession"][0] * 100, s["possession"][1] * 100, lambda v: f"{v:.0f}%", CA[0], CB[0]),
    fila_stat("Shots on target", s["shots_on_target"][0], s["shots_on_target"][1], ch=CA[0], ca=CB[0]),
    fila_stat("Big chances", s["big_chances_created"][0], s["big_chances_created"][1], ch=CA[0], ca=CB[0]),
    fila_stat("Fouls", s["fouls"][0], s["fouls"][1], ch=CA[0], ca=CB[0])]), f'<a href="Stats.dc.html" style="color: #8FA2FF; font-weight: 600">All stats</a>')

jug = I["jugadores"][:5]
NOTAS = tarjeta("Best players", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px">{franjas(KA if j["equipo"] == "Atlético Madrid" else KB, 26)}<div style="flex-grow: 1; display: flex; flex-direction: column">'
    f'<span style="font-size: 14px; font-weight: 700">{j["jugador"]}</span><span style="font-size: 12px; color: {MUT}">{j["pos"]} · {j["min"]}\'{" · 1 goal" if j["goles"] else ""}</span></div>'
    f'<span style="padding: 3px 9px; border-radius: 9px; background: {LIMA if j["nota"] >= 7.5 else "#3A4256"}; color: {BG if j["nota"] >= 7.5 else TXT}; {DISP}; font-size: 15px">{j["nota"]:.1f}</span></div>'
    for j in jug), "rating")

gk = [g for g in I["porteros"] if g["evitados"] is not None]


def gk_fila(g):
    ev_ = g["evitados"]
    t = ("+" if ev_ >= 0 else "") + f"{ev_:.2f} goals saved"
    c = chip(t, "#1F3A16" if ev_ >= 0 else "#3A2412", LIMA if ev_ >= 0 else "#FFB27A")
    return (f'<div style="display: flex; align-items: center; gap: 10px">{franjas(KA if g["equipo"] == "Atlético Madrid" else KB, 26)}<span style="flex-grow: 1; font-size: 14px; font-weight: 700">{g["jugador"]}</span>'
            f'<span style="font-size: 12px; color: {MUT}">{g["paradas"]} saves</span>{c}</div>')


PORTERO = tarjeta("Goalkeepers", "".join(gk_fila(g) for g in gk) + f'<span style="font-size: 12px; color: {MUT}">Goals saved = expected goals of shots on target minus goals conceded. Courtois kept it close.</span>', "shot-stopping")

ap, ci = I["cuotas"]["apertura"], I["cuotas"]["cierre"]
MERCADO = tarjeta("What the market said", f'''
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
{"".join(f'<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">{k}</span><span style="{DISP}; font-size: 20px">{c:.2f}</span><span style="display: block; font-size: 11px; color: {MUT}">opened {a:.2f}</span></div>' for k, a, c in (("Atlético", ap[0], ci[0]), ("Draw", ap[1], ci[1]), ("Madrid", ap[2], ci[2])))}
</div><span style="font-size: 12px; color: {MUT}">Closing odds, average of books. The market barely moved and backed Madrid until kick-off.</span>''', "closing odds")

cuerpo = cabecera("Report") + HISTORIA + MERECIDO + SORPRESA + ELO + STATS + NOTAS + PORTERO + MERCADO
page("Report.dc.html", "Atlético 2-1 Real Madrid report", 390, 3560, raiz(3560, cuerpo), JS0, nav_active="m")

# ---------------------------------------------------------------- estadísticas completas
def g(k):
    return float(M["l_" + k]), float(M["v_" + k])


GRUPOS = [("Attack", [("Expected goals", "expected_goals", lambda v: f"{v:.2f}"), ("Shots on target", "shots_on_target", None),
                      ("Shots off target", "shots_off_target", None), ("Blocked shots", "blocked_shots", None),
                      ("Inside the box", "shots_within_penalty_area", None), ("Big chances", "big_chances_created", None)]),
          ("Passing", [("Passes", "total_passes", None), ("Into final third", "passes_into_final_third", None),
                       ("Key passes", "key_passes", None), ("Crosses", "crosses", None)]),
          ("Defending", [("Tackles", "tackles", None), ("Interceptions", "interceptions", None), ("Clearances", "clearances", None),
                         ("Saves", "goalkeeper_saves", None)]),
          ("Discipline", [("Fouls", "fouls", None), ("Yellow cards", "yellow_cards", None), ("Red cards", "red_cards", None),
                          ("Offsides", "offsides", None)])]
bloques = ""
for tit, filas in GRUPOS:
    cuerpo_g = ""
    for nombre, k, fmt in filas:
        h_, a_ = g(k)
        cuerpo_g += fila_stat(nombre, h_, a_, fmt or (lambda v: f"{v:.0f}"), CA[0], CB[0])
    bloques += tarjeta(tit, cuerpo_g)
pos_l, pos_v = g("possession")
POSESION = f'''<section style="margin: 0 12px; padding: 18px 16px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; display: flex; align-items: center; gap: 16px">
<svg width="120" height="120" viewBox="0 0 132 132" role="img" aria-label="Possession Atlético {pos_l * 100:.0f} percent"><circle cx="66" cy="66" r="52" fill="none" stroke="{CB[0]}" stroke-width="14"></circle><circle cx="66" cy="66" r="52" fill="none" stroke="{CA[0]}" stroke-width="14" stroke-dasharray="{pos_l * 326.7:.1f} 326.7" transform="rotate(-90 66 66)"></circle>
<text x="66" y="64" text-anchor="middle" fill="{TXT}" font-family="Archivo, sans-serif" font-weight="800" font-size="30">{pos_l * 100:.0f}%</text><text x="66" y="82" text-anchor="middle" fill="{MUT}" font-family="Instrument Sans, sans-serif" font-size="11">possession</text></svg>
<div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: {SOFT}"><span>Atlético had the ball {pos_l * 100:.0f}% of the time and made {int(g("total_passes")[0])} passes to {int(g("total_passes")[1])}.</span><span>Madrid spent the second half with ten men.</span></div></section>'''
page("Stats.dc.html", "Match stats", 390, 2520, raiz(2520, cabecera("Stats", True) + POSESION + bloques), JS0, nav_active="m")

# ---------------------------------------------------------------- alineaciones reales
A = D["alineaciones_informe"]


def rc(n):
    if n is None:
        return ("#3A4256", TXT, "–")
    return (LIMA, BG, f"{n:.1f}") if n >= 7.5 else (("#3A4256", TXT, f"{n:.1f}") if n >= 6.5 else (NARANJA, BG, f"{n:.1f}"))


def dibuja(lineas, arriba, color):
    out = ""
    n_l = len(lineas)
    for i, linea in enumerate(lineas):
        y = (6 + i * (42 / (n_l - 1))) if arriba else (94 - i * (42 / (n_l - 1)))
        k = len(linea)
        for j, p in enumerate(linea):
            x = 50 if k == 1 else 12 + j * (76 / (k - 1))
            bg, fg, t = rc(p["nota"])
            nombre = p["jugador"].split(" ")[-1] if p["jugador"] != "?" else "?"
            out += (f'<div style="position: absolute; left: {x:.1f}%; top: {y:.1f}%; width: 70px; margin-left: -35px; margin-top: -22px; display: flex; flex-direction: column; align-items: center; gap: 3px">'
                    f'<div style="position: relative; width: 32px; height: 32px"><span style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(90deg, {color["c1"]} 0 50%, {color["c2"]} 50% 100%); display: block; box-shadow: 0 0 0 2px {color["c1"]}, 0 0 0 3px rgba(0,0,0,0.6)"></span>'
                    f'<span style="position: absolute; right: -16px; top: -8px; padding: 1px 6px; border-radius: 8px; background: {bg}; color: {fg}; font-size: 10px; font-weight: 800">{t}</span></div>'
                    f'<span style="font-size: 11px; font-weight: 700; white-space: nowrap; text-shadow: 0 1px 2px #000">{nombre}</span></div>')
    return out


CAMPO = f'''<section style="margin: 0 12px; position: relative; height: 700px; border-radius: 26px; background: #0F1B15; border: 1px solid #1F3026; overflow: hidden" aria-label="Both starting elevens">
<div style="position: absolute; left: 14px; right: 14px; top: 14px; bottom: 14px; border: 2px solid #25392E; border-radius: 6px"></div>
<div style="position: absolute; left: 14px; right: 14px; top: 349px; height: 2px; background: #25392E"></div>
<div style="position: absolute; left: 50%; top: 350px; width: 88px; height: 88px; margin: -44px 0 0 -44px; border: 2px solid #25392E; border-radius: 50%"></div>
<div style="position: absolute; left: 50%; top: 14px; width: 156px; height: 66px; margin-left: -78px; border: 2px solid #25392E; border-top: none"></div>
<div style="position: absolute; left: 50%; bottom: 14px; width: 156px; height: 66px; margin-left: -78px; border: 2px solid #25392E; border-bottom: none"></div>
{dibuja(A["local"]["lineas"], True, KA)}{dibuja(A["visitante"]["lineas"], False, KB)}
</section>'''
FORM = f'''<div style="display: flex; justify-content: space-between; align-items: center; padding: 0 16px">
<div style="display: flex; align-items: center; gap: 8px">{franjas(KA)}<span style="font-size: 14px; font-weight: 700">Atlético</span>{chip(A["local"]["formacion"])}</div>
<div style="display: flex; align-items: center; gap: 8px">{chip(A["visitante"]["formacion"])}<span style="font-size: 14px; font-weight: 700">Real Madrid</span>{franjas(KB)}</div></div>'''
LEY = f'''<div style="display: flex; gap: 14px; padding: 0 16px; font-size: 11px; color: {MUT}; align-items: center"><span style="font-weight: 700; color: {TXT}">Rating</span>
<span style="display: flex; align-items: center; gap: 5px"><span style="padding: 1px 7px; border-radius: 8px; background: {LIMA}; color: {BG}; font-weight: 800">7.5+</span>strong</span>
<span style="display: flex; align-items: center; gap: 5px"><span style="padding: 1px 7px; border-radius: 8px; background: #3A4256; color: #FFFFFF; font-weight: 800">6.5</span>fine</span>
<span style="display: flex; align-items: center; gap: 5px"><span style="padding: 1px 7px; border-radius: 8px; background: {NARANJA}; color: {BG}; font-weight: 800">&lt;6.5</span>weak</span></div>'''
page("Alineacion.dc.html", "Lineups", 390, 1180, raiz(1180, cabecera("Lineups", True) + FORM + CAMPO + LEY), JS0, nav_active="m")
print("s5b ok")
