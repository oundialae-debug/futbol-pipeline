"""Plantillas 9:16 de 2yellow (1080x1920 PNG) para TikTok/Instagram.

Una idea por imagen: un número gigante, una frase que lo explica, el partido
y la pregunta final. Cinco de previo y cinco de postpartido.
    python3 redes/plantillas/generar.py ejemplos/prediction.json   # una
    python3 redes/plantillas/generar.py --todos                    # todos los ejemplos
Zona segura TikTok + Instagram: texto y datos dentro de x 80-880 e y 318-1540 (iconos de TikTok a la derecha,
descripción abajo; IG en reel solo enseña el centro). --guias la dibuja. Sin API: solo datos que ya estén en disco.
"""
import argparse, base64, html, json, os, re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REC = AQUI / "recursos"
AMARILLO, ROJO, VERDE, GRIS, NOCHE = "#FFD21F", "#FF3B3B", "#2BD67B", "#5C6476", "#0A0C11"
KITS = json.loads((REC / "kits_camiseta.json").read_text())
GUIAS = False
ACTUAL = ({"c": "#F1F3F8"}, {"c": "#F1F3F8"})


def b64(p):
    return base64.b64encode((REC / p).read_bytes()).decode()


def e(t):
    return html.escape(str(t))


def _hls(c):
    import colorsys
    r, g, b = (int(c.lstrip("#")[k:k + 2], 16) / 255 for k in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def _hex(h, l, s):
    import colorsys
    return "#%02X%02X%02X" % tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, l, s))


def visible(c):
    """Sube la luz de los colores oscuros SIN perder el tono (no a gris), para el fondo noche."""
    h, l, s = _hls(c)
    if s < .2:                       # blanco, negro o gris: blanco
        return "#F1F3F8" if l > .5 or l < .25 else _hex(h, .75, s)
    return _hex(h, min(max(l, .52), .62), max(s, .7))


import equipaciones as EQ  # paleta de la app 2yellow (usuario 06/10: "úsala de ahora en adelante")


def color(eq):
    """Color del equipo con la paleta de la app (equipaciones.json: 1ª equipación real, aclarada a contraste 3:1 sobre
    el fondo). Equipo sin ficha: gris neutro de la app (nunca blanco: antes solo el Barça salía en color)."""
    if eq.get("color"):
        return visible(eq["color"])
    n = eq.get("kit", eq.get("name", ""))
    return EQ.kit(n, 0)["barra"]


def color_viejo(eq):
    """Método anterior (kits_camiseta.json de recursos); ya no se usa, se deja de referencia."""
    if eq.get("color"):
        return visible(eq["color"])
    if eq["name"] in COLOR_FIJO:
        return COLOR_FIJO[eq["name"]]
    kit = (KITS.get(eq.get("kit", eq["name"])) or [{}])[0]
    cand = [(c, p) for c, p in zip(kit.get("colores", []), kit.get("partes", [])) if p >= .04]
    vivos = [(c, p) for c, p in cand if _hls(c)[2] >= .35 and .08 < _hls(c)[1] < .92]
    if not vivos:
        return "#F1F3F8"
    return visible(max(vivos, key=lambda cp: cp[1] * (.5 + _hls(cp[0])[2]))[0])


def _parecidos(c1, c2):
    """Dos colores que en la imagen no se distinguen (rojo y rojo, blanco y gris claro)."""
    (h1, l1, s1), (h2, l2, s2) = _hls(c1), _hls(c2)
    if s1 < .2 or s2 < .2:
        return s1 < .2 and s2 < .2 and abs(l1 - l2) < .3
    dh = min(abs(h1 - h2), 1 - abs(h1 - h2))
    return dh < .08 and abs(l1 - l2) < .25


def _alternativas(eq):
    """Otros colores del equipo, del más al menos suyo: resto de la 1ª camiseta y luego la 2ª."""
    kits = KITS.get(eq.get("kit", eq["name"])) or []
    alt = []
    for n, kit in enumerate(kits[:2]):
        for c, pp in zip(kit.get("colores", []), kit.get("partes", [])):
            if pp >= .04:
                alt.append((visible(c), pp / (n + 1)))
    return alt


def separar(h, a):
    """Usuario, 06/10: nunca el mismo color para los dos equipos (Croacia y España, ambos rojos).
    Regla de la app: el local con su 1ª; el visitante con la 1ª, 2ª o 3ª que no choque (como en la TV)."""
    if h.get("color") or a.get("color"):
        pass
    else:
        kl, kv = EQ.colores_partido(h.get("kit", h["name"]), a.get("kit", a["name"]))
        h["c"], a["c"] = kl["barra"], kv["barra"]
        h["t"], a["t"] = texto_sobre(h["c"]), texto_sobre(a["c"])
        return
    if not _parecidos(h["c"], a["c"]):
        return
    mejor = None
    for t, otro in ((h, a), (a, h)):
        for c, peso in _alternativas(t):
            if not _parecidos(c, otro["c"]) and (mejor is None or peso > mejor[2]):
                mejor = (t, c, peso)
    t, c = (mejor[0], mejor[1]) if mejor else (a, AMARILLO)
    t["c"] = c
    t["t"] = texto_sobre(c)


# Equipos cuyo color de camiseta engaña (un detalle se lleva el protagonismo).
COLOR_FIJO = {"Germany": "#F1F3F8"}


