"""Informe post-partido Atlético 2-1 Real Madrid: resumen, estadísticas y alineaciones."""
import pandas as pd
from common import page
from real_ui import *
from s5a_real import raiz, JS0
from logo import icono

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
<span style="font-size: 11px; color: {MUT}">Goals shown per half.</span>''', "after the match")

m_ = I["merecido_xg"]
I2 = DX["informe2"]
MX = I2["merecido"]


def cara(nombre, par, fmt=lambda v: f"{v:.0f}"):
    return (f'<div style="display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-top: 1px solid #1E2330">'
            f'<span style="{DISP}; font-size: 17px; width: 60px; color: {CA[0]}">{fmt(par[0])}</span>'
            f'<span style="font-size: 12px; font-weight: 600; color: {SOFT}">{nombre}</span>'
            f'<span style="{DISP}; font-size: 17px; width: 60px; text-align: right; color: {CB[0]}">{fmt(par[1])}</span></div>')


gk_a, gk_b = MX["porteros"]["Atlético Madrid"], MX["porteros"]["Real Madrid"]
sg = lambda v: ("+" if v >= 0 else "−") + f"{abs(v):.2f}"
MERECIDO = tarjeta("Deserved?", f'''
<div style="display: flex; align-items: center; justify-content: space-between">
<div style="display: flex; flex-direction: column; gap: 2px"><span style="font-size: 12px; color: {MUT}">Expected goals</span><span style="{DISP}; font-size: 36px; line-height: 1"><span style="color: {CA[0]}">{I["xg"][0]:.2f}</span> <span style="color: {MUT}; font-size: 22px">vs</span> <span style="color: {CB[0]}">{I["xg"][1]:.2f}</span></span></div>
{chip("Deserved", "#1F3A16", LIMA)}</div>
<span style="font-size: 13px; color: {SOFT}">Replaying these chances 100 times:</span>
{tres(int(m_[0]), int(m_[1]), int(m_[2]), CA, CB, 40, 20)}
<div style="display: flex; justify-content: space-between; font-size: 12px; color: {MUT}"><span>Atlético win</span><span>draw</span><span>Madrid win</span></div>
<div style="display: flex; flex-direction: column">
{cara("Shots on target", MX["tiros_puerta"])}{cara("Shots off target", MX["tiros_fuera"])}{cara("Shots inside the box", MX["dentro_area"])}
{cara("Big chances", MX["ocasiones"])}{cara("Passes into final third", MX["ultimo_tercio"])}{cara("Key passes", MX["pases_clave"])}
{cara("Keeper saves", MX["paradas"])}</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">{gk_a["jugador"]} · goals prevented</span><span style="{DISP}; font-size: 22px; color: {CA[0]}">{sg(gk_a["evitados"])}</span></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">{gk_b["jugador"]} · goals prevented</span><span style="{DISP}; font-size: 22px; color: {CB[0]}">{sg(gk_b["evitados"])}</span></div></div>
<span style="font-size: 12px; color: {SOFT}">Courtois kept it at 2–1: it could have been more.</span>''', "by xG")

p_ = I["prob_previa"]
SORPRESA = tarjeta("How big a surprise?", f'''
<div style="display: flex; align-items: center; gap: 14px">
<span style="{DISP}; font-size: 48px; line-height: 1; color: {CA[0]}">{int(p_[0])}%</span>
<span style="font-size: 13px; color: {SOFT}">Atlético's win chance before kick-off by Elo. Madrid were favourites at {int(p_[2])}%.</span></div>
{tres(int(p_[0]), int(p_[1]), int(p_[2]), CA, CB, 26, 14)}''', "pre-match")

ea, ed = I["elo_antes"], I["elo_despues"]
ELO = tarjeta("Elo after this game", "".join(
    f'<div style="display: flex; align-items: center; gap: 10px">{escudo(n, 30, KA if n == "Atlético Madrid" else KB)}<span style="flex-grow: 1; font-size: 14px; font-weight: 700">{eq(n)[0]}</span>'
    f'<span style="font-size: 13px; color: {MUT}">{int(a)} →</span><span style="{DISP}; font-size: 22px; color: {(KA if n == "Atlético Madrid" else KB)["barra"]}">{int(d)}</span>'
    f'{chip(("+" if d >= a else "") + str(int(d - a)), "#1F3A16" if d >= a else "#3A2412", LIMA if d >= a else "#FFB27A")}</div>'
    for n, a, d in (("Atlético Madrid", ea[0], ed[0]), ("Real Madrid", ea[1], ed[1])))
, "strength rating")

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


PORTERO = tarjeta("Goalkeepers", "".join(gk_fila(g) for g in gk), "shot-stopping")

NU, CS, RE = I2["nuestro"], I2["casa"], I2["real"]
NOMBRES_1X2 = ["Atlético", "Draw", "Madrid"]


def marca(ok):
    return (f'<span style="width: 22px; height: 22px; border-radius: 50%; background: {"#1F3A16" if ok else "#3A1719"}; color: {LIMA if ok else "#FF8A80"}; '
            f'font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center">{"✓" if ok else "✗"}</span>')


def celda(txt, ok):
    return (f'<div style="display: flex; align-items: center; justify-content: flex-end; gap: 6px"><span style="{DISP}; font-size: 15px">{txt}</span>{marca(ok)}</div>')


def fila_mercado(nombre, nuestro, casa, pasa):
    return (f'<div style="display: grid; grid-template-columns: minmax(0, 1fr) 92px 92px; align-items: center; gap: 8px; padding: 9px 0; border-top: 1px solid #1E2330">'
            f'<span style="font-size: 13px; font-weight: 600">{nombre}</span>{nuestro}{casa}</div>')


i_n, i_c = max(range(3), key=lambda i: NU["1x2"][i]), max(range(3), key=lambda i: CS["1x2"][i])
filas_m = fila_mercado(f"Result · {NOMBRES_1X2[RE['1x2']]} won", celda(f"{NOMBRES_1X2[i_n]} {int(NU['1x2'][i_n])}%", i_n == RE["1x2"]),
                       celda(f"{NOMBRES_1X2[i_c]} {int(CS['1x2'][i_c])}%", i_c == RE["1x2"]), None)
for k, nombre in (("mas15", "Over 1.5 goals"), ("mas25", "Over 2.5 goals"), ("ambos", "Both teams score")):
    pn, pc = NU[k], CS[k][0]
    txt = lambda p_: f"{'Yes' if p_ >= 50 else 'No'} {int(max(p_, 100 - p_))}%"
    filas_m += fila_mercado(nombre, celda(txt(pn), (pn >= 50) == RE[k]), celda(txt(pc), (pc >= 50) == RE[k]), None)
aciertos = lambda d, k1: [i_n == RE["1x2"] if k1 == "n" else i_c == RE["1x2"]] + [((d[k] if k1 == "n" else d[k][0]) >= 50) == RE[k] for k in ("mas15", "mas25", "ambos")]
an, ac = sum(aciertos(NU, "n")), sum(aciertos(CS, "c"))
MERCADO = tarjeta("Our call vs the bookies", f'''
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px">
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}; display: flex; align-items: center; gap: 10px">{icono(28, "rep")}<div style="display: flex; flex-direction: column"><span style="{DISP}; font-size: 22px; line-height: 1">{an} / 4</span><span style="font-size: 11px; color: {MUT}">2yellow right</span></div></div>
<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}; display: flex; flex-direction: column"><span style="{DISP}; font-size: 22px; line-height: 1">{ac} / 4</span><span style="font-size: 11px; color: {MUT}">bookies right</span></div></div>
<div style="display: grid; grid-template-columns: minmax(0, 1fr) 92px 92px; gap: 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.6px; color: {MUT}"><span>MARKET</span><span style="text-align: right">2YELLOW</span><span style="text-align: right">BOOKIES</span></div>
<div style="display: flex; flex-direction: column">{filas_m}</div>
<span style="font-size: 11px; color: {MUT}">Both before kick-off. Bookies: {I2["casas_n"]["1x2"]} books, margin removed.</span>''', "pre-match")

ap, ci = I["cuotas"]["apertura"], I["cuotas"]["cierre"]
ODDS = tarjeta("What the market said", f'''
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px">
{"".join(f'<div style="padding: 10px 12px; border-radius: 14px; background: {SUB}"><span style="display: block; font-size: 11px; color: {MUT}">{k}</span><span style="{DISP}; font-size: 20px">{c:.2f}</span><span style="display: block; font-size: 11px; color: {MUT}">opened {a:.2f}</span></div>' for k, a, c in (("Atlético", ap[0], ci[0]), ("Draw", ap[1], ci[1]), ("Madrid", ap[2], ci[2])))}
</div><span style="font-size: 12px; color: {MUT}">Average of books. Madrid favourites until kick-off.</span>''', "closing odds")

cuerpo = cabecera("Report") + HISTORIA + MERECIDO + SORPRESA + ELO + STATS + NOTAS + PORTERO + ODDS + MERCADO
page("Report.dc.html", "Atlético 2-1 Real Madrid report", 390, 3000, raiz(3000, cuerpo), JS0, nav_active="m")

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
<div style="display: flex; flex-direction: column; gap: 10px; font-size: 13px; color: {SOFT}"><span>Passes <b style="color: {CA[0]}">{int(g("total_passes")[0])}</b> – <b style="color: {CB[0]}">{int(g("total_passes")[1])}</b></span><span>Madrid with ten from 52\'</span></div></section>'''
DU = DX["duelos"]


