"""Post-partido automático de 2yellow: vídeo publicado ~20 min después del pitido final.

APROBADO por el usuario el 10/10/2026 (excepción fija a la regla de la API): sondeo cada 5 min desde
inicio+1h45, solo los 2 partidos grandes del día de las 5 ligas, tope duro de 30 llamadas/día.
Workflow: .github/workflows/post_partido.yml (cron */5).

Cada pasada (fecha de hoy y de ayer en Europe/Madrid, para los partidos que acaban pasada la medianoche):
  - partidos = los mismos que `datos_clubes.py elegir <fecha>` (se importa, no se duplica).
  - marca data/redes/post_partido/<match_id>.json -> nada.
  - ahora < saque + 1h45 -> nada, CERO llamadas (el caso normal).
  - ahora > saque + 4h -> marca "abandonado".
  - si no: 1 llamada a /matches/{id} (backfill_historico.pedir). Sin terminar -> a la siguiente pasada.
    Terminado -> /statistics/{id} (backfill_historico.estadisticas_de) y se añade la fila a
    data/historico_partidos.csv con las MISMAS columnas que el backfill (sin duplicar; el backfill de la mañana
    ya no la vuelve a pedir). Si aún no hay xG y no han pasado 3 h, se espera a la siguiente pasada.
  - datos_clubes.post (LIENZO=reel) -> PNG en media/post_partido/<fecha>_<local>_<visitante>/ + vídeo MP4
    (como Live/scripts/montar_video.py: 5 tarjetas de 2.8 s, pista de Live/redes/biblioteca_musica.json, la menos
    usada) -> commit + push -> se comprueba la URL raw (200) -> Buffer, vídeo AUTOMÁTICO a TikTok e Instagram (reel),
    a ahora+3 min (scripts/buffer_envio.py, copia de Live/enviar_cola.py).
  - marca + fila en data/redes/post_partido_log.csv; consumo en data/redes/post_partido_consumo.json.

Uso:  python3 scripts/post_partido.py            (la pasada real; la lanza el cron)
      python3 scripts/post_partido.py hay        (sin pandas ni API: ¿algún partido en ventana? -> GITHUB_OUTPUT)
Pruebas sin red: scripts/prueba_post_partido.py (respuestas falsas de la API, sin git ni Buffer).
"""
import zlib, csv, json, os, re, shutil, subprocess, sys, tempfile, time, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]
MAD = ZoneInfo("Europe/Madrid")
LIGAS5 = ("Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1")
DESDE, HASTA, ESPERA_XG = timedelta(minutes=105), timedelta(hours=4), timedelta(hours=3)
TOPE_DIA = 30
N_ELEGIDOS = 2
SEGUNDOS, TARJETAS, FADE, RETRASO_AUDIO = 2.8, 5, 0.5, 1      # PLAYBOOK de Live: post-partido 5 tarjetas de 2.8 s
RAW = "https://raw.githubusercontent.com/oundialae-debug/futbol-pipeline/main/"
LIVE_RAW = "https://raw.githubusercontent.com/oundialae-debug/live/main/"
PISTAS = ["boom", "rage", "techno", "mtrap", "drill", "electro", "trapdark", "phonk", "anthem", "techhouse",
          "hh01", "hh02", "hh03", "hh04", "hh05", "hh06", "hh07", "hh08", "hh09", "hh10"]
HASH_LIGA = {"Premier League": "#PremierLeague", "La Liga": "#LaLiga", "Serie A": "#SerieA",
             "Bundesliga": "#Bundesliga", "Ligue 1": "#Ligue1"}

# rutas (las pruebas las cambian a una carpeta temporal con usar_rutas)
R = {}


def usar_rutas(base):
    base = Path(base)
    R.update(hist=base / "data/historico_partidos.csv", marcas=base / "data/redes/post_partido",
             log=base / "data/redes/post_partido_log.csv", consumo=base / "data/redes/post_partido_consumo.json",
             media=base / "media/post_partido", base=base)


usar_rutas(RAIZ)
OPC = {"simular": None, "git": True, "buffer": True, "red": True}   # red: comprobar URL raw y bajar música


def ahora():
    a = os.environ.get("AHORA")
    return datetime.fromisoformat(a).astimezone(timezone.utc) if a else datetime.now(timezone.utc)


def fechas(t):
    d = t.astimezone(MAD).date()
    return [d.isoformat(), (d - timedelta(days=1)).isoformat()]