def texto_sobre(c):
    r, g, b = (int(c.lstrip("#")[k:k + 2], 16) for k in (0, 2, 4))
    return NOCHE if 0.2126 * r + 0.7152 * g + 0.0722 * b > 150 else "#FFFFFF"


# ZONA SEGURA (usuario 07/10, "5ª o 6ª vez"): TikTok tapa la derecha (iconos: x>880) y abajo (descripción: y>1540);
# IG con música (reel) solo enseña y 285-1635 en el feed. Todo el texto/dato dentro de x 80-880, y 318-1540 (.safe).
CSS = f"""
@font-face{{font-family:Archivo;src:url(data:font/woff2;base64,{b64('Archivo-latin.woff2')}) format('woff2');
 font-weight:100 900;font-stretch:62% 125%}}
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;background:{NOCHE};color:#F1F3F8;font-family:Archivo,sans-serif;overflow:hidden}}
#v{{position:relative;width:1080px;height:1920px;overflow:hidden;
 background:radial-gradient(1100px 900px at 0% 0%,color-mix(in srgb,var(--c1) 62%,transparent),transparent 70%),
            radial-gradient(1100px 900px at 100% 0%,color-mix(in srgb,var(--c2) 58%,transparent),transparent 70%),{NOCHE}}}
.safe{{position:absolute;left:80px;right:200px;top:185px;bottom:380px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.top img{{height:80px;margin-left:-14px}}
.chip{{font-size:30px;font-weight:700;letter-spacing:2px;color:#C9CED9;text-transform:uppercase}}
.kick{{margin-top:30px;display:inline-block;align-self:flex-start;padding:10px 22px;border-radius:12px;
 background:{AMARILLO};color:{NOCHE};font-size:36px;font-weight:900;letter-spacing:3px;text-transform:uppercase}}
.cuerpo{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:44px}}
.num{{font-size:300px;line-height:.85;font-weight:900;font-stretch:72%;letter-spacing:-6px}}
.frase{{font-size:62px;line-height:1.05;font-weight:800;font-stretch:85%}}
.frase b{{color:{AMARILLO}}}
.disp{{font-weight:900;font-stretch:75%}}
.vs{{display:flex;align-items:center;justify-content:space-between;gap:20px}}
.eq{{display:inline-flex;align-items:center;padding:8px 24px;border-radius:14px;background:var(--c);color:var(--t);font-size:48px;font-weight:900;font-stretch:85%;white-space:nowrap}}
.eq i{{display:none}}
.eq.r{{flex-direction:row-reverse;text-align:right}}
.res{{font-size:150px;line-height:1;font-weight:900;font-stretch:72%;white-space:nowrap}}
.res s{{text-decoration:none;color:{GRIS};margin:0 8px}}
.vs.peq .eq{{font-size:38px;padding:6px 18px}} .vs.peq .res{{font-size:96px}} .vs.peq .eq i{{width:24px;height:24px}}
.mini{{font-size:38px;color:#AEB5C4;font-weight:600}}
.pill{{align-self:flex-start;padding:16px 30px;border-radius:999px;font-size:44px;font-weight:900;color:{NOCHE}}}
.q{{font-size:64px;font-weight:900;font-stretch:80%;line-height:1}}
.pie{{margin-top:18px;font-size:30px;color:#7D8597}}
.barra{{display:flex;height:34px;gap:6px}}
.barra div{{border-radius:8px}}
.leyenda{{display:flex;gap:6px;margin-top:14px}}
.leyenda div{{font-size:30px;font-weight:700;color:#AEB5C4}}
.leyenda b{{display:block;font-size:56px;font-weight:900;font-stretch:75%;color:#F1F3F8}}
.cuad{{display:flex;gap:12px}}
.cuad div{{width:84px;height:84px;border-radius:14px;display:grid;place-items:center;font-size:44px;font-weight:900;color:{NOCHE}}}
.fila{{display:flex;align-items:center;justify-content:space-between;font-size:var(--f,38px);font-weight:700;padding:6px 0;
 border-bottom:2px solid #1E2330}}
.fila .ok{{color:{VERDE};font-size:44px;font-weight:900}} .fila .ko{{color:{ROJO};font-size:44px;font-weight:900}}
"""


def pagina(d, kicker, cuerpo, pregunta):
    h, a = d["home"], d["away"]
    pie = d.get("footer", "")  # usuario 06/10: sin "not betting advice · 18+" en las imágenes (confunde al algoritmo)
    guias = (".safe{outline:3px dashed #FF3B3B}" if GUIAS else "") + CSS_IG45
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{guias}</style></head><body>'
            f'<div id="v" style="--c1:{h["c"]};--c2:{a["c"]}"><div class="safe">'
            f'<div class="top"><img src="data:image/png;base64,{b64("2yellow-logo-transparent-for-dark.png")}">'
            f'<div class="chip">{e(d.get("competition", ""))}</div></div>'
            f'<div style="display:flex;height:10px;gap:6px;margin-top:22px"><div style="flex:1;border-radius:5px;background:{h["c"]}"></div>'
            f'<div style="flex:1;border-radius:5px;background:{a["c"]}"></div></div>'
            f'<div class="kick">{e(kicker)}</div><div class="cuerpo">{cuerpo}</div>'
            f'<div class="q">{e(d.get("question", pregunta))}</div>'
            f'<div class="pie" style="display:flex;justify-content:space-between;align-items:center"><span>{e(pie)}</span>'
            f'{SWIPE if CARRUSEL and d["template"] not in SIN_SWIPE and d.get("swipe", True) else ""}</div></div></div></body></html>')


