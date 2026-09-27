"""
Onces confirmados sacados de la prensa -> data/selecciones/alineaciones_hoy.csv
(27/09/2026). Tema aparte del proyecto de ambos marcan.

La API no tuvo los onces ni el 26 ni el 27/09 (ni a 20 minutos del pitido).
Hasta ahora se cruzaban a mano con un script temporal, y salieron fallos:
  - "Schlager" cogió a A. Schlager (PORTERO) en vez de X. Schlager.
  - O'Brien / O'Shea no casaban: la API guarda el apóstrofo como "&apos;".
  - Dos Peretz en Israel: "Peretz" (portero) y "Eliel Peretz" se cruzaron al revés.

Uso (un equipo por argumento, nombres separados por comas, en el orden del once;
el PRIMERO debe ser el portero):
  python3 modelos/selecciones/onces_prensa.py "Germany: Nübel, Brown, Tah, ..." "Greece: ..."
Un nombre puede forzar el id con "Nombre=12345". Un jugador sin id en la API va con
id negativo y la media de su posición (hay que dar la posición: "Conte@Midfielder").

Reglas: SOLO onces confirmados (nada de "predicted"/"projected"); si dos fuentes no
coinciden, no se usa ninguno. Ver modelos/selecciones/CLAUDE.md.
"""
import html
import json
import re
import sys
import unicodedata
import pandas as pd

CARPETA = "data/selecciones"
POS_OK = {"Goalkeeper", "Defender", "Midfielder", "Forward"}


def norm(s):
    s = html.unescape(str(s))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", " ", s).split()


def main(args):
    eq = json.load(open(f"{CARPETA}/equipos.json"))
    ids, partido = eq["equipos"], {}
    for loc, vis, mid, *_ in eq["cruces"]:
        partido[loc] = partido[vis] = mid
    j = pd.read_csv(f"{CARPETA}/jugadores_partido.csv")
    p = pd.read_csv(f"{CARPETA}/partidos.csv").set_index("match_id")
    j["fecha"] = j.match_id.map(p.fecha)
    filas, problemas = [], []
    for arg in args:
        equipo, lista = arg.split(":", 1)
        equipo = equipo.strip()
        if equipo not in ids:
            sys.exit(f"'{equipo}' no está en equipos.json (nombres exactos de la API): {sorted(ids)}")
        tid = ids[equipo]
        pl = (j[j.equipo_id == tid].groupby(["jugador_id", "jugador"])
              .agg(pos=("posicion", lambda x: x.mode().iloc[0] if x.notna().any() else None),
                   ult=("fecha", "max"), mins=("minutos", "sum")).reset_index())
        pl["tok"] = pl.jugador.map(norm)
        usados = set()
        nombres = [n.strip() for n in lista.split(",") if n.strip()]
        if len(nombres) != 11:
            problemas.append(f"{equipo}: {len(nombres)} nombres, no 11")
        for k, nom in enumerate(nombres):
            pos_forzada = None
            if "@" in nom:
                nom, pos_forzada = nom.split("@")
            if "=" in nom:
                nom, jid = nom.split("=")
                r = pl[pl.jugador_id == int(jid)]
                filas.append((partido[equipo], equipo, tid, None, int(jid),
                              r.jugador.iloc[0] if len(r) else nom, r.pos.iloc[0] if len(r) else pos_forzada))
                usados.add(int(jid))
                continue
            t = norm(nom)
            apellido, inicial = t[-1], (t[0][0] if len(t) > 1 else None)
            c = pl[pl.tok.map(lambda x: apellido in x) & ~pl.jugador_id.isin(usados)]
            if k == 0:
                c = c[c.pos == "Goalkeeper"] if (c.pos == "Goalkeeper").any() else c
            else:
                c = c[c.pos != "Goalkeeper"] if (c.pos != "Goalkeeper").any() else c
            if inicial and len(c) > 1:
                ci = c[c.tok.map(lambda x: x[0][0] == inicial)]
                c = ci if len(ci) else c
            c = c.sort_values(["ult", "mins"], ascending=False)
            if len(c):
                r = c.iloc[0]
                usados.add(r.jugador_id)
                filas.append((partido[equipo], equipo, tid, None, int(r.jugador_id), r.jugador, r.pos))
                aviso = f"  <- {len(c)} candidatos: {', '.join(c.jugador)}" if len(c) > 1 else ""
                print(f"{equipo:22s} {nom:25s} -> {r.jugador} ({r.pos}){aviso}")
            else:
                pos = pos_forzada if pos_forzada in POS_OK else ("Goalkeeper" if k == 0 else None)
                filas.append((partido[equipo], equipo, tid, None, -(tid * 100 + k), nom, pos))
                print(f"{equipo:22s} {nom:25s} -> SIN ID (media de {pos or '¿posición?'})")
                if not pos:
                    problemas.append(f"{equipo}: {nom} sin id y sin posición (usar Nombre@Posicion)")
    if problemas:
        sys.exit("NO SE GUARDA:\n  " + "\n  ".join(problemas))
    nuevo = pd.DataFrame(filas, columns=["match_id", "equipo", "equipo_id", "formacion", "jugador_id",
                                         "jugador", "posicion"])
    ruta = f"{CARPETA}/alineaciones_hoy.csv"
    try:
        prev = pd.read_csv(ruta)
    except Exception:
        prev = pd.DataFrame(columns=nuevo.columns)
    pd.concat([prev[~prev.equipo_id.isin(nuevo.equipo_id)], nuevo]).to_csv(ruta, index=False)
    print(f"Guardado: {nuevo.equipo.nunique()} onces en {ruta}. Ahora: nota_jugadores_selecciones.py y "
          "pronostico_selecciones.py (sin '| head': se corta y no escribe).")


if __name__ == "__main__":
    main(sys.argv[1:])