def marca_de(mid):
    return R["marcas"] / f"{mid}.json"


# ---------- comprobación rápida, solo stdlib ----------

def hay():
    """¿Algún partido de las 5 ligas (hoy/ayer en Madrid) entre saque+1h45 y saque+4h05 sin marca? Superconjunto
    de lo que hará la pasada real; sirve para no instalar nada en la inmensa mayoría de pasadas."""
    t = ahora()
    si = False
    with open(RAIZ / "data/calendario.csv", newline="", encoding="utf-8") as f:
        for x in csv.DictReader(f):
            if x["liga"] not in LIGAS5 or x["fecha"] not in fechas(t) or marca_de(x["match_id"]).exists():
                continue
            k = datetime.fromisoformat(f"{x['fecha']}T{x['saque_utc']}:00+00:00")
            if k + DESDE <= t <= k + HASTA + timedelta(minutes=10):
                print(f"En ventana: {x['local']} - {x['visitante']} ({x['saque_utc']} UTC)")
                si = True
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"hay={'si' if si else 'no'}\n")
    print("hay =", "si" if si else "no")
    return si


# ---------- git, URL, consumo ----------

def git(*a):
    return subprocess.run(["git", "-C", str(RAIZ), *a], capture_output=True, text=True)


def subir(rutas, msg):
    if not OPC["git"]:
        print(f"[sin git] {msg}")
        return True
    git("add", *[str(p) for p in rutas])
    if git("diff", "--cached", "--quiet").returncode == 0:
        return True
    c = git("commit", "-m", msg)
    if c.returncode:
        print(c.stdout, c.stderr)
    for i in range(6):
        p = git("pull", "--rebase", "--autostash", "origin", "main")
        if p.returncode == 0 and git("push", "origin", "HEAD:main").returncode == 0:
            print("Subido:", msg)
            return True
        print("Reintento push", i + 1, p.stderr[-200:])
        time.sleep(5 + 5 * i)
    return False


def url_ok(u, espera=150):
    if not OPC["red"]:
        return True
    fin = time.time() + espera
    while time.time() < fin:
        try:
            with urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=20) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(10)
    return False


def leer_consumo():
    try:
        return json.loads(R["consumo"].read_text())
    except Exception:
        return {"dias": {}, "partidos": {}}


# ---------- datos ----------

def preparar_modulos():
    os.environ.setdefault("LIENZO", "reel")
    sys.path.insert(0, str(RAIZ / "scripts"))
    sys.path.insert(0, str(RAIZ / "redes/plantillas"))
    if OPC["simular"]:
        os.environ.setdefault("HIGHLIGHTLY_API_KEY", "falsa")
    import pandas as pd
    import backfill_historico as bh
    import datos_clubes as DC

    def leer(ruta):
        """Local, no origin/main: la fila recién añadida tiene que verse ya (el checkout es el main recién bajado)."""
        return pd.read_csv(R["hist"] if ruta == "data/historico_partidos.csv" else RAIZ / ruta)
    DC.leer = leer
    if OPC["simular"]:
        bh.requests = Falso(OPC["simular"])
    return pd, bh, DC


class Falso:
    """Sustituye a requests en backfill_historico: lee <dir>/matches_<id>.json, statistics_<id>.json (404 si no hay)."""
    def __init__(self, d):
        self.d = Path(d)

    def get(self, url, headers=None, params=None, timeout=None):
        f = self.d / (url.split("highlightly.net", 1)[1].strip("/").replace("/", "_") + ".json")

        class Resp:
            pass
        r = Resp()
        r.status_code = 200 if f.exists() else 404
        datos = json.loads(f.read_text()) if f.exists() else None
        r.json = lambda: datos
        return r


def en_historico(pd, mid):
    h = pd.read_csv(R["hist"], usecols=["match_id", "goles_l", "goles_v", "local", "visitante"])
    h = h[(h.match_id == mid) & h.goles_l.notna()]
    return None if h.empty else h.iloc[0]


