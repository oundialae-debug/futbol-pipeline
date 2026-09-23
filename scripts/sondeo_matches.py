"""
SONDEO: ¿/matches/{id} da árbitro y previsión meteorológica en partidos
VIEJOS, o solo en los recientes? ¿Y /lineups/{id} da alineación de partidos
ya jugados hace meses, o solo de los próximos a jugarse?

La spec (docs/openapi_highlightly.json) dice que el clima es un FORECAST
("Certain popular leagues... weather forecast") -- una previsión hecha
antes del partido. Que exista el campo para partidos futuros no prueba que
se conserve para partidos de hace un año: pipeline_diario.py ya usa
`referee` con éxito (88% de cobertura, 395/449 en su propio histórico),
pero nunca comprobó el clima, y ese histórico es todo de la temporada en
curso -- no dice nada de partidos viejos. Lo mismo con /lineups: se usa hoy
solo para partidos a punto de jugarse (predecir_puntual.py), nunca se ha
comprobado si guarda la alineación de un partido de hace meses.

Antes de backfillear ~2500 partidos con esto, se comprueba contra 5
partidos reales repartidos por fecha (el más viejo del histórico, tres
intermedios, el más reciente). Regla de CLAUDE.md: "un 404 en la ruta que
te inventaste no prueba que el dato no exista" -- pero tampoco lo prueba un
campo vacío en un solo partido; por eso se comprueban varios.
"""
import os
import requests

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

# match_id, fecha, descripción -- elegidos de data/historico_partidos.csv
# repartidos de más viejo a más reciente
CASOS = [
    (1183592008, "2025-08-15", "el más viejo del histórico"),
    (1181519823, "2025-11-08", "25%"),
    (1184611506, "2026-01-31", "50%"),
    (1183862626, "2026-04-21", "75%"),
    (1336412035, "2026-09-20", "el más reciente"),
]


def pedir(path):
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, timeout=25)
    return r.status_code, (r.json() if r.status_code == 200 else None)


def main():
    for mid, fecha, etiqueta in CASOS:
        codigo, j = pedir(f"/matches/{mid}")
        if codigo != 200 or not j:
            print(f"[{mid}] {fecha} ({etiqueta}): HTTP {codigo}, sin datos")
            continue
        datos = j[0] if isinstance(j, list) else j
        arbitro = datos.get("referee")
        clima = datos.get("forecast") or datos.get("weather")
        print(f"[{mid}] {fecha} ({etiqueta})")
        print(f"    arbitro : {arbitro}")
        print(f"    clima   : {clima}")
        # por si el campo se llama distinto a lo que dice la spec
        claves_sospechosas = [k for k in datos.keys()
                              if "weather" in k.lower() or "forecast" in k.lower()
                              or "referee" in k.lower() or "temp" in k.lower()]
        print(f"    claves relacionadas en la respuesta: {claves_sospechosas}")

        codigo_l, jl = pedir(f"/lineups/{mid}")
        if codigo_l != 200 or not jl:
            print(f"    lineups  : HTTP {codigo_l}, sin datos")
        else:
            dl = jl[0] if isinstance(jl, list) else jl
            equipos = dl if isinstance(dl, list) else dl.get("data", dl)
            n_equipos = len(equipos) if isinstance(equipos, list) else "?"
            print(f"    lineups  : HTTP 200, {n_equipos} bloques de equipo "
                  f"(claves top: {list(dl.keys()) if isinstance(dl, dict) else 'lista'})")
        print()


if __name__ == "__main__":
    main()
