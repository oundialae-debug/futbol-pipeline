"""Colores de las equipaciones (1ª, 2ª y 3ª) sacados de la ficha de Wikipedia
(en inglés) de cada selección y club: campos body/shorts/socks y pattern_b.

Petición del usuario (01/10/2026): colores originales de cada equipo, con
segunda y tercera equipación. Guarda la respuesta en kits_wiki.json.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PAGINAS = {
    # selecciones
    "England": "England national football team", "Croatia": "Croatia national football team",
    "Czech Republic": "Czech Republic national football team", "Spain": "Spain national football team",
    "France": "France national football team", "Italy": "Italy national football team",
    "Belgium": "Belgium national football team", "Turkey": "Turkey national football team",
    "Germany": "Germany national football team", "Netherlands": "Netherlands national football team",
    "Serbia": "Serbia national football team", "Greece": "Greece national football team",
    "Norway": "Norway national football team", "Denmark": "Denmark national football team",
    "Portugal": "Portugal national football team", "Wales": "Wales national football team",
    "Austria": "Austria national football team", "Republic of Ireland": "Republic of Ireland national football team",
    "Israel": "Israel national football team", "Kosovo National Team": "Kosovo national football team",
    "Azerbaijan": "Azerbaijan national football team", "Liechtenstein": "Liechtenstein national football team",
    "Malta": "Malta national football team", "Gibraltar": "Gibraltar national football team",
    "Argentina": "Argentina national football team", "Panama": "Panama national football team",
    "Ghana": "Ghana national football team", "Scotland": "Scotland national football team",
    "Switzerland": "Switzerland national football team", "Hungary": "Hungary national football team",
    "Poland": "Poland national football team", "Ukraine": "Ukraine national football team",
    "Sweden": "Sweden national football team", "Slovenia": "Slovenia national football team",
    "Slovakia": "Slovakia national football team", "Romania": "Romania national football team",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina national football team", "Iceland": "Iceland national football team",
    "Northern Ireland": "Northern Ireland national football team", "Georgia": "Georgia national football team",
    "Albania": "Albania national football team", "North Macedonia": "North Macedonia national football team",
    "Finland": "Finland national football team", "Bulgaria": "Bulgaria national football team",
    "Montenegro": "Montenegro national football team", "Armenia": "Armenia national football team",
    "Belarus": "Belarus national football team", "Kazakhstan": "Kazakhstan national football team",
    "Luxembourg": "Luxembourg national football team", "Cyprus": "Cyprus national football team",
    "Faroe Islands": "Faroe Islands national football team", "Estonia": "Estonia national football team",
    "Latvia": "Latvia national football team", "Lithuania": "Lithuania national football team",
    "Moldova": "Moldova national football team", "Andorra": "Andorra national football team",
    "San Marino": "San Marino national football team",
    # LaLiga
    "Barcelona": "FC Barcelona", "Real Madrid": "Real Madrid CF", "Atlético Madrid": "Atlético Madrid",
    "Villarreal": "Villarreal CF", "Real Betis": "Real Betis", "Sevilla FC": "Sevilla FC",
    "Real Sociedad": "Real Sociedad", "Alavés": "Deportivo Alavés", "Deportivo La Coruña": "Deportivo de A Coruña",
    "Athletic Club": "Athletic Bilbao", "Getafe": "Getafe CF", "Rayo Vallecano": "Rayo Vallecano",
    "Osasuna": "CA Osasuna", "Celta de Vigo": "RC Celta de Vigo", "Espanyol": "RCD Espanyol",
    "Racing Santander": "Racing de Santander", "Levante": "Levante UD", "Elche": "Elche CF",
    "Valencia": "Valencia CF", "Malaga": "Málaga CF", "Oviedo": "Real Oviedo", "Mallorca": "RCD Mallorca",
    "Girona": "Girona FC",
}
# 2yellow redes (06/10/2026): además, todos los clubes de las 5 grandes y de la Champions de nuestros datos.
# El título de Wikipedia se busca (equipos_extra.txt: un nombre por línea, como los da Highlightly).
EXTRA = Path(__file__).with_name("equipos_extra.txt")


def buscar_titulo(nombre):
    q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": f"{nombre} football club", "srlimit": 1, "format": "json"})
    r = json.load(urllib.request.urlopen(urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q,
                                                                 headers={"User-Agent": "2yellow-colores/1.0"}), timeout=30))
    hits = r.get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


if EXTRA.exists():
    for _n in [l.strip() for l in EXTRA.read_text().splitlines() if l.strip()]:
        if _n not in PAGINAS:
            try:
                _t = buscar_titulo(_n)
                if _t:
                    PAGINAS[_n] = _t
            except Exception as _e:  # noqa: BLE001
                print(_n, "sin título:", _e, file=sys.stderr)

CAMPOS = ("body", "shorts", "socks", "leftarm", "pattern_b")


def wikitexto(titulo):
    url = "https://en.wikipedia.org/w/index.php?" + urllib.parse.urlencode({"title": titulo, "action": "raw", "redirect": "true"})
    t = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "2yellow-colores/1.0"}), timeout=30).read().decode()
    m = re.match(r"#REDIRECT\s*\[\[([^\]#|]+)", t, re.I)
    return wikitexto(m.group(1)) if m else t


out = {}
for equipo, titulo in PAGINAS.items():
    try:
        t = wikitexto(titulo)
    except Exception as e:  # noqa: BLE001
        print(equipo, "ERROR", e, file=sys.stderr)
        continue
    kits = []
    for i in (1, 2, 3):
        k = {}
        for c in CAMPOS:
            m = re.search(rf"^\s*\|\s*{c}{i}\s*=\s*([^\n|<]*)", t, re.M)
            if m and m.group(1).strip():
                k[c] = m.group(1).strip()
        if "body" in k or "pattern_b" in k:
            kits.append(k)
    out[equipo] = {"pagina": titulo, "kits": kits}
    print(equipo, " | ".join(f'{k.get("body")}/{k.get("shorts")} {k.get("pattern_b", "")}' for k in kits))
Path(__file__).with_name("kits_wiki.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
