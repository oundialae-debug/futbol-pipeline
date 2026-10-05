#!/usr/bin/env python3
"""BACKUP SIN CLAUDE de la rutina diaria de 2yellow (previos, post-partido, vídeo del día).
Fases (las llama .github/workflows/redes_backup.yml, solo si la variable BACKUP_REDES = on):
  preparar manana   -> elige 2 partidos de hoy, genera plantillas, monta vídeos, deja redes/backup/pendientes.json
  preparar post     -> post-partido de los que ya acabaron (datos actualizados) y aún sin publicar
  publicar          -> sube a Buffer lo pendiente (el workflow ya hizo commit de redes/media/ para que las URL existan)
Necesita: secreto BUFFER_API_KEY; el repo Live en ./live (música, aprender.py, montar_video.py).
Solo selecciones por ahora (ligas: añadir su calendario en partidos_hoy())."""
import csv, json, os, random, subprocess, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LIVE, MAD = ROOT / "live", ZoneInfo("Europe/Madrid")
CANAL = {"instagram": "6ac3c8166a5c39ccb620dd8a", "tiktok": "6ac3c8456a5c39ccb620dec4"}
BUFFER = os.environ.get("BUFFER_URL", "https://api.buffer.com")
RAW = "https://raw.githubusercontent.com/oundialae-debug/futbol-pipeline/main/"
EST, PEND, LOG = (ROOT / "redes/backup" / n for n in ("estado.json", "pendientes.json", "publicaciones_backup.csv"))
SAL, MEDIA = ROOT / "redes/plantillas/salida", ROOT / "redes/media"
TAGS = "#Football #Soccer #NationsLeague #FootballData #Predictions"
ORDEN = {"pred": "pre1_prediction", "upset": "pre2_upset_alert", "key": "pre5_key_number", "goals": "pre3_goals"}
RESTO = ["pre2_upset_alert", "pre3_goals", "pre4_elo_form", "pre5_key_number", "pre1_prediction"]

def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True, cwd=ROOT)
    if r.returncode: print(r.stdout, r.stderr); raise SystemExit(f"fallo: {' '.join(a)[:120]}")
    return r.stdout

def cargar(p, d): return json.loads(p.read_text()) if p.exists() else d
def guardar(p, x): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(x, ensure_ascii=False, indent=1))
def elegir(tipo): return json.loads(sh("python3", "live/scripts/aprender.py", "elegir", tipo))

def partidos_hoy(hoy):
    c = pd.read_csv(ROOT / "data/selecciones/nl_calendario.csv")
    c["ko"] = pd.to_datetime(c.fecha, utc=True)
    c = c[(c.ko.dt.tz_convert(MAD).dt.date == hoy) & (~c.terminado.astype(bool))]
    f = pd.read_csv(ROOT / "data/selecciones/ranking_fifa.csv").sort_values("fecha").groupby("equipo").puntos.last()
    c = c.assign(peso=c.local.map(f).fillna(1000) + c.visitante.map(f).fillna(1000)).sort_values("peso", ascending=False)
    return c.head(2)

def a_jpg(png, dest):
    from PIL import Image
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.open(png).convert("RGB").save(dest, quality=90); return dest

def video(id_, imgs, seg, pista, delay, out):
    ped = {"id": id_, "images": [str(i) for i in imgs], "seconds": float(seg), "audio": f"live/musica/{pista}.mp3",
           "out": str(out), "fade": 0.5, "audio_delay": 1 if delay == "s1" else 0}
    p = ROOT / "redes/backup" / f"pedido_{id_}.json"; guardar(p, ped)
    sh("python3", "live/scripts/montar_video.py", str(p)); p.unlink()

def carpeta(fecha, l, v): return SAL / f"{fecha}_{l}_{v}".replace(" ", "_")

