"""NBA: box-score por partido (1 llamada/partido). Reanudable, del mas reciente hacia atras.

Fuente elegida: /box-score, NO /matches/{id}. Comprobado el 28/09/2026 (partido 1438539):
matchStatistics de /matches/{id} trae las estadisticas del LOCAL repetidas en el visitante.
El box-score suma exacto al marcador por cuartos. De aqui salen posesiones/ritmo,
eficiencia y quien jugo cuantos minutos.

Plan gratuito: 100/dia, cuota APARTE de la de futbol. Para al llegar a TOPE o a RESERVA.
"""
import json
import os
from pathlib import Path

import pandas as pd
import requests

H = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}
TOPE = int(os.environ.get("TOPE_LLAMADAS", "85"))
RESERVA = int(os.environ.get("RESERVA", "8"))
DIR = Path("data/nba/boxscore_crudo"); DIR.mkdir(parents=True, exist_ok=True)

p = pd.read_csv("data/nba/partidos.csv")
p = p[p.estado == "Finished"]
# fuera pretemporada: rivales que no son de la NBA (Ra'Anana...) y partidos antes de octubre
equipos_nba = set(p.local.value_counts().head(30).index)
p = p[p.local.isin(equipos_nba) & p.visitante.isin(equipos_nba)]
INICIO = {2022: "2021-10-19", 2023: "2022-10-18", 2024: "2023-10-24", 2025: "2024-10-22", 2026: "2025-10-21"}
# fuera pretemporada NBA-NBA. Temporada sin fecha apuntada: 20 de octubre (revisar al empezar)
p = p[p.fecha >= p.temporada.map(lambda t: INICIO.get(t, f"{t - 1}-10-20"))]
pendientes = [i for i in p.sort_values("fecha", ascending=False).id if not (DIR / f"{i}.json").exists()]
print(f"pendientes {len(pendientes)}")
hechos = 0
for i in pendientes[:TOPE]:
    r = requests.get(f"https://nba.highlightly.net/box-score/{i}", headers=H, timeout=30)
    quedan = r.headers.get("x-ratelimit-requests-remaining")
    if r.status_code == 429 or not r.ok:
        print(f"{i}: HTTP {r.status_code} {r.text[:200]}"); break
    (DIR / f"{i}.json").write_text(r.text)
    hechos += 1
    if quedan is not None and int(quedan) <= RESERVA:
        print(f"quedan {quedan}, paro"); break
print(f"guardados {hechos}, quedan pendientes {len(pendientes) - hechos}, cuota restante {quedan}")
