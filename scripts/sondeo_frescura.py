"""
¿SE MUEVEN DE VERDAD LAS CUOTAS EN VIVO?

Una segunda foto del precio tomada 33 minutos después de la primera devolvió
valores idénticos hasta el último decimal, en 14 líneas y 5 partidos, uno de
ellos ya en la segunda parte. Eso no es que no se haya reanudado el juego.

Lo que está en juego no es solo medir la ventaja por el movimiento del
precio. Si oddsType=live devuelve una foto congelada:

  - el "valor" que detectamos puede ser el mercado sin actualizar, no un
    error suyo;
  - y a ese precio no se podría apostar, porque no es el precio real.

O sea que el modelo del descanso entero se apoya en esto.

CÓMO SE COMPRUEBA
-----------------
Se coge un partido en juego y se pide /odds varias veces espaciadas dentro de
la misma pasada. Se mira si cambia ALGO, no solo las tarjetas: si el 1X2 y
los goles tampoco se mueven en diez minutos de partido, el feed está
congelado y no es cosa del mercado de tarjetas.

Se imprimen los valores crudos, que es lo único que decide.
"""
import os
import time
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
BASE_URL = "https://soccer.highlightly.net"
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime

VUELTAS = int(os.environ.get("VUELTAS", "5"))
ESPERA_ENTRE_VUELTAS = int(os.environ.get("ESPERA", "120"))
QUIETOS = ("finished", "cancel", "postpon", "abandon", "await", "not ",
           "scheduled", "tbd", "to be")


def pedir(path, params=None):
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=25)
    except Exception as e:
        print(f"  [red] {type(e).__name__}")
        return None
    if r.status_code != 200:
        print(f"  [HTTP {r.status_code}]")
        return None
    try:
        return r.json()
    except Exception:
        return None


def desempaquetar(d):
    return (d.get("data", []) or []) if isinstance(d, dict) else (d or [])


def estado_de(p):
    return ((p.get("state") or {}).get("description") or "").strip()


def minuto_de(p):
    try:
        return int((p.get("state") or {}).get("clock") or 0)
    except (TypeError, ValueError):
        return 0


def en_juego(p):
    d = estado_de(p).lower()
    return bool(d) and not any(d.startswith(q) for q in QUIETOS)


def foto(match_id):
    """Un diccionario {casa|mercado|seleccion: cuota} de TODO lo que cotizan."""
    datos = pedir("/odds", {"matchId": match_id, "oddsType": "live"})
    plano = {}
    for bloque in desempaquetar(datos):
        for c in (bloque.get("odds", []) or []):
            casa = c.get("bookmakerName")
            mercado = c.get("market")
            for v in (c.get("values") or []):
                clave = f"{casa} | {mercado} | {v.get('value')}"
                plano[clave] = v.get("odd")
    return plano