# Aviso de "hay más": SOLO en carrusel (CARRUSEL=1 en el entorno), en todas menos en la última y en las del perfil.
# En vídeo no hay nada que deslizar (usuario, 06/10).
CARRUSEL = os.environ.get("CARRUSEL") == "1"
# Imágenes sueltas de Instagram: 4:5 (1080x1350). IG recorta las 9:16 en el perfil y el feed (usuario 06/10).
IG45 = os.environ.get("LIENZO") == "4x5"
# LIENZO=reel (usuario 06/10): Instagram convierte la foto en reel al ponerle música (9:16) y en el feed solo enseña
# la franja central 4:5 (y 285-1635). Imagen 9:16 con TODO el contenido dentro de esa franja (margen incluido).
IGREEL = os.environ.get("LIENZO") == "reel"
ALTO = 1350 if IG45 else 1920
CSS_IG45 = (("body,#v{height:1350px!important}" if IG45 else "")
            + ".safe{top:%dpx!important;bottom:%dpx!important;right:%dpx!important}.num{font-size:230px!important}"
            % ((56, 48, 80) if IG45 else (318, 380, 200))) if (IG45 or IGREEL) else ""
SIN_SWIPE = {"follow", "our_calls", "picks_list", "head_to_head", "ranking", "xi", "indice"}
SWIPE = (f'<span style="display:inline-flex;align-items:center;gap:10px;background:{AMARILLO};color:{NOCHE};'
         f'border-radius:999px;padding:8px 22px;font-size:34px;font-weight:900;font-stretch:85%">Swipe'
         f'<span style="font-size:46px;line-height:.6;letter-spacing:-8px">&#8250;&#8250;&#8250;</span></span>')


def vs(h, a, centro='<span class="disp" style="font-size:56px;color:#5C6476">vs</span>', peq=False):
    return (f'<div class="vs{" peq" if peq else ""}"><div class="eq" style="--c:{h["c"]};--t:{h["t"]}"><i></i>{e(h["short"])}</div>'
            f'{centro}<div class="eq r" style="--c:{a["c"]};--t:{a["t"]}"><i></i>{e(a["short"])}</div></div>')


