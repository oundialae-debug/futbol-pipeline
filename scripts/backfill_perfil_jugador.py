"""
PERFIL DE JUGADOR: fecha de nacimiento, valor de mercado CON HISTORIAL y
lesiones (/players/{id}). Petición del usuario, 28/09/2026: dos variables
nuevas para ambos marcan, la edad media de los 10 titulares de campo (la
prioritaria) y el valor medio del equipo.

SIN FUGA
--------
- Edad: fecha de nacimiento, dato fijo. Edad = día del partido - nacimiento.
- Valor de mercado: la API da el HISTORIAL (`marketValue`, cada valoración con
  su `recordedDate`), no solo el de hoy. Para cada partido se usa la última
  valoración ANTERIOR a la fecha del partido. El valor de hoy no se usa para
  partidos viejos: llevaría dentro lo que el jugador hizo después.
- Solo los titulares: los cambios no se conocen antes del pitido.

QUÉ SE GUARDA (la respuesta entera que sirve, por si hay otra variable)
------------------------------------------------------------------------
  data/jugador_perfil.csv        nacimiento, altura, pie, posición (1 fila por jugador;
                                 también los que vienen vacíos, para no repedirlos)
  data/jugador_valor_mercado.csv historial de valoraciones
  data/jugador_lesiones.csv      historial de lesiones
  data/sondeo_perfil_jugador/    3 respuestas crudas, para comprobar formatos

Jugadores de las alineaciones (historico_lineups.csv), ordenados por cuántos
partidos aparecen. 1 llamada por jugador. Reanudable, con tope.
"""
import os
import csv
import json
import time
from datetime import datetime
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}

RUTA_LINEUPS = "data/historico_lineups.csv"
RUTA_PERFIL = "data/jugador_perfil.csv"
RUTA_VALOR = "data/jugador_valor_mercado.csv"
RUTA_LESION = "data/jugador_lesiones.csv"
CARPETA_CRUDO = "data/sondeo_perfil_jugador"
TOPE_LLAMADAS = int(os.environ.get("TOPE_LLAMADAS", "5000"))
COL_PERFIL = ["jugador_id", "nacimiento_txt", "nacimiento", "altura_cm", "pie",
              "posicion", "posicion_2", "n_valores", "n_lesiones"]
COL_VALOR = ["jugador_id", "fecha_txt", "fecha", "valor", "moneda", "club", "edad"]
COL_LESION = ["jugador_id", "motivo", "temporada", "desde", "hasta",
              "partidos_perdidos", "dias"]

llamadas = [0]
fallos_seguidos = [0]
CUOTA_AGOTADA = [False]
TOPE_FALLOS_SEGUIDOS = 8


def pedir(jugador_id):
    if llamadas[0] >= TOPE_LLAMADAS or CUOTA_AGOTADA[0]:
        return None
    llamadas[0] += 1
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}/players/{jugador_id}", headers=HEADERS, timeout=25)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            print(f"  [429: límite de la API] jugador {jugador_id}")
            time.sleep(5); continue
        if r.status_code != 200:
            fallos_seguidos[0] += 1
            if fallos_seguidos[0] >= TOPE_FALLOS_SEGUIDOS:
                CUOTA_AGOTADA[0] = True
            return None
        try:
            j = r.json()
            fallos_seguidos[0] = 0
            return j
        except Exception:
            return None
    fallos_seguidos[0] += 1
    if fallos_seguidos[0] >= TOPE_FALLOS_SEGUIDOS:
        CUOTA_AGOTADA[0] = True
    return None


