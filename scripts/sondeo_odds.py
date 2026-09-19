"""
SONDEO DEL ENDPOINT /odds -- solo lectura.

El endpoint admite más parámetros de los que estábamos usando: bookmakerId
o bookmakerName, matchId / date / leagueId, y oddsType (prematch o live).
Llamábamos solo con matchId, así que dos conclusiones anteriores quedan en
entredicho y hay que rehacerlas:

  1. "No hay cuotas en vivo". Se comprobó llamando sin oddsType y viendo
     que todo lo devuelto era type=prematch. Si el valor por defecto es
     prematch, esa prueba no demuestra nada sobre el directo.

  2. "Solo una casa cotiza tarjetas". Si la respuesta por defecto viene
     recortada (1922 entradas para un solo partido tiene pinta de tope),
     filtrando por casa podrían aparecer cotizaciones que no salían.

El script compara respuestas con y sin cada parámetro y busca señales de
truncamiento.
"""
import os
import time
import requests
from collections import Counter
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
LIGA_ID = int(os.environ.get("LIGA_ID", "119924"))

PISTAS_TARJETAS = ("card", "booking", "tarjeta")


def pedir(path, params=None, espera=0.4):
    """Devuelve (json, estado_texto, cabeceras_utiles)."""
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception as exc:
        return None, type(exc).__name__, {}
    time.sleep(espera)
    utiles = {k: v for k, v in r.headers.items()
              if "limit" in k.lower() or "total" in k.lower() or "count" in k.lower()}
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}", utiles
    try:
        return r.json(), "ok", utiles
    except Exception:
        return None, "no-JSON", utiles


def desempaquetar(datos):
    if isinstance(datos, dict):
        return datos.get("data", []) or []
    return datos or []


def aplanar(datos):
    planas = []
    for bloque in desempaquetar(datos):
        if isinstance(bloque, dict):
            planas.extend(bloque.get("odds", []) or [])
    return planas


def resumen(planas):
    tipos = Counter(c.get("type") for c in planas)
    casas = {c.get("bookmakerName") for c in planas if c.get("bookmakerName")}
    tarjetas = {(c.get("market") or "") for c in planas
                if any(x in (c.get("market") or "").lower() for x in PISTAS_TARJETAS)}
    casas_tarj = {c.get("bookmakerName") for c in planas
                  if any(x in (c.get("market") or "").lower() for x in PISTAS_TARJETAS)}
    return len(planas), dict(tipos), len(casas), sorted(tarjetas), sorted(x for x in casas_tarj if x)


def titulo(t):
    print("\n" + "=" * 76)
    print(t)
    print("=" * 76)


def elegir_partidos():
    """Un partido próximo y, si lo hay, uno en juego."""
    ahora = datetime.now(timezone.utc)
    proximo = en_juego = None
    for offset in (0, 1, 2):
        fecha = (ahora.date() + timedelta(days=offset)).isoformat()
        datos, _, _ = pedir("/matches", {"leagueId": LIGA_ID, "date": fecha})
        for p in desempaquetar(datos):
            desc = ((p.get("state") or {}).get("description") or "")
            if desc in ("Not started", "Scheduled") and proximo is None:
                proximo = p
    # cualquier partido en juego del mundo, para el test de oddsType=live
    for offset in (0, -1):
        if en_juego:
            break
        fecha = (ahora.date() + timedelta(days=offset)).isoformat()
        for pagina in range(0, 600, 100):
            datos, _, _ = pedir("/matches", {"date": fecha, "limit": 100, "offset": pagina}, espera=0.25)
            lote = desempaquetar(datos)
            if not lote:
                break
            for p in lote:
                desc = ((p.get("state") or {}).get("description") or "").lower()
                if desc and not any(desc.startswith(q) for q in
                                     ("finished", "not ", "scheduled", "cancel", "postpon",
                                      "abandon", "await", "tbd", "to be")):
                    en_juego = p
                    break
            if en_juego or len(lote) < 100:
                break
    return proximo, en_juego


