"""
Descarga de tennis-data.co.uk (ATP desde 2000, WTA desde 2007): resultado,
ranking y cuotas de cierre (Pinnacle PSW/PSL, Bet365, Max, Avg). Gratis, sin
clave, cero Highlightly (no tiene tenis). Bloqueada desde el contenedor de
Claude (403): corre en GitHub Actions (descargar_tenis.yml).

Guarda data/tenis/tennis_data/<circuito>_<año>.csv y
data/tenis/resumen_descarga.md con filas, fechas y columnas de cuota leídas
de cada fichero real.

Sackmann y TennisMyLife: descargar_tml_sackmann.py (sí llegan desde el
contenedor).
"""
import io
import os
import time

import pandas as pd
import requests

AÑO_FIN = int(os.environ.get("AÑO_FIN", "2026"))
DESDE_TD = {"atp": 2000, "wta": 2007}        # primer año de tennis-data
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



def main():
    os.makedirs(SALIDA, exist_ok=True)
    resumen = ["# Descarga de tenis (generado por descargar_tenis.py)\n",
               f"Fecha: {pd.Timestamp.utcnow():%Y-%m-%d %H:%M} UTC\n"]
    tennis_data(resumen)
    open(f"{SALIDA}/resumen_descarga.md", "w").write("\n".join(resumen) + "\n")


if __name__ == "__main__":
    main()
