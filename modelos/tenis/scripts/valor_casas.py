"""
Estrategia de apostador profesional, en PAPEL (10/10/2026): sin modelo, comparar casas con PINNACLE.

get_odds trae, en la MISMA llamada que ya hacemos cada hora, las cuotas previas de 9 casas (bet365, 1xBet,
Marathon, Betfair, Pncl = Pinnacle, Sbo, WilliamHill, BetVictor, Betano). Hasta hoy se guardaba solo la
mediana: se tiraba justo el dato que usa un profesional ("mira la respuesta entera", CLAUDE.md).

Cada hora, para cada partido individual aún sin empezar:
- prob. "verdadera" = Pinnacle sin margen (ganador; y juegos en cada línea que Pinnacle cotiza a los dos lados);
- si una casa blanda paga cuota × p_pinnacle − 1 >= VALOR, se apunta la apuesta en papel (la primera vez
  que aparece por partido, mercado, línea, lado y casa): data/tenis/api_tennis/valor/<fecha>.csv;
- "donde se equivoca la casa": el favorito claro (Pinnacle >= 75%) gana más de lo que dice el precio
  (sesgo favorito-marginado, visto en el cierre de Pinnacle 2020-26 y en nuestro directo, +2 a +4 puntos);
  se apunta UNA apuesta por partido a la MEJOR cuota blanda: <fecha>_favoritos.csv;
- se reescribe la última foto de Pinnacle del partido (la que queda es la más cercana al inicio = "cierre"):
  data/tenis/api_tennis/valor/<fecha>_cierre.csv, para medir si se le gana al cierre (CLV).
Las casas no actualizan a la vez: aunque vengan en la misma llamada, parte del "valor" puede ser una casa
que aún no ha movido. Por eso se mide también contra el cierre, no solo contra el resultado.
"""
import csv
import os
import statistics as S

VALOR = 0.03
FAV = 0.75     # "donde se equivoca la casa": el favorito claro gana más de lo que dice su cuota (ver CLAUDE.md)
SHARP = "Pncl"
DIR = "data/tenis/api_tennis/valor"
CAMPOS = ["hora", "event_key", "tipo", "torneo", "jugador1", "jugador2", "mercado", "linea", "lado", "casa", "cuota",
          "p_pinnacle", "cuota_pinnacle", "valor", "n_casas"]
CIERRE = ["hora", "event_key", "mercado", "linea", "lado", "p_pinnacle", "cuota_pinnacle"]


def _pares(o):
    """[(mercado, linea, {lado: {casa: cuota}})] de ganador y de cada línea de juegos."""
    out = []
    ha = o.get("Home/Away", {})
    if ha.get("Home") and ha.get("Away"):
        out.append(("ganador", "", {"jugador1": ha["Home"], "jugador2": ha["Away"]}))
    ou = o.get("Over/Under by Games in Match", {})
    ov, un = ou.get("Over/Under by Games in Match Over", {}), ou.get("Over/Under by Games in Match Under", {})
    for ln in ov:
        if ln in un and ln.endswith(".5"):
            out.append(("juegos", ln, {"más": ov[ln], "menos": un[ln]}))
    return out


