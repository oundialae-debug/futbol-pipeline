"""
Pronóstico de ambos marcan para los partidos de HOY de una liga, con el
modelo oficial (scripts/modelo_ambos_marcan.py: producción + precio, todo el
histórico anterior, 5 semillas). Pedido el 27/09/2026 para la Segunda.

Dos pasos:
  descargar   (GitHub Actions, gasta API) para cada partido de hoy de la liga
              en data/calendario.csv: /matches/{id} (ids de equipo, árbitro,
              tiempo), /lineups/{id} (once, si ya está) y /odds (cuotas).
              3 llamadas por partido. -> data/ambos_hoy/
  pronosticar (local, sin API) añade esos partidos al histórico SIN resultado,
              calcula sus rasgos solo con partidos anteriores, entrena con todo
              lo jugado y predice. El precio sale de las cuotas de hoy (mediana
              de casas sin margen: 1X2 y más/menos 2.5), no de la previa de
              football-data con la que se entrenó (fuente y hora distintas:
              comprobado el 25/09 que difieren ~0.9 puntos, correlación 0.997).
  evaluar     (local, sin API) cruza el registro de apuestas en papel con los
              resultados ya en data/historico_partidos.csv y escribe
              modelos/ambos_marcan/registro_papel.md.

REGISTRO EN PAPEL (desde el 27/09/2026, petición del usuario: "todo lo que se
haga a partir de ahora tiene que ir aprendiendo"): cada pronóstico se apunta
ANTES del partido en data/ambos_marcan/registro_papel.csv (1X2, más de 2.5 y
ambos marcan, modelo y mercado, y la apuesta de ambos marcan si VE > 0 contra
la cuota mediana). Es el único juez limpio: partidos que ninguna prueba ha
tocado. El modelo además se reentrena con todo lo jugado cada vez que se usa.
Uso: python scripts/ambos_marcan_hoy.py descargar|pronosticar|evaluar
     (LIGA_ID por defecto 120775 = Segunda, FECHA por defecto hoy UTC)
"""
import os
import sys
import json
import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd

LIGA_ID = int(os.environ.get("LIGA_ID", "120775"))
FECHA = os.environ.get("FECHA") or datetime.now(timezone.utc).date().isoformat()
CARPETA = "data/ambos_hoy"
REGISTRO = "data/ambos_marcan/registro_papel.csv"
BASE_URL = "https://soccer.highlightly.net"


def pedir(path, params=None):
    import requests
    h = {"x-rapidapi-key": os.environ["HIGHLIGHTLY_API_KEY"]}   # nunca se imprime
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=h, params=params, timeout=30)
        except Exception as e:
            print(f"  [sin respuesta: {type(e).__name__}] {path}"); time.sleep(3); continue
        if r.status_code == 429:
            print(f"  [429] {path}"); time.sleep(5); continue
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] {path}"); return None
        return r.json()
    return None


