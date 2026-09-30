"""Piezas comunes para las pantallas con datos reales de 2yellow."""
import json
from pathlib import Path
from logo import icono, palabra
from equipaciones import kit, colores_partido, KITS

APP = Path(__file__).resolve().parents[2]
D = json.loads((APP / "datos_app.json").read_text())
DJ = json.loads((APP / "datos.json").read_text())

BG, CARD, BORDE, SUB, MUT, TXT, SOFT = "#0A0C11", "#12151C", "#232838", "#1A1E28", "#8E96AA", "#F1F3F8", "#C6CBD8"
AZUL, LIMA, NARANJA, ROJO, AMARILLO = "#4A63FF", "#C8FF3D", "#FF8A3D", "#FF3B3B", "#FFD21F"
DISP = "font-family: 'Archivo', sans-serif; font-stretch: 78%; font-weight: 800"

EQ = {  # nombre de datos -> (corto, sigla, fondo, texto)
    "Real Madrid": ("Real Madrid", "RMA", "#F1F3F8", "#0A0C11"), "Atlético Madrid": ("Atlético", "ATM", "#CB3524", "#FFFFFF"),
    "Villarreal": ("Villarreal", "VIL", "#FFE11F", "#0A0C11"), "Barcelona": ("Barcelona", "BAR", "#A50044", "#FFFFFF"),
    "Real Betis": ("Betis", "BET", "#0BB363", "#0A0C11"), "Sevilla FC": ("Sevilla", "SEV", "#D8262F", "#FFFFFF"),
    "Real Sociedad": ("Real Sociedad", "RSO", "#1F5FB0", "#FFFFFF"), "Alavés": ("Alavés", "ALA", "#1F4E9E", "#FFFFFF"),
    "Deportivo La Coruña": ("Deportivo", "DEP", "#2B67C2", "#FFFFFF"), "Athletic Club": ("Athletic", "ATH", "#C8252F", "#FFFFFF"),
    "Getafe": ("Getafe", "GET", "#1B55A3", "#FFFFFF"), "Rayo Vallecano": ("Rayo", "RAY", "#E8ECF3", "#C8102E"),
    "Osasuna": ("Osasuna", "OSA", "#B3262E", "#FFFFFF"), "Celta de Vigo": ("Celta", "CEL", "#8BC4EA", "#0A0C11"),
    "Espanyol": ("Espanyol", "ESP", "#2A64B8", "#FFFFFF"), "Racing Santander": ("Racing", "RAC", "#2E8B57", "#FFFFFF"),
    "Levante": ("Levante", "LEV", "#7A1F3D", "#FFFFFF"), "Elche": ("Elche", "ELC", "#2E8B57", "#FFFFFF"),
    "Valencia": ("Valencia", "VAL", "#E8ECF3", "#0A0C11"), "Malaga": ("Málaga", "MAL", "#5AA0D8", "#0A0C11"),
    "Oviedo": ("Oviedo", "OVI", "#1D4E9E", "#FFFFFF"), "Mallorca": ("Mallorca", "MLL", "#C8102E", "#FFFFFF"),
    "Girona": ("Girona", "GIR", "#C8102E", "#FFFFFF"),
}
CORTO_A_LARGO = {v[0]: k for k, v in EQ.items()}
CORTO_A_LARGO.update({"Málaga": "Malaga", "Rayo": "Rayo Vallecano", "Athletic": "Athletic Club"})


def eq(nombre):
    n = CORTO_A_LARGO.get(nombre, nombre)
    return EQ.get(n, (nombre, nombre[:3].upper(), "#3A4256", "#FFFFFF"))


def escudo(nombre, px=24, k=None):
    """Escudo provisional con los colores de la equipación que lleva ese día."""
    c, s, _, _ = eq(nombre)
    k = k or kit(CORTO_A_LARGO.get(nombre, nombre))
    fs = max(7, round(px * 0.3))
    anillo = max(2, round(px / 18))
    return (f'<span style="width: {px}px; height: {px}px; flex-shrink: 0; border-radius: 50%; background: {k["c1"]}; color: {k["texto"]}; '
            f'font-size: {fs}px; font-weight: 800; display: flex; align-items: center; justify-content: center; '
            f'box-shadow: inset 0 0 0 {anillo}px {k["c2"]}">{s}</span>')


def franjas(k, alto=20):
    """Las dos franjas de color junto al nombre, como en el marcador de la TV."""
    return (f'<span aria-hidden="true" style="display: inline-flex; flex-shrink: 0; height: {alto}px; border-radius: 3px; overflow: hidden; box-shadow: 0 0 0 1px rgba(255,255,255,0.14)">'
            f'<span style="width: 5px; background: {k["c1"]}"></span><span style="width: 5px; background: {k["c2"]}"></span></span>')


def kits(local, visitante):
    return colores_partido(CORTO_A_LARGO.get(local, local), CORTO_A_LARGO.get(visitante, visitante))


def num(x, dec=1):
    return f"{x:.{dec}f}" if isinstance(x, (int, float)) else "–"


