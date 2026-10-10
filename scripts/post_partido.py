"""Post-partido automático de 2yellow, parte de DATOS (el vídeo y la publicación los hace Live).

APROBADO por el usuario el 10/10/2026 (excepción fija a la regla de la API): sondeo cada 5 min desde
inicio+1h45, solo los 2 partidos grandes del día de las 5 ligas, tope duro de 30 llamadas/día.
Workflow: .github/workflows/post_partido.yml (el cron */10 solo arranca; el sondeo cada 5 min va dentro del job).

Cada pasada (fecha de hoy y de ayer en Europe/Madrid, para los partidos que acaban pasada la medianoche):
  - partidos = los mismos que `datos_clubes.py elegir <fecha>` (se importa, no se duplica).
  - marca data/redes/post_partido/<match_id>.json -> nada.
  - ahora < saque + 1h45 -> nada, CERO llamadas (el caso normal).
  - ahora > saque + 4h -> marca "abandonado".
  - si no: 1 llamada a /matches/{id} (backfill_historico.pedir). Sin terminar -> al siguiente sondeo.
    Terminado -> /statistics/{id} (backfill_historico.estadisticas_de) y se añade la fila a
    data/historico_partidos.csv con las MISMAS columnas que el backfill (sin duplicar; el backfill de la mañana
    ya no la vuelve a pedir). Si aún no hay xG y no han pasado 3 h, se espera al siguiente sondeo.
  - fila + marca "datos_listos" (match_id, equipos, liga, fecha, saque_utc, resultado) en el MISMO commit + push.
    Live (oundialae-debug/live, scripts/post_partido_live.py dentro de enviar_cola.yml) lee las marcas "datos_listos",
    dibuja con `datos_clubes.py post`, monta el vídeo y lo publica (aquí no hay clave de Buffer ni hace falta).
  - registro en data/redes/post_partido_log.csv; consumo en data/redes/post_partido_consumo.json.

Uso:  python3 scripts/post_partido.py            (bucle: sondea cada 5 min en el mismo job hasta acabar; lo lanza el cron)
      python3 scripts/post_partido.py una        (una sola pasada)
      python3 scripts/post_partido.py hay        (sin pandas ni API: ¿algún partido en ventana? -> GITHUB_OUTPUT)
Pruebas sin red: scripts/prueba_post_partido.py (respuestas falsas de la API, sin git).
"""
import csv, json, os, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]
MAD = ZoneInfo("Europe/Madrid")
LIGAS5 = ("Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1")
DESDE, HASTA, ESPERA_XG = timedelta(minutes=105), timedelta(hours=4), timedelta(hours=3)
# RESPALDO (usuario 10/10): "20 minutos = 4 pasadas del primer recolector, que empieza a saque+1h45 y sondea cada 5 min".
# Si a saque+2h05 (105+20 min) sigue sin marca "datos_listos", el principal no ha arrancado o no avanza: lo recoge el
# workflow de respaldo (otro cron, otro grupo de concurrencia). Plantilla y Buffer (en Live) esperan a la marca.
RESPALDO_DESDE = DESDE + timedelta(minutes=20)
TOPE_DIA = 30
N_ELEGIDOS = 2
# rutas (las pruebas las cambian a una carpeta temporal con usar_rutas)
R = {}


def usar_rutas(base):
    base = Path(base)
    R.update(hist=base / "data/historico_partidos.csv", marcas=base / "data/redes/post_partido",
             log=base / "data/redes/post_partido_log.csv", consumo=base / "data/redes/post_partido_consumo.json",
             base=base)


usar_rutas(RAIZ)
OPC = {"simular": None, "git": True}


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


