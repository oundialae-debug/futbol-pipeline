"""Plantillas 9:16 de 2yellow (1080x1920 PNG) para TikTok/Instagram.

Una idea por imagen: un número gigante, una frase que lo explica, el partido
y la pregunta final. Cinco de previo y cinco de postpartido.
    python3 redes/plantillas/generar.py ejemplos/prediction.json   # una
    python3 redes/plantillas/generar.py --todos                    # todos los ejemplos
Zona segura de TikTok: nada a menos de 185 px arriba, 380 abajo, 140 a la derecha
(--guias la dibuja). Sin API: solo datos que ya estén en disco.
"""
import argparse, base64, html, json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REC = AQUI / "recursos"
AMARILLO, ROJO, VERDE, GRIS, NOCHE = "#FFD21F", "#FF3B3B", "#2BD67B", "#5C6476", "#0A0C11"
KITS = json.loads((REC / "kits_camiseta.json").read_text())
GUIAS = False


def b64(p):
    return base64.b64encode((REC / p).read_bytes()).decode()


def e(t):
    return html.escape(str(t))


def visible(c):
    """Aclara los colores muy oscuros para que se vean sobre el fondo noche."""
    r, g, b = (int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    if 0.2126 * r + 0.7152 * g + 0.0722 * b >= 70:
        return c
    return "#%02X%02X%02X" % tuple(round(v + (255 - v) * .45) for v in (r, g, b))


def color(eq):
    """Color de la 1ª equipación; si es blanca casi entera, el segundo color."""
    if eq.get("color"):
        return visible(eq["color"])
    kit = (KITS.get(eq.get("kit", eq["name"])) or [{}])[0]
    cs = kit.get("colores") or ["#9AA3B5"]
    if cs[0].upper() == "#FFFFFF" and len(cs) > 1 and kit["partes"][0] < 0.8:
        return visible(cs[1])
    return visible(cs[0])


CSS = f"""
@font-face{{font-family:Archivo;src:url(data:font/woff2;base64,{b64('Archivo-latin.woff2')}) format('woff2');
 font-weight:100 900;font-stretch:62% 125%}}
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;background:{NOCHE};color:#F1F3F8;font-family:Archivo,sans-serif;overflow:hidden}}
#v{{position:relative;width:1080px;height:1920px;overflow:hidden;
 background:radial-gradient(1100px 900px at 0% 0%,color-mix(in srgb,var(--c1) 38%,transparent),transparent 70%),
            radial-gradient(1100px 900px at 100% 0%,color-mix(in srgb,var(--c2) 34%,transparent),transparent 70%),{NOCHE}}}
.safe{{position:absolute;left:80px;right:140px;top:185px;bottom:380px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.top img{{height:80px;margin-left:-14px}}
.chip{{font-size:30px;font-weight:700;letter-spacing:2px;color:#C9CED9;text-transform:uppercase}}
.kick{{margin-top:40px;display:inline-block;align-self:flex-start;padding:10px 22px;border-radius:12px;
 background:{AMARILLO};color:{NOCHE};font-size:36px;font-weight:900;letter-spacing:3px;text-transform:uppercase}}
.cuerpo{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:44px}}
.num{{font-size:300px;line-height:.85;font-weight:900;font-stretch:72%;letter-spacing:-6px}}
.frase{{font-size:62px;line-height:1.05;font-weight:800;font-stretch:85%}}
.frase b{{color:{AMARILLO}}}
.disp{{font-weight:900;font-stretch:75%}}
.vs{{display:flex;align-items:center;justify-content:space-between;gap:20px}}
.eq{{display:flex;align-items:center;gap:18px;font-size:50px;font-weight:800;font-stretch:85%}}
.eq i{{width:30px;height:30px;border-radius:50%;background:var(--c);flex:none}}
.eq.r{{flex-direction:row-reverse;text-align:right}}
.res{{font-size:150px;line-height:1;font-weight:900;font-stretch:72%;white-space:nowrap}}
.res s{{text-decoration:none;color:{GRIS};margin:0 8px}}
.vs.peq .eq{{font-size:40px}} .vs.peq .res{{font-size:96px}} .vs.peq .eq i{{width:24px;height:24px}}
.mini{{font-size:38px;color:#AEB5C4;font-weight:600}}
.pill{{align-self:flex-start;padding:16px 30px;border-radius:999px;font-size:44px;font-weight:900;color:{NOCHE}}}
.q{{font-size:64px;font-weight:900;font-stretch:80%;line-height:1}}
.q span{{color:{AMARILLO}}}
.pie{{margin-top:18px;font-size:30px;color:#7D8597}}
.barra{{display:flex;height:34px;gap:6px}}
.barra div{{border-radius:8px}}
.leyenda{{display:flex;gap:6px;margin-top:14px}}
.leyenda div{{font-size:30px;font-weight:700;color:#AEB5C4}}
.leyenda b{{display:block;font-size:56px;font-weight:900;font-stretch:75%;color:#F1F3F8}}
.cuad{{display:flex;gap:12px}}
.cuad div{{width:84px;height:84px;border-radius:14px;display:grid;place-items:center;font-size:44px;font-weight:900;color:{NOCHE}}}
.fila{{display:flex;align-items:center;justify-content:space-between;font-size:38px;font-weight:700;padding:9px 0;
 border-bottom:2px solid #1E2330}}
.fila .ok{{color:{VERDE};font-size:44px;font-weight:900}} .fila .ko{{color:{ROJO};font-size:44px;font-weight:900}}
"""


def pagina(d, kicker, cuerpo, pregunta):
    h, a = d["home"], d["away"]
    pie = d.get("footer", "Data, not betting advice · 18+")
    guias = ".safe{outline:3px dashed #FF3B3B}" if GUIAS else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{guias}</style></head><body>'
            f'<div id="v" style="--c1:{h["c"]};--c2:{a["c"]}"><div class="safe">'
            f'<div class="top"><img src="data:image/png;base64,{b64("2yellow-logo-transparent-for-dark.png")}">'
            f'<div class="chip">{e(d.get("competition", ""))}</div></div>'
            f'<div class="kick">{e(kicker)}</div><div class="cuerpo">{cuerpo}</div>'
            f'<div class="q">{e(d.get("question", pregunta))} <span>&#8595;</span></div>'
            f'<div class="pie">{e(pie)}</div></div></div></body></html>')


