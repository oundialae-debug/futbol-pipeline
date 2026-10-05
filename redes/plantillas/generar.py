"""Plantillas 9:16 de 2yellow (1080x1920 PNG) para TikTok/Instagram.

Solo se rellenan equipos y datos en un JSON; el resto (titular, veredicto,
acierto/fallo, colores de camiseta) sale solo. Uso:
    python3 redes/plantillas/generar.py redes/plantillas/ejemplos/deserved.json
    python3 redes/plantillas/generar.py ejemplo.json -o salida.png
Plantillas: "deserved" y "prediction". Ejemplos en redes/plantillas/ejemplos/.
Zona segura de TikTok: nada a menos de 185 px arriba, 380 px abajo, 140 px a la derecha.
Sin API: solo datos que ya tengas.
"""
import argparse, base64, html, json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REC = AQUI / "recursos"
AMARILLO, ROJO, VERDE, NOCHE = "#FFD21F", "#FF3B3B", "#2BD67B", "#0A0C11"


def b64(p):
    return base64.b64encode((REC / p).read_bytes()).decode()


KITS = json.loads((REC / "kits_camiseta.json").read_text())


def color(eq):
    """Color de la 1ª equipación; si es blanca casi entera, el segundo color."""
    if eq.get("color"):
        return eq["color"]
    kit = (KITS.get(eq["name"]) or [{}])[0]
    cs = kit.get("colores") or ["#9AA3B5"]
    if cs[0].upper() in ("#FFFFFF", "#FFFFFE") and len(cs) > 1 and kit["partes"][0] < 0.8:
        return cs[1]
    return cs[0]


