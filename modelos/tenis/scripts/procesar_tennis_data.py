"""
Convierte los ficheros de tennis-data.co.uk que el usuario baja A MANO a CSV
en data/tenis/tennis_data/<circuito>_<año>.csv, y escribe
data/tenis/resumen_tennis_data.md con filas, fechas y columnas de cuota.

Entrada: data/tenis/tennis_data_crudo/, con los ficheros TAL CUAL salen de la
web (.zip, .xlsx o .xls, cualquier nombre, ATP y WTA mezclados). El circuito
se saca del contenido (columna "ATP" o "WTA", el número de torneo que trae
cada fichero) y el año de la columna Date. No se fía del nombre del fichero.

Por qué a mano: tennis-data limita el uso a particulares y bloquea a los
agentes de IA en robots.txt. Un workflow que la descargaba (30/09/2026) dio
47 de 47 fallos con la ejecución en verde; se retiró.

Sale con error si no convierte nada: un resumen vacío no es un éxito.
"""
import glob
import io
import os
import sys
import zipfile

import pandas as pd

CRUDO = "data/tenis/tennis_data_crudo"
SALIDA = "data/tenis/tennis_data"
CUOTAS = ("PS", "B365", "Max", "Avg", "EX", "LB", "SJ", "CB", "UB", "GB", "IW", "SB")


def hojas(ruta):
    """(nombre, bytes) de cada libro Excel, abriendo los .zip."""
    if ruta.lower().endswith(".zip"):
        with zipfile.ZipFile(ruta) as z:
            for n in z.namelist():
                if n.lower().endswith((".xlsx", ".xls")) and not n.startswith("__MACOSX"):
                    yield f"{os.path.basename(ruta)}:{n}", z.read(n)
    elif ruta.lower().endswith((".xlsx", ".xls")):
        yield os.path.basename(ruta), open(ruta, "rb").read()


def leer(nombre, datos):
    motor = "openpyxl" if datos[:2] == b"PK" else "xlrd"   # xlsx es un zip; xls no
    return pd.read_excel(io.BytesIO(datos), engine=motor)


def main():
    os.makedirs(SALIDA, exist_ok=True)
    rutas = sorted(glob.glob(f"{CRUDO}/**/*", recursive=True))
    lineas = ["# tennis-data.co.uk (ficheros bajados a mano)\n",
              "| fichero | origen | filas | primera fecha | última fecha | cuotas (columnas) |",
              "|---|---|---|---|---|---|"]
    fallos, hechos = [], {}
    for ruta in rutas:
        if os.path.isdir(ruta) or ruta.endswith(".md"):
            continue
        try:
            libros = list(hojas(ruta))
        except Exception as e:
            fallos.append(f"{os.path.basename(ruta)}: no se pudo abrir ({e})")
            continue
        if not libros:
            fallos.append(f"{os.path.basename(ruta)}: no es .zip/.xlsx/.xls")
        for nombre, datos in libros:
            try:
                df = leer(nombre, datos)
            except Exception as e:
                fallos.append(f"{nombre}: no se pudo leer ({e})")
                continue
            circuito = "wta" if "WTA" in df.columns else "atp" if "ATP" in df.columns else None
            fechas = pd.to_datetime(df.get("Date"), errors="coerce")
            if circuito is None or fechas.isna().all():
                fallos.append(f"{nombre}: sin columna ATP/WTA o sin fechas; columnas {list(df.columns)[:8]}")
                continue
            año = int(fechas.dt.year.mode()[0])
            salida = f"{circuito}_{año}.csv"
            if salida in hechos:
                fallos.append(f"{nombre}: {salida} repetido (ya salió de {hechos[salida]}); se queda el primero")
                continue
            df.to_csv(f"{SALIDA}/{salida}", index=False)
            hechos[salida] = nombre
            cuotas = [str(c) for c in df.columns if str(c).startswith(CUOTAS)]
            lineas.append(f"| {salida} | {nombre} | {len(df)} | {fechas.min():%Y-%m-%d} | "
                          f"{fechas.max():%Y-%m-%d} | {' '.join(cuotas) or 'ninguna'} |")
    lineas[3:] = sorted(lineas[3:])
    if fallos:
        lineas += ["", "## Fallos", ""] + [f"- {x}" for x in fallos]
    open("data/tenis/resumen_tennis_data.md", "w").write("\n".join(lineas) + "\n")
    print("\n".join(lineas))
    if not hechos:
        sys.exit(f"Nada convertido en {CRUDO}: {len(fallos)} fallos.")


if __name__ == "__main__":
    main()
