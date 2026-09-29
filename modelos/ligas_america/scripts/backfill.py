"""
Backfill de las ligas de América, reutilizando los backfills del repo padre
SIN tocarlos: se importa cada módulo y se le cambian las rutas y las ligas
antes de llamar a su main(). Todo se escribe en modelos/ligas_america/data/,
nunca en data/ (los modelos oficiales no ven ni un partido de aquí).

PASOS (env PASOS, separados por comas, en orden):
  partidos  -> historico_partidos.csv  (/matches + /statistics, 1 llamada/partido)
  arbitro   -> historico_arbitro_clima.csv (/matches/{id})
  lineups   -> historico_lineups.csv   (/lineups/{id}, desde abr-2024)
  h2h       -> historico_h2h_profundo.csv (/head-2-head por par)
  jugadores -> historico_jugador_stats.csv (temporada anterior de cada titular)

LIGAS: id=nombre separados por comas. Por ID, nunca por nombre (Serie A de
Brasil 61205, Liga MX 223746; la de Argentina se eligió mirando
partidos_hoy.md). El orden de LIGAS es la prioridad: si la cuota se acaba,
la primera queda completa.
"""
import os
import sys
import pandas as pd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
DATOS = "modelos/ligas_america/data"

LIGAS = {int(k): v for k, v in (x.split("=", 1) for x in os.environ["LIGAS"].split(","))}
TEMPORADAS = [int(x) for x in os.environ.get("TEMPORADAS", "2026,2025,2024,2023").split(",")]
PASOS = os.environ.get("PASOS", "partidos").split(",")
TOPE = int(os.environ.get("TOPE_LLAMADAS", "3000"))
HIST = f"{DATOS}/historico_partidos.csv"


def hist_priorizado():
    """Copia del histórico ordenada por la prioridad de LIGAS y temporada
    reciente primero (los backfills de árbitro/lineups recorren en orden)."""
    h = pd.read_csv(HIST)
    orden = {lid: i for i, lid in enumerate(LIGAS)}
    h = h[h.liga_id.isin(orden)]
    h = h.assign(_o=h.liga_id.map(orden)).sort_values(["_o", "temporada", "fecha"],
                                                        ascending=[True, False, False])
    ruta = f"{DATOS}/_hist_orden.csv"
    h.drop(columns="_o").to_csv(ruta, index=False)
    return ruta


def main():
    os.makedirs(DATOS, exist_ok=True)
    for paso in PASOS:
        print(f"\n===== {paso} =====")
        if paso == "partidos":
            import backfill_historico as B
            B.RUTA, B.LIGAS, B.TEMPORADAS, B.TOPE_LLAMADAS = HIST, LIGAS, TEMPORADAS, TOPE
            try:
                B.main()
            except SystemExit as e:
                print(f"[!] backfill_historico salió con {e.code} (ligas vacías, ver arriba)")
        elif paso == "arbitro":
            import backfill_arbitro_clima as B
            B.RUTA_HIST, B.RUTA_SALIDA, B.TOPE_LLAMADAS = hist_priorizado(), f"{DATOS}/historico_arbitro_clima.csv", TOPE
            B.main()
        elif paso == "lineups":
            import backfill_lineups as B
            B.RUTA_HIST, B.RUTA_SALIDA, B.TOPE_LLAMADAS = hist_priorizado(), f"{DATOS}/historico_lineups.csv", TOPE
            B.main()
        elif paso == "h2h":
            import backfill_h2h_profundo as B
            B.RUTA_HIST, B.RUTA_SALIDA, B.TOPE_LLAMADAS = hist_priorizado(), f"{DATOS}/historico_h2h_profundo.csv", TOPE
            B.main()
        elif paso == "jugadores":
            import backfill_jugador_stats as B
            B.RUTA_LINEUPS, B.RUTA_SALIDA, B.TOPE_LLAMADAS = (f"{DATOS}/historico_lineups.csv",
                                                               f"{DATOS}/historico_jugador_stats.csv", TOPE)
            B.main()
    if os.path.exists(f"{DATOS}/_hist_orden.csv"):
        os.remove(f"{DATOS}/_hist_orden.csv")


if __name__ == "__main__":
    main()