def texto(tipo, hook, l, v, d=None):
    probs = (d or {}).get("probs") or {}
    top = max(probs, key=probs.get) if isinstance(probs, dict) and probs else None
    dato = f"{probs[top]*100:.0f}% " if top and probs[top] <= 1 else ""
    base = {"pre": {"dato": f"{l} vs {v}: our model's call, in 6 cards. Swipe 👆",
                    "pregunta": f"{l} or {v}? Here's what the data says 👇",
                    "reto": f"Think you know {l} vs {v}? Check the numbers first 👇"},
            "post": {"dato": f"{l} vs {v}: what the numbers really said.",
                     "pregunta": f"Did {l} vs {v} go as the data expected? 👇",
                     "reto": f"We called {l} vs {v}. How did we do? 👇"},
            "daily": {"dato": "Yesterday's record and today's calls. 📊",
                      "pregunta": "How did our calls do yesterday? And today's? 👇",
                      "reto": "Yesterday's results vs the model. Today's calls inside. 👇"}}[tipo][hook]
    return f"{base}\nData, not betting advice. 18+\n{TAGS}"

def pendiente(tipo, partido, video_rel, txt, due, variante, musica):
    L = cargar(PEND, [])
    for red in CANAL:
        L.append({"tipo": tipo, "partido": partido, "red": red, "video": video_rel, "text": txt, "dueAt": due,
                  "variante": variante, "musica": musica})
    guardar(PEND, L)

def preparar_manana():
    ahora, hoy = datetime.now(MAD), datetime.now(MAD).date()
    est = cargar(EST, {"partidos": {}, "daily": {}})
    ps = partidos_hoy(hoy)
    if ps.empty: print("Sin partidos hoy: no se publica nada."); return
    for _, r in ps.iterrows():
        k = f"{hoy}_{r.local}_{r.visitante}"
        if k in est["partidos"]: continue
        sh("python3", "redes/plantillas/datos_selecciones.py", "pre", r.local, str(hoy))
        c = carpeta(hoy, r.local, r.visitante)
        var = elegir("pre"); ko = r.ko.tz_convert(MAD).to_pydatetime()
        t = min(ahora.replace(hour=18, minute=30, second=0, microsecond=0), ko - timedelta(hours=int(var["ante"])))
        t = max(t, ahora + timedelta(minutes=10))
        if t > ko - timedelta(minutes=20): print("Muy cerca del saque, no se publica el previo:", k); continue
        orden = [ORDEN[var["primera"]]] + [x for x in RESTO if x != ORDEN[var["primera"]]] + ["pre6_lista"]
        imgs = [a_jpg(c / f"{n}.png", MEDIA / str(hoy) / f"{r.local}_{r.visitante}_{n}.jpg") for n in orden]
        out = MEDIA / str(hoy) / f"pre_{r.local}_{r.visitante}.mp4".replace(" ", "_")
        video(k.replace(" ", "_"), imgs, var["seg"], var["musica"], var["arranque"], out)
        d = cargar(c / "pre1_prediction.json", {})
        pendiente("pre", k, str(out.relative_to(ROOT)), texto("pre", var["hook"], r.local, r.visitante, d),
                  t.isoformat(), var["variante"], var["musica"])
        est["partidos"][k] = {"ko": r.ko.isoformat(), "local": r.local, "visit": r.visitante, "fecha": str(hoy), "post": False}
    if str(hoy) not in est["daily"]:
        sh("python3", "redes/plantillas/datos_selecciones.py", "hoy", str(hoy))
        imgs = list((SAL / f"{hoy}_perfil_{hoy}").glob("perfil_picks_hoy.png"))
        ayer = sorted((MEDIA / str(hoy - timedelta(days=1))).glob("*post5*.jpg"))
        if imgs:
            var = elegir("daily"); lista = [*ayer[:1], a_jpg(imgs[0], MEDIA / str(hoy) / "daily_picks.jpg")]
            out = MEDIA / str(hoy) / "daily.mp4"
            video(f"daily_{hoy}", lista, 4.5, var["musica"], var["arranque"], out)
            t = max(ahora.replace(hour=9, minute=30, second=0, microsecond=0), ahora + timedelta(minutes=10))
            pendiente("daily", f"daily_{hoy}", str(out.relative_to(ROOT)), texto("daily", var["hook"], "", ""),
                      t.isoformat(), var["variante"], var["musica"])
            est["daily"][str(hoy)] = True
    guardar(EST, est)

