from common import page
from real_ui import *
from equipaciones import KITS, kit, colores_partido, n_kits, se_parecen

LIGA26 = [f["equipo"] for f in D["tabla_elo"]["filas"]]


def marcador(a, b, ga, gb):
    ka, kb = colores_partido(a, b)
    return (f'<div style="display: flex; align-items: stretch; height: 44px; border-radius: 12px; overflow: hidden; background: #161A23; border: 1px solid {BORDE}">'
            f'<span style="width: 8px; background: {ka["c1"]}"></span><span style="width: 8px; background: {ka["c2"]}"></span>'
            f'<span style="flex-grow: 1; padding: 0 12px; display: flex; align-items: center; font-size: 14px; font-weight: 700">{eq(a)[1]}</span>'
            f'<span style="padding: 0 12px; display: flex; align-items: center; background: {BG}; {DISP}; font-size: 22px">{ga}–{gb}</span>'
            f'<span style="flex-grow: 1; padding: 0 12px; display: flex; align-items: center; justify-content: flex-end; font-size: 14px; font-weight: 700">{eq(b)[1]}</span>'
            f'<span style="width: 8px; background: {kb["c2"]}"></span><span style="width: 8px; background: {kb["c1"]}"></span></div>'
            f'<span style="font-size: 12px; color: {MUT}">{eq(a)[0]} vs {eq(b)[0]}{["", " · away in second kit", " · away in third kit"][kb["cual"]] if kb["c1"] == KITS[b][min(kb["cual"], len(KITS[b]) - 1)][0] else " · away in its second colour"}</span>')


filas = "".join(
    f'<div style="display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-top: 1px solid #1E2330">'
    f'<span style="flex-grow: 1; font-size: 14px; font-weight: 600">{eq(t)[0]}</span>'
    + "".join(f'<span style="display: flex; align-items: center; gap: 6px; width: 84px">{franjas(kit(t, i), 24)}<span style="font-size: 12px; color: {MUT}">{n}</span></span>'
              if i < n_kits(t) else '<span style="width: 84px"></span>' for i, n in enumerate(("home", "away", "third")))
    + '</div>'
    for t in LIGA26)
_n = sum(1 for a in LIGA26 for b in LIGA26 if a != b)
_malos = sum(1 for a in LIGA26 for b in LIGA26 if a != b and se_parecen(*colores_partido(a, b)))
CHOQUES = f"No clashes left across all {_n} LaLiga pairings." if not _malos else f"{_malos} of {_n} LaLiga pairings still clash."
print("choques LaLiga:", _malos, "de", _n)
ejemplos = "".join(f'<div style="display: flex; flex-direction: column; gap: 6px">{marcador(*m)}</div>' for m in (
    ("Real Sociedad", "Deportivo La Coruña", 1, 0), ("Real Madrid", "Valencia", 2, 0), ("Sevilla FC", "Real Madrid", 1, 1),
    ("Athletic Club", "Atlético Madrid", 0, 2), ("Barcelona", "Levante", 3, 1), ("Atlético Madrid", "Real Madrid", 2, 1)))
body = f'''<div style="width: 880px; height: 1320px; box-sizing: border-box; padding: 40px; background: {BG}; display: flex; gap: 32px">
<div style="flex: 1 1 0; display: flex; flex-direction: column; gap: 14px">
<span style="{DISP}; font-size: 34px">Club colours</span>
<span style="font-size: 13px; color: {SOFT}">2026/27 home, away and third kits. Home first; the away side switches to its second or third kit when the colours clash.</span>
<section style="border-radius: 22px; background: {CARD}; border: 1px solid {BORDE}; overflow: hidden">{filas}</section>
</div>
<div style="width: 380px; display: flex; flex-direction: column; gap: 14px">
<span style="{DISP}; font-size: 34px">Clash check</span>
<span style="font-size: 13px; color: {SOFT}">{CHOQUES}</span>
{ejemplos}
</div></div>'''
page("Kits.dc.html", "Club colours", 880, 1320, body, "class Component extends DCLogic {\n  renderVals() { return {}; }\n}")
print("kits ok")