def anadir_fila(bh, m, est, liga_id):
    """Misma fila que backfill_historico.main (liga por ID, del calendario; temporada por la fecha)."""
    loc, vis = m.get("homeTeam") or {}, m.get("awayTeam") or {}
    gl, gv = bh.goles(m)
    t = datetime.fromisoformat(str(m["date"]).replace("Z", "+00:00"))
    fila = {"match_id": str(m["id"]), "fecha": m.get("date"), "liga_id": liga_id, "liga": bh.LIGAS.get(liga_id),
            "temporada": t.year if t.month >= 7 else t.year - 1, "ronda": m.get("round"),
            "local_id": loc.get("id"), "local": loc.get("name"), "visitante_id": vis.get("id"),
            "visitante": vis.get("name"), "goles_l": gl, "goles_v": gv}
    for lado, tid in (("l", loc.get("id")), ("v", vis.get("id"))):
        d = est.get(tid, {})
        for s in bh.ESTADISTICAS:
            fila[f"{lado}_{s.replace(' ', '_').lower()}"] = d.get(s)
    with open(R["hist"], "rb+") as f:                 # que la fila nueva no se pegue a la última
        f.seek(-1, 2)
        if f.read(1) != b"\n":
            f.write(b"\n")
    with open(R["hist"], "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=bh.columnas()).writerow(fila)
    return fila


# ---------- vídeo ----------

def elegir_pista(mid):
    """La pista menos usada de la biblioteca de Live (+ las que ya usó este script); empate -> por match_id."""
    usos = {p: 0 for p in PISTAS}
    if OPC["red"]:
        try:
            b = json.load(urllib.request.urlopen(LIVE_RAW + "redes/biblioteca_musica.json", timeout=30))
            usos = {p["id"]: len(p.get("usos") or []) for p in b.get("pistas", []) if p.get("id")}
        except Exception as e:
            print("Biblioteca de música no disponible:", type(e).__name__)
    if R["log"].exists():
        for x in csv.DictReader(open(R["log"], encoding="utf-8")):
            if x.get("musica") in usos:
                usos[x["musica"]] += 1
    usos.pop("electro", None)                # "hueco de 0.5 s en 6 s: evitar" (biblioteca de Live)
    orden = sorted(usos, key=lambda p: (usos[p], zlib.crc32(f"{p}{mid}".encode())))
    return orden[0]


def bajar_pista(pista, carpeta):
    destino = Path(carpeta) / f"{pista}.mp3"
    if OPC["red"]:
        urllib.request.urlretrieve(LIVE_RAW + f"musica/{pista}.mp3", destino)
    else:                                      # pruebas: 15 s de tono
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=15",
                        str(destino)], check=True)
    return destino


def montar_video(imgs, audio, out):
    """Igual que Live/scripts/montar_video.py (mismo filtro de ffmpeg)."""
    def run(cmd):
        return subprocess.run(cmd, capture_output=True, text=True)
    sec, fade, dur = SEGUNDOS, FADE, round(len(imgs) * SEGUNDOS, 2)
    vol = run(["ffmpeg", "-hide_banner", "-t", "5", "-i", str(audio), "-af", "volumedetect", "-f", "null", "-"]).stderr
    m = re.search(r"mean_volume: (-?[\d.]+) dB", vol)
    flojo = bool(m) and float(m.group(1)) < -20
    af = "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05," + ("loudnorm=I=-14:TP=-1.5," if flojo else "")
    dl = int(RETRASO_AUDIO * 1000)
    if dl:
        af += f"adelay={dl}|{dl},"
    af += f"atrim=0:{dur},afade=t=out:st={max(dur - fade, 0)}:d={fade}"
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for i in imgs:
        cmd += ["-loop", "1", "-t", str(sec), "-i", str(i)]
    cmd += ["-i", str(audio)]
    n = len(imgs)
    ins = "".join(f"[{k}:v]" for k in range(n))
    fc = f"{ins}concat=n={n}:v=1:a=0,scale=1080:1920,fps=30,format=yuv420p[v];[{n}:a]{af}[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    r = run(cmd)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    print("Vídeo", out, dur, "s", "(loudnorm)" if flojo else "")


def preparar_render():
    """En el runner: playwright + chromium y ffmpeg, SOLO cuando hay algo que dibujar (no en cada pasada)."""
    if os.environ.get("PREPARAR_RENDER") != "1":
        return
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"], check=True)
    if not shutil.which("ffmpeg"):
        subprocess.run("sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg", shell=True, check=True)
    os.environ["PREPARAR_RENDER"] = "hecho"


# ---------- texto ----------

