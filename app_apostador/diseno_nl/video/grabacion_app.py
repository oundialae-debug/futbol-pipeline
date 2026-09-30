"""Vídeo vertical (1080x1920, 30 fps) que simula a alguien usando 2yellow en el móvil:
Matches -> previa Croacia-Inglaterra -> clasificación del grupo -> ficha de Inglaterra.

1. Chromium dibuja cada pantalla entera (las páginas ya expandidas con su estado inicial,
   las mismas que se ven en el lienzo) a 2,2x, sin la barra de navegación, que va fija aparte.
2. Se guardan las posiciones de lo que se toca (fila del partido, pestaña Group, corazón).
3. PIL monta cada fotograma: marco de móvil, desplazamiento, toques y transiciones.
Uso: python3 grabacion_app.py <carpeta con las páginas .html expandidas> <carpeta de trabajo>
"""
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
PAGINAS, TRABAJO = Path(sys.argv[1]), Path(sys.argv[2])
TRABAJO.mkdir(parents=True, exist_ok=True)
FUENTES_CSS = PAGINAS.parent / "video" / "fonts" / "local.css"
ESC = 2.2                      # escala: 390 px CSS -> 858 px
VW, VH = 390, 790              # pantalla del móvil en px CSS
SW, SH = int(VW * ESC), int(VH * ESC)
W, H = 1080, 1920
X0, Y0 = (W - SW) // 2, (H - SH) // 2 + 20
FPS = 30

# ---------------------------------------------------------------- 1-2. capturas y posiciones
POS = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": VW, "height": VH}, device_scale_factor=ESC)
    for nombre in ("Main", "Partido", "Elo", "Equipo"):
        pg.goto(f"file://{PAGINAS / (nombre + '.html')}")
        # las fuentes de la marca, en local (Chromium aquí no llega a Google Fonts)
        pg.evaluate(f"""() => {{ const l = document.createElement('link'); l.rel = 'stylesheet';
            l.href = 'file://{FUENTES_CSS}'; document.head.appendChild(l); }}""")
        pg.wait_for_timeout(1500)
        # la raíz a su altura natural; la barra de navegación, fuera (va fija aparte)
        alto = pg.evaluate("""() => { const r = document.body.firstElementChild; r.style.height = 'auto';
            const n = r.querySelector('nav[aria-label="Main"]'); n.style.visibility = 'hidden'; return r.scrollHeight; }""")
        pg.locator("body > div").first.screenshot(path=str(TRABAJO / f"{nombre}.png"))
        pg.evaluate("""() => { const n = document.querySelector('nav[aria-label="Main"]'); n.style.visibility = 'visible';
            n.style.position = 'fixed'; n.style.bottom = '18px'; document.body.firstElementChild.style.visibility = 'hidden';
            n.style.visibility = 'visible'; }""")
        pg.screenshot(path=str(TRABAJO / f"nav_{nombre}.png"), clip={"x": 0, "y": VH - 100, "width": VW, "height": 100})
        pg.evaluate("() => { document.body.firstElementChild.style.visibility = 'visible'; }")
        caja = lambda sel: pg.evaluate(f"""() => {{ const e = document.querySelector({json.dumps(sel)}); if (!e) return null;
            const r = e.getBoundingClientRect(); return [r.x, r.y + window.scrollY, r.width, r.height]; }}""")
        POS[nombre] = {"alto": alto}
        if nombre == "Main":
            POS[nombre]["fila"] = caja('a[href="Partido.dc.html"]')
        if nombre == "Partido":
            POS[nombre]["grupo"] = caja('nav[aria-label="Sections"] a[href="Elo.dc.html"]')
            POS[nombre]["secciones"] = pg.evaluate("""() => [...document.querySelectorAll('section')].map(s => s.getBoundingClientRect().y + window.scrollY)""")
        if nombre == "Equipo":
            POS[nombre]["secciones"] = pg.evaluate("""() => [...document.querySelectorAll('section')].map(s => s.getBoundingClientRect().y + window.scrollY)""")
        POS[nombre]["corazon"] = [VW - 16 - 6 - 50 + 0, VH - 18 - 64 + 7, 50, 50]
    b.close()
print(json.dumps(POS)[:600])

IM = {n: Image.open(TRABAJO / f"{n}.png").convert("RGB") for n in POS}
NAV = {n: Image.open(TRABAJO / f"nav_{n}.png").convert("RGB") for n in POS}


# ---------------------------------------------------------------- 3. guion
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def maxs(n):
    return max(0, POS[n]["alto"] - VH)


