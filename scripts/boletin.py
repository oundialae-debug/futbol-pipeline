"""
EL BOLETÍN: qué apostar, a cuánto, y con qué parte de la banca

MI TRABAJO AQUÍ
---------------
Decir el stake. No dar una lista de partidos "interesantes" para que decidas
tú cuánto arriesgar: cada línea sale con el porcentaje de banca y el euro
concreto. Si no sé cuánto, es que no sé si apostar.

LAS CUATRO REGLAS QUE MANDAN SOBRE TODO LO DEMÁS
------------------------------------------------

1. **Solo TUS casas.** Nada de "la mejor cuota de cincuenta casas". Ese número
   es un espejismo en esta API (las cuotas de distintas casas no son
   simultáneas: 29% de partidos de 1X2 con arbitraje imposible) y además no
   tienes esas cuentas. Se compara solo contra las casas de `MIS_CASAS`, y el
   precio que se usa es el mejor DE ESAS.

2. **El consenso se mide con TODAS las casas.** Aquí sí valen las cincuenta:
   el consenso es el instrumento de medida y la API lo da gratis. La cuenta
   solo hace falta donde se apuesta. Pero con una advertencia: ese consenso no
   es simultáneo, así que no se usa para detectar "valor" -- se usa para
   situar nuestra probabilidad y para avisar cuando nos alejamos mucho de él.

3. **La puerta.** Si el modelo no ha demostrado fuera de muestra que bate al
   mercado, este fichero NO emite apuestas. Ninguna. Un experto dice "hoy no
   hay nada" la mayoría de las semanas, y eso es la parte del trabajo que
   distingue a uno de un tipo con opiniones.

4. **El margen es el suelo.** La ventaja se calcula contra el precio real que
   vas a pagar, no contra una probabilidad limpia. Si la ventaja no supera al
   error del modelo, no sale en la lista.

LO QUE ESTE FICHERO NO HACE
---------------------------
No apuesta solo. No manda nada a ninguna casa. Escribe un boletín para que lo
leas tú.
"""
import os
import json
import numpy as np
import pandas as pd

import gestion_banca as gb

# --- TUS CASAS. Cámbialo por las que tengas de verdad. ------------------
# Solo se apuesta en estas. El nombre tiene que ser el EXACTO que devuelve la
# API (`/bookmakers`): "bet365", "Betano", "Winamax"... Si te equivocas en el
# nombre no da error, simplemente esa casa no aparecerá nunca. Por eso el
# boletín avisa si alguna de tus casas no se encontró en ningún partido.
MIS_CASAS = [c.strip() for c in os.environ.get(
    "MIS_CASAS", "bet365,Betano,Bwin,Betfair,Winamax,888sport,Unibet,Betsson"
).split(",") if c.strip()]

BANCA = float(os.environ.get("BANCA", "1000"))
RUTA_SALIDA = "boletin.md"
RUTA_VALIDACION = "data/validacion_modelo.json"


def modelo_validado():
    """
    ¿Ha demostrado el modelo que bate al mercado fuera de muestra?

    Devuelve (bool, motivo). Mientras sea False, el boletín no emite apuestas.
    El fichero lo escribe `evaluar_contra_mercado.py`, no este script: nadie
    se da el visto bueno a sí mismo.
    """
    if not os.path.exists(RUTA_VALIDACION):
        return False, ("el modelo no se ha evaluado todavía contra el mercado "
                       "(falta data/validacion_modelo.json)")
    try:
        v = json.load(open(RUTA_VALIDACION))
    except Exception as e:
        return False, f"validación ilegible: {type(e).__name__}"
    if not v.get("bate_al_mercado"):
        return False, (f"el modelo NO bate al mercado fuera de muestra: "
                       f"{v.get('motivo', 'sin motivo registrado')}")
    if v.get("sigmas", 0) < 2:
        return False, (f"la ventaja sobre el mercado es de solo "
                       f"{v.get('sigmas', 0):.2f} sigmas: no es distinguible "
                       f"del azar")
    return True, (f"validado: {v.get('motivo')} ({v.get('sigmas'):.2f} sigmas, "
                  f"{v.get('partidos')} partidos)")


def mejor_precio_mio(cuotas_por_casa, lado):
    """La mejor cuota de TUS casas para ese lado, y de cuál es."""
    mejor, quien = 0.0, None
    for casa, c in cuotas_por_casa.items():
        if casa in MIS_CASAS and c.get(lado) and c[lado] > mejor:
            mejor, quien = c[lado], casa
    return mejor, quien


def consenso_de(cuotas_por_casa, lado):
    """
    Mediana de la probabilidad desmarginada de TODAS las casas.

    Las cuotas idénticas cuentan una vez: Goldenbet, Mystake, Freshbet y
    Jackbit devolvían el mismo 32.44 y no son cuatro opiniones.
    """
    vistas = {}
    for casa, c in cuotas_por_casa.items():
        vals = [v for v in c.values() if v and v > 1]
        if len(vals) < 2 or not c.get(lado):
            continue
        suma = sum(1 / v for v in vals)
        if suma <= 0:
            continue
        vistas[round((1 / c[lado]) / suma, 6)] = casa
    return float(np.median(list(vistas))) if vistas else None


