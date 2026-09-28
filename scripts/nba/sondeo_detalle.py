"""NBA: mirar la respuesta ENTERA de /matches/{id} y /box-score/{id} de un partido (2 llamadas)."""
import json
import os
from pathlib import Path

import requests

H = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}
ID = os.environ.get("PARTIDO", "1438539")  # Rockets-Mavericks, 01/02/2026
out = Path("data/nba/sondeo"); out.mkdir(parents=True, exist_ok=True)
for nombre, url in [("partido", f"https://nba.highlightly.net/matches/{ID}"),
                    ("boxscore", f"https://nba.highlightly.net/box-score/{ID}")]:
    r = requests.get(url, headers=H, timeout=30)
    print(nombre, r.status_code, "quedan", r.headers.get("x-ratelimit-requests-remaining"), len(r.content), "bytes")
    (out / f"{nombre}_{ID}.json").write_text(r.text)