def cerca(n, y):
    """Desplazamiento para dejar la sección que empieza en y cerca de arriba."""
    return min(max(0, y - 70), maxs(n))


fila = POS["Main"]["fila"]
s_main = min(max(0, fila[1] - 330), maxs("Main"))
sp = POS["Partido"]["secciones"]
se = POS["Equipo"]["secciones"]
# (inicio, fin, pantalla, desplazamiento de, a)
GUION = [
    (0.0, 1.6, "Main", 0, 0),
    (1.6, 3.4, "Main", 0, s_main),
    (3.4, 4.4, "Main", s_main, s_main),          # toque en Croacia - Inglaterra a los 3,8 s
    (4.4, 5.0, ("Main", "Partido"), s_main, 0),   # transición
    (5.0, 7.0, "Partido", 0, 0),
    (7.0, 8.4, "Partido", 0, cerca("Partido", sp[1])),       # goles
    (8.4, 10.0, "Partido", cerca("Partido", sp[1]), cerca("Partido", sp[1])),
    (10.0, 11.4, "Partido", cerca("Partido", sp[1]), cerca("Partido", sp[3])),  # forma
    (11.4, 12.8, "Partido", cerca("Partido", sp[3]), cerca("Partido", sp[3])),
    (12.8, 14.2, "Partido", cerca("Partido", sp[3]), cerca("Partido", sp[4])),  # onces
    (14.2, 15.8, "Partido", cerca("Partido", sp[4]), cerca("Partido", sp[4])),
    (15.8, 17.0, "Partido", cerca("Partido", sp[4]), 0),
    (17.0, 17.8, "Partido", 0, 0),                # toque en Group a los 17,3 s
    (17.8, 18.4, ("Partido", "Elo"), 0, 0),
    (18.4, 21.4, "Elo", 0, 0),                    # toque en el corazón a los 21,0 s
    (21.4, 22.0, ("Elo", "Equipo"), 0, 0),
    (22.0, 24.0, "Equipo", 0, 0),
    (24.0, 25.4, "Equipo", 0, cerca("Equipo", se[1])),       # forma / ranking
    (25.4, 27.0, "Equipo", cerca("Equipo", se[1]), cerca("Equipo", se[1])),
    (27.0, 28.4, "Equipo", cerca("Equipo", se[1]), cerca("Equipo", se[3])),     # goles vs xG
    (28.4, 30.0, "Equipo", cerca("Equipo", se[3]), cerca("Equipo", se[3])),
    (30.0, 31.4, "Equipo", cerca("Equipo", se[3]), maxs("Equipo")),             # goleadores
    (31.4, 33.4, "Equipo", maxs("Equipo"), maxs("Equipo")),
]
g = POS["Partido"]["grupo"]
cz = POS["Elo"]["corazon"]
TOQUES = [(3.8, fila[0] + fila[2] * 0.45, fila[1] + fila[3] * 0.4 - s_main),
          (17.3, g[0] + g[2] / 2, g[1] + g[3] / 2),
          (21.0, cz[0] + cz[2] / 2, cz[1] + cz[3] / 2)]
FIN = 33.4 + 2.6   # cierre con el logo


def vista(n, s):
    """Lo que se ve de la pantalla n con desplazamiento s (px CSS), barra fija incluida."""
    im = IM[n]
    s = int(round(s * ESC))
    v = im.crop((0, s, SW, s + SH))
    nav = NAV[n].resize((SW, int(100 * ESC)))
    v.paste(nav, (0, SH - nav.height))
    return v