def linea_boletin(partido, mercado, lado, p_modelo, error_modelo,
                  cuotas_por_casa, banca=BANCA):
    """Una fila del boletín, o None si no hay apuesta."""
    cuota, casa = mejor_precio_mio(cuotas_por_casa, lado)
    if not cuota:
        return None
    ap = gb.Apuesta(f"{partido} | {mercado} | {lado}", p_modelo, cuota,
                    error_modelo)
    fraccion, motivo = gb.decidir(ap)
    if fraccion <= 0:
        return None
    cons = consenso_de(cuotas_por_casa, lado)
    return {
        "partido": partido, "mercado": mercado, "apuesta": lado,
        "casa": casa, "cuota": round(cuota, 2),
        "prob_modelo": round(p_modelo * 100, 1),
        "prob_mercado": round(cons * 100, 1) if cons else None,
        "ventaja": round(gb.ventaja(p_modelo, cuota) * 100, 2),
        "stake_pct": round(fraccion * 100, 2),
        "stake_eur": round(banca * fraccion, 2),
        "motivo": motivo,
    }


def escribir(lineas, banca=BANCA, casas_vistas=None, nota_puerta=None):
    out = ["# Boletín\n"]
    if nota_puerta:
        out += [f"> **Sin apuestas.** {nota_puerta}\n",
                "Mientras esto siga así, este boletín no da apuestas. No es "
                "prudencia: es que recomendar stakes sobre un modelo no "
                "validado es exactamente el error del que va todo este "
                "repositorio.\n"]
        return "\n".join(out)

    out.append(f"Banca: **{banca:,.0f} €**. Casas usadas: "
               f"{', '.join(MIS_CASAS)}.\n")
    if not lineas:
        out += ["**Hoy no hay ninguna apuesta.**\n",
                "Es el resultado normal. Un mercado bien hecho no deja hueco "
                "casi nunca, y forzar una apuesta para tener algo que hacer es "
                "la forma más rápida de devolver lo ganado.\n"]
        return "\n".join(out)

    total = sum(l["stake_eur"] for l in lineas)
    out += [f"**{len(lineas)} apuestas**, {total:,.2f} € en total "
            f"({total/banca*100:.1f}% de la banca).\n",
            "| Partido | Mercado | Apuesta | Casa | Cuota | Nuestra | "
            "Mercado | Ventaja | **Stake** |", "|---|---|---|---|---|---|---|---|---|"]
    for l in sorted(lineas, key=lambda x: -x["ventaja"]):
        pm = f"{l['prob_mercado']}%" if l["prob_mercado"] else "—"
        out.append(f"| {l['partido']} | {l['mercado']} | {l['apuesta']} | "
                   f"{l['casa']} | {l['cuota']} | {l['prob_modelo']}% | {pm} | "
                   f"{l['ventaja']:+.2f}% | **{l['stake_pct']:.2f}% = "
                   f"{l['stake_eur']:,.2f} €** |")
    out += ["\n## Cómo se ha calculado el stake\n",
            f"Kelly partido en {1/gb.FRACCION_KELLY:.0f}, con tope del "
            f"{gb.TOPE_POR_APUESTA*100:.0f}% de la banca por apuesta.\n",
            "Kelly entero es óptimo solo si conoces la probabilidad exacta. "
            "Nosotros la estimamos, y un error de dos puntos con Kelly entero "
            "puede triplicar lo que deberías jugarte. Partirlo crece casi "
            "igual y hunde la caída máxima.\n",
            "> Con una ventaja **real** del 4%, se pierde dinero en el 21% de "
            "las series de 500 apuestas. Eso no es un fallo del método: es "
            "apostar.\n"]
    if casas_vistas is not None:
        faltan = [c for c in MIS_CASAS if c not in casas_vistas]
        if faltan:
            out.append(f"\n> ⚠ Estas casas tuyas no aparecieron en ningún "
                       f"partido: **{', '.join(faltan)}**. O no cotizan estas "
                       f"ligas, o el nombre no es el exacto de la API. "
                       f"Compruébalo: un nombre mal escrito no da error, "
                       f"simplemente no sale nunca.\n")
    return "\n".join(out)


def main():
    ok, motivo = modelo_validado()
    if not ok:
        texto = escribir([], nota_puerta=motivo)
        with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"PUERTA CERRADA: {motivo}")
        print(f"Escrito {RUTA_SALIDA} sin apuestas.")
        return
    print(motivo)
    print("La puerta está abierta, pero aún falta enganchar el modelo a las "
          "cuotas del día.")


if __name__ == "__main__":
    main()
