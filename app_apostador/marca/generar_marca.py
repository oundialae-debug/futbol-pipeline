"""Paquete de marca de 2yellow: iconos, favicons, perfiles, logotipos y cabeceras.
Todo sale del logo aprobado (diseno_nuevo/generador/logo.py). Chromium dibuja los PNG.
Uso: python3 generar_marca.py   (escribe en app_apostador/marca/2yellow_brand/)
"""
import base64
import io
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "diseno_nuevo" / "generador"))
from logo import icono, palabra, Y, R, D  # noqa: E402

OUT = AQUI / "2yellow_brand"
shutil.rmtree(OUT, ignore_errors=True)
for c in ("icon", "favicon", "app-icon", "profile", "logo", "wordmark", "social"):
    (OUT / c).mkdir(parents=True)
FUENTE = AQUI / "fuentes" / "Archivo-latin.woff2"     # Archivo, licencia OFL (Google Fonts)
F64 = base64.b64encode(FUENTE.read_bytes()).decode()
CLARO, TINTA, OSCURO_2 = "#F4F2EC", "#0A0C11", "#E0A800"
FACE = (f"@font-face{{font-family:'Archivo';src:url(data:font/woff2;base64,{F64}) format('woff2');"
        f"font-weight:500 900;font-stretch:62% 125%}}")


# ---------------------------------------------------------------- SVG (vectores de verdad)
def svg_icono(fondo=None, amarillo=Y, rojo=R, borde=D, radio=0, pad=0):
    """Icono en SVG. fondo=None: transparente."""
    a = 'x="7" y="7" width="20" height="30" rx="3.2" transform="rotate(-14 17 22)"'
    b = 'x="21" y="11" width="20" height="30" rx="3.2" transform="rotate(10 31 26)"'
    v = 48 + 2 * pad
    bg = f'<rect x="{-pad}" y="{-pad}" width="{v}" height="{v}" rx="{radio}" fill="{fondo}"/>' if fondo else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad} {-pad} {v} {v}" width="512" height="512">{bg}'
            f'<defs><clipPath id="cA"><rect {a}/></clipPath></defs>'
            f'<rect {a} fill="{amarillo}"/><rect {b} fill="{amarillo}" stroke="{borde}" stroke-width="2"/>'
            f'<rect {b} fill="{rojo}" stroke="{borde}" stroke-width="2" clip-path="url(#cA)"/></svg>')


def svg_logo(texto, dos, fondo=None, borde=D, solo_palabra=False):
    """Icono + «2yellow» con la fuente incrustada (se ve igual sin tener Archivo instalada)."""
    w = 480 if not solo_palabra else 350
    x_txt = 118 if not solo_palabra else 10
    bg = f'<rect width="{w}" height="120" fill="{fondo}"/>' if fondo else ""
    ic = "" if solo_palabra else (
        f'<g transform="translate(6 12) scale(2)"><defs><clipPath id="cB"><rect x="7" y="7" width="20" height="30" rx="3.2" transform="rotate(-14 17 22)"/></clipPath></defs>'
        f'<rect x="7" y="7" width="20" height="30" rx="3.2" transform="rotate(-14 17 22)" fill="{Y}"/>'
        f'<rect x="21" y="11" width="20" height="30" rx="3.2" transform="rotate(10 31 26)" fill="{Y}" stroke="{borde}" stroke-width="2"/>'
        f'<rect x="21" y="11" width="20" height="30" rx="3.2" transform="rotate(10 31 26)" fill="{R}" stroke="{borde}" stroke-width="2" clip-path="url(#cB)"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 120" width="{w * 2}" height="240"><style>{FACE}'
            f'text{{font-family:Archivo,sans-serif;font-weight:900;font-stretch:78%;font-size:100px;letter-spacing:-0.5px}}</style>'
            f'{bg}{ic}<text x="{x_txt}" y="95" fill="{texto}"><tspan fill="{dos}">2</tspan>yellow</text></svg>')