def zona_html(tit, z, k_at, k_df, n_at, n_df):
    at, df = z["ataque"], z["defensa"]
    gana = at["xg"] >= 1.2  # el ataque manda si generó ocasiones de verdad
    veredicto = chip(f"{n_at} on top", "#1F3A16", LIMA) if gana else chip(f"{n_df} held", "#1E2A66", "#A9B8FF")

    def lado(k, titulo, filas):
        return (f'<div style="flex: 1 1 0; min-width: 0; padding: 12px; border-radius: 16px; background: {SUB}; display: flex; flex-direction: column; gap: 8px">'
                f'<div style="display: flex; align-items: center; gap: 6px">{franjas(k, 16)}<span style="font-size: 12px; font-weight: 700">{titulo}</span></div>'
                + "".join(f'<div style="display: flex; justify-content: space-between; align-items: baseline"><span style="font-size: 12px; color: {MUT}">{a_}</span>'
                          f'<span style="{DISP}; font-size: 17px; color: {k["barra"]}">{b_}</span></div>' for a_, b_ in filas) + '</div>')
    return tarjeta(tit, f'<div style="display: flex; gap: 8px; align-items: stretch">'
                   + lado(k_at, f"{n_at} attack", [("xG", f"{at['xg']:.2f}"), ("Shots", at["tiros"]), ("Dribbles", at["regates"]), ("Duels won", f"{at['duelos']}/{at['duelos_t']}")])
                   + '<span style="align-self: center; {DISP}; font-size: 13px; color: {MUT}">VS</span>'.replace("{DISP}", DISP).replace("{MUT}", MUT)
                   + lado(k_df, f"{n_df} defence", [("Tackles", df["entradas"]), ("Interceptions", df["intercep"]), ("Duels won", f"{df['duelos']}/{df['duelos_t']}"), ("Avg rating", f"{df['nota']:.1f}")])
                   + '</div>', veredicto)