def lista(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def descargar():
    os.makedirs(CARPETA, exist_ok=True)
    cal = pd.read_csv("data/calendario.csv")
    hoy = cal[(cal.liga_id == LIGA_ID) & (cal.fecha.astype(str) == FECHA)]
    filas, cuotas = [], []
    for _, c in hoy.iterrows():
        mid = int(c.match_id)
        m = pedir(f"/matches/{mid}")
        m = m[0] if isinstance(m, list) and m else m
        if not isinstance(m, dict):
            continue
        clima = m.get("forecast") or {}
        lu = pedir(f"/lineups/{mid}")
        lu = lu[0] if isinstance(lu, list) and lu else lu
        ids = {}
        for lado in ("homeTeam", "awayTeam"):
            t = (lu or {}).get(lado) or {} if isinstance(lu, dict) else {}
            jug = [j for linea in (t.get("initialLineup") or [])
                   for j in (linea if isinstance(linea, list) else [linea]) if isinstance(j, dict)]
            ids[lado] = ("|".join(str(j.get("id")) for j in jug) if len(jug) >= 11 else None,
                         t.get("formation") if len(jug) >= 11 else None)
        filas.append({"match_id": mid, "fecha": m.get("date"), "saque_utc": c.saque_utc,
                      "local_id": (m.get("homeTeam") or {}).get("id"), "local": (m.get("homeTeam") or {}).get("name"),
                      "visitante_id": (m.get("awayTeam") or {}).get("id"),
                      "visitante": (m.get("awayTeam") or {}).get("name"),
                      "estado": ((m.get("state") or {}).get("description")),
                      "arbitro": (m.get("referee") or {}).get("name"),
                      "clima_status": clima.get("status"), "clima_temp_txt": clima.get("temperature"),
                      "local_ids": ids["homeTeam"][0], "local_formacion": ids["homeTeam"][1],
                      "visitante_ids": ids["awayTeam"][0], "visitante_formacion": ids["awayTeam"][1]})
        for b in lista(pedir("/odds", {"matchId": mid, "oddsType": "prematch"})):
            for mk in (b.get("odds") or []) if isinstance(b, dict) else []:
                if mk.get("market") in ("Full Time Result", "Total Goals 2.5", "Both Teams To Score"):
                    for v in mk.get("values") or []:
                        try:
                            cuotas.append({"match_id": mid, "mercado": mk["market"], "casa": mk.get("bookmakerName"),
                                           "lado": str(v.get("value")), "cuota": float(v.get("odd"))})
                        except (TypeError, ValueError):
                            pass
    pd.DataFrame(filas).to_csv(f"{CARPETA}/partidos.csv", index=False)
    pd.DataFrame(cuotas).to_csv(f"{CARPETA}/cuotas.csv", index=False)
    print(f"{FECHA}, liga {LIGA_ID}: {len(filas)} partidos, {len(cuotas)} cuotas, "
          f"onces: {sum(1 for f in filas if f['local_ids'])}")


def precio(cuotas, mid):
    c = cuotas[cuotas.match_id == mid]
    def sin_margen(mercado):
        med = c[c.mercado == mercado].groupby("lado").cuota.median()
        return (1 / med) / (1 / med).sum(), med
    r, _ = sin_margen("Full Time Result")
    o, _ = sin_margen("Total Goals 2.5")
    b, mb = sin_margen("Both Teams To Score")
    casas_b = c[(c.mercado == "Both Teams To Score")].casa.nunique()
    return r, o, b, mb, casas_b


def pronosticar():
    import rasgos, modelo_xgboost as M, modelo_ambos_marcan as A
    sys.path.insert(0, "scripts")
    import rasgos, modelo_xgboost as M
    from btts_implicito import ajustar
    from cuota_como_variable import MKT
    from apuesta_ambos_marcan import rasgos_mercado
    hoy = pd.read_csv(f"{CARPETA}/partidos.csv")
    empezados = hoy[hoy.estado.astype(str) != "Not started"]
    if len(empezados):
        print("Ya empezados o jugados (no se pronostican): " +
              ", ".join(f"{a}-{b} ({e})" for a, b, e in zip(empezados.local, empezados.visitante, empezados.estado)))
    hoy = hoy[hoy.estado.astype(str) == "Not started"].reset_index(drop=True)
    cuotas = pd.read_csv(f"{CARPETA}/cuotas.csv")
    M.TEMPORADA_MINIMA = A.TEMPORADA_MINIMA   # 2022/23 dentro, solo para ambos marcan
    rasgos.COBERTURA_MINIMA = 0.2   # que el xG del equipo no desaparezca de la tabla: 1X2 y 2.5 lo siguen usando
    hist = M.cargar()
    ult = hist[hist.liga_id == LIGA_ID].sort_values("fecha").iloc[-1]
    nuevas = pd.DataFrame({"match_id": hoy.match_id, "fecha": hoy.fecha, "liga_id": LIGA_ID, "liga": ult.liga,
                           "temporada": ult.temporada, "local_id": hoy.local_id, "local": hoy.local,
                           "visitante_id": hoy.visitante_id, "visitante": hoy.visitante,
                           "arbitro": hoy.arbitro, "local_ids": hoy.local_ids, "visitante_ids": hoy.visitante_ids,
                           "local_formacion": hoy.local_formacion, "visitante_formacion": hoy.visitante_formacion})
    todo = pd.concat([hist[~hist.match_id.isin(nuevas.match_id)], nuevas], ignore_index=True)
    bt = rasgos.construir(todo).sort_values("fecha").reset_index(drop=True)
    import portero
    cols = A.columnas(bt)                                                # ambos marcan: modelo oficial
    cols_otros = rasgos.columnas_rasgo_default(bt) + portero.COLS + MKT  # 1X2 y 2.5: como antes
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    bt = bt.merge(rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    bt = bt.merge(portero.historico(), on="match_id", how="left")
    # portero de hoy: el del once confirmado si ya está; si no, su último titular
    for _, h in hoy.iterrows():
        for lado, eq, ids in (("loc", h.local_id, h.local_ids), ("vis", h.visitante_id, h.visitante_ids)):
            lista_ids = str(ids).split("|") if isinstance(ids, str) else []
            bt.loc[bt.match_id == h.match_id, f"{lado}_gk_gp90"] = portero.para_partido(lista_ids, eq, h.fecha)
    # precio de hoy para los partidos de hoy (misma construcción que rasgos_mercado)
    for mid in hoy.match_id:
        r, o, b, mb, n = precio(cuotas, mid)
        if len(r) < 3 or "Over" not in o:
            continue
        pl, pe, pv, po = r.get("Home"), r.get("Draw"), r.get("Away"), o.get("Over")
        ll, lv = ajustar(pl, pe, pv, po)
        vals = dict(mkt_p_local=pl, mkt_p_empate=pe, mkt_p_visitante=pv, mkt_p_mas_2_5=po,
                    mkt_lambda_l=ll, mkt_lambda_v=lv,
                    mkt_p_btts_implicito=(1 - np.exp(-ll)) * (1 - np.exp(-lv)))
        for k, v in vals.items():
            bt.loc[bt.match_id == mid, k] = v
    ent = bt[bt.goles_l.notna() & ~bt.match_id.isin(hoy.match_id)]
    de_2022 = set(hist[hist.temporada.astype(int) < 2023].match_id)
    test = bt[bt.match_id.isin(hoy.match_id)]
    prob = {}
    for obj, nc in (("ambos_marcan", 2), ("mas_2_5", 2), ("resultado", 3)):
        e, c = (ent, cols) if obj == "ambos_marcan" else (ent[~ent.match_id.isin(de_2022)], cols_otros)
        y = e[obj].values.astype(int)
        prob[obj] = np.mean([M.probabilidades(M.entrenar(e[c].values, y, nc, semilla=s), test[c].values, nc)
                             for s in (0, 1, 2, 3, 4)], axis=0)
    test = test.assign(p=prob["ambos_marcan"][:, 1], p_mas25=prob["mas_2_5"][:, 1], p_1=prob["resultado"][:, 0],
                       p_x=prob["resultado"][:, 1], p_2=prob["resultado"][:, 2])
    print(f"Entrenado con {len(ent)} partidos, {len(cols)} variables. Último partido de la liga en el "
          f"histórico: {str(ult.fecha)[:10]}\n")
    L = [f"# Ambos marcan, {FECHA} (liga {LIGA_ID})", "",
         f"Modelo oficial de ambos marcan (producción + precio, {len(ent)} partidos de entrenamiento). "
         "Mercado = mediana de casas sin margen. Cuota mínima = 1/p del modelo.", "",
         "| partido | hora (España) | modelo: sí | mercado: sí | lado del modelo | cuota mínima | cuota mediana | VE | once |",
         "|---|---|---|---|---|---|---|---|---|"]
    for _, h in hoy.iterrows():
        t = test[test.match_id == h.match_id]
        if t.empty:
            continue
        pm = float(t.p.iloc[0])
        _, _, b, mb, n = precio(cuotas, h.match_id)
        pk = b.get("Yes", np.nan)
        si = pm >= 0.5
        lado, pl = ("sí", pm) if si else ("no", 1 - pm)
        cuota = mb.get("Yes" if si else "No", np.nan)
        ve = pl * cuota - 1
        hora = (pd.Timestamp(h.fecha).tz_convert("Europe/Madrid").strftime("%H:%M")
                if pd.notna(h.fecha) else "")
        once = "real" if isinstance(h.local_ids, str) and isinstance(h.visitante_ids, str) else "sin once"
        falta_precio = t[MKT].isna().any(axis=1).iloc[0]
        L.append(f"| {h.local} - {h.visitante} | {hora} | {pm*100:.0f}% | {pk*100:.0f}% | **{lado}** | "
                 f"{1/pl:.2f} | {cuota:.2f} | {ve*100:+.1f}% | {once}{', SIN precio' if falta_precio else ''} |")
        print(f"{h.local:>14s} - {h.visitante:<15s} {hora}  modelo sí {pm*100:4.1f}%  mercado sí {pk*100:4.1f}% "
              f"({n} casas)  -> {lado} a {cuota:.2f} (mín {1/pl:.2f}, VE {ve*100:+.1f}%)  {once}  estado {h.estado}")
    open(f"{CARPETA}/pronostico.md", "w").write("\n".join(L) + "\n")
    registrar(hoy, test, cuotas)


def registrar(hoy, test, cuotas):
    """Una fila por partido en el registro en papel, hecha ANTES del pitido."""
    ahora = datetime.now(timezone.utc)
    filas = []
    for _, h in hoy.iterrows():
        t = test[test.match_id == h.match_id]
        if t.empty or pd.to_datetime(h.fecha, utc=True) <= ahora:
            continue
        t = t.iloc[0]
        r, o, b, mb, n = precio(cuotas, h.match_id)
        si = t.p >= 0.5
        pl = t.p if si else 1 - t.p
        cuota = mb.get("Yes" if si else "No", np.nan)
        filas.append({"generado": ahora.isoformat(timespec="seconds"), "match_id": h.match_id, "liga_id": LIGA_ID,
                      "saque": h.fecha, "local": h.local, "visitante": h.visitante,
                      "mod_1": round(t.p_1, 4), "mod_x": round(t.p_x, 4), "mod_2": round(t.p_2, 4),
                      "mkt_1": round(r.get("Home", np.nan), 4), "mkt_x": round(r.get("Draw", np.nan), 4),
                      "mkt_2": round(r.get("Away", np.nan), 4),
                      "mod_mas25": round(t.p_mas25, 4), "mkt_mas25": round(o.get("Over", np.nan), 4),
                      "mod_ambos": round(t.p, 4), "mkt_ambos": round(b.get("Yes", np.nan), 4),
                      "lado_ambos": "si" if si else "no", "cuota_ambos": cuota,
                      "ve_ambos": round(pl * cuota - 1, 4), "apuesta": bool(pl * cuota - 1 > 0)})
    if filas:
        os.makedirs(os.path.dirname(REGISTRO), exist_ok=True)
        r = pd.DataFrame(filas)
        if os.path.exists(REGISTRO):
            r = pd.concat([pd.read_csv(REGISTRO), r])
        r.to_csv(REGISTRO, index=False)
        print(f"\nApuntados {len(filas)} partidos en {REGISTRO}")


def evaluar():
    """Cruza el registro con los resultados: lo último dicho antes del pitido de cada partido."""
    if not os.path.exists(REGISTRO):
        print("Sin registro todavía."); return
    r = pd.read_csv(REGISTRO)
    r["generado"] = pd.to_datetime(r.generado, utc=True, format="ISO8601")
    r = r[r.generado < pd.to_datetime(r.saque, utc=True, format="ISO8601")]
    r = r.sort_values("generado").groupby("match_id").tail(1)
    h = pd.read_csv("data/historico_partidos.csv")[["match_id", "goles_l", "goles_v"]]
    d = r.merge(h, on="match_id", how="left")
    jugados = d[d.goles_l.notna()].copy()
    gl, gv = jugados.goles_l, jugados.goles_v
    jugados["ambos"] = ((gl > 0) & (gv > 0)).astype(int)
    jugados["mas25"] = ((gl + gv) > 2.5).astype(int)
    jugados["res"] = np.select([gl > gv, gl == gv], ["1", "x"], "2")
    ap = jugados[jugados.apuesta]
    gano = np.where(ap.lado_ambos == "si", ap.ambos == 1, ap.ambos == 0)
    benef = np.where(gano, ap.cuota_ambos - 1, -1.0)
    def brier(p, y): return float(np.mean((p - y) ** 2))
    L = ["# Registro en papel: modelo de ambos marcan (desde el 27/09/2026)", "",
         "Cada pronóstico se apunta ANTES del partido; aquí se cruza con lo que pasó. Apuesta = ambos marcan, "
         "1 unidad, solo si el valor esperado es positivo contra la cuota mediana. Es la prueba limpia del "
         "modelo: no se toca nada del modelo por lo que salga aquí hasta tener muestra (100+ apuestas).", "",
         f"**Partidos jugados: {len(jugados)}** (pendientes {d.goles_l.isna().sum()}).", ""]
    if len(jugados):
        acierto = lambda col_mod, col_real, umbral=0.5: float(((jugados[col_mod] >= umbral).astype(int) == jugados[col_real]).mean())
        pick_mod = jugados[["mod_1", "mod_x", "mod_2"]].values.argmax(1)
        pick_mkt = jugados[["mkt_1", "mkt_x", "mkt_2"]].values.argmax(1)
        real = jugados.res.map({"1": 0, "x": 1, "2": 2}).values
        L += ["| mercado | acierto modelo | acierto mercado | Brier modelo | Brier mercado |", "|---|---|---|---|---|",
              f"| ambos marcan | {acierto('mod_ambos', 'ambos')*100:.0f}% | {acierto('mkt_ambos', 'ambos')*100:.0f}% | "
              f"{brier(jugados.mod_ambos, jugados.ambos):.3f} | {brier(jugados.mkt_ambos, jugados.ambos):.3f} |",
              f"| más de 2.5 | {acierto('mod_mas25', 'mas25')*100:.0f}% | {acierto('mkt_mas25', 'mas25')*100:.0f}% | "
              f"{brier(jugados.mod_mas25, jugados.mas25):.3f} | {brier(jugados.mkt_mas25, jugados.mas25):.3f} |",
              f"| 1X2 | {(pick_mod == real).mean()*100:.0f}% | {(pick_mkt == real).mean()*100:.0f}% | - | - |", "",
              f"**Apuestas de ambos marcan:** {len(ap)}, ganadas {int(gano.sum())}, beneficio "
              f"{benef.sum():+.2f} unidades ({(benef.mean()*100 if len(ap) else 0):+.1f}% por apuesta).", "",
              "| saque | partido | resultado | ambos (modelo/mercado) | apuesta | cuota | beneficio |",
              "|---|---|---|---|---|---|---|"]
        for _, j in jugados.sort_values("saque").iterrows():
            ben = ""
            if j.apuesta:
                g = (j.ambos == 1) if j.lado_ambos == "si" else (j.ambos == 0)
                ben = f"{(j.cuota_ambos - 1) if g else -1:+.2f}"
            L.append(f"| {str(j.saque)[:16].replace('T', ' ')} | {j.local} - {j.visitante} | {int(j.goles_l)}-{int(j.goles_v)} | "
                     f"{j.mod_ambos*100:.0f}% / {j.mkt_ambos*100:.0f}% | {j.lado_ambos if j.apuesta else '-'} | "
                     f"{j.cuota_ambos:.2f} | {ben} |")
    os.makedirs("modelos/ambos_marcan", exist_ok=True)
    open("modelos/ambos_marcan/registro_papel.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[4:6] + L[6:12]))


if __name__ == "__main__":
    {"descargar": descargar, "pronosticar": pronosticar, "evaluar": evaluar}[sys.argv[1]]()
