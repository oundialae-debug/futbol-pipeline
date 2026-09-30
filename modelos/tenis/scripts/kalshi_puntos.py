"""
Modelo de puntos contra los precios de Kalshi (30/09/2026): partido
(ATP, WTA, Challenger), total de juegos y hándicap de juegos.

Reglas fijadas ANTES de ver los precios:
- Precio de Kalshi como en calibracion_kalshi.py (foto a cierre - 4 h, ATP
  6 h; punto medio si el diferencial <= 0,10, si no el último negociado).
- Probabilidad del modelo: distribución exacta de juegos (markov_tenis) con
  la prob. de punto al saque de cada jugador ANTES del partido
  (modelo_puntos, parámetros fijos). Partido: P(gana el jugador "sí").
  Total: P(juegos > línea). Hándicap: P(juegos del jugador "sí" − rival > línea).
- Juegos/hándicap: una línea por partido, la más cercana al 50% en Kalshi.
- Emparejamiento: nombres del texto del mercado ("X vs Y") con el historial
  (apellido + inicial), inicio del torneo entre 20 días antes del cierre y
  el día del cierre.
- Apuesta al lado con p_modelo − coste > umbral (0% y 5%), coste = precio de
  venta del lado + comisión 0,07·c·(1−c). Un partido = una apuesta.
Escribe data/tenis/kalshi_puntos.md.
"""
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "modelos/tenis/scripts")
import calibracion_kalshi as CK  # noqa: E402
import cruce_fuentes as C  # noqa: E402
import markov_tenis as K  # noqa: E402
import modelo_puntos as P  # noqa: E402

SERIES = {"KXATPMATCH": ("atp", "partido"), "KXATPCHALLENGERMATCH": ("atp", "partido"),
          "KXWTAMATCH": ("wta", "partido"), "KXWTACHALLENGERMATCH": ("wta", "partido"),
          "KXATPGTOTAL": ("atp", "total"), "KXWTAGTOTAL": ("wta", "total"), "KXATPGSPREAD": ("atp", "hándicap")}
# el "the" INMEDIATAMENTE anterior a "X vs Y": en juegos el texto empieza "If the number of
# completed games...", y un "the (.+?) vs" cogía esa frase como nombre (solo 17 emparejados)
NOMBRES = re.compile(r"the ((?:(?!the ).)+?) vs\.? (.+?) professional tennis match")


def historiales():
    out = {}
    for c in ("atp", "wta"):
        h, _ = P.calcular(c, P.PARAMS[c])
        h["kw"] = h["winner_name"].map(C.clave_completo)
        h["kl"] = h["loser_name"].map(C.clave_completo)
        h["bo"] = np.where(pd.to_numeric(h["best_of"], errors="coerce") == 5, 5, 3)
        h = h[h["inicio"] >= "2025-01-01"]
        idx = {}
        for i, (a, b) in enumerate(zip(h["kw"].values, h["kl"].values)):
            idx.setdefault(a, []).append(i)
            idx.setdefault(b, []).append(i)
        out[c] = (h.reset_index(drop=True), idx)
    return out


def emparejar(fila, h, idx, tipo):
    """Fila del historial del mismo partido, o None.
    Partido: el texto solo trae apellidos ("the Hurkacz vs Davidovich Fokina match") y los dos
    lados del mercado llevan el nombre del MISMO jugador; se empareja el nombre completo del
    jugador "sí" y el apellido del rival. Juegos: el texto trae los dos nombres completos."""
    m = NOMBRES.search(str(fila["rules_primary"]))
    if not m:
        return None
    if tipo == "partido":
        si = C.clave_completo(fila["yes_sub_title"])
        ap_si = C.norm(str(fila["yes_sub_title"]).split()[-1])
        rival = [x for x in (m.group(1), m.group(2)) if C.norm(x.split()[-1]) != ap_si]
        if len(rival) != 1:
            return None
        ap_rival = C.norm(rival[0].split()[-1])
        candidatos = [i for i in idx.get(si, []) if ap_rival in
                      (h.at[i, "kl"].split("|")[0] if h.at[i, "kw"] == si else h.at[i, "kw"].split("|")[0])]
    else:
        a, b = C.clave_completo(m.group(1)), C.clave_completo(m.group(2))
        candidatos = [i for i in idx.get(a, []) if b in (h.at[i, "kw"], h.at[i, "kl"])]
    cierre = pd.Timestamp(fila["close_time"]).tz_convert(None)
    mejor = None
    for i in candidatos:
        dias = (cierre.normalize() - h.at[i, "inicio"]).days
        if -1 <= dias <= 20 and (mejor is None or dias < mejor[1]):
            mejor = (i, dias)
    return None if mejor is None else mejor[0]


