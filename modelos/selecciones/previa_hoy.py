"""
Previa de Inglaterra-España y Chequia-Croacia (26/09/2026): TODAS las cuotas
prematch (todos los mercados, no solo 1X2/2.5/ambos) y /matches/{id}
(árbitro, tiempo). 4 llamadas. Guarda la respuesta entera en raw/ y una tabla
plana data/selecciones/cuotas_hoy.csv. Tema aparte de ambos marcan.
"""
import os, json, requests
import pandas as pd

HEADERS = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}   # nunca se imprime
BASE = "https://soccer.highlightly.net"
RAW = "data/selecciones/raw"
eq = json.load(open("data/selecciones/equipos.json"))
filas = []
for loc, vis, mid in eq["cruces"]:
    for ruta, params, nombre in ((f"/matches/{mid}", None, f"partido_hoy_{mid}"),
                                 ("/odds", {"matchId": mid, "oddsType": "prematch"}, f"cuotas_hoy_{mid}")):
        r = requests.get(BASE + ruta, headers=HEADERS, params=params, timeout=30)
        print(f"{loc} - {vis} {ruta}: HTTP {r.status_code}")
        if r.status_code != 200:
            continue
        j = r.json()
        json.dump(j, open(f"{RAW}/{nombre}.json", "w"), ensure_ascii=False)
        if ruta != "/odds":
            continue
        for b in (j.get("data") if isinstance(j, dict) else j) or []:
            for c in (b.get("odds") or []) if isinstance(b, dict) else []:
                for v in c.get("values") or []:
                    try:
                        filas.append({"partido": f"{loc} - {vis}", "match_id": mid, "mercado": c.get("market"),
                                      "casa": c.get("bookmakerName"), "lado": str(v.get("value")),
                                      "cuota": float(v.get("odd"))})
                    except (TypeError, ValueError):
                        pass
d = pd.DataFrame(filas)
d.to_csv("data/selecciones/cuotas_hoy.csv", index=False)
print(f"{len(d)} filas de cuota, {d.mercado.nunique() if len(d) else 0} mercados")
