"""Logotipo de 2yellow: dos tarjetas amarillas; donde se solapan, roja."""
Y, R, D = "#FFD21F", "#FF3B3B", "#0A0C11"

def icono(size, uid, fondo=D, amarillo=Y, rojo=R, borde=None):
    borde = borde or fondo
    a = 'x="7" y="7" width="20" height="30" rx="3.2" transform="rotate(-14 17 22)"'
    b = 'x="21" y="11" width="20" height="30" rx="3.2" transform="rotate(10 31 26)"'
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 48 48" aria-hidden="true">'
            f'<defs><clipPath id="cA{uid}"><rect {a}></rect></clipPath></defs>'
            f'<rect {a} fill="{amarillo}"></rect>'
            f'<rect {b} fill="{amarillo}" stroke="{borde}" stroke-width="2"></rect>'
            f'<rect {b} fill="{rojo}" stroke="{borde}" stroke-width="2" clip-path="url(#cA{uid})"></rect>'
            f'</svg>')

def palabra(px, color="#F1F3F8", dos=Y):
    return (f'<span style="font-family: \'Archivo\', sans-serif; font-stretch: 78%; font-weight: 900; '
            f'font-size: {px}px; line-height: 1; letter-spacing: -0.5px; color: {color}">'
            f'<span style="color: {dos}">2</span>yellow</span>')