def vs(h, a, centro='<span class="disp" style="font-size:56px;color:#5C6476">vs</span>', peq=False):
    return (f'<div class="vs{" peq" if peq else ""}"><div class="eq" style="--c:{h["c"]}"><i></i>{e(h["short"])}</div>'
            f'{centro}<div class="eq r" style="--c:{a["c"]}"><i></i>{e(a["short"])}</div></div>')


def res(gh, ga):
    return f'<div class="res">{gh}<s>–</s>{ga}</div>'


def num(n, col="#F1F3F8"):
    return f'<div class="num" style="color:{col}">{e(n)}</div>'


def barra3(d, p, resaltar):
    h, a = d["home"], d["away"]
    cols = [h["c"], GRIS, a["c"]]
    noms = [h["short"], "Draw", a["short"]]
    seg = "".join(f'<div style="width:{p[i]}%;background:{cols[i]};opacity:{1 if i == resaltar else .4}"></div>' for i in range(3))
    ley = "".join(f'<div style="width:{p[i]}%;{"text-align:right" if i == 2 else ""}"><b>{p[i]:.0f}%</b>{e(noms[i])}</div>'
                  for i in range(3))
    return f'<div><div class="barra">{seg}</div><div class="leyenda">{ley}</div></div>'


# ---------- previo ----------

def prediction(d):
    h, a, p = d["home"], d["away"], d["probs"]
    i = max(range(3), key=lambda k: p[k])
    quien = [f"{h['short']} win", "a draw", f"{a['short']} win"][i]
    ps = d["predicted_score"]
    cuerpo = (vs(h, a) + num(f"{p[i]:.0f}%", AMARILLO) + f'<div class="frase">chance of <b>{e(quien)}</b></div>'
              + barra3(d, p, i) + f'<div class="mini">Most likely score: <b style="color:#F1F3F8">{ps[0]}–{ps[1]}</b></div>')
    return pagina(d, "Our prediction", cuerpo, "Agree?")


