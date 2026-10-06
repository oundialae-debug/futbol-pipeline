"""De kits_camiseta.json (colores medidos en los dibujos de Wikipedia) a
equipaciones.json, la tabla que usa 2yellow: por equipo, hasta tres
equipaciones [principal, secundario, un_color].

Regla: principal = color que más ocupa la camiseta. Si el segundo color ocupa
al menos el 15% (rayas, cuadros, mangas), la camiseta es de dos colores y ese
es el secundario; si no, es de un color y el secundario es el del pantalón.
Las correcciones a mano (CORREGIR) van con su motivo.
"""
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
NEGRO_SOMBRA = 0.06   # líneas de dibujo negras: por debajo de esto no cuentan

# Correcciones a mano, con motivo. Formato: equipo: {nº de equipación (0, 1, 2): [principal, secundario, un_color]}
RAYAS = "rayas o cuadros a partes iguales: manda el color del club, no el que más píxeles tiene en el dibujo"
CORREGIR = {
    # RAYAS
    "Croatia": {0: ["#E30613", "#FFFFFF", False]},
    "Argentina": {0: ["#75AADB", "#FFFFFF", False]},          # el dibujo trae las rayas celestes; el fondo blanco las tapaba
    "Atlético Madrid": {0: ["#CB3524", "#FFFFFF", False]},
    "Athletic Club": {0: ["#EE2523", "#FFFFFF", False]},
    "Real Sociedad": {0: ["#0042FF", "#FFFFFF", False]},
    "Girona": {0: ["#D7182A", "#FFFFFF", False]},
    "Espanyol": {0: ["#1E6FC8", "#FFFFFF", False]},
    "Alavés": {0: ["#1F4E9E", "#FFFFFF", False]},
    "Deportivo La Coruña": {0: ["#2B67C2", "#FFFFFF", False], 2: ["#2B67C2", "#FFFFFF", False]},
    "Real Betis": {0: ["#0BB363", "#FFFFFF", False]},
    "Malaga": {0: ["#5AA0D8", "#FFFFFF", False]},
    "Barcelona": {0: ["#A50044", "#004D98", False]},
    "Mallorca": {0: ["#E2001A", "#111111", True]},             # roja con pantalón negro; el dibujo sale casi negro
    "Czech Republic": {0: ["#DD0000", "#11457E", True],          # roja lisa, pantalón azul (el blanco del dibujo son detalles)
                       1: ["#FFFFFF", "#11457E", True]},       # blanca con detalles azules
    # --- 2yellow redes, 06/10/2026: clubes de las 5 grandes y Champions ---
    # RAYAS / color del club (el dibujo da más píxeles al color que no es el del club)
    "Inter": {0: ["#0068A8", "#000000", False]},
    "AC Milan": {0: ["#FB090B", "#000000", False]},
    "Atalanta": {0: ["#1E71B8", "#000000", False]},
    "Bayer Leverkusen": {0: ["#E32221", "#000000", False]},
    "Bournemouth": {0: ["#DA291C", "#000000", False]},
    "Paris Saint Germain": {0: ["#004170", "#DA291C", False]},   # azul marino con franja roja; el dibujo sacaba el rojo
    "Toulouse": {0: ["#5F00B5", "#FFFFFF", False]},              # "Les Violets": manda el violeta
    "Crystal Palace": {0: ["#1B458F", "#C4122E", False]},        # rayas rojas y azules; el dibujo salió blanco
    # una camiseta lisa sin segundo color en la ficha (secundario = color de su escudo/detalles)
    "Real Madrid": {0: ["#FFFFFF", "#1E2B5C", True]},
    "Sevilla FC": {0: ["#FFFFFF", "#D8262F", True]},
    "Villarreal": {0: ["#FFE11F", "#005187", True]},
    "Tottenham": {0: ["#FFFFFF", "#132257", True]},
    "Marseille": {0: ["#FFFFFF", "#2FAEE0", True]},
    "Auxerre": {0: ["#FFFFFF", "#0055A4", True]},
    "Borussia Mönchengladbach": {0: ["#FFFFFF", "#000000", True]},
    "FC Koln": {0: ["#FFFFFF", "#ED1C24", True]},
    "FSV Mainz 05": {0: ["#ED1C24", "#FFFFFF", True]},
    "Monza": {0: ["#E30613", "#FFFFFF", True]},
    "Brighton": {0: ["#0057B8", "#FFFFFF", False]},             # rayas azules y blancas
    "Estac Troyes": {0: ["#0055A4", "#FFFFFF", True]},
    "Paris FC": {0: ["#000060", "#FFFFFF", True]},
    "SC Paderborn 07": {0: ["#005CA9", "#000000", True]},        # azul y negro; el dibujo salió negro
    "Venezia": {0: ["#000000", "#F26522", True]},                # negro, naranja y verde
    # sin ficha de equipaciones utilizable en Wikipedia
    "Frosinone": {0: ["#FFED00", "#0047AB", True]},
    "Olympiakos Piraeus": {0: ["#E2001A", "#FFFFFF", False]},
    # sin ficha de equipaciones en Wikipedia (comprobado: la página no tiene los campos)
    "Sweden": {0: ["#FECC00", "#005BAC", True], 1: ["#005BAC", "#FECC00", True]},
}


def hexa(h):
    h = (h or "").strip().lstrip("#").upper()
    return "#" + h if len(h) == 6 else None


def kit(x):
    cols, partes = x["colores"], x["partes"]
    pares = [(c, p) for c, p in zip(cols, partes) if not (c == "#000000" and p < NEGRO_SOMBRA)]
    if not pares:
        return None
    c1 = pares[0][0]
    if len(pares) > 1 and pares[1][1] >= 0.15:
        return [c1, pares[1][0], False]
    return [c1, hexa(x.get("pantalon")) or (pares[1][0] if len(pares) > 1 else "#F4F4F4"), True]


med = json.loads((AQUI / "kits_camiseta.json").read_text())
out = {}
for e in CORREGIR:
    med.setdefault(e, [])
for e, ks in med.items():
    lista = [k for k in (kit(x) for x in ks) if k]
    for i, v in CORREGIR.get(e, {}).items():
        if i < len(lista):
            lista[i] = v
        else:
            lista.append(v)
    if lista:
        out[e] = lista
(AQUI / "equipaciones.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
for e, ks in out.items():
    print(f"{e:24s}", " | ".join(f"{a} {b} {'1c' if u else '2c'}" for a, b, u in ks))