def visible(c):
    """Aclara los colores muy oscuros para que se vean sobre el fondo noche."""
    r, g, b = (int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if lum >= 70:
        return c
    k = 0.45
    return "#%02X%02X%02X" % tuple(round(v + (255 - v) * k) for v in (r, g, b))


def e(t):
    return html.escape(str(t))


CSS = f"""
@font-face{{font-family:Archivo;src:url(data:font/woff2;base64,{b64('Archivo-latin.woff2')}) format('woff2');
 font-weight:100 900;font-stretch:62% 125%}}
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;background:{NOCHE};color:#F1F3F8;font-family:Archivo,sans-serif;overflow:hidden}}
#v{{position:relative;width:1080px;height:1920px;overflow:hidden;
 background:radial-gradient(1000px 800px at 0% 0%,color-mix(in srgb,var(--c1) 45%,transparent),transparent 70%),
            radial-gradient(1000px 800px at 100% 0%,color-mix(in srgb,var(--c2) 40%,transparent),transparent 70%),{NOCHE}}}
.safe{{position:absolute;left:80px;right:140px;top:185px;bottom:380px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center;height:64px}}
.top img{{height:84px;margin-left:-14px}}
.chip{{font-size:28px;font-weight:700;letter-spacing:2px;color:#C9CED9;text-transform:uppercase}}
.kick{{margin-top:70px;font-size:34px;font-weight:800;letter-spacing:6px;color:{AMARILLO};text-transform:uppercase}}
.hook{{margin-top:14px;font-size:104px;line-height:.98;font-weight:900;font-stretch:75%;letter-spacing:-1px}}
.hook b{{color:{AMARILLO};white-space:nowrap}}
.disp{{font-weight:900;font-stretch:75%}}
.score{{margin-top:60px;display:flex;align-items:center;justify-content:space-between}}
.tm{{display:flex;align-items:center;gap:16px;font-size:52px;font-weight:800;width:250px}}
.tm.r{{justify-content:flex-end}}
.bar{{width:12px;height:54px;border-radius:4px;background:var(--c)}}
.res{{font-size:190px;line-height:1;font-weight:900;font-stretch:75%}}
.res i{{font-style:normal;color:#5C6476;margin:0 10px}}
.card{{background:#161A23E6;border-radius:28px;padding:30px 34px}}
.lbl{{font-size:26px;font-weight:700;letter-spacing:3px;color:#8E96A8;text-transform:uppercase}}
.row{{display:grid;grid-template-columns:120px 1fr 120px;align-items:center;gap:18px;margin-top:26px}}.row:first-child{{margin-top:0}}
.row .v{{font-size:54px;font-weight:900;font-stretch:80%}}
.row .v.r{{text-align:right}}
.mid{{text-align:center}}
.mid .lbl{{font-size:22px;letter-spacing:2px}}
.split{{display:flex;height:14px;border-radius:7px;overflow:hidden;margin-top:8px;gap:4px}}
.split div{{height:100%;border-radius:7px}}
.pill{{margin-top:48px;align-self:center;padding:20px 36px;border-radius:999px;font-size:40px;font-weight:800;color:{NOCHE}}}
.q{{margin-top:auto;font-size:56px;font-weight:900;font-stretch:80%;text-align:center}}
.q span{{color:{AMARILLO}}}
.pie{{margin-top:22px;text-align:center;font-size:24px;color:#7D8597}}
"""


def pagina(c1, c2, cuerpo):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body><div id="v" style="--c1:{c1};--c2:{c2}"><div class="safe">{cuerpo}</div></div></body></html>')


def cabecera(d, kicker):
    return (f'<div class="top"><img src="data:image/png;base64,{b64("2yellow-logo-transparent-for-dark.png")}">'
            f'<div class="chip">{e(d.get("competition", ""))}</div></div><div class="kick">{e(kicker)}</div>')


def marcador(h, a, gh, ga):
    return (f'<div class="score"><div class="tm" style="--c:{h["c"]}"><div class="bar"></div>{e(h["code"])}</div>'
            f'<div class="res">{gh}<i>–</i>{ga}</div>'
            f'<div class="tm r" style="--c:{a["c"]}">{e(a["code"])}<div class="bar"></div></div></div>')


def fila(nombre, vh, va, h, a, fmt="{}"):
    tot = (float(vh) + float(va)) or 1
    ph = 100 * float(vh) / tot
    return (f'<div class="row"><div class="v">{fmt.format(vh)}</div><div class="mid"><div class="lbl">{e(nombre)}</div>'
            f'<div class="split"><div style="width:{ph:.1f}%;background:{h["c"]}"></div>'
            f'<div style="flex:1;background:{a["c"]}"></div></div></div>'
            f'<div class="v r">{fmt.format(va)}</div></div>')


def pie(d, por_defecto):
    return (f'<div class="q">{e(d.get("question", por_defecto))} <span>&#8595;</span></div>'
            f'<div class="pie">{e(d.get("footer", "2yellow data · not betting advice · 18+"))}</div>')


def deserved(d):
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    xh, xa = d["xg"]
    dif = xh - xa
    if abs(dif) < 0.3:
        quien, veredicto, col = None, "xG verdict: a draw was fair", AMARILLO
    else:
        quien = h if dif > 0 else a
        veredicto, col = f'xG verdict: {quien["code"]} deserved it', AMARILLO
    ganador = h if gh > ga else a if ga > gh else None
    if "hook" in d:
        hook = d["hook"]
    elif ganador and quien and ganador is not quien:
        perd = quien
        hook = f'{e(perd["code"])} lost with <b>{max(xh, xa):.2f} xG</b>'
        col = ROJO
    elif ganador and quien is None:
        hook = f'{e(ganador["code"])} won on <b>{xh if ganador is h else xa:.2f} xG</b>'
    elif ganador is None and quien:
        hook = f'{e(quien["code"])} drew with <b>{max(xh, xa):.2f} xG</b>'
    else:
        hook = f'{e(ganador["code"])} won <b>{gh}–{ga}</b>. Fair?'
    filas = fila("Expected goals", f"{xh:.2f}", f"{xa:.2f}", h, a)
    for nombre, vh, va in d.get("stats", [])[:4]:
        filas += fila(nombre, vh, va, h, a)
    cuerpo = (cabecera(d, "Deserved?") + f'<div class="hook">{hook}</div>' + marcador(h, a, gh, ga)
              + f'<div class="card" style="margin-top:36px">{filas}</div>'
              + f'<div class="pill" style="background:{col}">{e(veredicto)}</div>'
              + pie(d, "Robbery or deserved?"))
    return pagina(h["c"], a["c"], cuerpo)


def prediction(d):
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    p = d["probs"]  # [local, empate, visitante] en %
    etiquetas = [h["code"], "Draw", a["code"]]
    pick = max(range(3), key=lambda i: p[i])
    real = 0 if gh > ga else 1 if gh == ga else 2
    acierto = pick == real
    exacto = d.get("predicted_score") == [gh, ga]
    hook = d.get("hook") or (f'We gave {e(etiquetas[pick])} <b>{p[pick]:.0f}%</b>' if pick != 1
                             else f'We said draw at <b>{p[1]:.0f}%</b>')
    colores = [h["c"], "#5C6476", a["c"]]
    seg = "".join(f'<div style="width:{p[i]}%;background:{colores[i]};opacity:{1 if i == pick else .45}"></div>' for i in range(3))
    nums = "".join(f'<div style="width:{p[i]}%;text-align:center"><div class="disp" style="font-size:{60 if i == pick else 40}px;'
                   f'color:{"#F1F3F8" if i == pick else "#8E96A8"}">{p[i]:.0f}%</div><div class="lbl" style="font-size:22px">'
                   f'{e(etiquetas[i])}</div></div>' for i in range(3))
    ps = d.get("predicted_score")
    marc = (f'<div style="margin-top:22px;font-size:32px;color:#C9CED9">Most likely score '
            f'<span class="disp" style="font-size:52px;color:#F1F3F8;margin-left:12px">{ps[0]}–{ps[1]}</span></div>') if ps else ""
    texto = "Exact score!" if exacto else "Called it" if acierto else "Missed it"
    sello = (f'<div class="pill" style="background:{VERDE if acierto else ROJO}">'
             f'{"&#10003;" if acierto else "&#10007;"} {texto}</div>')
    cuerpo = (cabecera(d, "Prediction vs result") + f'<div class="hook">{hook}</div>'
              + f'<div class="card" style="margin-top:40px"><div class="lbl">Our call · pre-match</div>'
              + f'<div class="split" style="height:22px;margin-top:22px">{seg}</div>'
              + f'<div style="display:flex;gap:4px;margin-top:14px">{nums}</div>{marc}</div>'
              + f'<div class="lbl" style="margin-top:40px">Full time</div>' + marcador(h, a, gh, ga).replace('margin-top:44px', '')
              + sello + pie(d, "Did you see it coming?"))
    return pagina(h["c"], a["c"], cuerpo)


PLANTILLAS = {"deserved": deserved, "prediction": prediction}


def renderizar(d, salida):
    for k in ("home", "away"):
        d[k]["c"] = visible(color(d[k]))
        d[k].setdefault("code", d[k]["name"][:3].upper())
    pag = PLANTILLAS[d["template"]](d)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium") if Path("/opt/pw-browsers/chromium").exists() \
            else pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.set_content(pag)
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(salida))
        b.close()
    return salida


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("datos")
    ap.add_argument("-o", "--salida")
    ap.add_argument("--guias", action="store_true", help="dibuja la zona segura (solo para revisar)")
    x = ap.parse_args()
    d = json.loads(Path(x.datos).read_text())
    out = Path(x.salida or Path(x.datos).with_suffix(".png"))
    if x.guias:
        CSS += ".safe{outline:3px dashed #FF3B3B}"
    print("OK", renderizar(d, out))
