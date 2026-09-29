"""
Comprobación barata (sin API, sin pandas: solo la librería estándar) para el
workflow ambos_marcan_diario.yml. Así una pasada sin nada que hacer dura
segundos y no instala dependencias.

  python scripts/ambos_hay_partido.py previa   -> "si" si algún partido de hoy
      empieza en los próximos VENTANA_MIN minutos y aún no tiene pronóstico
      hecho en los 90 minutos antes de su pitido.
  python scripts/ambos_hay_partido.py ayer     -> "si" si ayer hubo partidos
      (solo entonces se piden los resultados).
Escribe `hay=si|no` en $GITHUB_OUTPUT si existe.
"""
import csv
import os
import sys
from datetime import datetime, timedelta, timezone

CARPETA = "data/ambos_hoy"
REGISTRO = "data/ambos_marcan/registro_papel.csv"
VENTANA_MIN = int(os.environ.get("VENTANA_MIN", "45"))
YA_HECHO_MIN = 90


def fecha(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def partidos(dia):
    ruta = f"{CARPETA}/dia_{dia.isoformat()}.csv"
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pendientes_previa(ahora):
    hechos = {}
    if os.path.exists(REGISTRO):
        with open(REGISTRO, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                hechos.setdefault(r["match_id"], []).append(fecha(r["generado"]))
    out = []
    for p in partidos(ahora.date()):
        saque = fecha(p["fecha"])
        if not (ahora < saque <= ahora + timedelta(minutes=VENTANA_MIN)):
            continue
        if any(g >= saque - timedelta(minutes=YA_HECHO_MIN) for g in hechos.get(p["match_id"], [])):
            continue
        out.append(p)
    return out


def main():
    ahora = datetime.now(timezone.utc)
    modo = sys.argv[1] if len(sys.argv) > 1 else "previa"
    if modo == "ayer":
        hay = bool(partidos(ahora.date() - timedelta(days=1)))
    else:
        p = pendientes_previa(ahora)
        hay = bool(p)
        for x in p:
            print(f"  pronto: {x['local']} - {x['visitante']} ({x['fecha']})")
    print(f"{modo}: {'si' if hay else 'no'}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"hay={'si' if hay else 'no'}\n")


if __name__ == "__main__":
    main()
