"""
Descarga de TennisMyLife y de la copia de archivo de Sackmann (30/09/2026,
aprobada por el usuario). Gratis, sin clave, cero Highlightly. Las dos webs
responden desde el contenedor, así que no hace falta GitHub Actions.

- TennisMyLife (stats.tennismylife.org, licencia MIT, actualización diaria):
  lista de ficheros en /api/data-files. Se bajan circuito ATP, Challenger,
  WTA, previas ATP, torneos en curso y la base de jugadores. No se bajan sus
  copias de seguridad (backup_*) ni ficheros ocultos (.*).
- Sackmann: los repos originales (JeffSackmann/tennis_atp, tennis_wta) ya no
  existen en GitHub. Copia de archivo, snapshot de junio de 2026:
  huggingface.co/datasets/Aneeshers/tennis-sackmann-archive (CC BY-NC-SA 4.0).

Salida: data/tenis/tennismylife/ y data/tenis/sackmann/, con un
resumen_<fuente>.md de filas y fechas leídas de cada fichero real.
"""
import os
import re
import time

import pandas as pd
import requests

DESDE_PRINCIPAL = 1991   # stats de saque desde 1991
DESDE_SEGUNDO = 2010     # Challenger / previas / ITF
SALIDA = "data/tenis"
HF = "https://huggingface.co/datasets/Aneeshers/tennis-sackmann-archive"


def bajar(url, ruta):
    for intento in range(3):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and r.content:
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                open(ruta, "wb").write(r.content)
                return True
            print(f"  {url}: HTTP {r.status_code}")
            if r.status_code == 404:
                return False
        except Exception as e:
            print(f"  {url}: {e}")
        time.sleep(3 * (intento + 1))
    return False


def describir(ruta, col_fecha):
    df = pd.read_csv(ruta, low_memory=False, encoding="latin-1")
    rango = " | "
    if col_fecha in df:
        f = pd.to_datetime(df[col_fecha].astype(str).str[:8], format="%Y%m%d", errors="coerce")
        rango = f"{f.min():%Y-%m-%d} | {f.max():%Y-%m-%d}"
    return f"| {os.path.basename(ruta)} | {len(df)} | {len(df.columns)} | {rango} |"


def año(nombre):
    m = re.match(r"(?:.*/)?(\d{4})", nombre)
    return int(m.group(1)) if m else None


def tennismylife():
    carpeta = f"{SALIDA}/tennismylife"
    lista = requests.get("https://stats.tennismylife.org/api/data-files", timeout=60).json()["files"]
    elegidos = []
    for f in lista:
        n = f["name"]
        if n.startswith(".") or n.startswith("backup_") or "amateur" in n or "doubles" in n:
            continue
        a = año(n)
        if a is None:
            elegidos.append(f)                       # jugadores, torneos en curso, rankings
        elif ("challenger" in n or "quali" in n) and a >= DESDE_SEGUNDO:
            elegidos.append(f)
        elif "challenger" not in n and "quali" not in n and a >= DESDE_PRINCIPAL:
            elegidos.append(f)
    resumen = ["# TennisMyLife (descarga del " + f"{pd.Timestamp.utcnow():%Y-%m-%d %H:%M} UTC)\n",
               "| fichero | filas | columnas | primera fecha | última fecha |", "|---|---|---|---|---|"]
    for f in elegidos:
        ruta = f"{carpeta}/{f['name']}"
        if not bajar(f["url"], ruta):
            resumen.append(f"| {f['name']} | FALLO | | | |")
            continue
        try:
            resumen.append(describir(ruta, "tourney_date").replace(os.path.basename(ruta), f["name"], 1))
        except Exception as e:
            resumen.append(f"| {f['name']} | ilegible: {e} | | | |")
    open(f"{SALIDA}/resumen_tennismylife.md", "w").write("\n".join(resumen) + "\n")
    print(f"TennisMyLife: {len(elegidos)} ficheros")


def sackmann():
    carpeta = f"{SALIDA}/sackmann"
    info = requests.get(f"https://huggingface.co/api/datasets/Aneeshers/tennis-sackmann-archive", timeout=60).json()
    revision = info.get("sha", "main")
    elegidos = []
    for s in info["siblings"]:
        n = s["rfilename"]
        base = os.path.basename(n)
        if n in ("LICENSE", "README.md") or base in ("UPSTREAM_README.md", "matches_data_dictionary.txt") \
                or base.endswith("_players.csv"):
            elegidos.append(n)
            continue
        m = re.match(r"(atp|wta)_matches_(qual_chall_|qual_itf_)?(\d{4})\.csv$", base)
        if not m:
            continue                                  # dobles, futures, amateur, rankings, slams
        a = int(m.group(3))
        if (m.group(2) and a >= DESDE_SEGUNDO) or (not m.group(2) and a >= DESDE_PRINCIPAL):
            elegidos.append(n)
    resumen = [f"# Sackmann, copia de archivo ({HF}, revisión {revision[:10]})\n",
               "| fichero | filas | columnas | primera fecha | última fecha |", "|---|---|---|---|---|"]
    for n in elegidos:
        ruta = f"{carpeta}/{n.replace('/', '_') if n in ('LICENSE', 'README.md') or n.endswith('.md') or n.endswith('.txt') else os.path.basename(n)}"
        if not bajar(f"{HF}/resolve/{revision}/{n}", ruta):
            resumen.append(f"| {n} | FALLO | | | |")
            continue
        if ruta.endswith(".csv"):
            resumen.append(describir(ruta, "tourney_date"))
    open(f"{SALIDA}/resumen_sackmann.md", "w").write("\n".join(resumen) + "\n")
    print(f"Sackmann: {len(elegidos)} ficheros")


if __name__ == "__main__":
    tennismylife()
    sackmann()
