"""Vídeo vertical (1080x1920, 30 fps) de la previa Croacia - Inglaterra para redes.
Datos: diseno_nl/datos_nl.json (modelo de selecciones, sin API). Se dibuja cada fotograma
con Chromium (Playwright) y se monta con ffmpeg. Uso:
    python3 video_cro_eng.py <carpeta_de_trabajo> <fuentes_css_local>
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "diseno_nuevo" / "generador"))
from logo import icono, palabra  # noqa: E402

TRABAJO = Path(sys.argv[1])
FUENTES = Path(sys.argv[2])
N = json.loads((AQUI.parent / "datos_nl.json").read_text())
PV = N["previa"]
FPS, DUR = 30, 23.0

BG, CARD, SUB, TXT, MUT, SOFT = "#0A0C11", "#12151C", "#1A1E28", "#F1F3F8", "#8E96AA", "#C6CBD8"
LIMA, NAR, AMA = "#C8FF3D", "#FF8A3D", "#FFD21F"
CRO, ENG = "#E30613", "#F4F4F4"
DISP = "font-family: 'Archivo', sans-serif; font-stretch: 78%; font-weight: 800"
p1, px, p2 = [int(v) for v in PV["p1x2"]]


def forma(e):
    out = []
    for f in PV["forma"][e]:
        r = "W" if f["gf"] > f["gc"] else ("D" if f["gf"] == f["gc"] else "L")
        riv = {"Panama": "PAN", "Ghana": "GHA", "Portugal": "POR", "Czech Republic": "CZE", "Spain": "ESP",
               "Norway": "NOR", "Argentina": "ARG", "France": "FRA"}.get(f["riv"], f["riv"][:3].upper())
        out.append((r, f'{f["gf"]}-{f["gc"]}', ("" if f["casa"] else "@") + riv))
    return out


def top2(e):
    o = sorted(PV["once"][e], key=lambda j: -j["nota"])[:2]
    corto = lambda n: n if n.split(" ")[0].endswith(".") or " " not in n else f"{n[0]}. {n.split(' ', 1)[1]}"
    return [(corto(j["jugador"]), j["nota"]) for j in o]


def media(e):
    return sum(j["nota"] for j in PV["once"][e]) / len(PV["once"][e])


def tiles(e, col):
    s = ""
    for i, (r, m, riv) in enumerate(forma(e)):
        bg = LIMA if r == "W" else (NAR if r == "L" else "#3A4256")
        fg = BG if r != "D" else TXT
        s += (f'<div class="tile" data-i="{i}" style="display: flex; flex-direction: column; align-items: center; gap: 12px">'
              f'<div style="width: 150px; height: 120px; border-radius: 28px; background: {bg}; color: {fg}; {DISP}; font-size: 56px; display: flex; align-items: center; justify-content: center">{m}</div>'
              f'<span style="font-size: 30px; font-weight: 700; color: {SOFT}">{riv}</span></div>')
    return (f'<div style="display: flex; flex-direction: column; gap: 22px"><div style="display: flex; align-items: center; gap: 18px">'
            f'<span style="width: 18px; height: 50px; border-radius: 6px; background: {col}"></span><span style="font-size: 44px; font-weight: 700">{e}</span></div>'
            f'<div style="display: flex; gap: 18px">{s}</div></div>')


def jugador(n, v, col, i):
    return (f'<div class="jug" data-i="{i}" style="display: flex; flex-direction: column; gap: 14px">'
            f'<div style="display: flex; align-items: baseline; justify-content: space-between">'
            f'<span style="display: flex; align-items: center; gap: 16px; font-size: 46px; font-weight: 700"><span style="width: 14px; height: 44px; border-radius: 5px; background: {col}"></span>{n}</span>'
            f'<span style="{DISP}; font-size: 64px; color: {LIMA if v >= 7.2 else TXT}">{v:.2f}</span></div>'
            f'<div style="height: 18px; border-radius: 9px; background: #1E2330"><div class="barj" data-w="{(v - 6.0) / 1.6 * 100:.1f}" style="width: 0%; height: 18px; border-radius: 9px; background: {col}"></div></div></div>')


def anillo(clase, v, txt):
    return (f'<div style="display: flex; align-items: center; gap: 44px">'
            f'<div style="position: relative; width: 250px; height: 250px; flex-shrink: 0">'
            f'<svg width="250" height="250" viewBox="0 0 120 120"><circle cx="60" cy="60" r="48" fill="none" stroke="#232838" stroke-width="12"></circle>'
            f'<circle class="{clase}" data-v="{v}" cx="60" cy="60" r="48" fill="none" stroke="{LIMA if v >= 60 else "#A9B8FF"}" stroke-width="12" stroke-linecap="round" stroke-dasharray="0 302" transform="rotate(-90 60 60)"></circle></svg>'
            f'<span class="{clase}n" style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; {DISP}; font-size: 76px">0%</span></div>'
            f'<span style="font-size: 54px; font-weight: 700">{txt}</span></div>')


kc, ke = top2("Croatia"), top2("England")
HTML = f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="fonts/local.css">
<style>
html,body{{margin:0;background:{BG}}}
#v{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{BG};color:{TXT};font-family:"Instrument Sans",sans-serif}}
.sc{{position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;padding:0 80px;box-sizing:border-box}}
.glow{{position:absolute;width:900px;height:900px;border-radius:50%;filter:blur(160px);opacity:.35}}
.kick{{font-size:34px;font-weight:700;letter-spacing:4px;color:{LIMA}}}
.h{{{DISP};font-size:120px;line-height:1}}
</style></head><body><div id="v">
<span class="glow" style="left:-380px;top:-300px;background:{CRO}"></span>
<span class="glow" style="right:-380px;top:-300px;background:#8FA2FF;opacity:.22"></span>

<div id="barra" style="position:absolute;left:80px;right:80px;top:110px;display:flex;align-items:center;justify-content:space-between;opacity:0">
<span style="display:flex;align-items:center;gap:14px">{icono(64, "b")}{palabra(52)}</span>
<span style="display:flex;align-items:center;gap:14px;font-size:34px;font-weight:700"><span style="width:12px;height:38px;border-radius:4px;background:{CRO}"></span>CRO <span style="color:{MUT}">v</span> ENG<span style="width:12px;height:38px;border-radius:4px;background:{ENG}"></span></span></div>

<div class="sc" id="s1" style="justify-content:center;align-items:center;text-align:center;gap:40px">
<div id="logo1" style="display:flex;align-items:center;gap:26px">{icono(170, "l1")}{palabra(150)}</div>
<span class="kick">NATIONS LEAGUE · MATCHDAY 3</span>
<div style="display:flex;align-items:center;gap:40px">
<div style="display:flex;flex-direction:column;align-items:center;gap:20px"><span style="width:190px;height:190px;border-radius:50%;background:{CRO};box-shadow:inset 0 0 0 10px {ENG};{DISP};font-size:64px;display:flex;align-items:center;justify-content:center;color:#fff">CRO</span><span style="font-size:48px;font-weight:700">Croatia</span></div>
<span class="h" style="font-size:90px;color:{MUT}">vs</span>
<div style="display:flex;flex-direction:column;align-items:center;gap:20px"><span style="width:190px;height:190px;border-radius:50%;background:{ENG};box-shadow:inset 0 0 0 10px #1E2B5C;{DISP};font-size:64px;display:flex;align-items:center;justify-content:center;color:{BG}">ENG</span><span style="font-size:48px;font-weight:700">England</span></div></div>
<span style="font-size:40px;color:{SOFT}">Sat 3 Oct · 18:00 CEST · Rijeka</span></div>

<div class="sc" id="s2" style="justify-content:center;gap:56px">
<span class="kick">WHO WINS?</span><span class="h">Win chance</span>
<div style="display:flex;height:170px;border-radius:40px;overflow:hidden;gap:8px">
<div id="w1" style="width:33%;background:{CRO};color:#fff;{DISP};font-size:64px;display:flex;align-items:center;justify-content:center">0%</div>
<div id="wx" style="width:33%;background:#3A4256;{DISP};font-size:64px;display:flex;align-items:center;justify-content:center">0%</div>
<div id="w2" style="width:34%;background:{ENG};color:{BG};{DISP};font-size:84px;display:flex;align-items:center;justify-content:center">0%</div></div>
<div style="display:flex;justify-content:space-between;font-size:40px;color:{SOFT}"><span>Croatia</span><span>Draw</span><span>England</span></div>
<div style="display:flex;justify-content:space-between;font-size:36px;color:{MUT}"><span>FIFA {PV["fifa_puesto"][0]}th</span><span>FIFA {PV["fifa_puesto"][1]}th</span></div></div>

<div class="sc" id="s3" style="justify-content:center;gap:50px">
<span class="kick">GOALS</span><span class="h">Expected goals</span>
<div style="display:flex;align-items:center;justify-content:center;gap:50px;{DISP};font-size:220px;line-height:1">
<span id="g1" style="color:{CRO}">0.00</span><span style="font-size:120px;color:{MUT}">–</span><span id="g2">0.00</span></div>
<div id="marc" style="align-self:center;padding:28px 50px;border-radius:40px;background:{SUB};display:flex;align-items:center;gap:30px;opacity:0">
<span style="font-size:42px;color:{SOFT}">Most likely score</span><span style="{DISP};font-size:96px">{PV["marcador"][0]}–{PV["marcador"][1]}</span></div></div>

<div class="sc" id="s4" style="justify-content:center;gap:56px">
<span class="kick">GOAL MARKETS</span><span class="h">How many?</span>
{anillo("r1", int(PV["mas15"]), "Over 1.5 goals")}{anillo("r2", int(PV["mas25"]), "Over 2.5 goals")}{anillo("r3", int(PV["btts"]), "Both teams score")}</div>

<div class="sc" id="s5" style="justify-content:center;gap:70px">
<span class="kick">LAST 5 GAMES</span><span class="h">Form</span>
{tiles("Croatia", CRO)}{tiles("England", ENG)}</div>

<div class="sc" id="s6" style="justify-content:center;gap:48px">
<span class="kick">KEY MEN · FAIR RATING</span><span class="h">Who's in form</span>
{jugador(ke[0][0], ke[0][1], ENG, 0)}{jugador(ke[1][0], ke[1][1], ENG, 1)}{jugador(kc[0][0], kc[0][1], CRO, 2)}{jugador(kc[1][0], kc[1][1], CRO, 3)}
<div class="jug" data-i="4" style="padding:30px 36px;border-radius:32px;background:{SUB};display:flex;justify-content:space-between;font-size:40px;color:{SOFT}">
<span>XI average</span><span><b style="color:{CRO}">{media("Croatia"):.2f}</b> · <b style="color:{ENG}">{media("England"):.2f}</b></span></div></div>

<div class="sc" id="s7" style="justify-content:center;align-items:center;text-align:center;gap:50px">
<span class="kick">YOUR CALL</span>
<span class="h" style="font-size:140px">Croatia or<br>England?</span>
<div style="display:flex;gap:30px">
<span style="width:200px;height:200px;border-radius:40px;background:{CRO};color:#fff;{DISP};font-size:110px;display:flex;align-items:center;justify-content:center">1</span>
<span style="width:200px;height:200px;border-radius:40px;background:#3A4256;{DISP};font-size:110px;display:flex;align-items:center;justify-content:center">X</span>
<span style="width:200px;height:200px;border-radius:40px;background:{ENG};color:{BG};{DISP};font-size:110px;display:flex;align-items:center;justify-content:center">2</span></div>
<span style="font-size:46px;color:{SOFT}">Drop it in the comments</span>
<div style="display:flex;align-items:center;gap:22px;margin-top:40px">{icono(120, "l7")}{palabra(104)}</div>
<span style="font-size:32px;color:{SOFT}">Football data, before and after the match</span></div>

<div id="pie" style="position:absolute;left:0;right:0;bottom:70px;text-align:center;font-size:26px;color:{MUT};opacity:0">2yellow model · probabilities, not betting advice · 18+</div>
</div>
<script>
const E=(x)=>x<0?0:x>1?1:1-Math.pow(1-x,3);
const T=[[0,2.6],[2.6,6.2],[6.2,9.6],[9.6,13.4],[13.4,16.8],[16.8,20.2],[20.2,23]];
const $=(s)=>document.querySelector(s), $$=(s)=>[...document.querySelectorAll(s)];
function vis(el,t,a,b){{const fi=E((t-a)/0.45), fo=b>=23?1:1-E((t-(b-0.35))/0.35);const k=Math.min(fi,fo);
 el.style.opacity=k; el.style.transform=`translateY(${{(1-fi)*60}}px) scale(${{0.97+0.03*fi}})`;}}
window.render=(t)=>{{
 T.forEach(([a,b],i)=>{{const el=$('#s'+(i+1)); if(t<a-0.01||t>b+0.01){{el.style.opacity=0;return;}} vis(el,t,a,b);}});
 const bar=$('#barra'); bar.style.opacity=(t>2.6&&t<20.2)?Math.min(E((t-2.6)/0.4),1-E((t-19.9)/0.3)):0;
 $('#pie').style.opacity=t>2.6?E((t-2.6)/0.5):0;
 // escena 1: logo
 $('#logo1').style.transform=`scale(${{0.8+0.2*E(t/0.8)}})`;
 // escena 2: barra 1X2
 let k=E((t-3.0)/1.4); const P=[{p1},{px},{p2}];
 const w=[33+(P[0]-33)*k,33+(P[1]-33)*k]; w.push(100-w[0]-w[1]);
 ['#w1','#wx','#w2'].forEach((s,i)=>{{$(s).style.width=w[i]+'%'; $(s).textContent=Math.round(P[i]*k)+'%';}});
 // escena 3: goles
 k=E((t-6.6)/1.6); $('#g1').textContent=({PV["lam"][0]}*k).toFixed(2); $('#g2').textContent=({PV["lam"][1]}*k).toFixed(2);
 const km=E((t-8.0)/0.5); $('#marc').style.opacity=km; $('#marc').style.transform=`scale(${{0.9+0.1*km}})`;
 // escena 4: anillos
 ['r1','r2','r3'].forEach((c,i)=>{{const e=$('.'+c), v=+e.dataset.v, kk=E((t-10.0-i*0.45)/1.1);
  e.setAttribute('stroke-dasharray',(v/100*302*kk)+' 302'); $('.'+c+'n').textContent=Math.round(v*kk)+'%';}});
 // escena 5: forma
 $$('#s5 .tile').forEach((el,j)=>{{const i=+el.dataset.i; const kk=E((t-13.8-i*0.16-(j>=5?0.5:0))/0.35); el.style.opacity=kk; el.style.transform=`translateY(${{(1-kk)*40}}px)`;}});
 // escena 6: jugadores
 $$('#s6 .jug').forEach((el)=>{{const i=+el.dataset.i; const kk=E((t-17.2-i*0.3)/0.4); el.style.opacity=kk; el.style.transform=`translateX(${{(1-kk)*-60}}px)`;
  const b=el.querySelector('.barj'); if(b) b.style.width=(+b.dataset.w*E((t-17.4-i*0.3)/0.8))+'%';}});
}};
window.render(0);
</script></body></html>'''

TRABAJO.mkdir(parents=True, exist_ok=True)
shutil.copytree(FUENTES.parent, TRABAJO / "fonts", dirs_exist_ok=True)
(TRABAJO / "video.html").write_text(HTML)
cuadros = TRABAJO / "cuadros"
shutil.rmtree(cuadros, ignore_errors=True)
cuadros.mkdir()
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + str(TRABAJO / "video.html"))
    pg.wait_for_timeout(1500)
    n = int(FPS * DUR)
    for i in range(n):
        pg.evaluate(f"window.render({i / FPS})")
        pg.locator("#v").screenshot(path=str(cuadros / f"f{i:04d}.jpg"), type="jpeg", quality=92)
    b.close()
salida = AQUI / "2yellow_croatia_england.mp4"
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(cuadros / "f%04d.jpg"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", str(salida)], check=True)
print("OK", salida, round(salida.stat().st_size / 1e6, 1), "MB")
