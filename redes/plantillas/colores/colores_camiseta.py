"""Color real de cada camiseta: baja el dibujo del cuerpo (Kit_body<pattern>.png,
Wikimedia Commons), lo pinta sobre el color de fondo de la ficha y saca los
dos colores dominantes. Lee kits_wiki.json y escribe kits_camiseta.json.

Las rayas, cuadros y degradados solo están en el dibujo, no en el texto de la
ficha: sin esto, Croacia saldría blanca y el Celta sin color.
"""
import hashlib
import io
import json
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
CACHE = AQUI / "dibujos"
CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "2yellow-colores/1.0 (oundialae@gmail.com)"}


def dibujo(pat):
    """Baja el dibujo directamente de upload.wikimedia.org (ruta por md5 del
    nombre, sin pasar por la API), despacio y con reintentos."""
    nombre = f"Kit_body{pat}.png"
    f = CACHE / nombre
    if not f.exists():
        h = hashlib.md5(nombre.encode()).hexdigest()
        url = f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{urllib.parse.quote(nombre)}"
        for intento in range(5):
            try:
                b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
                Image.open(io.BytesIO(b))
                f.write_bytes(b)
                break
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    print("   sin dibujo:", nombre)
                    break
                time.sleep(10 * (intento + 1))
            except Exception:  # noqa: BLE001
                time.sleep(10 * (intento + 1))
        time.sleep(1.5)
    return Image.open(f).convert("RGBA") if f.exists() else None


def hexa(c):
    return "#%02X%02X%02X" % c


def lab(c):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(x) for x in c)
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116  # noqa: E731
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def dist(a, b):
    return sum((p - q) ** 2 for p, q in zip(lab(a), lab(b))) ** 0.5


def rgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else None


def dominantes(k):
    fondo = rgb(k.get("body", "")) if k.get("body") else None
    im = dibujo(k["pattern_b"]) if k.get("pattern_b") else None
    if im is None:
        return ([hexa(fondo)], [1.0]) if fondo else ([], [])
    base = Image.new("RGBA", im.size, (*(fondo or (0, 0, 0)), 255 if fondo else 0))
    im = Image.alpha_composite(base, im)
    px = [p[:3] for p in im.getdata() if p[3] > 200]
    if not px:
        return ([hexa(fondo)], [1.0]) if fondo else ([], [])
    # agrupar colores parecidos (CIE76 < 25), contar
    grupos = []
    for c, n in sorted(Image.new("RGB", (len(px), 1)).getcolors() or [], reverse=True):
        pass
    cuenta = {}
    for p in px:
        cuenta[p] = cuenta.get(p, 0) + 1
    for c, n in sorted(cuenta.items(), key=lambda x: -x[1]):
        for g in grupos:
            if dist(g[0], c) < 25:
                g[1] += n
                break
        else:
            grupos.append([c, n])
    grupos.sort(key=lambda g: -g[1])
    tot = sum(g[1] for g in grupos)
    return [hexa(g[0]) for g in grupos[:3]], [round(g[1] / tot, 2) for g in grupos[:3]]


wiki = json.loads((AQUI / "kits_wiki.json").read_text())
_prev = AQUI / "kits_camiseta.json"
out = json.loads(_prev.read_text()) if _prev.exists() else {}  # fusiona: no se pierde lo ya medido
for equipo, d in wiki.items():
    if out.get(equipo):
        continue
    out[equipo] = []
    for k in d["kits"]:
        cols, partes = dominantes(k)
        out[equipo].append({"colores": cols, "partes": partes, "pantalon": k.get("shorts"), "dibujo": k.get("pattern_b")})
    print(equipo, " | ".join(" ".join(f"{c}:{p}" for c, p in zip(x["colores"], x["partes"])) for x in out[equipo]))
(AQUI / "kits_camiseta.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
