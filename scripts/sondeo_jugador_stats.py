"""
SONDEO: /players/{id}/statistics -- ¿de verdad rompe por temporada, y la
temporada pasada (ya cerrada) es un dato fijo que no cambia con el tiempo?

La spec dice "Refresh interval: once a day" y que perCompetition trae un
campo `season`. Si es así, se puede usar la temporada ANTERIOR ya cerrada
de cada jugador como rasgo -- es un hecho histórico congelado, no puede
haber fuga aunque se pida hoy. Si en cambio NO rompe limpio por temporada
o la temporada pasada aparece incompleta/mezclada, esto no sirve para
entrenar sobre el histórico sin fuga, solo para predicciones en vivo.
"""
import os
import json
import requests

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

# IDs reales de jugadores tomados de historico_lineups.csv
JUGADORES = [
    (7565544, "Álvaro Valles"),
    (7660373, "Chimy Ávila"),
]


def main():
    for jid, nombre in JUGADORES:
        r = requests.get(f"{BASE_URL}/players/{jid}/statistics",
                         headers=HEADERS, timeout=25)
        print(f"[{nombre} ({jid})] HTTP {r.status_code}")
        if r.status_code != 200:
            print(r.text[:500])
            continue
        j = r.json()
        d = j[0] if isinstance(j, list) else j
        per_comp = d.get("perCompetition", [])
        print(f"  perCompetition: {len(per_comp)} entradas")
        for c in per_comp[:8]:
            print(f"    temporada={c.get('season')} liga={c.get('league')} "
                  f"club={c.get('club')} partidos={c.get('gamesPlayed')} "
                  f"goles={c.get('goals')} asist={c.get('assists')} "
                  f"minutos={c.get('minutesPlayed')}")
        print()


if __name__ == "__main__":
    main()
