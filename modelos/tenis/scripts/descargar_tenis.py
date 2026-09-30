"""
Descarga de datos de tenis (ATP y WTA). Fuentes gratuitas, sin clave, cero
llamadas a Highlightly (Highlightly no tiene tenis: comprobado en
docs/otros_deportes/spec_sport.json el 30/09/2026).

1. tennis-data.co.uk: un fichero por año y circuito con resultado, ranking y
   cuotas de cierre (Pinnacle, Bet365, máxima y media). ATP desde 2000, WTA
   desde 2007. Se guarda como CSV en data/tenis/tennis_data/<circuito>_<año>.csv.
2. Jeff Sackmann (github.com/JeffSackmann/tennis_atp y tennis_wta): todos los
   partidos con estadísticas de saque. Licencia CC BY-NC-SA 4.0 (uso no
   comercial). El workflow clona los repos; este script copia los ficheros
   elegidos a data/tenis/sackmann/.

Desde el contenedor de Claude las dos fuentes están bloqueadas (403 y sin
acceso a otros repos de GitHub), por eso corre en GitHub Actions
(descargar_tenis.yml).

No se supone nada sobre lo que traen: data/tenis/resumen_descarga.md se
escribe con filas, fechas y columnas de cuota leídas de cada fichero real.
"""
import io
import os
import shutil
import time

import pandas as pd
import requests

AÑO_FIN = int(os.environ.get("AÑO_FIN", "2026"))
DESDE_TD = {"atp": 2000, "wta": 2007}        # primer año de tennis-data
DESDE_TOUR = 1991                              # Sackmann, circuito principal (stats de saque desde 1991)
DESDE_SEGUNDO = 2010                           # Sackmann, Challenger/qualy (ATP) y qualy/ITF (WTA)
CLONES = os.environ.get("CLONES", "/tmp/sackmann")
SALIDA = "data/tenis"


def bajar(url):
    for intento in range(3):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200 and r.content:
                return r.content
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(3 * (intento + 1))
    return None


def tennis_data(resumen):
    carpeta = f"{SALIDA}/tennis_data"
    os.makedirs(carpeta, exist_ok=True)
    resumen += ["## tennis-data.co.uk\n",
                "| fichero | filas | primera fecha | última fecha | cuotas (columnas) |",
                "|---|---|---|---|---|"]
    for circuito, desde in DESDE_TD.items():
        sufijo = "w" if circuito == "wta" else ""
        for año in range(desde, AÑO_FIN + 1):
            contenido, ext = None, None
            for ext in ("xlsx", "xls"):
                contenido = bajar(f"http://www.tennis-data.co.uk/{año}{sufijo}/{año}.{ext}")
                if contenido:
                    break
            nombre = f"{circuito}_{año}.csv"
            if not contenido:
                print(f"  {nombre}: FALLO")
                resumen.append(f"| {nombre} | FALLO | | | |")
                continue
            df = pd.read_excel(io.BytesIO(contenido), engine="openpyxl" if ext == "xlsx" else "xlrd")
            df.to_csv(f"{carpeta}/{nombre}", index=False)
            fechas = pd.to_datetime(df.get("Date"), errors="coerce")
            cuotas = [c for c in df.columns
                      if str(c).startswith(("PS", "B365", "Max", "Avg", "EX", "LB", "SJ", "CB", "UB", "GB", "IW", "SB"))]
            print(f"  {nombre}: {len(df)} filas, cuotas {cuotas}")
            resumen.append(f"| {nombre} | {len(df)} | {fechas.min():%Y-%m-%d} | {fechas.max():%Y-%m-%d} | "
                           f"{' '.join(map(str, cuotas)) or 'ninguna'} |")
    resumen.append("")


def sackmann(resumen):
    carpeta = f"{SALIDA}/sackmann"
    os.makedirs(carpeta, exist_ok=True)
    resumen += ["## Jeff Sackmann (CC BY-NC-SA 4.0)\n",
                "| fichero | filas | primera fecha | última fecha |",
                "|---|---|---|---|"]
    for circuito, segundo in (("atp", "qual_chall"), ("wta", "qual_itf")):
        repo = f"{CLONES}/tennis_{circuito}"
        if not os.path.isdir(repo):
            print(f"  tennis_{circuito}: no se pudo clonar (ver sondeo_sackmann.md)")
            resumen.append(f"| tennis_{circuito} | NO SE PUDO CLONAR | | |")
            continue
        commit = os.popen(f"git -C {repo} log -1 --format='%h %cs'").read().strip()
        resumen.append(f"| tennis_{circuito} (commit {commit}) | | | |")
        elegidos = [f"{circuito}_players.csv"]
        elegidos += [f"{circuito}_matches_{a}.csv" for a in range(DESDE_TOUR, AÑO_FIN + 1)]
        elegidos += [f"{circuito}_matches_{segundo}_{a}.csv" for a in range(DESDE_SEGUNDO, AÑO_FIN + 1)]
        for nombre in elegidos:
            origen = f"{repo}/{nombre}"
            if not os.path.exists(origen):
                print(f"  {nombre}: no existe en el repo")
                resumen.append(f"| {nombre} | NO EXISTE | | |")
                continue
            shutil.copy(origen, f"{carpeta}/{nombre}")
            df = pd.read_csv(origen, low_memory=False, encoding="latin-1")
            if "tourney_date" in df:
                f = pd.to_datetime(df["tourney_date"].astype(str), format="%Y%m%d", errors="coerce")
                rango = f"{f.min():%Y-%m-%d} | {f.max():%Y-%m-%d}"
            else:
                rango = " | "
            print(f"  {nombre}: {len(df)} filas")
            resumen.append(f"| {nombre} | {len(df)} | {rango} |")
    resumen.append("")


def main():
    os.makedirs(SALIDA, exist_ok=True)
    resumen = ["# Descarga de tenis (generado por descargar_tenis.py)\n",
               f"Fecha: {pd.Timestamp.utcnow():%Y-%m-%d %H:%M} UTC\n"]
    tennis_data(resumen)
    sackmann(resumen)
    open(f"{SALIDA}/resumen_descarga.md", "w").write("\n".join(resumen) + "\n")


if __name__ == "__main__":
    main()