def upset_alert(d):
    h, a = d["home"], d["away"]
    t = d[d["underdog"]]
    m, c = d["model_pct"], d["bookies_pct"]
    fila = lambda nom, v, col: (f'<div style="display:flex;align-items:center;gap:20px"><div class="mini" style="width:250px">{nom}</div>'
                                f'<div style="flex:1;height:44px;background:#1E2330;border-radius:10px">'
                                f'<div style="width:{v * 2}%;height:100%;background:{col};border-radius:10px"></div></div>'
                                f'<div class="disp" style="font-size:60px;width:120px;text-align:right">{v}%</div></div>')
    cuerpo = (vs(h, a) + num(f"{m}%", ROJO)
              + f'<div class="frase">chance of a <b>{e(t["short"])}</b> win. The bookies only see {c}%.</div>'
              + '<div style="display:flex;flex-direction:column;gap:18px">'
              + fila("Our model", m, ROJO) + fila("Bookies", c, GRIS) + '</div>')
    return pagina(d, "Upset alert", cuerpo, "Shock incoming?")


def goals(d):
    h, a = d["home"], d["away"]
    xh, xa = d["exp_goals"]
    centro = f'<div class="res" style="font-size:120px">{xh:.1f}<s>·</s>{xa:.1f}</div>'
    cuerpo = (num(f'{d["btts"]}%', AMARILLO) + '<div class="frase"><b>both teams</b> score, says our model</div>'
              + '<div class="mini">Expected goals</div>' + vs(h, a, centro))
    return pagina(d, "Goals or nothing?", cuerpo, "Over or under?")


def form(d):
    h, a = d["home"], d["away"]
    col = {"W": VERDE, "D": GRIS, "L": ROJO}
    def racha(eq, f):
        cs = "".join(f'<div style="background:{col[x]}">{x}</div>' for x in f[-5:])
        return f'<div><div class="eq" style="--c:{eq["c"]};margin-bottom:16px"><i></i>{e(eq["short"])}</div><div class="cuad">{cs}</div></div>'
    cuerpo = (num(d["number"], AMARILLO) + f'<div class="frase">{d["text"]}</div>'
              + racha(h, d["form_home"]) + racha(a, d["form_away"]) + '<div class="mini">Last 5 games, newest on the right</div>')
    return pagina(d, "Form check", cuerpo, d.get("question", "Can they keep it going?"))


def key_number(d):
    h, a = d["home"], d["away"]
    cuerpo = (num(d["number"], AMARILLO) + f'<div class="frase">{d["text"]}</div>' + vs(h, a)
              + f'<div class="mini">{e(d.get("when", ""))}</div>')
    return pagina(d, "Key number", cuerpo, d.get("question", "Does the streak end?"))


# ---------- postpartido ----------

def deserved(d):
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    xh, xa = d["xg"]
    if abs(xh - xa) < 0.3:
        veredicto, col = "A draw was fair", AMARILLO
    else:
        mejor = h if xh > xa else a
        gano = (gh > ga) == (xh > xa) and gh != ga
        veredicto = f'{mejor["short"]} deserved it'
        col = VERDE if gano else ROJO
    centro_xg = f'<div class="res" style="font-size:130px;color:{AMARILLO}">{xh:.1f}<s>·</s>{xa:.1f}</div>'
    cuerpo = ('<div class="mini">Final score</div>' + vs(h, a, res(gh, ga), peq=True)
              + '<div class="mini">Chances created (xG)</div>' + vs(h, a, centro_xg, peq=True)
              + f'<div class="pill" style="background:{col}">{e(veredicto)}</div>')
    return pagina(d, "Deserved?", cuerpo, "Robbery or fair?")