def apellido(n):
    if n == "?":
        return "?"
    t = n.split(" ")
    return t[0] if t[-1] in ("Júnior", "Junior") else t[-1]


def duelo(p, k_at, k_df):
    a_, d_ = p["at"], p["df"]
    gana_a = (a_["nota"] or 0) >= (d_["nota"] or 0)

    def caja(j, k, lado, gana, datos):
        return (f'<div style="flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; gap: 4px; align-items: {"flex-start" if lado == "i" else "flex-end"}">'
                f'<div style="display: flex; align-items: center; gap: 6px; flex-direction: {"row" if lado == "i" else "row-reverse"}">{franjas(k, 18)}<span style="font-size: 14px; font-weight: 700; white-space: nowrap">{apellido(j["jugador"])}</span></div>'
                f'<span style="font-size: 11px; color: {MUT}">{datos} · {j["min"]}\'</span>'
                f'<span style="padding: 2px 8px; border-radius: 8px; background: {k["barra"] if gana else "#2A3040"}; color: {k["texto"] if gana else TXT}; {DISP}; font-size: 15px">{j["nota"]:.1f}</span></div>')
    da = f'{a_["duelos"]}/{a_["duelos_t"]} duels · {a_["regates"]} dribbles'
    dd = f'{d_["duelos"]}/{d_["duelos_t"]} duels · {d_["entradas"] + d_["intercep"]} tkl+int'
    return (f'<div style="display: flex; align-items: center; gap: 8px; padding: 10px 0; border-top: 1px solid #1E2330">'
            + caja(a_, k_at, "i", gana_a, da) + f'<span style="{DISP}; font-size: 12px; color: {MUT}">VS</span>' + caja(d_, k_df, "d", not gana_a, dd) + '</div>')


ZONAS = (zona_html("Atlético attack vs Madrid defence", DU["atm_ataque"], KA, KB, "Atlético", "Madrid")
         + zona_html("Madrid attack vs Atlético defence", DU["rma_ataque"], KB, KA, "Madrid", "Atlético"))