def tarjeta(titulo, cuerpo, derecha="", extra_style=""):
    der = f'<span style="font-size: 12px; color: {MUT}">{derecha}</span>' if derecha else ""
    return (f'<section style="margin: 0 12px; padding: 16px; border-radius: 24px; background: {CARD}; border: 1px solid {BORDE}; '
            f'display: flex; flex-direction: column; gap: 12px; {extra_style}">'
            f'<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 8px">'
            f'<span style="font-size: 16px; font-weight: 700">{titulo}</span>{der}</div>{cuerpo}</section>')


def chip(txt, bg="#1E2330", fg=SOFT):
    return f'<span style="padding: 3px 9px; border-radius: 9px; background: {bg}; color: {fg}; font-size: 11px; font-weight: 700; white-space: nowrap">{txt}</span>'


def barra_dos(h, a, ch=AZUL, ca=NARANJA, alto=7):
    t = (h or 0) + (a or 0) or 1
    wh, wa = round((h or 0) / t * 100), round((a or 0) / t * 100)
    return (f'<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px">'
            f'<div style="height: {alto}px; border-radius: 4px 0 0 4px; background: #1E2330; display: flex; justify-content: flex-end">'
            f'<span style="width: {wh}%; height: {alto}px; border-radius: 4px 0 0 4px; background: {ch}"></span></div>'
            f'<div style="height: {alto}px; border-radius: 0 4px 4px 0; background: #1E2330">'
            f'<span style="display: block; width: {wa}%; height: {alto}px; border-radius: 0 4px 4px 0; background: {ca}"></span></div></div>')


def fila_stat(nombre, h, a, fmt=lambda v: num(v, 0), ch=AZUL, ca=NARANJA):
    return (f'<div style="display: flex; flex-direction: column; gap: 6px">'
            f'<div style="display: flex; justify-content: space-between; align-items: baseline">'
            f'<span style="{DISP}; font-size: 18px; width: 70px">{fmt(h)}</span>'
            f'<span style="font-size: 12px; font-weight: 600; color: {MUT}">{nombre}</span>'
            f'<span style="{DISP}; font-size: 18px; width: 70px; text-align: right">{fmt(a)}</span></div>'
            f'{barra_dos(h, a, ch, ca)}</div>')


def tres(p1, px, p2, c1, c2, alto=44, grande=24):
    return (f'<div style="display: flex; height: {alto}px; border-radius: 14px; overflow: hidden; gap: 3px">'
            f'<div style="width: {p1}%; background: {c1[0]}; color: {c1[1]}; display: flex; align-items: center; justify-content: center; {DISP}; font-size: {grande}px">{p1}</div>'
            f'<div style="width: {px}%; background: #3A4256; display: flex; align-items: center; justify-content: center; {DISP}; font-size: {grande - 4}px">{px}</div>'
            f'<div style="width: {p2}%; background: {c2[0]}; color: {c2[1]}; display: flex; align-items: center; justify-content: center; {DISP}; font-size: {grande - 4}px">{p2}</div></div>')


def sparkline(vals, w=64, h=22, color=LIMA):
    v = [x for x in vals if x is not None]
    if len(v) < 2:
        return ""
    lo, hi = min(v), max(v)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i / (len(v) - 1) * (w - 4) + 2:.1f},{h - 2 - (x - lo) / rng * (h - 4):.1f}" for i, x in enumerate(v))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></polyline></svg>')


def volver(href, sub_1, sub_2, derecha=""):
    return (f'<header style="position: relative; display: flex; align-items: center; gap: 4px; padding: 12px 8px 0 4px">'
            f'<a href="{href}" aria-label="Back" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center">'
            f'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"></path></svg></a>'
            f'<div style="flex-grow: 1; display: flex; flex-direction: column"><span style="font-size: 14px; font-weight: 700">{sub_1}</span>'
            f'<span style="font-size: 12px; color: {SOFT}">{sub_2}</span></div>{derecha}</header>')


def pestañas(activa, enlaces):
    out = [f'<nav aria-label="Sections" style="display: flex; gap: 22px; padding: 0 16px; border-bottom: 1px solid {BORDE}">']
    for n, href in enlaces:
        on = n == activa
        cur = 'aria-current="page"' if on else ""
        out.append(f'<a href="{href}" {cur} style="height: 46px; display: flex; align-items: center; '
                   f'border-bottom: 3px solid {LIMA if on else "transparent"}; color: {TXT if on else MUT}; font-size: 14px; font-weight: 700; white-space: nowrap">{n}</a>')
    out.append("</nav>")
    return "".join(out)


def glow(c1, c2, alto=240):
    return (f'<span style="position: absolute; left: -60px; top: -70px; width: {alto}px; height: {alto}px; border-radius: 50%; background: {c1}; opacity: 0.35; filter: blur(60px)"></span>'
            f'<span style="position: absolute; right: -60px; top: -70px; width: {alto}px; height: {alto}px; border-radius: 50%; background: {c2}; opacity: 0.35; filter: blur(60px)"></span>')


def nota_pie(txt):
    return f'<p style="margin: 0 20px; font-size: 11px; line-height: 1.5; color: {MUT}">{txt}</p>'
