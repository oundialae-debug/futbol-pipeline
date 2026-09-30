"""Carrusel de TikTok (1080x1920 PNG): el último fotograma de cada escena del vídeo.
Usa el video.html que deja video_cro_eng.py en la carpeta de trabajo. Uso:
    python3 carrusel_cro_eng.py <carpeta_de_trabajo>
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

TRABAJO = Path(sys.argv[1])
SALIDA = Path(__file__).resolve().parent / "carrusel"
SALIDA.mkdir(exist_ok=True)
MOMENTOS = [2.2, 5.8, 9.2, 13.0, 16.4, 19.8, 22.9]   # final de cada escena, ya animada
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + str(TRABAJO / "video.html"))
    pg.wait_for_timeout(1500)
    for i, t in enumerate(MOMENTOS, 1):
        pg.evaluate(f"window.render({t})")
        pg.locator("#v").screenshot(path=str(SALIDA / f"{i:02d}_cro_eng.png"))
    b.close()
print("OK", sorted(p.name for p in SALIDA.glob("*.png")))
