"""
Convierte los ficheros de tennis-data.co.uk que el usuario baja A MANO
(data/tenis/tennis_data_crudo/<circuito>_<año>.xlsx|xls) a CSV en
data/tenis/tennis_data/, y escribe data/tenis/resumen_tennis_data.md con
filas, fechas y columnas de cuota leídas de cada fichero.

Por qué a mano: tennis-data limita el uso a particulares y bloquea a los
agentes de IA en robots.txt. Un workflow que la descargaba (30/09/2026) dio
47 de 47 fallos con la ejecución en verde; se retiró.

Sale con error si no convierte nada: un resumen vacío no es un éxito.
"""
import glob
import os
import re
import sys

import pandas as pd

CRUDO = "data/tenis/tennis_data_crudo"
SALIDA = "data/tenis/tennis_data"
CUOTAS = ("PS", "B365", "Max", "Avg", "EX", "LB", "SJ", "CB", "UB", "GB", "IW", "SB")


def main():
    os.makedirs(SALIDA, exist_ok=True)
    ficheros = sorted(f for f in glob.glob(f"{CRUDO}/*") if f.endswith((".xlsx", ".xls")))
    lineas = ["# tennis-data.co.uk (ficheros bajados a mano)\n",
              "| fichero | filas | primera fecha | última fecha | cuotas (columnas) |",
              "|---|---|---|---|---|"]
    fallos, hechos = [], 0
    for f in ficheros:
        base = os.path.basename(f)
        m = re.match(r"(atp|wta)_(\d{4})\.xlsx?$", base)
        if not m:
            fallos.append(f"{base}: nombre no reconocido (esperado atp_AAAA.xlsx o wta_AAAA.xls)")
            continue
        try:
            df = pd.read_excel(f, engine="openpyxl" if base.endswith("xlsx") else "xlrd")
        except Exception as e:
            fallos.append(f"{base}: no se pudo leer ({e})")
            continue
        nombre = f"{m.group(1)}_{m.group(2)}.csv"
        df.to_csv(f"{SALIDA}/{nombre}", index=False)
        fechas = pd.to_datetime(df.get("Date"), errors="coerce")
        cuotas = [str(c) for c in df.columns if str(c).startswith(CUOTAS)]
        lineas.append(f"| {nombre} | {len(df)} | {fechas.min():%Y-%m-%d} | {fechas.max():%Y-%m-%d} | "
                      f"{' '.join(cuotas) or 'ninguna'} |")
        hechos += 1
    if fallos:
        lineas += ["", "## Fallos", ""] + [f"- {x}" for x in fallos]
    open("data/tenis/resumen_tennis_data.md", "w").write("\n".join(lineas) + "\n")
    print("\n".join(lineas))
    if hechos == 0:
        sys.exit(f"Nada convertido: {len(ficheros)} ficheros en {CRUDO}, {len(fallos)} fallos.")


if __name__ == "__main__":
    main()