def prediction_vs_result(d):
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    ph, pa = d["predicted_score"]
    p = d["probs"]
    i = max(range(3), key=lambda k: p[k])
    real = 0 if gh > ga else 1 if gh == ga else 2
    ok = i == real
    texto = "Exact score!" if [ph, pa] == [gh, ga] else "Called it" if ok else "Missed it"
    bloque = lambda t, x, y, op: (f'<div style="opacity:{op}"><div class="mini">{t}</div>{vs(h, a, res(x, y), peq=True)}</div>')
    cuerpo = (bloque("We said", ph, pa, .75) + bloque("It ended", gh, ga, 1)
              + f'<div class="pill" style="background:{VERDE if ok else ROJO};font-size:64px;padding:20px 40px">'
              + f'{"&#10003;" if ok else "&#10007;"} {texto}</div>')
    return pagina(d, "Prediction vs result", cuerpo, "Did you see it coming?")


def upset_happened(d):
    h, a = d["home"], d["away"]
    t = d[d["underdog"]]
    gh, ga = d["score"]
    cuerpo = (num(f'{d["pre_pct"]}%', ROJO)
              + f'<div class="frase">That was <b>{e(t["short"])}</b>’s chance before kick-off. They won.</div>'
              + vs(h, a, res(gh, ga)))
    return pagina(d, "Upset!", cuerpo, "Who called it?")


def stat_of_match(d):
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    cuerpo = (num(d["number"], AMARILLO) + f'<div class="frase">{d["text"]}</div>' + vs(h, a, res(gh, ga), peq=True))
    return pagina(d, "Stat of the match", cuerpo, d.get("question", "Seen worse?"))


def weekend_record(d):
    ok = sum(1 for m in d["matches"] if m[4])
    filas = "".join(f'<div class="fila"><span>{e(m[0])} <b class="disp">{m[1]}–{m[2]}</b> {e(m[3])}</span>'
                    f'<span class="{"ok" if m[4] else "ko"}">{"&#10003;" if m[4] else "&#10007;"}</span></div>'
                    for m in d["matches"])
    marca = num(f"{ok}/{len(d['matches'])}", AMARILLO)
    cuerpo = (f'<div style="display:flex;align-items:flex-end;gap:30px">{marca}'
              f'<div class="frase" style="padding-bottom:20px">correct<br>calls</div></div><div>{filas}</div>')
    return pagina(d, "Our matchday", cuerpo, "Beat us next week?")


PLANTILLAS = {"prediction": prediction, "upset_alert": upset_alert, "goals": goals, "form": form,
              "key_number": key_number, "deserved": deserved, "prediction_vs_result": prediction_vs_result,
              "upset_happened": upset_happened, "stat_of_match": stat_of_match, "weekend_record": weekend_record}


def html_de(d):
    d.setdefault("home", {"name": "", "short": "", "color": "#FFD21F"})
    d.setdefault("away", {"name": "", "short": "", "color": "#FF3B3B"})
    for k in ("home", "away"):
        d[k]["c"] = color(d[k])
        d[k].setdefault("short", d[k]["name"])
    return PLANTILLAS[d["template"]](d)


def renderizar(trabajos):
    """trabajos: lista de (datos, ruta_png)."""
    from playwright.sync_api import sync_playwright
    exe = Path("/opt/pw-browsers/chromium")
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=str(exe)) if exe.exists() else pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for d, out in trabajos:
            pg.set_content(html_de(d))
            pg.wait_for_timeout(200)
            pg.screenshot(path=str(out))
            print("OK", out)
        b.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("datos", nargs="*")
    ap.add_argument("--todos", action="store_true", help="renderiza todos los ejemplos/*.json")
    ap.add_argument("-o", "--carpeta", help="carpeta de salida (por defecto, junto al json)")
    ap.add_argument("--guias", action="store_true", help="dibuja la zona segura (solo para revisar)")
    x = ap.parse_args()
    GUIAS = x.guias
    rutas = sorted((AQUI / "ejemplos").glob("*.json")) if x.todos else [Path(p) for p in x.datos]
    renderizar([(json.loads(p.read_text()), (Path(x.carpeta) if x.carpeta else p.parent) / (p.stem + ".png"))
                for p in rutas])