DUELOS = tarjeta("Head to head", "".join(duelo(p, KA, KB) for p in DU["pares_atm"]) + "".join(duelo(p, KB, KA) for p in DU["pares_rma"])
                 + f'<span style="font-size: 11px; color: {MUT}">Paired by position in the lineup. Rating decides.</span>', "who beat whom")
page("Stats.dc.html", "Match stats", 390, 3000, raiz(3000, cabecera("Stats", True) + POSESION + ZONAS + DUELOS + bloques), JS0, nav_active="m")

# ---------------------------------------------------------------- alineaciones reales
A = D["alineaciones_informe"]


def rc(n):
    if n is None:
        return ("#3A4256", TXT, "–")
    return (LIMA, BG, f"{n:.1f}") if n >= 7.5 else (("#3A4256", TXT, f"{n:.1f}") if n >= 6.5 else (NARANJA, BG, f"{n:.1f}"))


# Posiciones por dibujo, desde el punto de vista de cada equipo: x de su izquierda (0) a su
# derecha (100), profundidad de su portería (0) a medio campo (1). Las alineaciones vienen
# de izquierda a derecha en cada línea.
FORMAS = {
    "4-4-2": [[(50, .05)], [(12, .30), (37, .20), (63, .20), (88, .30)], [(13, .58), (38, .50), (62, .50), (87, .58)], [(36, .86), (64, .82)]],
    "4-2-3-1": [[(50, .05)], [(12, .30), (37, .20), (63, .20), (88, .30)], [(36, .45), (64, .45)], [(14, .72), (50, .68), (86, .72)], [(50, .90)]],
    "4-3-3": [[(50, .05)], [(12, .30), (37, .20), (63, .20), (88, .30)], [(30, .50), (50, .44), (70, .50)], [(16, .82), (50, .88), (84, .82)]],
}


def dibuja(lineas, arriba, color):
    out = ""
    forma = FORMAS.get("-".join(str(len(l_)) for l_ in lineas[1:]))
    for i, linea in enumerate(lineas):
        for j, p in enumerate(linea):
            if forma:
                x, d = forma[i][j]
            else:
                x, d = (50 if len(linea) == 1 else 12 + j * 76 / (len(linea) - 1)), 0.05 + i * 0.85 / (len(lineas) - 1)
            # el de arriba ataca hacia abajo: su izquierda cae a la derecha de la pantalla
            sx = 100 - x if arriba else x
            sy = 3 + d * 44 if arriba else 97 - d * 44
            bg, fg, t = rc(p["nota"])
            nombre = apellido(p["jugador"])
            out += (f'<div style="position: absolute; left: {sx:.1f}%; top: {sy:.1f}%; width: 76px; margin-left: -38px; margin-top: -18px; display: flex; flex-direction: column; align-items: center; gap: 2px">'
                    f'<div style="position: relative; width: 28px; height: 28px"><span style="width: 28px; height: 28px; border-radius: 50%; background: {color["c1"] if color.get("una") else "linear-gradient(90deg, " + color["c1"] + " 0 50%, " + color["c2"] + " 50% 100%)"}; display: block; box-shadow: 0 0 0 2px {color["c2"] if color.get("una") else color["c1"]}, 0 0 0 3px rgba(0,0,0,0.6)"></span>'
                    f'<span style="position: absolute; right: -18px; top: -7px; padding: 1px 5px; border-radius: 7px; background: {bg}; color: {fg}; font-size: 10px; font-weight: 800">{t}</span></div>'
                    f'<span style="max-width: 76px; overflow: hidden; text-overflow: ellipsis; font-size: 10.5px; font-weight: 700; white-space: nowrap; text-shadow: 0 1px 2px #000">{nombre}</span></div>')
    return out


CAMPO = f'''<section style="margin: 0 12px; position: relative; height: 620px; border-radius: 26px; background: #0F1B15; border: 1px solid #1F3026; overflow: hidden" aria-label="Both starting elevens">
<div style="position: absolute; left: 14px; right: 14px; top: 14px; bottom: 14px; border: 2px solid #25392E; border-radius: 6px"></div>
<div style="position: absolute; left: 14px; right: 14px; top: 309px; height: 2px; background: #25392E"></div>
<div style="position: absolute; left: 50%; top: 310px; width: 88px; height: 88px; margin: -44px 0 0 -44px; border: 2px solid #25392E; border-radius: 50%"></div>
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
page("Alineacion.dc.html", "Lineups", 390, 1010, raiz(1010, cabecera("Lineups", True) + FORM + CAMPO + LEY), JS0, nav_active="m")
print("s5b ok")