def main():
    print("¿SE MUEVEN LAS CUOTAS EN VIVO?")
    print("Momento:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print(f"Plan: {VUELTAS} vueltas cada {ESPERA_ENTRE_VUELTAS}s "
          f"({VUELTAS*ESPERA_ENTRE_VUELTAS/60:.0f} minutos en total)\n")

    vivos = []
    for salto in (0, -1):
        fecha = (datetime.now(timezone.utc).date() + timedelta(days=salto)).isoformat()
        for offset in (0, 100, 200, 300, 400, 500):
            lote = desempaquetar(pedir("/matches", {"date": fecha, "limit": 100, "offset": offset}))
            if not lote:
                break
            vivos.extend(p for p in lote if en_juego(p))
            if len(lote) < 100:
                break
        if vivos:
            break

    # El partido tiene que estar EN JUEGO de verdad. La primera versión tenía
    # un "or vivos" de reserva y con él eligió un partido ya TERMINADO
    # (Sarasota Paradise, estado Finished, minuto 90): los 261 cambios que
    # midió podían ser el mercado liquidándose, no cotizando. Es el mismo
    # error de los partidos muertos clavados en el minuto 90.
    #
    # Sin reserva. Si no hay partido válido se dice y no se concluye nada: un
    # sondeo sobre el partido equivocado es peor que no tener sondeo.
    corriendo = [p for p in vivos
                 if 5 <= minuto_de(p) <= 85
                 and any(x in estado_de(p).lower()
                         for x in ("first half", "second half"))]
    if not corriendo:
        print("No hay ningún partido con el reloj corriendo ahora mismo.")
        print("Estados vistos:", sorted({estado_de(p) for p in vivos})[:12])
        print("Hay que repetirlo cuando haya fútbol en juego. De aquí no se")
        print("concluye nada: un partido terminado no cotiza, liquida.")
        return
    candidatos = corriendo

    elegidos = []
    for p in candidatos[:12]:
        if len(foto(p["id"])) >= 5:
            elegidos.append(p)
        if len(elegidos) == 2:
            break
    if not elegidos:
        print("Ningún partido en juego tiene cuotas en vivo ahora mismo.")
        return

    historial = {p["id"]: [] for p in elegidos}
    for vuelta in range(VUELTAS):
        marca = datetime.now(timezone.utc).strftime("%H:%M:%S")
        for p in elegidos:
            historial[p["id"]].append((marca, foto(p["id"]), minuto_de(p), estado_de(p)))
        estados = ", ".join(f"{p['homeTeam']['name'][:14]} min {minuto_de(p)} "
                            f"[{estado_de(p)}]" for p in elegidos)
        print(f"  vuelta {vuelta+1}/{VUELTAS} a las {marca}  ({estados})")
        if vuelta < VUELTAS - 1:
            time.sleep(ESPERA_ENTRE_VUELTAS)
            # se refresca el estado para ver si el reloj avanza
            for i, p in enumerate(elegidos):
                d = pedir(f"/matches/{p['id']}")
                if d:
                    elegidos[i] = d[0] if isinstance(d, list) else d

    print("\n" + "=" * 70)
    for p in elegidos:
        nombre = f"{p['homeTeam']['name']} vs {p['awayTeam']['name']}"
        serie = historial[p["id"]]
        relojes = [mn for _, _, mn, _ in serie]
        print(f"\n{nombre}  ({estado_de(p)}, minuto {minuto_de(p)})")
        print(f"  reloj en cada vuelta: {relojes}")
        if len(set(relojes)) == 1:
            print("  AVISO: el reloj NO avanzó. Con el partido parado, que el")
            print("  precio no se mueva no prueba absolutamente nada.")
        print(f"  {len(serie[0][1])} cuotas cotizadas")

        cambiadas = set()
        for clave in serie[0][1]:
            valores = [v.get(clave) for _, v, _mn, _es in serie]
            if len(set(map(str, valores))) > 1:
                cambiadas.add(clave)

        print(f"  Cuotas que se movieron: {len(cambiadas)} de {len(serie[0][1])}")
        if cambiadas:
            for clave in sorted(cambiadas)[:10]:
                valores = " -> ".join(str(v.get(clave)) for _, v, _mn, _es in serie)
                print(f"    {clave}: {valores}")
        else:
            print("    NINGUNA. Mismos valores en todas las vueltas.")
            muestra = sorted(serie[0][1])[:5]
            for clave in muestra:
                print(f"    {clave}: {serie[0][1][clave]} (fijo)")

    print("\n" + "=" * 70)
    print("LECTURA")
    total_cambios, saltos = 0, []
    for p in elegidos:
        serie = historial[p["id"]]
        for clave in serie[0][1]:
            valores = [str(v.get(clave)) for _, v, _mn, _es in serie]
            if len(set(valores)) > 1:
                total_cambios += 1
                # En cuántas vueltas cambió. Un solo salto en toda la serie
                # apunta a un caché que se refresca por intervalos; cambios en
                # casi cada vuelta, a un precio que fluye de verdad.
                saltos.append(sum(1 for i in range(1, len(valores))
                                   if valores[i] != valores[i - 1]))
    if saltos:
        media = sum(saltos) / len(saltos)
        oportunidades = len(historial[elegidos[0]["id"]]) - 1
        print(f"  Saltos por cuota movida: {media:.2f} de {oportunidades} posibles")
        if media <= 1.3:
            print("  UN SOLO SALTO por cuota: el precio no fluye, se refresca a")
            print("  intervalos. Es un caché. Hay que medir cada cuánto antes de")
            print("  fiarse de dos fotos separadas por pocos minutos.")
        else:
            print("  Varios saltos por cuota: el precio se mueve de verdad.")
    if total_cambios == 0:
        print("  Ninguna cuota se movió en toda la prueba, con el reloj corriendo.")
        print("  El feed de cuotas en vivo está CONGELADO: no es el precio real.")
        print("  Eso invalida medir la ventaja por el movimiento del precio, y")
        print("  obliga a revisar el 'valor' que venimos calculando -- podría ser")
        print("  el mercado sin actualizar y no un error suyo.")
    else:
        print(f"  {total_cambios} cuotas se movieron: el feed va en vivo de verdad.")
        print("  Que las tarjetas no se movieran en la otra prueba habrá que")
        print("  mirarlo aparte -- puede ser que ese mercado concreto se refresque")
        print("  mucho más despacio que el 1X2.")


if __name__ == "__main__":
    main()