SVGS = {
    "icon/2yellow-icon-dark.svg": svg_icono(D, radio=11, pad=6),
    "icon/2yellow-icon-transparent.svg": svg_icono(None),
    "icon/2yellow-icon-yellow.svg": svg_icono(Y, amarillo=TINTA, borde=Y, radio=11, pad=6),
    "icon/2yellow-icon-light.svg": svg_icono(CLARO, borde=CLARO, radio=11, pad=6),
    "favicon/favicon.svg": svg_icono(D, radio=11, pad=4),
    "logo/2yellow-logo-on-dark.svg": svg_logo("#F1F3F8", Y, fondo=D),
    "logo/2yellow-logo-on-light.svg": svg_logo(TINTA, OSCURO_2, fondo=CLARO, borde=CLARO),
    "logo/2yellow-logo-transparent-for-dark.svg": svg_logo("#F1F3F8", Y),
    "logo/2yellow-logo-transparent-for-light.svg": svg_logo(TINTA, OSCURO_2, borde="#FFFFFF"),
    "wordmark/2yellow-wordmark-for-dark.svg": svg_logo("#F1F3F8", Y, solo_palabra=True),
    "wordmark/2yellow-wordmark-for-light.svg": svg_logo(TINTA, OSCURO_2, solo_palabra=True),
}
for ruta, svg in SVGS.items():
    (OUT / ruta).write_text(svg)

# ---------------------------------------------------------------- PNG (Chromium)
CSS_FUENTE = f"<style>{FACE} body{{margin:0}}</style>"


def lienzo(w, h, fondo, cuerpo, radio=0):
    bg = "transparent" if fondo is None else fondo
    return (f'<!doctype html><html><head><meta charset="utf-8">{CSS_FUENTE}</head><body style="background:transparent">'
            f'<div id="c" style="width:{w}px;height:{h}px;background:{bg};border-radius:{radio}px;display:flex;align-items:center;'
            f'justify-content:center;overflow:hidden;position:relative">{cuerpo}</div></body></html>')


def lockup(px, color="#F1F3F8", dos=Y, fondo_icono=D):
    return (f'<div style="display:flex;align-items:center;gap:{px * 0.17:.0f}px">{icono(int(px * 1.25), "l" + str(px), fondo=fondo_icono)}'
            f'{palabra(px, color=color, dos=dos)}</div>')


def brillo(color, op=0.12, w=900, h=560):
    return (f'<span style="position:absolute;left:50%;top:50%;width:{w}px;height:{h}px;margin:-{h // 2}px 0 0 -{w // 2}px;'
            f'border-radius:50%;background:{color};opacity:{op};filter:blur(120px)"></span>')


PNGS = []   # (ruta, w, h, html, transparente)
# iconos de app: cuadrado a sangre (iOS y Android redondean ellos)
for s in (1024, 512, 192, 180):
    nombre = "apple-touch-icon.png" if s == 180 else f"app-icon-{s}.png"
    PNGS.append((f"app-icon/{nombre}", s, s, lienzo(s, s, D, icono(int(s * 0.8), f"a{s}")), False))
