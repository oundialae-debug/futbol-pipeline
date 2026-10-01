"""Vídeo explicativo para nuevos usuarios (1080x1920, 30 fps) con su guion de locución
(petición del usuario, 01/10/2026): se para en las tarjetas que diferencian a 2yellow.
Matches -> previa Croacia-Inglaterra -> Tips -> informe Chequia 0-2 Inglaterra.
El guion y el vídeo salen de la MISMA lista de segmentos (SEG): cada frase dura lo que
tarda en leerse a 2,5 palabras por segundo, y el vídeo se ajusta a eso. Escribe
2yellow_app_explainer.mp4 y 2yellow_app_explainer.md (mismo nombre).
Misma maquinaria que grabacion_app.py.
Tres guiones (GUIONES): explainer (la app entera), england (próximo partido) y
england_record (Inglaterra en el pasado). Cada uno escribe <nombre>.mp4 y <nombre>.md.
Uso: python3 grabacion_explicada.py <páginas .html expandidas> <carpeta de trabajo> <guion>
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
PAGINAS, TRABAJO, CUAL = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
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
    for nombre in ("Main", "Partido", "Tips", "Report", "Alineacion", "Elo", "Equipo", "Historial"):
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
        secciones = pg.evaluate("""() => [...document.querySelectorAll('section')].map(s => s.getBoundingClientRect().y + window.scrollY)""")
        POS[nombre]["secciones"] = secciones
        if nombre == "Main":
            POS[nombre]["fila"] = caja('a[href="Partido.dc.html"]')
            POS[nombre]["informe"] = caja('a[href="Report.dc.html"]')
            POS[nombre]["aviso"] = caja('a[href="Tips.dc.html"]')
        for dest in ("Tips", "Elo", "Alineacion", "Historial"):   # pestañas de sección
            POS[nombre]["tab_" + dest] = caja(f'nav[aria-label="Sections"] a[href="{dest}.dc.html"]')
        # botones de la barra de abajo (va fija: solo cuenta la x)
        POS[nombre]["barra"] = pg.evaluate("""() => [...document.querySelectorAll('nav[aria-label="Main"] a, nav[aria-label="Main"] button')]
            .map(a => { const r = a.getBoundingClientRect(); return [r.x, r.width]; })""")
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


fila, inf, aviso = POS["Main"]["fila"], POS["Main"]["informe"], POS["Main"]["aviso"]
s_main = min(max(0, fila[1] - 330), maxs("Main"))
s_aviso = min(max(0, aviso[1] + aviso[3] - VH + 110), maxs("Main"))
c = lambda n, i: cerca(n, POS[n]["secciones"][i])
P = lambda i: c("Partido", i)
T = lambda i: c("Tips", i)
R = lambda i: c("Report", i)
E_ = lambda i: c("Equipo", i)
H_ = lambda i: c("Historial", i)
s_al = min(120, maxs("Alineacion"))
# Previa: 0 Win chance, 1 Goals, 2 Corners & cards, 3 Form, 4 What's at stake, 5 Likely XIs,
# 6 Squads this season, 7 Style clash, 8 Last time out, 9 Last meeting.
# Informe: 0 Match story, 1 Deserved?, 2 Shots, 3 Our call vs the bookies, 4 Key stats,
# 5 Best players, 6 From the bench, 7 Goalkeepers, 8 In the news.
# Tips: 0 Your team, 1 Anytime scorer; luego las tarjetas de la jornada.
# Equipo: 0 FIFA ranking, 1 Form, 2 Goals vs chances, 3 Top scorers, 4 Best rated.
# Historial: 0 Since March 2025, 1 WC qualifying, 2 World Cup 2026, 3 How England play,
# 4 Clean sheets, 5 Biggest wins, 6 The 4 defeats.
#
# SEG: (pantalla, desplazamiento de, a, locución, qué se ve). Si la pantalla es una tupla,
# el segmento empieza con la transición (0,6 s) y el toque va al final del anterior.
WPS = 2.5            # palabras por segundo de la locución
GUIONES = {
    "explainer": ("2yellow_app_explainer", "Croatia – England · Sat 18:00", [
        ("Main", 0, 0, "This is 2yellow: football data, before and after the match.", "Home: latest results"),
        ("Main", 0, s_main, "Every game gets a win chance from our own model, home, draw or away.", "Matchday list with win chances"),
        ("Main", s_main, s_aviso, "And we keep score. Our favourite has won sixty-one percent of the time.", "Our favourite won 61% of the time"),
        (("Main", "Partido"), s_aviso, 0, "Tap a match for the full preview. Croatia against England, Saturday, in Rijeka.", "Preview header: venue and forecast"),
        ("Partido", 0, P(0), "We turn every probability into a fair price. England win fifty-six percent of the time, so their fair odds are one seventy-nine.", "Win chance and fair odds"),
        ("Partido", P(0), P(4), "What's at stake? We play the rest of the group twenty thousand times. If England win on Saturday, they finish top two ninety-five percent of the time.", "What's at stake: group simulation"),
        ("Partido", P(4), P(5), "Likely line-ups, with a fair rating for every player: club form and country form in one number.", "Likely XIs with fair ratings"),
        ("Partido", P(5), P(6), "And how both squads are really doing: market value, plus minutes, goals and assists for their clubs this season.", "Squads this season"),
        ("Partido", P(6), P(9), "Last meeting, minute by minute: every goal and every chance, from the World Cup four-two.", "Last meeting: England 4-2 Croatia"),
        ("Partido", P(9), 0, "Want it all in one place? Open Tips.", "Back to the top, tap Tips"),
        (("Partido", "Tips"), 0, 0, "Every prediction for the game, from most to least likely.", "Tips: your team"),
        ("Tips", 0, T(1), "Plus who is likely to score. Harry Kane: forty-three percent.", "Anytime scorer"),
        ("Tips", T(1), maxs("Tips"), "For the other games, we show the best price, and whether the bookmakers agree with us.", "Tips of the day"),
        ("Tips", maxs("Tips"), maxs("Tips"), "After the whistle, every match gets its own report.", "Tap Matches"),
        (("Tips", "Main"), maxs("Tips"), 0, "Like Czechia against England.", "Home, tap the result"),
        (("Main", "Report"), 0, R(0), "The match story: shots every five minutes, the goals, and the red card that changed the game.", "Match story"),
        ("Report", R(0), R(1), "Did they deserve it? We replay every chance a hundred times.", "Deserved?"),
        ("Report", R(1), R(3), "We put our call next to the bookmakers', market by market.", "Our call vs the bookies"),
        ("Report", R(3), R(6), "Even the bench: who came on, and how they played.", "From the bench"),
        ("Report", R(6), R(6), "2yellow: football data, before and after the match.", "Report"),
    ]),
    "england": ("2yellow_app_england", "Croatia – England · Sat 18:00", [
        ("Main", 0, 0, "This is 2yellow. Here's everything you need before England's next game.", "Home"),
        ("Main", 0, s_main, "Croatia against England, on Saturday. Our model gives England a fifty-six percent chance to win.", "Matchday list, Croatia – England"),
        (("Main", "Partido"), s_main, 0, "Open the preview: venue, forecast and kick-off, right at the top.", "Preview header: Rijeka, 20°C, 18:00"),
        ("Partido", 0, P(0), "Every probability comes with a fair price. Fifty-six percent means fair odds of one seventy-nine.", "Win chance and fair odds"),
        ("Partido", P(0), P(1), "Goals: we expect almost two from England and one from Croatia. The most likely score is one-one.", "Goals"),
        ("Partido", P(1), P(4), "What's at stake? Twenty thousand simulations of the group. A win on Saturday puts England in the top two ninety-five percent of the time. A defeat, only forty-eight.", "What's at stake"),
        ("Partido", P(4), P(5), "Likely line-ups, with a fair rating for every player. Kane and Saka lead the way for England.", "Likely XIs"),
        ("Partido", P(5), P(6), "England's eleven is worth seven hundred and forty-five million euros. Croatia's, one hundred and seventy-two.", "Squads this season"),
        ("Partido", P(6), P(7), "Style clash: England keep the ball more and concede less. Fourteen clean sheets in twenty-four games.", "Style clash"),
        ("Partido", P(7), P(9), "And the last meeting, minute by minute: England four, Croatia two, at the World Cup. Kane scored twice.", "Last meeting"),
        ("Partido", P(9), 0, "Ready to make your call? Open Tips.", "Back to the top, tap Tips"),
        (("Partido", "Tips"), 0, 0, "Every prediction for the game. Over one and a half goals: eighty-one percent. England or a draw: seventy-eight.", "Tips: your team"),
        ("Tips", 0, T(1), "And the likely scorers. Harry Kane: forty-three percent.", "Anytime scorer"),
        ("Tips", T(1), maxs("Tips"), "Plus today's tips across the Nations League, with the best price.", "Tips of the day"),
        (("Tips", "Elo"), maxs("Tips"), 0, "England's group: Spain lead, England are second.", "Standings, Group 1"),
        (("Elo", "Equipo"), 0, 0, "Follow England, and their page keeps it all together.", "England page"),
        ("Equipo", 0, E_(2), "FIFA ranking, recent form, and goals against expected goals.", "FIFA ranking, form, goals vs chances"),
        ("Equipo", E_(2), E_(3), "Top scorer since twenty twenty-five: Harry Kane, seventeen goals.", "Top scorers"),
    ]),
    "england_record": ("2yellow_app_england_record", "England · 18 wins in 24 games", [
        ("Main", 0, 0, "England won in Prague on Tuesday. Here's how 2yellow tells the story.", "Home: Czechia 0-2 England"),
        (("Main", "Report"), 0, 0, "The report opens with the venue, the referee and the weather.", "Report header"),
        ("Report", 0, R(0), "The match story: shots every five minutes. Šulc was sent off after twenty-five minutes. Gordon and Kane scored after the break.", "Match story"),
        ("Report", R(0), R(1), "Did England deserve it? We replay every chance a hundred times. England win sixty-four of them.", "Deserved?"),
        ("Report", R(1), R(2), "Twenty-two shots to six. And this is where England aimed.", "Shots"),
        ("Report", R(2), R(3), "We put our call next to the bookmakers'. Three out of four right, for both of us.", "Our call vs the bookies"),
        ("Report", R(3), R(6), "From the bench: who came on, and how they played.", "From the bench"),
        ("Report", R(6), R(8), "And the headlines from the match.", "In the news"),
        ("Report", R(8), 0, "Now, the line-ups.", "Back to the top, tap Lineups"),
        (("Report", "Alineacion"), 0, s_al, "Every player's rating, in the position they played. Gordon, eight point one five.", "Lineups with ratings"),
        (("Alineacion", "Equipo"), s_al, 0, "Then England's own page.", "England page"),
        (("Equipo", "Historial"), 0, 0, "Their record since March twenty twenty-five: eighteen wins, two draws and four defeats.", "Record"),
        ("Historial", 0, H_(1), "A perfect World Cup qualifying campaign: eight wins, twenty-two goals, none conceded.", "World Cup qualifying"),
        ("Historial", H_(1), H_(2), "At the World Cup: twenty goals in eight games, beaten only by Argentina.", "World Cup 2026"),
        ("Historial", H_(2), H_(3), "How England play: sixty-four percent of the ball, on average.", "How England play"),
        ("Historial", H_(3), H_(4), "And fourteen clean sheets in twenty-four games.", "Clean sheets"),
    ]),
}
NOMBRE, PILDORA, SEG = GUIONES[CUAL]
CIERRE_VOZ = "2yellow. Probabilities, not betting advice. Eighteen plus."
TRAMOS, TOQUES_EN = [], []
for i, (pant, s1, s2, voz, _) in enumerate(SEG):
    dur = max(len(voz.split()) / WPS + 0.5, 2.4)
    if isinstance(pant, tuple):
        TOQUES_EN.append((len(TRAMOS) - 1, pant))       # toque al final del tramo anterior
        TRAMOS.append((0.6, pant, s1, 0))
        dur -= 0.6
        pant, s1 = pant[1], 0
    if s1 != s2:
        TRAMOS.append((1.2, pant, s1, s2))
        dur -= 1.2
    TRAMOS.append((max(dur, 0.8), pant, s2, s2))
GUION, t0 = [], 0.0
for dur, pant, s1, s2 in TRAMOS:
    GUION.append((t0, t0 + dur, pant, s1, s2))
    t0 += dur
fin_de = lambda i: GUION[i][1]
FILA_BARRA = POS["Main"]["corazon"][1] + POS["Main"]["corazon"][3] / 2   # la barra va fija abajo


def barra(pant, i):
    x, w = POS[pant]["barra"][i]
    return (x + w / 2, FILA_BARRA, True)


def tab(pant, dest):
    b_ = POS[pant]["tab_" + dest]
    return (b_[0] + b_[2] / 2, b_[1] + b_[3] / 2, False)


DONDE = {("Main", "Partido"): (fila[0] + fila[2] * 0.45, fila[1] + fila[3] * 0.4, False),
         ("Main", "Report"): (inf[0] + inf[2] * 0.5, inf[1] + inf[3] * 0.45, False),
         ("Partido", "Tips"): tab("Partido", "Tips"),
         ("Report", "Alineacion"): tab("Report", "Alineacion"),
         ("Equipo", "Historial"): tab("Equipo", "Historial"),
         ("Tips", "Main"): barra("Tips", 0),
         ("Tips", "Elo"): barra("Tips", 1),
         ("Elo", "Equipo"): barra("Elo", 3),
         ("Alineacion", "Equipo"): barra("Alineacion", 3)}
TOQUES = []
for i, p in TOQUES_EN:
    x, y, fija = DONDE[p]
    TOQUES.append((fin_de(i) - 0.45, x, y if fija else y - GUION[i][4]))   # menos el desplazamiento de ese momento
T_FIN = GUION[-1][1]
FIN = T_FIN + max(len(CIERRE_VOZ.split()) / WPS + 0.6, 2.6)   # cierre con el logo y su frase

# ---------------------------------------------------------------- guion de locución (mismo nombre que el vídeo)


def mmss(x):
    return f"{int(x // 60)}:{x % 60:04.1f}"


inicios, t0 = [], 0.0
for pant, s1, s2, voz, _ in SEG:
    inicios.append(t0)
    t0 += max(len(voz.split()) / WPS + 0.5, 2.4)
lineas = [f"# {NOMBRE}", "", "Voice-over script. Times match the video "
          f"({mmss(FIN)} long). Pace: about {WPS:g} words per second; each line starts at its time code.", "",
          "| Time | On screen | Voice-over |", "|---|---|---|"]
for (pant, s1, s2, voz, ve), a in zip(SEG, inicios):
    lineas.append(f"| {mmss(a)} | {ve} | {voz} |")
lineas.append(f"| {mmss(T_FIN)} | 2yellow logo | {CIERRE_VOZ} |")
lineas += ["", "## Full text", "", " ".join(s[3] for s in SEG) + " " + CIERRE_VOZ, ""]
(AQUI / f"{NOMBRE}.md").write_text("\n".join(lineas))


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
    k = ease((t - T_FIN) / 0.6)
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
<span style="margin-top:30px;padding:26px 60px;border-radius:60px;background:#C8FF3D;color:#0A0C11;font-family:'Archivo',sans-serif;font-stretch:78%;font-weight:800;font-size:56px">{PILDORA}</span>
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
salida = AQUI / f"{NOMBRE}.mp4"
ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                       "-preset", "medium", "-movflags", "+faststart", str(salida)], stdin=subprocess.PIPE)
fotograma_ultimo = None
n = int(FIN * FPS)
for i in range(n):
    t = i / FPS
    im = fotograma(t) if t < T_FIN else cierre_img(t)
    if t < T_FIN:
        fotograma_ultimo = im
    if i in tuple(int((GUION[j][0] + GUION[j][1]) / 2 * FPS) for j in range(0, len(GUION), 2)) + (int((T_FIN + 2) * FPS),):
        im.save(TRABAJO / f"muestra_{i:04d}.jpg", quality=85)
    ff.stdin.write(np.asarray(im, dtype=np.uint8).tobytes())
ff.stdin.close()
ff.wait()
print("OK", salida, round(salida.stat().st_size / 1e6, 1), "MB", n, "fotogramas")
