"""
AGENDA DE HOY: los descansos de hoy, a partir del calendario del mes.

Lee data/calendario.csv y saca los partidos de hoy con su ventana de
descanso, agrupadas en franjas. Sirve para dos cosas:

  1. Verlo de un vistazo: qué hay hoy y a qué horas hay que estar.
  2. Dárselo al comparador, que así va directo a esos partidos por su id en
     vez de barrer todos los partidos del mundo buscando cuáles están en el
     descanso.

SOBRE LOS CRONS
---------------
La tentación es que esto reescriba el workflow cada día con un cron por
partido. No se hace, y por un motivo concreto: el cron de GitHub Actions no
es puntual -- se retrasa entre cinco y quince minutos con frecuencia. Un
descanso dura quince. Un cron "a las 20:47" puede caer a las 21:00, con el
partido ya en la segunda parte, y encima un workflow recién empujado tarda en
registrar su calendario.

Con un cron fijo cada cuarto de hora, en cambio, el retraso da igual: alguna
pasada cae dentro. Lo que ahorra el calendario no son pasadas, son llamadas
por pasada: ir a cuatro ids conocidos en vez de paginar el mundo entero.
"""
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

RUTA_CALENDARIO = "data/calendario.csv"
RUTA_AGENDA = "data/agenda_hoy.csv"
RUTA_INFORME = "agenda_hoy.md"


def cargar(dia=None):
    if not os.path.exists(RUTA_CALENDARIO):
        return None, None
    cal = pd.read_csv(RUTA_CALENDARIO)
    dia = dia or datetime.now(timezone.utc).date().isoformat()
    return cal[cal["fecha"] == dia].sort_values("saque_utc"), dia


def franjas(hoy):
    """Agrupa los descansos que caen juntos. Una franja con cinco partidos es
    una pasada que los coge todos; cinco franjas sueltas son cinco pasadas."""
    grupos = []
    for _, f in hoy.iterrows():
        desde = datetime.strptime(f["descanso_desde"], "%H:%M")
        for g in grupos:
            if abs((desde - g["desde"]).total_seconds()) <= 25 * 60:
                g["partidos"].append(f)
                g["desde"] = min(g["desde"], desde)
                g["hasta"] = max(g["hasta"], datetime.strptime(f["descanso_hasta"], "%H:%M"))
                break
        else:
            grupos.append({"desde": desde,
                           "hasta": datetime.strptime(f["descanso_hasta"], "%H:%M"),
                           "partidos": [f]})
    return sorted(grupos, key=lambda g: g["desde"])


def main():
    hoy, dia = cargar()
    if hoy is None:
        print(f"No existe {RUTA_CALENDARIO}. Hay que generar el calendario primero.")
        return

    ahora = datetime.now(timezone.utc)
    print(f"AGENDA DEL {dia}  (ahora son las {ahora.strftime('%H:%M')} UTC)")

    if hoy.empty:
        print("Hoy no hay partidos de las seis ligas.")
        lineas = [f"# Agenda del {dia}\n",
                  "*Hoy no hay partidos de las seis ligas que cotizan tarjetas en vivo.*\n",
                  "El comparador seguirá mirando igual: puede haber descansos de otras "
                  "ligas que también sirven para acumular muestra.\n"]
        with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lineas) + "\n")
        pd.DataFrame(columns=["match_id", "liga", "saque_utc", "local", "visitante",
                              "descanso_desde", "descanso_hasta"]).to_csv(RUTA_AGENDA, index=False)
        return

    hoy.to_csv(RUTA_AGENDA, index=False)
    grupos = franjas(hoy)

    lineas = [
        f"# Agenda del {dia}\n",
        f"**{len(hoy)} partidos** en {hoy['liga'].nunique()} ligas, "
        f"repartidos en **{len(grupos)} franjas** de descanso.\n",
        "> Las horas son estimadas (saque + 45 a + 62 minutos). El comparador "
        "comprueba el estado real antes de calcular: si el partido no está "
        "parado en el intermedio, no se evalúa.\n",
    ]

    for g in grupos:
        titulo = f"{g['desde'].strftime('%H:%M')}-{g['hasta'].strftime('%H:%M')} UTC"
        pasado = ahora.strftime("%H:%M") > g["hasta"].strftime("%H:%M")
        lineas.append(f"\n## {titulo}  ({len(g['partidos'])} partidos)"
                      + ("  *[ya pasó]*" if pasado else ""))
        for f in g["partidos"]:
            lineas.append(f"- **{f['local']} vs {f['visitante']}** "
                          f"({f['liga']}, saque {f['saque_utc']})")
        print(f"  {titulo}: {len(g['partidos'])} partidos"
              + ("  [ya pasó]" if pasado else ""))

    ids = ",".join(str(int(x)) for x in hoy["match_id"].dropna())
    lineas += ["\n## Para el comparador\n",
               "Ids de hoy, para ir directo a ellos sin barrer todos los partidos "
               "del mundo:\n", "```", ids, "```\n"]

    with open(RUTA_INFORME, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print(f"\n{len(hoy)} partidos -> {RUTA_AGENDA}")


if __name__ == "__main__":
    main()