def etiqueta(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    return "#" + re.sub(r"[^A-Za-z0-9]", "", n)


def texto(DC, datos, liga):
    p = next(iter(datos.values()))
    a, b = p["home"]["short"], p["away"]["short"]
    gh, ga = p["score"]
    res = f"{a} {gh}-{ga} {b}"
    if "post1_deserved" in datos:
        xh, xa = datos["post1_deserved"]["xg"]
        gana = a if xh > xa else b
        hook = f"Expected goals: {xh:.1f} vs {xa:.1f}, {gana} created more."
        pregunta = "Did the better team win?"
    elif "post4_stat_of_match" in datos:
        s = datos["post4_stat_of_match"]
        hook = f'{s["number"]} ' + re.sub(r"<[^>]+>", "", s["text"])
        pregunta = s.get("question", "Fair result?")
    else:
        hook, pregunta = "Full-time numbers inside.", "Fair result?"
    tags = ["#football", HASH_LIGA.get(liga, "#football"), etiqueta(a), etiqueta(b), "#fulltime"]
    return f"{res}\n{hook} {pregunta}\n\n{' '.join(tags)}", f"{res} | {hook}"[:90]


# ---------- un partido ----------

def procesar(pd, bh, DC, x, fecha, t, uso):
    mid = int(x.match_id)
    marca = marca_de(mid)
    if marca.exists():
        return "ya_hecho"
    k = x.t.to_pydatetime()
    if t < k + DESDE:
        return "pronto"                                         # cero llamadas
    base = {"match_id": mid, "local": x.local, "visitante": x.visitante, "liga": x.liga, "fecha": fecha,
            "saque_utc": k.isoformat()}
    if t > k + HASTA:
        if fecha != fechas(t)[0]:
            return "fuera"                                      # de ayer y ya pasado: ni marca ni commit
        fin(marca, {**base, "estado": "abandonado", "hora": t.isoformat(timespec="seconds"),
                    "llamadas": uso["partidos"].get(str(mid), 0)}, f"post-partido: {x.local}-{x.visitante} abandonado")
        return "abandonado"
    fila = en_historico(pd, mid)
    if fila is None:
        if bh.llamadas[0] >= bh.TOPE_LLAMADAS:
            print(f"Tope de {TOPE_DIA} llamadas/día alcanzado: no se pide {x.local}-{x.visitante}")
            return "tope"
        antes = bh.llamadas[0]
        try:
            m = bh.pedir(f"/matches/{mid}")
            m = m[0] if isinstance(m, list) and m else m
            if not isinstance(m, dict):
                return "sin_respuesta"
            estado = (m.get("state") or {}).get("description") if isinstance(m.get("state"), dict) else m.get("state")
            if not bh.terminado(m) or bh.goles(m)[0] is None:
                print(f"{x.local}-{x.visitante}: {estado} -> siguiente pasada")
                return "en_juego"
            est = bh.estadisticas_de(mid)
            if not est:
                return "sin_estadisticas"
            xg = all((est.get(i) or {}).get("Expected Goals") is not None
                     for i in ((m.get("homeTeam") or {}).get("id"), (m.get("awayTeam") or {}).get("id")))
            if not xg and t < k + ESPERA_XG:
                print("Terminado pero sin xG todavía -> siguiente pasada")
                return "esperando_xg"
            f_ = anadir_fila(bh, m, est, int(x.liga_id))
            print(f"Añadido a historico_partidos: {f_['local']} {f_['goles_l']}-{f_['goles_v']} {f_['visitante']}")
            fila = en_historico(pd, mid)
        finally:
            uso["partidos"][str(mid)] = uso["partidos"].get(str(mid), 0) + bh.llamadas[0] - antes
    return publicar(pd, DC, x, fecha, t, uso, fila, base, marca)


def publicar(pd, DC, x, fecha, t, uso, fila, base, marca):
    local, visitante = fila.local, fila.visitante              # nombres tal y como los guarda el histórico
    try:
        _, datos = DC.post(local, visitante, fecha)
    except SystemExit as e:
        print("datos_clubes post no pudo:", e)
        return "error_datos"
    carpeta = R["media"] / f"{fecha}_{local}_{visitante}".replace(" ", "_")
    carpeta.mkdir(parents=True, exist_ok=True)
    preparar_render()
    trabajos = [(d, carpeta / f"{n}.png") for n, d in datos.items()]
    DC.G.renderizar(trabajos)
    pngs = [p for _, p in trabajos]
    pista = elegir_pista(x.match_id)
    with tempfile.TemporaryDirectory() as tmp:
        video = carpeta / "post.mp4"
        montar_video(pngs[:TARJETAS], bajar_pista(pista, tmp), video)
    rel = lambda p: p.relative_to(R["base"]).as_posix()
    url = lambda p: RAW + urllib.parse.quote(rel(p))
    cuerpo, titulo = texto(DC, datos, x.liga)
    if not subir([carpeta, R["hist"]], f"post-partido: {local}-{visitante} imágenes y vídeo"):
        return "error_push"
    if not url_ok(url(video)):
        print("La URL raw del vídeo no responde 200 en ~2.5 min: se reintenta en la siguiente pasada")
        return "url_no_lista"
    due = max(t, datetime.now(timezone.utc)) + timedelta(minutes=3)
    ids, errores = {}, {}
    for red in ("tiktok", "instagram"):
        item = {"red": red, "text": cuerpo, "titulo": titulo, "video": url(video), "recordatorio": False}
        if not OPC["buffer"]:
            import buffer_envio as BE
            print(f"[sin Buffer] {red}:", json.dumps(BE.entrada(item, due), ensure_ascii=False)[:300])
            ids[red] = "simulado"
            continue
        import buffer_envio as BE
        try:
            ids[red], resp = BE.enviar(item, due)
        except Exception as e:
            ids[red], resp = None, f"{type(e).__name__}: {e}"[:300]
        if not ids[red]:
            errores[red] = resp
        print(red, ids[red], resp)
    marca_d = {**base, "estado": "enviado" if not errores else "error_buffer",
               "resultado": f"{int(fila.goles_l)}-{int(fila.goles_v)}",
               "hora": t.isoformat(timespec="seconds"), "dueAt": due.isoformat(timespec="seconds"),
               "buffer": ids, "errores": errores, "texto": cuerpo, "musica": pista, "video": url(video),
               "imagenes": [url(p) for p in pngs], "llamadas": uso["partidos"].get(str(x.match_id), 0)}
    fin(marca, marca_d, f"post-partido: {local}-{visitante} enviado a Buffer")
    return marca_d["estado"]


def fin(marca, d, msg):
    """Marca (impide repetir) + fila de registro + push."""
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    nuevo = not R["log"].exists()
    with open(R["log"], "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "match_id", "local", "visitante", "estado", "resultado", "hora", "llamadas",
                        "buffer_tiktok", "buffer_instagram", "musica", "video"])
        b = d.get("buffer") or {}
        w.writerow([d["fecha"], d["match_id"], d["local"], d["visitante"], d["estado"], d.get("resultado", ""),
                    d["hora"], d.get("llamadas", 0), b.get("tiktok", ""), b.get("instagram", ""),
                    d.get("musica", ""), d.get("video", "")])
    subir([marca, R["log"], R["consumo"]] if R["consumo"].exists() else [marca, R["log"]], msg)