def res(gh, ga):
    h, a = ACTUAL
    return f'<div class="res"><span style="color:{h["c"]}">{gh}</span><s>–</s><span style="color:{a["c"]}">{ga}</span></div>'


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
    cuerpo = (vs(h, a) + num(f"{p[i]:.0f}%", [h["c"], AMARILLO, a["c"]][i]) + f'<div class="frase">chance of <b>{e(quien)}</b></div>'
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
    cuerpo = (vs(h, a) + num(f"{m}%", t["c"])
              + f'<div class="frase">chance of a <b>{e(t["short"])}</b> win. The consensus only sees {c}%.</div>'
              + '<div style="display:flex;flex-direction:column;gap:18px">'
              + fila("Our model", m, ROJO) + fila("Consensus", c, GRIS) + '</div>')
    return pagina(d, "Upset alert", cuerpo, "Shock incoming?")


def goals(d):
    h, a = d["home"], d["away"]
    xh, xa = d["exp_goals"]
    centro = (f'<div class="res" style="font-size:120px"><span style="color:{h["c"]}">{xh:.1f}</span><s>·</s>'
              f'<span style="color:{a["c"]}">{xa:.1f}</span></div>')
    cuerpo = (num(f'{d["btts"]}%', AMARILLO) + '<div class="frase"><b>both teams</b> score, says our model</div>'
              + '<div class="mini">Expected goals</div>' + vs(h, a, centro))
    return pagina(d, "Goals or nothing?", cuerpo, "Over or under?")


def elo_chart(d):
    """Línea del Elo de los dos equipos en sus últimos partidos (SVG)."""
    h, a = d["home"], d["away"]
    W, H, pad = 860, 250, 16
    todos = d["elo_home"] + d["elo_away"]
    lo, hi = min(todos) - 10, max(todos) + 10
    def linea(vs_, c, nombre):
        n = len(vs_)
        pts = [(pad + k * (W - 2 * pad - 150) / (n - 1), pad + (hi - v) * (H - 2 * pad) / (hi - lo)) for k, v in enumerate(vs_)]
        x, y = pts[-1]
        return (f'<polyline points="{" ".join(f"{px:.0f},{py:.0f}" for px, py in pts)}" fill="none" stroke="{c}" '
                f'stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/><circle cx="{x:.0f}" cy="{y:.0f}" r="14" fill="{c}"/>'
                f'<text x="{x + 26:.0f}" y="{y + 16:.0f}" fill="{c}" font-size="46" font-weight="900" '
                f'font-stretch="75%" font-family="Archivo">{vs_[-1]}</text>'
                f'<text x="{x + 26:.0f}" y="{y + 50:.0f}" fill="{c}" font-size="28" font-weight="800" '
                f'font-family="Archivo">{e(nombre)}</text>')
    return (f'<svg width="{W}" height="{H + 40}" style="overflow:visible">{linea(d["elo_away"], a["c"], a["short"])}'
            f'{linea(d["elo_home"], h["c"], h["short"])}</svg>')


def elo_form(d):
    h, a = d["home"], d["away"]
    t = d[d["focus"]]
    serie = d["elo_" + d["focus"]]
    cambio = serie[-1] - serie[-6]
    signo = "+" if cambio >= 0 else "−"
    cuerpo = (num(f"{signo}{abs(cambio)}", t["c"])
              + f'<div class="frase">Elo points for <b>{e(t["short"])}</b> in 5 games. {d.get("extra", "")}</div>'
              + f'<div><div class="mini" style="margin-bottom:10px">2yellow Elo · last {len(serie)} games</div>{elo_chart(d)}</div>'
              + vs(h, a, peq=True))
    return pagina(d, "Elo check", cuerpo, d.get("question", "Real form or a lucky run?"))

def key_number(d):
    h, a = d["home"], d["away"]
    cuerpo = (num(d["number"], d[d["team"]]["c"] if d.get("team") else AMARILLO) + f'<div class="frase">{d["text"]}</div>' + vs(h, a)
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
    centro_xg = (f'<div class="res" style="font-size:130px"><span style="color:{h["c"]}">{xh:.1f}</span><s>·</s>'
                 f'<span style="color:{a["c"]}">{xa:.1f}</span></div>')
    cuerpo = ('<div class="mini">Final score</div>' + vs(h, a, res(gh, ga), peq=True)
              + '<div class="mini">Chances created (xG)</div>' + vs(h, a, centro_xg, peq=True)
              + f'<div class="pill" style="background:{col}">{e(veredicto)}</div>')
    return pagina(d, "Deserved?", cuerpo, "Robbery or fair?")


MERCADOS = {"home": "{h} to win", "draw": "Draw", "away": "{a} to win", "over25": "Over 2.5 goals",
            "under25": "Under 2.5 goals", "btts_yes": "Both teams score", "btts_no": "Not both teams score",
            "over15": "Over 1.5 goals", "under15": "Under 1.5 goals", "over35": "Over 3.5 goals", "under35": "Under 3.5 goals"}


def acierto(m, gh, ga):
    return {"home": gh > ga, "draw": gh == ga, "away": ga > gh, "over25": gh + ga > 2, "under25": gh + ga < 3,
            "btts_yes": gh > 0 and ga > 0, "btts_no": gh == 0 or ga == 0, "over15": gh + ga > 1, "under15": gh + ga < 2,
            "over35": gh + ga > 3, "under35": gh + ga < 4}[m]


def nombre_mercado(m, h="Home", a="Away"):
    return MERCADOS[m].format(h=h, a=a)


def prediction_vs_result(d):
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    m, pct = d["market"], d["pct"]
    ok = acierto(m, gh, ga)
    cuerpo = ('<div class="mini">We said</div>'
              + f'<div class="frase" style="font-size:84px;line-height:1"><b>{e(nombre_mercado(m, h["short"], a["short"]))}</b></div>'
              + f'<div class="frase" style="margin-top:-24px">{pct}% chance, before kick-off</div>'
              + '<div class="mini">It ended</div>' + vs(h, a, res(gh, ga))
              + f'<div class="pill" style="background:{VERDE if ok else ROJO};font-size:64px;padding:20px 40px">'
              + f'{"&#10003; Called it" if ok else "&#10007; Missed it"}</div>')
    return pagina(d, "Prediction vs result", cuerpo, d.get("question", "Did you see it coming?"))

def upset_happened(d):
    """Sorpresa: ganó el que no esperábamos o hubo un empate improbable (underdog = "draw")."""
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    if d["underdog"] == "draw":
        fuerte = h if d.get("favourite") == "home" else a
        debil = a if fuerte is h else h
        col, txt = AMARILLO, (f'That was the chance of a draw. <b>{e(debil["short"])}</b> held '
                              f'<b>{e(fuerte["short"])}</b>.')
    else:
        t = d[d["underdog"]]
        col, txt = t["c"], f'That was <b>{e(t["short"])}</b>’s chance before kick-off. They won.'
    cuerpo = num(f'{d["pre_pct"]}%', col) + f'<div class="frase">{txt}</div>' + vs(h, a, res(gh, ga))
    return pagina(d, "Upset!", cuerpo, d.get("question", "Who called it?"))


def stat_of_match(d):
    h, a = d["home"], d["away"]
    gh, ga = d["score"]
    cuerpo = (num(d["number"], d[d["team"]]["c"] if d.get("team") else AMARILLO) + f'<div class="frase">{d["text"]}</div>' + vs(h, a, res(gh, ga), peq=True))
    return pagina(d, "Stat of the match", cuerpo, d.get("question", "Seen worse?"))


PRINCIPALES = ("1X2", "Over/Under 2.5", "Both teams score")   # 1.5 y 3.5 son demasiado fáciles


def mejores_aciertos(ms, max_fallos=2):
    """Por partido, el acierto MÁS DIFÍCIL (menor probabilidad que le dábamos) en los mercados
    principales; si no acertamos ninguno, nuestro fallo en 1X2. Siempre 1 o 2 fallos a la vista."""
    filas = []
    for loc, gh, ga, vis, picks in ms:
        cand = [(pct, pick, acierto(pick, gh, ga)) for fam, (pick, pct) in picks.items() if fam in PRINCIPALES]
        buenos = sorted(c for c in cand if c[2])
        malos = [c for c in cand if not c[2]]
        fallo = next((c for c in malos if c[1] in ("home", "draw", "away")), malos[0] if malos else None)
        filas.append({"m": (loc, gh, ga, vis), "bien": buenos[0] if buenos else None, "mal": fallo})
    con_fallo = [f for f in filas if f["bien"] is None]
    if not con_fallo:     # todo acertado: enseñamos el fallo del partido cuyo acierto era más fácil
        f = max((f for f in filas if f["mal"]), key=lambda f: f["bien"][0], default=None)
        if f:
            f["bien"] = None
    elif len(con_fallo) > max_fallos:
        quitar = con_fallo[max_fallos:]
        filas = [f for f in filas if f not in quitar]
    return [(*f["m"], *(f["bien"] or f["mal"])) for f in filas]


def weekend_record(d):
    """Lo mejor de la jornada: el acierto más difícil de cada partido y 1-2 fallos."""
    filas_m = mejores_aciertos(d["matches"])
    ok = sum(1 for x in filas_m if x[6])
    filas = "".join(f'<div class="fila"><span>{e(loc)} <b class="disp">{gh}–{ga}</b> {e(vis)}</span>'
                    f'<span style="display:flex;gap:16px;align-items:center"><span class="mini" style="font-size:28px">'
                    f'{e(nombre_mercado(p, loc, vis))} · {round(pct * 100)}%</span>'
                    f'<span class="{"ok" if x else "ko"}">{"&#10003;" if x else "&#10007;"}</span></span></div>'
                    for loc, gh, ga, vis, pct, p, x in filas_m)
    marca = f'<div class="num" style="color:{AMARILLO};font-size:220px">{ok}/{len(filas_m)}</div>'
    cuerpo = (f'<div style="display:flex;align-items:flex-end;gap:30px">{marca}'
              f'<div class="frase" style="padding-bottom:20px">correct<br>calls</div></div>'
              f'<div class="frase" style="margin-top:-20px">Our boldest calls this matchday, with the % we gave</div>'
              f'<div style="--f:32px">{filas}</div>')
    return pagina(d, "Our matchday", cuerpo, d.get("question", "Beat us next week?"))


def follow(d):
    """Última del carrusel: el próximo partido grande con nuestro % TAPADO. Poco texto, mucha curiosidad."""
    h, a = d["home"], d["away"]
    t = d[d["side"]] if d.get("side") in ("home", "away") else {"c": AMARILLO}
    flechas = "".join(f'<span style="opacity:{o}">&#8250;</span>' for o in (.35, .65, 1))
    badge = (f'<div class="pill" style="background:{VERDE};font-size:40px">&#10003; {e(d["badge"])}</div>'
             if d.get("badge") else "")
    oculto = (f'<div style="position:relative;align-self:center">'
              f'<div class="num" style="font-size:340px;color:{t["c"]};filter:blur(44px)">{d["hidden_pct"]}%</div>'
              f'<div style="position:absolute;inset:0;display:grid;place-items:center">'
              f'<svg width="150" height="170" viewBox="0 0 24 27"><rect x="2" y="11" width="20" height="15" rx="3" fill="#F1F3F8"/>'
              f'<path d="M6 11V7a6 6 0 0 1 12 0v4" fill="none" stroke="#F1F3F8" stroke-width="3"/></svg></div></div>')
    cta = (f'<div style="display:flex;align-items:center;gap:24px;background:{AMARILLO};color:{NOCHE};'
           f'border-radius:28px;padding:22px 28px">'
           f'<img src="data:image/png;base64,{b64("perfil.png")}" style="width:110px;height:110px;border-radius:50%;border:4px solid {NOCHE}">'
           f'<div class="disp" style="flex:1;font-size:58px">@2yellowdata</div>'
           f'<div class="disp" style="font-size:150px;line-height:.7;letter-spacing:-18px">{flechas}</div></div>')
    cuerpo = (badge + vs(h, a) + oculto
              + f'<div class="frase" style="text-align:center">{e(d.get("text", "Our call is on our profile."))}</div>' + cta)
    return pagina(d, d.get("kicker", "Next up"), cuerpo, d.get("question", "Follow. Don’t miss it."))


def our_calls(d):
    """Post fijo del perfil: los pronósticos que se tapan en la 6ª, destapados, todos en una imagen."""
    tarjetas = ""
    for m in d["matches"]:
        h, a = dict(m["home"]), dict(m["away"])
        for t in (h, a):
            t["c"] = color(t); t["t"] = texto_sobre(t["c"]); t.setdefault("short", t["name"])
        separar(h, a)
        p = m["probs"]
        i = max(range(3), key=lambda k: p[k])
        quien = [f'{h["short"]} win', "Draw", f'{a["short"]} win'][i]
        col = [h["c"], AMARILLO, a["c"]][i]
        cols = [h["c"], GRIS, a["c"]]
        seg = "".join(f'<div style="width:{p[k]}%;background:{cols[k]};opacity:{1 if k == i else .35}"></div>' for k in range(3))
        mk, pc = m["extra"]
        tarjetas += (f'<div style="background:#12151DE6;border-radius:28px;padding:26px 30px;display:flex;flex-direction:column;gap:18px">'
                     f'<div class="mini" style="font-size:30px;letter-spacing:2px;text-transform:uppercase">{e(m["when"])}</div>'
                     f'{vs(h, a, peq=True)}'
                     f'<div style="display:flex;align-items:baseline;gap:22px"><div class="num" style="font-size:150px;color:{col}">{p[i]}%</div>'
                     f'<div class="frase" style="font-size:52px">{e(quien)}</div></div>'
                     f'<div class="barra" style="height:22px">{seg}</div>'
                     f'<div class="mini">{e(nombre_mercado(mk, h["short"], a["short"]))}: '
                     f'<b style="color:#F1F3F8">{round(pc * 100)}%</b></div></div>')  # sin "Score" (usuario 06/10: chocaba con el over)
    cuerpo = f'<div class="frase" style="font-size:70px">{e(d.get("title", "Our calls"))}</div>' + tarjetas
    return pagina(d, d.get("kicker", "Unlocked"), cuerpo, d.get("question", "Who are you backing?"))


def picks_list(d):
    """Todos los pronósticos del día en una imagen: hora, partido, nuestra elección y su %."""
    filas = ""
    vel = "filter:blur(22px);opacity:.9;user-select:none" if d.get("locked") else ""   # 6ª: pronóstico y % tapados
    for m in d["picks"]:
        h, a = dict(m["home"]), dict(m["away"])
        for t in (h, a):
            t["c"] = color(t); t["t"] = texto_sobre(t["c"]); t.setdefault("short", t["name"])
        separar(h, a)
        filas += (f'<div style="display:flex;align-items:center;gap:20px;padding:8px 0;border-bottom:2px solid #1E2330">'
                  f'<div class="mini" style="width:92px;font-size:30px">{e(m["time"])}</div>'
                  f'<div style="flex:1;min-width:0"><div style="font-size:36px;font-weight:800;white-space:nowrap">'
                  f'<span style="color:{h["c"]}">&#9679;</span> {e(h["short"])} <span style="color:{GRIS}">v</span> '
                  f'{e(a["short"])} <span style="color:{a["c"]}">&#9679;</span></div>'
                  f'<div style="font-size:32px;font-weight:700;color:{AMARILLO};margin-top:2px;{vel}">{e(m["pick"])}</div></div>'
                  f'<div class="disp" style="font-size:72px;{vel}">{m["pct"]}%</div></div>')
    flechas = "".join(f'<span style="opacity:{o}">&#8250;</span>' for o in (.35, .65, 1))
    cta = (f'<div style="display:flex;align-items:center;gap:22px;background:{AMARILLO};color:{NOCHE};border-radius:26px;'
           f'padding:14px 26px"><img src="data:image/png;base64,{b64("perfil.png")}" style="width:84px;height:84px;'
           f'border-radius:50%;border:4px solid {NOCHE}"><div class="disp" style="flex:1;font-size:54px">@2yellowdata</div>'
           f'<div class="disp" style="font-size:120px;line-height:.7;letter-spacing:-14px">{flechas}</div></div>'
           if d.get("cta", True) else "")
    candado = ('<svg width="64" height="72" viewBox="0 0 24 27" style="vertical-align:middle;margin-right:14px">'
               '<rect x="2" y="11" width="20" height="15" rx="3" fill="#F1F3F8"/>'
               '<path d="M6 11V7a6 6 0 0 1 12 0v4" fill="none" stroke="#F1F3F8" stroke-width="3"/></svg>') if d.get("locked") else ""
    cuerpo = (f'<div class="frase" style="font-size:62px">{candado}{e(d.get("title", "Today’s calls"))}</div>'
              f'<div>{filas}</div>{cta}')
    return pagina(d, d.get("kicker", "Unlocked"), cuerpo, d.get("question", "Which one are you taking?"))


# ---------- formatos de cara a cara y ranking (usuario, 06/10: probar lo que hizo crecer a otras cuentas de datos) ----------

def _fmt(v, dec):
    return f"{v:.{dec}f}" if isinstance(v, (int, float)) else str(v)


def head_to_head(d):
    """Dos equipos o jugadores frente a frente: 4-6 filas, la cifra mejor en su color y la peor en gris.
    stats: [{"label", "h", "a", "dec": 0, "menos_mejor": false}]"""
    h, a = d["home"], d["away"]
    fotos = bool(h.get("foto") and a.get("foto"))
    tam = 54 if fotos else 76
    filas, gana = "", [0, 0]
    for st in d["stats"]:
        vh, va, dec = st["h"], st["a"], st.get("dec", 0)
        if vh == va:
            ch = ca = "#F1F3F8"
        else:
            mejor_h = (vh < va) if st.get("menos_mejor") else (vh > va)
            gana[0 if mejor_h else 1] += 1
            ch, ca = (h["c"], GRIS) if mejor_h else (GRIS, a["c"])
        tot = (abs(vh) + abs(va)) or 1
        filas += (f'<div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:18px;padding:{4 if fotos else 10}px 0;'
                  f'border-bottom:2px solid #1E2330"><div class="disp" style="font-size:{tam}px;color:{ch}">{_fmt(vh, dec)}</div>'
                  f'<div class="mini" style="text-align:center;font-size:32px;max-width:340px">{e(st["label"])}</div>'
                  f'<div class="disp" style="font-size:{tam}px;color:{ca};text-align:right">{_fmt(va, dec)}</div></div>'
                  f'<div style="display:flex;height:12px;gap:4px;margin-top:-4px"><div style="width:{abs(vh) / tot * 100:.0f}%;'
                  f'border-radius:6px;background:{ch}"></div><div style="width:{abs(va) / tot * 100:.0f}%;border-radius:6px;'
                  f'background:{ca}"></div></div>')
    marcador = (f'<span class="disp" style="font-size:64px;white-space:nowrap;flex:none"><span style="color:{h["c"]}">{gana[0]}</span>'
                f'<span style="color:{GRIS}">–</span><span style="color:{a["c"]}">{gana[1]}</span></span>')
    nota = d.get("note", "")
    if fotos:
        # Usuario 06/10: caras de los jugadores con degradado hacia el centro; nada encima de las caras.
        def media(t, lado):
            hacia = "right" if lado == "l" else "left"
            img = base64.b64encode(Path(t["foto"]).read_bytes()).decode()
            mask = (f"linear-gradient(to {hacia},#000 45%,transparent 98%),linear-gradient(to bottom,transparent 0%,#000 14%,#000 68%,transparent 100%)")
            return (f'<div style="position:relative;flex:1;height:100%;overflow:hidden">'
                    f'<div style="position:absolute;inset:0;background:radial-gradient(circle at {"30%" if lado == "l" else "70%"} 45%,'
                    f'color-mix(in srgb,{t["c"]} 55%,transparent),transparent 70%)"></div>'
                    f'<img src="data:image/jpeg;base64,{img}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
                    f'object-position:center {t.get("foco", "18%")};-webkit-mask-image:{mask};-webkit-mask-composite:source-in;'
                    f'mask-image:{mask};mask-composite:intersect"></div>')
        banda = f'<div style="display:flex;height:330px;margin:0 -10px">{media(h, "l")}{media(a, "r")}</div>'
        cr = [t["credito"] for t in (h, a) if t.get("credito")]
        creditos = cr[0].replace("Photo:", "Photos:") if len(cr) == 2 and cr[0] == cr[1] else " · ".join(cr)
        nota = f"{nota}  ·  {creditos}" if creditos else nota
        creditos = ""
        cuerpo = (banda + vs(h, a, marcador)
                  + f'<div style="display:flex;flex-direction:column;gap:4px">{filas}</div>'
                  + (f'<div class="mini" style="font-size:22px">{e(nota)}</div>' if nota else "")
                  + (f'<div class="mini" style="font-size:20px;color:#5C6476">{e(creditos)}</div>' if creditos else ""))
        return pagina(d, d.get("kicker", "Head to head"), cuerpo, d.get("question", "Who takes it?"))
    cuerpo = (f'<div class="frase">{d.get("title", "")}</div>' + vs(h, a, marcador)
              + f'<div style="display:flex;flex-direction:column;gap:8px">{filas}</div>'
              + (f'<div class="mini">{e(nota)}</div>' if nota else ""))
    return pagina(d, d.get("kicker", "Head to head"), cuerpo, d.get("question", "Who takes it?"))


def ranking(d):
    """Top 5 de una métrica: posición, nombre (con el color de su equipo) y cifra con barra.
    rows: [{"name", "team", "value", "sub"}]; el 1º va resaltado en amarillo."""
    rows = d["rows"][:d.get("top", 5)]
    mx = max(abs(r["value"]) for r in rows) or 1
    dec = d.get("dec", 0)
    filas = ""
    for i, r in enumerate(rows):
        c = AMARILLO if i == 0 else "#3A4150"  # uniforme: solo el 1º destaca (usuario 06/10: Yamal salía resaltado por su kit)
        filas += (f'<div style="display:grid;grid-template-columns:70px 1fr auto;align-items:center;gap:20px;padding:12px 0;'
                  f'border-bottom:2px solid #1E2330"><div class="disp" style="font-size:64px;color:{AMARILLO if i == 0 else GRIS}">{i + 1}</div>'
                  f'<div style="min-width:0"><div style="font-size:46px;font-weight:900;font-stretch:85%;white-space:nowrap;'
                  f'overflow:hidden;text-overflow:ellipsis">{e(r["name"])}</div>'
                  f'<div class="mini" style="font-size:30px">{e(r.get("sub", r.get("team", "")))}</div>'
                  f'<div style="height:12px;margin-top:8px;border-radius:6px;background:{c};width:{abs(r["value"]) / mx * 100:.0f}%"></div></div>'
                  f'<div class="disp" style="font-size:80px;color:{AMARILLO if i == 0 else "#F1F3F8"}">{_fmt(r["value"], dec)}{e(d.get("unit", ""))}</div></div>')
    cuerpo = (f'<div class="frase">{d["title"]}</div>'
              + (f'<div class="mini">{e(d["metric"])}</div>' if d.get("metric") else "")
              + f'<div>{filas}</div>')
    return pagina(d, d.get("kicker", "Top 5"), cuerpo, d.get("question", "Who's missing?"))


# ---------- formatos propios de 2yellow (usuario 06/10: "que sea especial nuestra, nos da estatus") ----------
# Sello común: la tarjeta amarilla (2yellow = dos amarillas) lleva la nota/índice de cada jugador.

def tarjeta(valor, grande=False, color=AMARILLO):
    w, h, f = (96, 128, 52) if grande else (66, 88, 36)
    return (f'<div style="width:{w}px;height:{h}px;border-radius:10px;background:{color};color:{NOCHE};display:grid;'
            f'place-items:center;transform:rotate(-6deg);box-shadow:6px 6px 0 #00000055;font-weight:900;font-stretch:75%;'
            f'font-size:{f}px;flex:none">{e(valor)}</div>')


def xi(d):
    """2yellow XI: el once de la jornada por nota media (4-3-3 sobre un campo). players: [{"name","team","pos","value"}],
    pos en GK/DF/MF/FW; el mejor (estrella) en tarjeta grande con borde."""
    lineas = {"FW": [], "MF": [], "DF": [], "GK": []}
    for pl in d["players"]:
        lineas[pl["pos"]].append(pl)
    top = max(d["players"], key=lambda q: q["value"])
    def jugador(pl):
        c = color({"name": pl.get("team", "")})
        estrella = pl is top
        return (f'<div style="display:flex;flex-direction:column;align-items:center;gap:8px;width:190px">'
                f'{tarjeta(pl["value"] if isinstance(pl["value"], int) else f"{pl["value"]:.1f}", grande=estrella)}'
                f'<div style="font-size:{30 if estrella else 27}px;font-weight:900;font-stretch:85%;white-space:nowrap;'
                f'max-width:200px;overflow:hidden;text-overflow:ellipsis;text-align:center">{e(pl["name"])}</div>'
                f'<div style="display:flex;align-items:center;gap:6px;font-size:21px;color:#AEB5C4;white-space:nowrap">'
                f'<span style="width:12px;height:12px;border-radius:50%;background:{c}"></span>{e(pl.get("team", ""))}</div></div>')
    filas = "".join(f'<div style="display:flex;justify-content:space-around">{"".join(jugador(q) for q in lineas[k])}</div>'
                    for k in ("FW", "MF", "DF", "GK"))
    campo = (f'<div style="position:relative;border:3px solid #2A3040;border-radius:22px;padding:26px 6px;'
             f'display:flex;flex-direction:column;gap:22px;background:linear-gradient(#11161F,#0C1017)">'
             f'<div style="position:absolute;left:30%;right:30%;top:-3px;height:70px;border:3px solid #2A3040;border-top:0;border-radius:0 0 12px 12px"></div>'
             f'<div style="position:absolute;left:30%;right:30%;bottom:-3px;height:70px;border:3px solid #2A3040;border-bottom:0;border-radius:12px 12px 0 0"></div>'
             f'<div style="position:relative;display:flex;flex-direction:column;gap:22px">{filas}</div></div>')
    cuerpo = (f'<div class="frase" style="font-size:58px">{d["title"]}</div>'
              + (f'<div class="mini" style="font-size:30px">{e(d["metric"])}</div>' if d.get("metric") else "") + campo)
    return pagina(d, d.get("kicker", "2yellow XI"), cuerpo, d.get("question", "Who did we leave out?"))


def indice(d):
    """2yellow Index: top 5 con la tarjeta amarilla como nota (0-100) y el desglose debajo del nombre.
    rows: [{"name","team","value","detail"}]"""
    filas = ""
    for i, r in enumerate(d["rows"][:5]):
        c = color({"name": r.get("team", "")})
        filas += (f'<div style="display:flex;align-items:center;gap:26px;padding:14px 0;border-bottom:2px solid #1E2330">'
                  f'<div class="disp" style="font-size:56px;width:46px;color:{AMARILLO if i == 0 else GRIS}">{i + 1}</div>'
                  f'<div style="flex:1;min-width:0"><div style="font-size:46px;font-weight:900;font-stretch:85%;white-space:nowrap;'
                  f'overflow:hidden;text-overflow:ellipsis">{e(r["name"])}</div>'
                  f'<div style="display:flex;align-items:center;gap:8px;font-size:28px;color:#AEB5C4;white-space:nowrap">'
                  f'<span style="width:14px;height:14px;border-radius:50%;background:{c}"></span>{e(r.get("team", ""))}</div>'
                  # el desglose en su propia línea: en una sola se metía debajo de la tarjeta (07/10)
                  f'<div style="font-size:26px;color:#8B93A5;margin-top:2px">{e(r.get("detail", ""))}</div></div>'
                  f'<div style="padding-right:16px">{tarjeta(r["value"], grande=(i == 0), color=AMARILLO if i == 0 else "#F1F3F8")}</div></div>')
    cuerpo = (f'<div class="frase">{d["title"]}</div>'
              + (f'<div class="mini" style="font-size:30px">{e(d["metric"])}</div>' if d.get("metric") else "")
              + f'<div>{filas}</div>')
    return pagina(d, d.get("kicker", "2yellow Index"), cuerpo, d.get("question", "Who's too low?"))


PLANTILLAS = {"prediction": prediction, "upset_alert": upset_alert, "goals": goals, "elo_form": elo_form,
              "key_number": key_number, "deserved": deserved, "prediction_vs_result": prediction_vs_result,
              "upset_happened": upset_happened, "stat_of_match": stat_of_match, "weekend_record": weekend_record,
              "follow": follow, "our_calls": our_calls,
              "picks_list": picks_list, "head_to_head": head_to_head, "ranking": ranking, "xi": xi, "indice": indice}


def html_de(d):
    d.setdefault("home", {"name": "", "short": "", "color": "#FFD21F"})
    d.setdefault("away", {"name": "", "short": "", "color": "#FF3B3B"})
    for k in ("home", "away"):
        d[k]["c"] = color(d[k])
        d[k]["t"] = texto_sobre(d[k]["c"])
        d[k].setdefault("short", d[k]["name"])
    separar(d["home"], d["away"])
    global ACTUAL
    ACTUAL = (d["home"], d["away"])
    out = PLANTILLAS[d["template"]](d)
    for t in (d["home"], d["away"]):
        if t["short"]:
            out = re.sub(r"<b>([^<]*\b%s\b[^<]*)</b>" % re.escape(html.escape(t["short"])),
                         r'<b style="color:%s">\1</b>' % t["c"], out)
    return out


def renderizar(trabajos):
    """trabajos: lista de (datos, ruta_png)."""
    from playwright.sync_api import sync_playwright
    exe = Path("/opt/pw-browsers/chromium")
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=str(exe)) if exe.exists() else pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": ALTO})
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