def registrar(ahora, partidos, odds):
    os.makedirs(DIR, exist_ok=True)
    fecha = f"{ahora:%Y-%m-%d}"
    ruta, rc = f"{DIR}/{fecha}.csv", f"{DIR}/{fecha}_cierre.csv"
    vistos = set()
    if os.path.exists(ruta):
        vistos = {(r["event_key"], r["mercado"], r["linea"], r["lado"], r["casa"]) for r in csv.DictReader(open(ruta))}
    cierre = {}
    if os.path.exists(rc):
        for r in csv.DictReader(open(rc)):
            cierre[(r["event_key"], r["mercado"], r["linea"], r["lado"])] = r
    nuevas, favs = [], []
    rf = f"{DIR}/{fecha}_favoritos.csv"
    ya_fav = set()
    if os.path.exists(rf):
        ya_fav = {r["event_key"] for r in csv.DictReader(open(rf))}
    for p in partidos:
        k = str(p.get("event_key"))
        o = odds.get(k) if isinstance(odds, dict) else None
        if not o or p.get("event_status") or "/" in str(p.get("event_first_player")):
            continue
        for mer, ln, lados in _pares(o):
            a, b = list(lados)
            pa_, pb_ = lados[a].get(SHARP), lados[b].get(SHARP)
            try:
                pa_, pb_ = float(pa_), float(pb_)
            except (TypeError, ValueError):
                continue
            inv = 1 / pa_ + 1 / pb_
            prob = {a: (1 / pa_) / inv, b: (1 / pb_) / inv}
            if mer == "ganador":
                for lado in (a, b):
                    if prob[lado] >= FAV and k not in ya_fav:     # favorito claro según Pinnacle: a la MEJOR cuota
                        blandas = {c_: float(x) for c_, x in lados[lado].items()
                                   if c_ not in (SHARP, "Betfair") and x not in (None, "")}
                        if blandas:
                            casa, c = max(blandas.items(), key=lambda z: z[1])
                            ya_fav.add(k)
                            favs.append({"hora": f"{ahora:%Y-%m-%d %H:%M}", "event_key": k, "tipo": p.get("event_type_type"),
                                         "torneo": p.get("tournament_name"), "jugador1": p.get("event_first_player"),
                                         "jugador2": p.get("event_second_player"), "mercado": "favorito", "linea": "",
                                         "lado": lado, "casa": casa, "cuota": c, "p_pinnacle": round(prob[lado], 4),
                                         "cuota_pinnacle": lados[lado][SHARP], "valor": round(c * prob[lado] - 1, 4),
                                         "n_casas": len(blandas)})
            for lado in (a, b):
                cierre[(k, mer, ln, lado)] = {"hora": f"{ahora:%Y-%m-%d %H:%M}", "event_key": k, "mercado": mer,
                                              "linea": ln, "lado": lado, "p_pinnacle": round(prob[lado], 4),
                                              "cuota_pinnacle": lados[lado][SHARP]}
                for casa, c in lados[lado].items():
                    if casa in (SHARP, "Betfair"):          # Betfair es bolsa (comisión aparte): no es casa blanda
                        continue
                    try:
                        c = float(c)
                    except (TypeError, ValueError):
                        continue
                    v = c * prob[lado] - 1
                    clave = (k, mer, ln, lado, casa)
                    if v >= VALOR and clave not in vistos:
                        vistos.add(clave)
                        nuevas.append({"hora": f"{ahora:%Y-%m-%d %H:%M}", "event_key": k, "tipo": p.get("event_type_type"),
                                       "torneo": p.get("tournament_name"), "jugador1": p.get("event_first_player"),
                                       "jugador2": p.get("event_second_player"), "mercado": mer, "linea": ln,
                                       "lado": lado, "casa": casa, "cuota": c, "p_pinnacle": round(prob[lado], 4),
                                       "cuota_pinnacle": lados[lado][SHARP], "valor": round(v, 4),
                                       "n_casas": len(lados[lado])})
    nuevo = not os.path.exists(ruta)
    with open(ruta, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerows(nuevas)
    nuevo = not os.path.exists(rf)
    with open(rf, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        w.writerows(favs)
    with open(rc, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CIERRE)
        w.writeheader()
        w.writerows(cierre.values())
    print(f"valor: {len(nuevas)} apuestas de valor y {len(favs)} de favorito nuevas en papel")


def tabla():
    """Informe: apuestas de valor contra el resultado y contra el cierre de Pinnacle."""
    import glob

    import numpy as np
    import pandas as pd
    fs = sorted(f for f in glob.glob(f"{DIR}/*.csv") if not f.endswith("_cierre.csv"))   # incluye _favoritos
    lin = ["## Comparar casas con Pinnacle (profesional, en papel desde el 10/10)", ""]
    if not fs:
        return lin + ["Todavía sin datos."]
    v = pd.concat(pd.read_csv(f, dtype={"linea": str}) for f in fs)
    ci = pd.concat(pd.read_csv(f, dtype={"linea": str}) for f in glob.glob(f"{DIR}/*_cierre.csv"))
    ci = ci.sort_values("hora").drop_duplicates(["event_key", "mercado", "linea", "lado"], keep="last")
    res = pd.concat(pd.read_csv(f) for f in glob.glob("data/tenis/api_tennis/resultados/*.csv")).drop_duplicates(
        "event_key", keep="last")
    res = res[res.estado == "Finished"].copy()
    s = res.sets.astype(str).str.split("-", expand=True)
    res["s1"], res["s2"] = pd.to_numeric(s[0], errors="coerce"), pd.to_numeric(s[1], errors="coerce")
    v["linea"] = v.linea.fillna("").astype(str)
    ci["linea"] = ci.linea.fillna("").astype(str)
    v = v.merge(res[["event_key", "s1", "s2", "juegos_totales"]], on="event_key")
    v["_m"] = v.mercado.replace({"favorito": "ganador"})
    v = v.merge(ci[["event_key", "mercado", "linea", "lado", "p_pinnacle"]].rename(
        columns={"p_pinnacle": "p_cierre", "mercado": "_m"}), on=["event_key", "_m", "linea", "lado"], how="left")
    if v.empty:
        return lin + ["Ninguna apuesta resuelta todavía."]
    ln = pd.to_numeric(v.linea, errors="coerce")
    v.loc[v.mercado == "favorito", "mercado"] = "favorito >= 75% a la mejor cuota"
    v["gana"] = np.select([v.lado == "jugador1", v.lado == "jugador2", v.lado == "más", v.lado == "menos"],
                          [v.s1 > v.s2, v.s2 > v.s1, v.juegos_totales > ln, v.juegos_totales < ln], False)
    v["benef"] = np.where(v.gana, v.cuota - 1, -1.0)
    v["clv"] = v.cuota * v.p_cierre - 1                  # valor contra el cierre de Pinnacle
    lin += ["| mercado | apuestas | partidos | aciertos | valor esperado (Pinnacle al apostar) | valor contra el cierre | beneficio real | sigmas (por partido) |",
            "|---|---|---|---|---|---|---|---|"]
    for mer, g in list(v.groupby("mercado")) + [("todo", v)]:
        pp = g.groupby("event_key").benef.mean()        # agrupado por partido: sus apuestas ganan y pierden juntas
        sig = pp.mean() / (pp.std(ddof=1) / np.sqrt(len(pp))) if len(pp) > 1 else float("nan")
        lin.append(f"| {mer} | {len(g)} | {g.event_key.nunique()} | {g.gana.mean():.0%} | {g.valor.mean():+.1%} | "
                   f"{g.clv.mean():+.1%} | {g.benef.mean():+.1%} | {sig:+.2f} |")
    fv = v[v.mercado.str.startswith("favorito")]
    if len(fv):
        b = np.where(fv.gana, pd.to_numeric(fv.cuota_pinnacle, errors="coerce") - 1, -1.0)
        lin.append(f"| favorito >= 75% a cuota de PINNACLE | {len(fv)} | {fv.event_key.nunique()} | {fv.gana.mean():.0%} | "
                   f"| | {np.nanmean(b):+.1%} | |")
    lin += ["", "Por casa (todas las apuestas):", "", "| casa | apuestas | beneficio | contra el cierre |", "|---|---|---|---|"]
    for casa, g in v.groupby("casa"):
        lin.append(f"| {casa} | {len(g)} | {g.benef.mean():+.1%} | {g.clv.mean():+.1%} |")
    return lin