def hay_respaldo():
    """Como hay(), pero solo partidos con 4 pasadas del recolector principal cumplidas (saque+2h05) y sin marca:
    señal de que el bucle principal no ha arrancado. Sin API ni instalaciones."""
    t = ahora()
    si = False
    with open(RAIZ / "data/calendario.csv", newline="", encoding="utf-8") as f:
        for x in csv.DictReader(f):
            if x["liga"] not in LIGAS5 or x["fecha"] not in fechas(t) or marca_de(x["match_id"]).exists():
                continue
            k = datetime.fromisoformat(f"{x['fecha']}T{x['saque_utc']}:00+00:00")
            if k + RESPALDO_DESDE <= t <= k + HASTA + timedelta(minutes=10):
                print(f"RESPALDO: {x['local']} - {x['visitante']} sin datos a saque+{int((t - k).total_seconds() // 60)} min")
                si = True
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"hay={'si' if si else 'no'}\n")
    print("hay_respaldo =", "si" if si else "no")
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
    """Datos listos: la marca (con los nombres tal y como los guarda el histórico, que son los que pide
    `datos_clubes.py post`) va en el MISMO commit que la fila del histórico, así Live nunca ve una sin la otra."""
    marca_d = {**base, "local": fila.local, "visitante": fila.visitante, "estado": "datos_listos",
               "resultado": f"{int(fila.goles_l)}-{int(fila.goles_v)}", "hora": t.isoformat(timespec="seconds"),
               "llamadas": uso["partidos"].get(str(x.match_id), 0)}
    fin(marca, marca_d, f"post-partido: {fila.local}-{fila.visitante} datos listos", extra=[R["hist"]])
    return "datos_listos"


def fin(marca, d, msg, extra=()):
    """Marca (impide repetir) + fila de registro + push."""
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    nuevo = not R["log"].exists()
    with open(R["log"], "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "match_id", "local", "visitante", "estado", "resultado", "hora", "llamadas",
                        "buffer_tiktok", "buffer_instagram", "musica", "video"])
        w.writerow([d["fecha"], d["match_id"], d["local"], d["visitante"], d["estado"], d.get("resultado", ""),
                    d["hora"], d.get("llamadas", 0), "", "", "", ""])      # las 4 últimas: de cuando se publicaba desde aquí
    subir([marca, R["log"], *extra] + ([R["consumo"]] if R["consumo"].exists() else []), msg)


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


PENDIENTES = {"en_juego", "esperando_xg", "sin_estadisticas", "sin_respuesta", "error_push"}
SONDEO = int(os.environ.get("SONDEO_SEG", "300"))     # 5 min entre sondeos dentro del mismo job
DURACION_MAX = timedelta(minutes=int(os.environ.get("DURACION_MAX_MIN", "135")))   # el job tiene timeout 150


def bucle(dormir=time.sleep):
    """10/10: el cron de GitHub no es fiable (1 pasada en 20 min). Si un partido está en ventana y sin terminar, el
    MISMO job sigue sondeando cada 5 min (<=1 llamada por sondeo) hasta que termina, pasa saque+4h o se agota el tope
    de 30/día. El cron solo arranca el bucle; la concurrencia del workflow evita dos bucles a la vez."""
    inicio = time.monotonic()
    while True:
        out, n = main()
        pend = [m for m, e in out.items() if e in PENDIENTES]
        if not pend:
            return out
        if any(e == "tope" for e in out.values()):
            print("Tope diario alcanzado: fin del bucle")
            return out
        if timedelta(seconds=time.monotonic() - inicio) + timedelta(seconds=SONDEO) > DURACION_MAX:
            print("Duración máxima del job: lo retoma la siguiente pasada del cron")
            return out
        print(f"Pendientes {pend}: siguiente sondeo en {SONDEO} s")
        sys.stdout.flush()
        dormir(SONDEO)


if __name__ == "__main__":
    if sys.argv[1:2] == ["hay"]:
        hay()
    elif sys.argv[1:2] == ["hay_respaldo"]:
        hay_respaldo()
    elif sys.argv[1:2] == ["una"]:
        main()
    else:
        bucle()