def preparar_post():
    ahora = datetime.now(timezone.utc)
    est = cargar(EST, {"partidos": {}, "daily": {}})
    res = pd.read_csv(ROOT / "data/selecciones/partidos.csv")
    for k, p in est["partidos"].items():
        if p["post"] or ahora < datetime.fromisoformat(p["ko"]) + timedelta(hours=2, minutes=25): continue
        if ahora > datetime.fromisoformat(p["ko"]) + timedelta(hours=14): p["post"] = True; continue  # caducado
        m = res[(res.fecha == p["fecha"]) & (res.local == p["local"]) & (res.visitante == p["visit"])]
        if m.empty or not bool(m.iloc[0].terminado): continue  # datos aún sin actualizar: reintenta
        sh("python3", "redes/plantillas/datos_selecciones.py", "post", p["local"], p["fecha"])
        c = carpeta(p["fecha"], p["local"], p["visit"]); var = elegir("post")
        nombres = ["post1_deserved", "post2_prediction_vs_result", "post3_upset_happened", "post4_stat_of_match", "post5_weekend_record"]
        imgs = [a_jpg(c / f"{n}.png", MEDIA / p["fecha"] / f"{p['local']}_{p['visit']}_{n}.jpg") for n in nombres if (c / f"{n}.png").exists()]
        out = MEDIA / p["fecha"] / f"post_{p['local']}_{p['visit']}.mp4".replace(" ", "_")
        video("post_" + k.replace(" ", "_"), imgs, var["seg"], var["musica"], var["arranque"], out)
        pendiente("post", k, str(out.relative_to(ROOT)), texto("post", var["hook"], p["local"], p["visit"]),
                  None, var["variante"], var["musica"])
        p["post"] = True
    guardar(EST, est)

def gql(q, v):
    rq = urllib.request.Request(BUFFER, json.dumps({"query": q, "variables": v}).encode(),
                                {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["BUFFER_API_KEY"]})
    return json.load(urllib.request.urlopen(rq, timeout=60))

def publicar():
    L = cargar(PEND, [])
    if not L: print("Nada pendiente."); return
    q = "mutation($i:CreatePostInput!){createPost(input:$i){__typename ... on PostActionSuccess{post{id}} ... on MutationError{message}}}"
    hechos = []
    for x in L:
        url = RAW + x["video"]
        for _ in range(30):  # espera a que la URL pública exista
            try:
                if urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20).status == 200: break
            except Exception: time.sleep(10)
        meta = {"instagram": {"type": "reel", "shouldShareToFeed": True}} if x["red"] == "instagram" \
            else {"tiktok": {"title": x["text"].split("\n")[0][:90]}}
        i = {"channelId": CANAL[x["red"]], "schedulingType": "automatic", "text": x["text"],
             "assets": [{"video": {"url": url}}], "metadata": meta,
             "mode": "customScheduled" if x["dueAt"] else "shareNow"}
        if x["dueAt"]: i["dueAt"] = x["dueAt"]
        r = gql(q, {"i": i}); print(x["red"], x["partido"], json.dumps(r)[:200])
        d = (r.get("data") or {}).get("createPost") or {}
        if d.get("__typename") == "PostActionSuccess":
            hechos.append(x)
            nuevo = not LOG.exists()
            with open(LOG, "a", newline="") as f:
                w = csv.writer(f)
                if nuevo: w.writerow("fecha,tipo,partido,red,buffer_id,programado,musica,variante,origen".split(","))
                w.writerow([datetime.now(MAD).date(), x["tipo"], x["partido"], x["red"], d["post"]["id"], x["dueAt"] or "ya", x["musica"], x["variante"], "backup"])
    guardar(PEND, [x for x in L if x not in hechos])
    if len(hechos) < len(L): raise SystemExit("Algunos posts no se pudieron publicar (ver log).")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "preparar": (preparar_manana if a[1] == "manana" else preparar_post)()
    else: publicar()