# ---------- pasada ----------

def main():
    t = ahora()
    pd, bh, DC = preparar_modulos()
    uso = leer_consumo()
    dia = t.astimezone(MAD).date().isoformat()
    usadas = uso["dias"].get(dia, 0)
    bh.TOPE_LLAMADAS = max(0, TOPE_DIA - usadas)
    bh.llamadas[0] = 0
    out = {}
    try:
        for fecha in fechas(t):
            c = DC.del_dia(fecha)
            for x in c.head(N_ELEGIDOS).itertuples():
                out[int(x.match_id)] = procesar(pd, bh, DC, x, fecha, t, uso)
                print(f"{fecha} {x.local} - {x.visitante}: {out[int(x.match_id)]}")
    finally:
        if bh.llamadas[0]:
            uso["dias"][dia] = usadas + bh.llamadas[0]
            R["consumo"].parent.mkdir(parents=True, exist_ok=True)
            R["consumo"].write_text(json.dumps(uso, indent=1, sort_keys=True))
            subir([R["consumo"], R["hist"]], f"post-partido: consumo {dia} ({uso['dias'][dia]} llamadas)")
        print(f"Llamadas a la API en esta pasada: {bh.llamadas[0]} (hoy {uso['dias'].get(dia, usadas)} de {TOPE_DIA})")
    return out, bh.llamadas[0]


if __name__ == "__main__":
    if sys.argv[1:2] == ["hay"]:
        hay()
    else:
        main()
