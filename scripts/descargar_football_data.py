"""
Cuotas históricas de Pinnacle (y otras casas) de football-data.co.uk.

Idea del usuario (25/09/2026): las cuotas cosechadas de Highlightly solo
empiezan el 24/08/2026 (la API no guarda más de 28 días), así que toda
comparación contra el mercado se hace con ~219 partidos del arranque de
2026/27. football-data.co.uk publica gratis, por liga y temporada, las
cuotas de cierre de Pinnacle y de otras casas para partidos YA JUGADOS.

No toca la API de Highlightly (cero cuota). Desde el contenedor de Claude la
web está bloqueada por la política de red; por eso se descarga en GitHub
Actions (descargar_football_data.yml).

Guarda los CSV tal cual en data/football_data/<temporada>_<liga>.csv y
escribe data/football_data/columnas.md con qué mercados trae cada fichero
-- sin suponer nada: se mira la cabecera real.
"""
import os
import time
import requests

LIGAS = {"E0": "Premier League", "SP1": "La Liga", "I1": "Serie A",
         "D1": "Bundesliga", "F1": "Ligue 1", "SP2": "Segunda"}
TEMPORADAS = os.environ.get("TEMPORADAS", "2324,2425,2526,2627").split(",")
CARPETA = "data/football_data"


def main():
    os.makedirs(CARPETA, exist_ok=True)
    resumen = ["# Qué trae football-data.co.uk (cabeceras reales)\n",
               "| fichero | filas | columnas | Pinnacle (PS*/P>/PC*) | ambos marcan (BTTS) |",
               "|---|---|---|---|---|"]
    for t in TEMPORADAS:
        for codigo, liga in LIGAS.items():
            url = f"https://www.football-data.co.uk/mmz4281/{t.strip()}/{codigo}.csv"
            r = None
            for intento in range(3):
                try:
                    r = requests.get(url, timeout=30)
                    break
                except Exception:
                    time.sleep(3 * (intento + 1))
            if r is None or r.status_code != 200 or not r.content:
                print(f"  {t} {liga:15s} FALLO ({getattr(r, 'status_code', 'sin respuesta')})")
                resumen.append(f"| {t}_{codigo}.csv | FALLO | | | |")
                continue
            ruta = f"{CARPETA}/{t.strip()}_{codigo}.csv"
            open(ruta, "wb").write(r.content)
            texto = r.content.decode("latin-1")
            lineas = [l for l in texto.splitlines() if l.strip()]
            cab = lineas[0].split(",")
            pinnacle = [c for c in cab if c.startswith(("PS", "PC", "P>", "P<", "PAH"))]
            btts = [c for c in cab if "btts" in c.lower() or "bts" in c.lower()]
            print(f"  {t} {liga:15s} {len(lineas)-1:4d} partidos, {len(cab)} columnas, "
                  f"Pinnacle {len(pinnacle)}, BTTS {len(btts)}")
            resumen.append(f"| {t}_{codigo}.csv | {len(lineas)-1} | {len(cab)} | "
                           f"{' '.join(pinnacle) or '-'} | {' '.join(btts) or 'ninguna'} |")
    todas = set()
    for f in os.listdir(CARPETA):
        if f.endswith(".csv"):
            todas |= set(open(f"{CARPETA}/{f}", encoding="latin-1").readline().strip().split(","))
    resumen += ["\n## Todas las columnas vistas\n", " ".join(sorted(todas))]
    open(f"{CARPETA}/columnas.md", "w", encoding="utf-8").write("\n".join(resumen) + "\n")
    print(f"\nEscrito {CARPETA}/columnas.md")


if __name__ == "__main__":
    main()