def prob_modelo(tipo, fila, r, jugador_si):
    """r: fila del historial. jugador_si: clave del jugador del lado 'sí' (partido/hándicap)."""
    si_es_ganador = jugador_si is None or jugador_si == r["kw"]
    pa, pb = (r["p_w"], r["p_l"]) if si_es_ganador else (r["p_l"], r["p_w"])
    gana, total, dif = K.partido(K.redondear(pa), K.redondear(pb), int(r["bo"]))
    if tipo == "partido":
        return gana
    linea = float(fila["floor_strike"])
    if tipo == "total":
        return sum(v for k, v in total.items() if k > linea)
    return sum(v for k, v in dif.items() if k > linea)


def main():
    hs = historiales()
    out = ["# Modelo de puntos contra los precios de Kalshi\n",
           "Generado por `modelos/tenis/scripts/kalshi_puntos.py`. Log-loss: negativo = el modelo es mejor",
           "que el precio de Kalshi. Apuestas al precio de venta con comisión.\n",
           "| mercado | partidos emparejados | acierto modelo | acierto Kalshi | log-loss modelo | log-loss Kalshi | "
           "modelo - Kalshi (sigmas) | apuestas valor>0: n / rendimiento (sigmas) | valor>5%: n / rendimiento (sigmas) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for serie, (circ, tipo) in SERIES.items():
        d = CK.cargar(serie)
        if d is None:
            out.append(f"| {serie} | sin precios | | | | | | | |")
            continue
        d = d.dropna(subset=["p"])
        d = d[(d.p > 0) & (d.p < 1)]
        if tipo != "partido":
            d = CK.una_linea(d)
        h, idx = hs[circ]
        filas = []
        for _, f in d.iterrows():
            e = emparejar(f, h, idx, tipo)
            if e is None:
                continue
            r = h.iloc[e]
            si = None
            if tipo == "partido":
                si = C.clave_completo(f["yes_sub_title"])
            elif tipo == "hándicap":
                si = C.clave_completo(re.sub(r"\s*-?[\d.]+ games?$", "", str(f["yes_sub_title"])))
            if si is not None and si not in (r["kw"], r["kl"]):
                continue
            pm = prob_modelo(tipo, f, r, si)
            filas.append({"y": f["y"], "p_k": f["p"], "p_m": pm, "ask_si": f["ask_si"], "ask_no": f["ask_no"]})
        x = pd.DataFrame(filas)
        if len(x) < 50:
            out.append(f"| {serie} | {len(x)} | | | | | | | |")
            continue
        x["p_m"] = x["p_m"].clip(0.01, 0.99)
        llm = -(x.y * np.log(x.p_m) + (1 - x.y) * np.log(1 - x.p_m))
        llk = -(x.y * np.log(x.p_k) + (1 - x.y) * np.log(1 - x.p_k))
        dif = llm - llk
        celdas = []
        for u in (0.0, 0.05):
            ret = []
            for _, r in x.iterrows():
                ops = []
                for coste, p_lado, gana in ((r.ask_si, r.p_m, r.y == 1), (r.ask_no, 1 - r.p_m, r.y == 0)):
                    if coste == coste and 0 < coste < 1:
                        c = coste + 0.07 * coste * (1 - coste)
                        ops.append((p_lado - c, c, gana))
                if ops:
                    v, c, gana = max(ops)
                    if v > u:
                        ret.append(1 / c - 1 if gana else -1.0)
            ret = np.array(ret)
            celdas.append(f"{len(ret)} / {ret.mean():+.2%} ({ret.mean() / (ret.std(ddof=1) / np.sqrt(len(ret))):+.2f})"
                          if len(ret) > 1 else f"{len(ret)} / -")
        acm = ((x.p_m > 0.5) == (x.y == 1)).mean()
        ack = ((x.p_k > 0.5) == (x.y == 1)).mean()
        out.append(f"| {serie} | {len(x)} de {len(d)} | {acm:.1%} | {ack:.1%} | {llm.mean():.4f} | {llk.mean():.4f} | "
                   f"{dif.mean():+.4f} ({dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif))):+.2f}) | "
                   f"{celdas[0]} | {celdas[1]} |")
        print(out[-1], flush=True)
    open("data/tenis/kalshi_puntos.md", "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