PNGS.append(("app-icon/app-icon-yellow-1024.png", 1024, 1024, lienzo(1024, 1024, Y, icono(820, "ay", fondo=Y, amarillo=TINTA, rojo=R)), False))
# favicons: icono casi a sangre, esquina redondeada (se ve mejor en la pestaña)
for s in (16, 32, 48, 64, 96):
    PNGS.append((f"favicon/favicon-{s}.png", s, s, lienzo(s, s, D, icono(int(s * 0.92), f"f{s}"), radio=max(2, s // 5)), True))
# fotos de perfil (redes: se recortan en círculo, el icono va centrado con margen)
PNGS.append(("profile/profile-dark-1080.png", 1080, 1080, lienzo(1080, 1080, D, brillo(Y, 0.10) + f'<div style="position:relative">{icono(640, "pd")}</div>'), False))
PNGS.append(("profile/profile-yellow-1080.png", 1080, 1080, lienzo(1080, 1080, Y, icono(640, "py", fondo=Y, amarillo=TINTA, rojo=R)), False))
PNGS.append(("profile/profile-dark-400.png", 400, 400, lienzo(400, 400, D, icono(240, "pd4")), False))
PNGS.append(("profile/profile-yellow-400.png", 400, 400, lienzo(400, 400, Y, icono(240, "py4", fondo=Y, amarillo=TINTA, rojo=R)), False))
# logotipo horizontal
PNGS.append(("logo/2yellow-logo-on-dark.png", 2000, 700, lienzo(2000, 700, D, brillo(Y, 0.08, 1200, 500) + f'<div style="position:relative">{lockup(300)}</div>'), False))
PNGS.append(("logo/2yellow-logo-on-light.png", 2000, 700, lienzo(2000, 700, CLARO, lockup(300, TINTA, OSCURO_2, CLARO)), False))
PNGS.append(("logo/2yellow-logo-transparent-for-dark.png", 2000, 700, lienzo(2000, 700, None, lockup(300)), True))
PNGS.append(("logo/2yellow-logo-transparent-for-light.png", 2000, 700, lienzo(2000, 700, None, lockup(300, TINTA, OSCURO_2, "#FFFFFF")), True))
PNGS.append(("logo/2yellow-logo-on-yellow.png", 2000, 700, lienzo(2000, 700, Y, lockup(300, TINTA, TINTA, Y).replace(f'fill="{Y}"', f'fill="{TINTA}"')), False))
# solo la palabra
PNGS.append(("wordmark/2yellow-wordmark-for-dark.png", 1600, 500, lienzo(1600, 500, None, palabra(300)), True))
PNGS.append(("wordmark/2yellow-wordmark-for-light.png", 1600, 500, lienzo(1600, 500, None, palabra(300, color=TINTA, dos=OSCURO_2)), True))
# redes: cabecera de X, portada de YouTube, imagen al compartir enlaces (Open Graph)
lema = '<span style="font-family:Archivo,sans-serif;font-stretch:100%;font-weight:600;color:#C6CBD8;font-size:{}px">Football data, before and after the match</span>'
PNGS.append(("social/x-header-1500x500.png", 1500, 500, lienzo(1500, 500, D, brillo(Y, 0.10, 1000, 420) + brillo(R, 0.10, 600, 300).replace("left:50%", "left:85%")
             + f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;gap:26px">{lockup(130)}{lema.format(36)}</div>'), False))
PNGS.append(("social/youtube-banner-2560x1440.png", 2560, 1440, lienzo(2560, 1440, D, brillo(Y, 0.10, 1600, 700)
             + f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;gap:40px">{lockup(190)}{lema.format(52)}</div>'), False))
PNGS.append(("social/og-image-1200x630.png", 1200, 630, lienzo(1200, 630, D, brillo(Y, 0.10, 900, 400)
             + f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;gap:26px">{lockup(120)}{lema.format(32)}</div>'), False))
PNGS.append(("social/story-1080x1920.png", 1080, 1920, lienzo(1080, 1920, D, brillo(Y, 0.10, 900, 900)
             + f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;gap:36px">{icono(420, "st")}{palabra(170)}{lema.format(40)}</div>'), False))

tmp = AQUI / "_tmp.html"
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    for ruta, w, h, html, transp in PNGS:
        pg = b.new_page(viewport={"width": w, "height": h})
        tmp.write_text(html)
        pg.goto(f"file://{tmp}")
        pg.wait_for_timeout(300)
        pg.locator("#c").screenshot(path=str(OUT / ruta), omit_background=True)
        pg.close()
    b.close()
tmp.unlink()

# favicon.ico con 16, 32 y 48 dentro
ico = Image.open(OUT / "favicon/favicon-48.png")
ico.save(OUT / "favicon/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
(OUT / "favicon/head-snippet.html").write_text(
    '<link rel="icon" href="/favicon.ico" sizes="any">\n<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n')
(OUT / "README.txt").write_text("""2yellow brand kit

Colours: card yellow #FFD21F · sent-off red #FF3B3B · night #0A0C11 · paper #F4F2EC
Font: Archivo (condensed 78%, weight 900) for the wordmark. OFL licence, free to use.

icon/       the mark alone, SVG (dark, light, yellow, transparent)
app-icon/   square, full bleed: stores round the corners themselves (1024, 512, 192, apple-touch 180)
favicon/    favicon.ico (16/32/48), favicon.svg, PNG 16-96, head-snippet.html
profile/    profile pictures, safe for circle crops (1080 and 400; dark and yellow)
logo/       mark + wordmark, SVG and PNG (on dark, on light, on yellow, transparent)
wordmark/   "2yellow" alone, SVG and PNG
social/     X header 1500x500, YouTube banner 2560x1440, link preview 1200x630, story 1080x1920
""")
zp = AQUI / "2yellow_brand.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(OUT.parent))
print("OK", len(list(OUT.rglob("*.*"))), "ficheros;", round(zp.stat().st_size / 1e6, 2), "MB")