def main():
    print("SONDEO DEL ENDPOINT /odds")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    proximo, en_juego = elegir_partidos()
    if proximo:
        print(f"\nPartido próximo: {proximo['homeTeam']['name']} vs {proximo['awayTeam']['name']} ({proximo['id']})")
    if en_juego:
        st = en_juego.get("state") or {}
        print(f"Partido EN JUEGO: {en_juego['homeTeam']['name']} vs {en_juego['awayTeam']['name']} "
              f"({en_juego['id']}) [{st.get('description')}, min {st.get('clock')}]")
    else:
        print("Partido EN JUEGO: ninguno encontrado")

    # ---------- 1. oddsType ----------
    titulo("1. ¿EXISTE oddsType Y CAMBIA LA RESPUESTA?")
    objetivo = en_juego or proximo
    if objetivo is None:
        print("  Sin partido que sondear.")
    else:
        etiqueta = "EN JUEGO" if en_juego else "próximo"
        print(f"  Sondeando sobre el partido {etiqueta} (id {objetivo['id']})\n")
        for descripcion, params in [
            ("sin oddsType (lo que usábamos)", {"matchId": objetivo["id"]}),
            ("oddsType=prematch", {"matchId": objetivo["id"], "oddsType": "prematch"}),
            ("oddsType=live", {"matchId": objetivo["id"], "oddsType": "live"}),
            ("oddsType=inplay", {"matchId": objetivo["id"], "oddsType": "inplay"}),
        ]:
            datos, estado, cab = pedir(params=params, path="/odds")
            if datos is None:
                print(f"    {descripcion:32s} -> {estado}")
                continue
            n, tipos, casas, lineas_t, casas_t = resumen(aplanar(datos))
            print(f"    {descripcion:32s} -> {n:5d} cuotas | tipos={tipos} | {casas} casas")
            if lineas_t:
                print(f"       {' '*29} tarjetas: {len(lineas_t)} líneas, casas {casas_t}")

    # ---------- 2. ¿viene recortada la respuesta? ----------
    titulo("2. ¿LA RESPUESTA POR DEFECTO VIENE RECORTADA?")
    if proximo:
        base, estado, cab = pedir("/odds", {"matchId": proximo["id"]})
        n_base = len(aplanar(base))
        print(f"  Sin parámetros extra: {n_base} cuotas   (cabeceras: {cab or 'ninguna'})")
        for descripcion, params in [
            ("limit=5000", {"matchId": proximo["id"], "limit": 5000}),
            ("offset=1000", {"matchId": proximo["id"], "offset": 1000}),
            ("limit=100", {"matchId": proximo["id"], "limit": 100}),
        ]:
            datos, estado, _ = pedir("/odds", params)
            n = len(aplanar(datos)) if datos is not None else 0
            marca = ""
            if n > n_base:
                marca = "  <-- DEVUELVE MÁS: la respuesta por defecto estaba recortada"
            elif n and n < n_base:
                marca = "  (menos: el parámetro sí filtra)"
            print(f"    {descripcion:32s} -> {n:5d} cuotas [{estado}]{marca}")

    # ---------- 3. filtrar por casa ----------
    titulo("3. FILTRAR POR CASA: ¿APARECEN TARJETAS QUE NO SALÍAN?")
    if proximo:
        base = aplanar(pedir("/odds", {"matchId": proximo["id"]})[0])
        casas_base = sorted({c.get("bookmakerName") for c in base if c.get("bookmakerName")})
        _, _, _, lineas_base, casas_t_base = resumen(base)
        print(f"  En la respuesta por defecto: {len(casas_base)} casas, "
              f"tarjetas en {casas_t_base or 'ninguna'}")
        print(f"  Probando casa por casa (las 12 primeras) a ver si alguna trae tarjetas:\n")
        encontradas = {}
        for casa in casas_base[:12]:
            datos, estado, _ = pedir("/odds", {"matchId": proximo["id"], "bookmakerName": casa}, espera=0.3)
            if datos is None:
                print(f"    {str(casa)[:24]:24s} -> {estado}")
                continue
            planas = aplanar(datos)
            n, tipos, _, lineas_t, _ = resumen(planas)
            if lineas_t:
                encontradas[casa] = lineas_t
            print(f"    {str(casa)[:24]:24s} -> {n:4d} cuotas"
                  f"{'   TARJETAS: ' + ', '.join(lineas_t[:4]) if lineas_t else ''}")
        print()
        nuevas = {k: v for k, v in encontradas.items() if k not in casas_t_base}
        if nuevas:
            print("  >>> APARECEN CASAS CON TARJETAS QUE NO SALÍAN POR DEFECTO:")
            for k, v in nuevas.items():
                print(f"      {k}: {', '.join(v)}")
            print("  >>> Mi censo anterior estaba mal: la respuesta por defecto no lo traía todo.")
        elif encontradas:
            print("  >>> Las mismas casas que ya salían. El censo anterior se sostiene.")
        else:
            print("  >>> Ninguna casa de las probadas cotiza tarjetas.")

    # ---------- 4. por liga ----------
    titulo("4. /odds POR LIGA Y FECHA (para no pedir partido a partido)")
    hoy = datetime.now(timezone.utc).date().isoformat()
    for descripcion, params in [
        ("leagueId + date", {"leagueId": LIGA_ID, "date": hoy}),
        ("solo leagueId", {"leagueId": LIGA_ID}),
        ("solo date", {"date": hoy}),
    ]:
        datos, estado, _ = pedir("/odds", params)
        if datos is None:
            print(f"    {descripcion:24s} -> {estado}")
            continue
        bloques = desempaquetar(datos)
        print(f"    {descripcion:24s} -> {len(bloques)} partidos, {len(aplanar(datos))} cuotas [{estado}]")


if __name__ == "__main__":
    main()
