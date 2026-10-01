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
CORREGIR = {}


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