# ---------------------------------------------------------------- fondo y marco
fondo = Image.new("RGB", (W, H), "#07080C")
brillo = Image.new("RGB", (W, H), "#07080C")
d = ImageDraw.Draw(brillo)
d.ellipse((-300, -200, 700, 800), fill="#3A1216")
d.ellipse((500, 1100, 1400, 2100), fill="#141C3A")
fondo = brillo.filter(ImageFilter.GaussianBlur(160))
mascara = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(mascara).rounded_rectangle((0, 0, SW, SH), 64, fill=255)
marco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dm = ImageDraw.Draw(marco)
dm.rounded_rectangle((X0 - 16, Y0 - 16, X0 + SW + 16, Y0 + SH + 16), 80, outline="#2A3040", width=16)
dm.rounded_rectangle((X0 - 18, Y0 - 18, X0 + SW + 18, Y0 + SH + 18), 82, outline="#3A4256", width=3)
dm.rounded_rectangle((W // 2 - 70, Y0 + 14, W // 2 + 70, Y0 + 44), 15, fill="#000000")   # cámara

cierre = Image.open(TRABAJO / "cierre.png").convert("RGB") if (TRABAJO / "cierre.png").exists() else None


def fotograma(t):
    for (a, b_, pant, s1, s2) in GUION:
        if a <= t < b_:
            k = ease((t - a) / (b_ - a))
            if isinstance(pant, tuple):   # la nueva pantalla entra desde la derecha
                v1, v2 = vista(pant[0], s1), vista(pant[1], 0)
                x = int(SW * (1 - k))
                pantalla = v1.copy()
                pantalla.paste(v1.crop((SW - x, 0, SW, SH)).resize((max(x, 1), SH)) if False else v1, (int(-SW * 0.25 * k), 0))
                pantalla.paste(v2, (x, 0))
            else:
                pantalla = vista(pant, s1 + (s2 - s1) * k)
            break
    else:
        pantalla = None
    f = fondo.copy()
    if pantalla is None:   # cierre
        return cierre_img(t)
    capa = Image.new("RGB", (SW, SH))
    capa.paste(pantalla)
    f.paste(capa, (X0, Y0), mascara)
    # toques: círculo que crece y se desvanece
    for (tt, x, y) in TOQUES:
        if tt - 0.05 <= t <= tt + 0.45:
            k = (t - tt + 0.05) / 0.5
            r = int((26 + 40 * k) * ESC / 2.2 * 1.0 * 1.6)
            a = int(150 * (1 - k))
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            do = ImageDraw.Draw(ov)
            cx, cy = X0 + x * ESC, Y0 + y * ESC
            do.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, a), outline=(255, 255, 255, min(255, a + 60)), width=4)
            f = Image.alpha_composite(f.convert("RGBA"), ov).convert("RGB")
    f = Image.alpha_composite(f.convert("RGBA"), marco).convert("RGB")
    return f


def cierre_img(t):
    k = ease((t - 33.4) / 0.6)
    base = fotograma_ultimo.copy()
    return Image.blend(base, cierre, k)


# ---------------------------------------------------------------- cierre: logo (lo dibuja Chromium)
sys.path.insert(0, str(AQUI.parents[1] / "diseno_nuevo" / "generador"))
from logo import icono, palabra  # noqa: E402
fuentes = PAGINAS.parent / "video" / "fonts" / "local.css"
html = f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="file://{fuentes}"></head>
<body style="margin:0"><div id="c" style="width:1080px;height:1920px;background:#0A0C11;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:44px;font-family:'Instrument Sans',sans-serif;color:#F1F3F8">
<div style="display:flex;align-items:center;gap:30px">{icono(190, "c")}{palabra(170)}</div>
<span style="font-size:44px;color:#C6CBD8">Football data, before and after the match</span>
<span style="margin-top:30px;padding:26px 60px;border-radius:60px;background:#C8FF3D;color:#0A0C11;font-family:'Archivo',sans-serif;font-stretch:78%;font-weight:800;font-size:56px">Croatia – England · Sat 18:00</span>
<span style="position:absolute;bottom:80px;font-size:28px;color:#8E96AA">Probabilities, not betting advice · 18+</span></div></body></html>'''
(TRABAJO / "cierre.html").write_text(html)
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(f"file://{TRABAJO / 'cierre.html'}")
    pg.wait_for_timeout(1200)
    pg.locator("#c").screenshot(path=str(TRABAJO / "cierre.png"))
    b.close()
cierre = Image.open(TRABAJO / "cierre.png").convert("RGB")

# ---------------------------------------------------------------- fotogramas -> mp4
salida = AQUI / "2yellow_app_england.mp4"
ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                       "-preset", "medium", "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)
fotograma_ultimo = None
n = int(FIN * FPS)
for i in range(n):
    t = i / FPS
    im = fotograma(t) if t < 33.4 else cierre_img(t)
    if t < 33.4:
        fotograma_ultimo = im
    if i in (int(2 * FPS), int(3.85 * FPS), int(6 * FPS), int(9 * FPS), int(19 * FPS), int(23 * FPS), int(29 * FPS), int(35 * FPS)):
        im.save(TRABAJO / f"muestra_{i:04d}.jpg", quality=85)
    ff.stdin.write(np.asarray(im, dtype=np.uint8).tobytes())
ff.stdin.close()
ff.wait()
print("OK", salida, round(salida.stat().st_size / 1e6, 1), "MB", n, "fotogramas")