def fecha(txt):
    """'16/12/1986' (formato REAL de la API; la especificación decía 'Feb 2, 1989')
    -> '1986-12-16'. Vacío si no se entiende (se cuenta, no se inventa)."""
    for f in ("%d/%m/%Y", "%b %d, %Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(txt).strip(), f).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""


def altura(txt):
    try:
        return round(float(str(txt).replace("m", "").replace(",", ".").strip()) * 100)
    except Exception:
        return ""


def jugadores_unicos():
    df = pd.read_csv(RUTA_LINEUPS)
    conteo = {}
    for col in ("local_ids", "visitante_ids"):
        for s in df[col].dropna():
            for x in str(s).split("|"):
                if x.strip().isdigit():
                    conteo[int(x)] = conteo.get(int(x), 0) + 1
    return [jid for jid, _ in sorted(conteo.items(), key=lambda kv: -kv[1])]


def ya_tengo():
    if not os.path.exists(RUTA_PERFIL):
        return set()
    return set(pd.read_csv(RUTA_PERFIL, usecols=["jugador_id"]).jugador_id.astype(int))


def abrir(ruta, cols):
    nuevo = not os.path.exists(ruta)
    f = open(ruta, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=cols)
    if nuevo:
        w.writeheader()
    return f, w


def main():
    todos = jugadores_unicos()
    vistos = ya_tengo()
    pendientes = [j for j in todos if j not in vistos]
    print(f"Jugadores únicos: {len(todos)}. Ya tenía: {len(vistos)}. Pendientes: {len(pendientes)}.")
    print(f"Tope de esta pasada: {TOPE_LLAMADAS} llamadas.\n")
    os.makedirs(CARPETA_CRUDO, exist_ok=True)
    crudos = len(os.listdir(CARPETA_CRUDO))
    fp, wp = abrir(RUTA_PERFIL, COL_PERFIL)
    fv, wv = abrir(RUTA_VALOR, COL_VALOR)
    fl, wl = abrir(RUTA_LESION, COL_LESION)
    guardados = sin_datos = sin_nacimiento = 0
    try:
        for jid in pendientes:
            if llamadas[0] >= TOPE_LLAMADAS:
                break
            j = pedir(jid)
            if CUOTA_AGOTADA[0]:
                print(f"\n[!] {fallos_seguidos[0]} llamadas seguidas han fallado: "
                      "probablemente la cuota diaria está agotada. Paro aquí.")
                break
            if j is None:            # fallo de red o HTTP: no se marca, se reintenta otra vez
                sin_datos += 1
                continue
            d = j[0] if isinstance(j, list) and j else j
            if not isinstance(d, dict):
                wp.writerow({"jugador_id": jid})   # vacío: no se vuelve a pedir
                sin_datos += 1
                continue
            if crudos < 3:
                json.dump(d, open(f"{CARPETA_CRUDO}/jugador_{jid}.json", "w"), ensure_ascii=False, indent=1)
                crudos += 1
            p = d.get("profile") or {}
            pos = p.get("position") or {}
            valores = d.get("marketValue") or []
            lesiones = d.get("injuries") or []
            valores = [valores] if isinstance(valores, dict) else valores
            lesiones = [lesiones] if isinstance(lesiones, dict) else lesiones
            sec = pos.get("secondary") if isinstance(pos, dict) else None
            sec = "|".join(map(str, sec)) if isinstance(sec, list) else (sec or "")
            nac = fecha(p.get("birthDate"))
            sin_nacimiento += not nac
            wp.writerow({"jugador_id": jid, "nacimiento_txt": p.get("birthDate"), "nacimiento": nac,
                         "altura_cm": altura(p.get("height")), "pie": p.get("foot"),
                         "posicion": pos.get("main") if isinstance(pos, dict) else pos,
                         "posicion_2": sec,
                         "n_valores": len(valores), "n_lesiones": len(lesiones)})
            for v in valores:
                wv.writerow({"jugador_id": jid, "fecha_txt": v.get("recordedDate"),
                             "fecha": fecha(v.get("recordedDate")), "valor": v.get("value"),
                             "moneda": v.get("currency"), "club": v.get("club"), "edad": v.get("age")})
            for l in lesiones:
                wl.writerow({"jugador_id": jid, "motivo": l.get("reason"), "temporada": l.get("season"),
                             "desde": l.get("fromDate"), "hasta": l.get("toDate"),
                             "partidos_perdidos": l.get("missedGames"), "dias": l.get("absentDurationInDays")})
            guardados += 1
            if guardados % 200 == 0:
                for f in (fp, fv, fl):
                    f.flush()
                print(f"  {guardados} jugadores guardados  (llamadas {llamadas[0]})", flush=True)
    finally:
        for f in (fp, fv, fl):
            f.close()
    print(f"\n{guardados} jugadores nuevos, {sin_datos} sin respuesta útil, "
          f"{sin_nacimiento} sin fecha de nacimiento entendible.")
    print(f"Llamadas: {llamadas[0]} de {TOPE_LLAMADAS}.")
    if llamadas[0] >= TOPE_LLAMADAS:
        print("[!] Tope alcanzado: vuelve a lanzarlo, continúa donde lo dejó.")


if __name__ == "__main__":
    main()
