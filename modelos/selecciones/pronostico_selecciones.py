"""
Pronósticos de los partidos de selecciones de la jornada (equipos.json, que
escribe nations_league.py): 1X2, más/menos 2.5, ambos marcan, tarjetas,
córners y goles. Tema APARTE del proyecto de ambos marcan.

Nacido el 26/09/2026 con Inglaterra-España y Chequia-Croacia; generalizado
el mismo día a todos los partidos de la Nations League.

Tres probabilidades por mercado:
  modelo    modelo_selecciones.py (Poisson de selecciones con todos los
            partidos descargados desde 2025) + ajuste de forma del once con la
            nota justa (notas_jugadores.csv) + árbitro en tarjetas.
  mercado   mediana de casas sin margen (cuotas_hoy.csv).
  final     w * modelo + (1 - w) * mercado. El peso w de cada mercado lo
            APRENDE evaluar_selecciones.py de los partidos ya jugados
            (pesos_mezcla.json) en cuanto hay 30 evaluados; hasta entonces,
            PESOS_INICIALES.
Pronóstico = el lado más probable según "final", con la cuota mínima (1/p).

Cada ejecución añade una fila por partido a data/selecciones/registro_pronosticos.csv
(lo que se dijo ANTES del partido: con eso aprende la evaluación).

Prueba hacia delante del 26/09 (48 partidos de 4 selecciones): 1X2 +1.91s y
ambos marcan +1.28s contra la tasa previa; goles totales, córners y tarjetas,
peor que la tasa previa. De ahí los pesos iniciales.
"""
import sys
import os
import json
import warnings
from datetime import datetime, timezone
warnings.filterwarnings("ignore")
sys.path.insert(0, "modelos/selecciones")
import numpy as np
import pandas as pd
import modelo_selecciones as S

B_FORMA = 0.5           # 0.1 puntos de nota del once -> ~5% de goles (a mano, sin calibrar)
K_ARBITRO = 10
DISPERSION = {"corners": 1.18, "amarillas": 1.67}   # de la prueba hacia delante del 26/09
PESOS_INICIALES = {"1": 0.5, "X": 0.5, "2": 0.5, "btts": 0.5}   # el resto 0: el modelo no aportó
RUTA_PESOS = f"{S.CARPETA}/pesos_mezcla.json"
RUTA_REGISTRO = f"{S.CARPETA}/registro_pronosticos.csv"
SALIDA = "modelos/selecciones/pronosticos.md"

# clave -> (mercado de la API, lado "sí")
MERCADOS = {"1": ("Full Time Result", "Home"), "X": ("Full Time Result", "Draw"),
            "2": ("Full Time Result", "Away"), "mas_2.5": ("Total Goals 2.5", "Over"),
            "btts": ("Both Teams To Score", "Yes"), "mas_1.5": ("Total Goals 1.5", "Over"),
            "mas_3.5": ("Total Goals 3.5", "Over"),
            "corners_mas_8.5": ("Total Corners 8.5", "Over"), "corners_mas_9.5": ("Total Corners 9.5", "Over"),
            "tarjetas_mas_3.5": ("Total Cards 3.5", "Over"), "tarjetas_mas_4.5": ("Total Cards 4.5", "Over"),
            "primero_local": ("First Team To Score", "Home")}


def mercado(c, partido, nombre):
    g = c[(c.partido == partido) & (c.mercado == nombre)]
    if g.empty:
        return {}
    med = g.groupby("lado").cuota.median()
    tot = (1 / med).sum()
    # mejor cuota SIN atípicos: una casa un 12% por encima de la mediana suele ser
    # una foto vieja o un error (Casumo daba España a 2.55 con mediana 2.12)
    return {l: {"p": 1 / o / tot, "mediana": o,
                "mejor": g[(g.lado == l) & (g.cuota <= o * 1.12)].cuota.max(),
                "casas": int((g.lado == l).sum())} for l, o in med.items()}


def arbitro(mid):
    ruta = f"{S.CARPETA}/raw/partido_hoy_{mid}.json"
    if not os.path.exists(ruta):
        return None, 1.0, 0
    j = json.load(open(ruta))
    j = j[0] if isinstance(j, list) and j else j
    nombre = ((j or {}).get("referee") or {}).get("name") if isinstance(j, dict) else None
    h = pd.read_csv("data/historico_partidos.csv").merge(
        pd.read_csv("data/historico_arbitro_clima.csv")[["match_id", "arbitro"]], on="match_id")
    h["tarj"] = h.l_yellow_cards + h.v_yellow_cards
    h = h[h.tarj.notna()]
    h["media_liga"] = h.groupby(["liga", "temporada"]).tarj.transform("mean")
    g = h[h.arbitro == nombre] if nombre else h.iloc[:0]
    if g.empty:
        return nombre, 1.0, 0
    m = g.media_liga.mean()
    return nombre, (g.tarj.sum() + K_ARBITRO * m) / (g.media_liga.sum() + K_ARBITRO * m), len(g)


def forma(notas, equipo):
    n = notas[notas.seleccion == equipo]
    o, h = n[n.once_probable], n[n.once_habitual]
    if o.empty or h.empty:
        return 0.0, o
    return float(o.nota.mean() - h.sel_nota_bruta.fillna(h.nota).mean()), o


def pesos():
    w = {k: PESOS_INICIALES.get(k, 0.0) for k in MERCADOS}
    if os.path.exists(RUTA_PESOS):
        aprendidos = json.load(open(RUTA_PESOS))
        w.update({k: v["peso"] for k, v in aprendidos.items() if v.get("aprendido")})
    return w


def main():
    p, q, roto, sinq = S.cargar()
    eq = json.load(open(f"{S.CARPETA}/equipos.json"))
    ids, cruces = eq["equipos"], eq["cruces"]
    ahora = datetime.now(timezone.utc)
    L = [f"# Pronósticos de selecciones ({ahora:%d/%m/%Y %H:%M} UTC)", "",
         "Tema aparte del proyecto de ambos marcan. Por mercado: **modelo** (selecciones + nota justa "
         "de los jugadores + árbitro), **mercado** (mediana de casas sin margen) y **final** (mezcla con "
         "el peso que se aprende de los partidos ya jugados, ver `evaluacion.md`). Pronóstico = el lado "
         "más probable según final. **Cuota mínima** = 1/probabilidad final: por debajo no compensa.", "",
         f"Datos del modelo: {len(p)} partidos de selecciones desde 2025 (descartados {sinq} contra rivales "
         f"sin jugadores en la API y {roto} xG roto).", ""]
    if not cruces:
        L.append("No hay partidos de la Nations League en las próximas horas.")
        open(SALIDA, "w").write("\n".join(L) + "\n")
        print("Sin partidos en la jornada.")
        return
    notas = pd.read_csv(f"{S.CARPETA}/notas_jugadores.csv")
    ruta_c = f"{S.CARPETA}/cuotas_hoy.csv"
    c = pd.read_csv(ruta_c) if os.path.exists(ruta_c) and os.path.getsize(ruta_c) > 5 else \
        pd.DataFrame(columns=["partido", "mercado", "lado", "cuota"])
    w = pesos()
    # un ajuste por objetivo para toda la jornada (antes se reajustaba en cada partido)
    f_gol = [S.ajustar(p[p[f"{o}_l"].notna()], q, o) for o in ("goles", "xg")]
    f_cor = S.ajustar(p[p.corners_l.notna()], q, "corners")
    f_tar = S.ajustar(p[p.amarillas_l.notna()], q, "amarillas")
    registro = []
    for cruce in cruces:
        loc, vis, mid = cruce[:3]
        fecha = cruce[3] if len(cruce) > 3 else ""
        partido = f"{loc} - {vis}"
        tl, tv = ids[loc], ids[vis]
        if tl not in q.index or tv not in q.index:
            L += [f"## {partido}", "", "Sin datos de jugadores de alguna de las dos selecciones: sin pronóstico.", ""]
            print(f"{partido}: sin datos, se salta")
            continue
        lam = (np.mean([f(tl, tv, 1.0) for f in f_gol]), np.mean([f(tv, tl, 0.0) for f in f_gol]))
        fl, ol = forma(notas, loc)
        fv, ov = forma(notas, vis)
        lam = (lam[0] * np.exp(B_FORMA * fl - 0.5 * B_FORMA * fv), lam[1] * np.exp(B_FORMA * fv - 0.5 * B_FORMA * fl))
        gm = S.goles(*lam)
        cor = f_cor(tl, tv, 1.0) + f_cor(tv, tl, 0.0)
        arb, r_arb, n_arb = arbitro(mid)
        tar = (f_tar(tl, tv, 1.0) + f_tar(tv, tl, 0.0)) * r_arb
        con_gol = max(1 - gm["sin_goles"], 1e-9)
        mod = {"1": gm["1"], "X": gm["X"], "2": gm["2"], "mas_2.5": gm["mas_2.5"], "btts": gm["btts"],
               "mas_1.5": gm["mas_1.5"], "mas_3.5": gm["mas_3.5"],
               "corners_mas_8.5": S.prob_mas(cor, 8.5, DISPERSION["corners"]),
               "corners_mas_9.5": S.prob_mas(cor, 9.5, DISPERSION["corners"]),
               "tarjetas_mas_3.5": S.prob_mas(tar, 3.5, DISPERSION["amarillas"]),
               "tarjetas_mas_4.5": S.prob_mas(tar, 4.5, DISPERSION["amarillas"]),
               "primero_local": gm["primero_local"] / con_gol}
        mk, info = {}, {}
        for k, (nombre, lado) in MERCADOS.items():
            m = mercado(c, partido, nombre)
            if lado in m:
                mk[k] = m[lado]["p"]
                info[k] = m
        fin = {k: (w[k] * mod[k] + (1 - w[k]) * mk[k]) if k in mk else mod[k] for k in MERCADOS}
        tot = fin["1"] + fin["X"] + fin["2"]
        for k in ("1", "X", "2"):
            fin[k] /= tot
        fila = {"generado": ahora.isoformat(), "match_id": mid, "fecha_partido": fecha, "local": loc,
                "visitante": vis, "fuente_once": ol.fuente_once.iloc[0] if len(ol) else "-",
                "lam_l": round(lam[0], 3), "lam_v": round(lam[1], 3), "corners": round(cor, 2),
                "tarjetas": round(tar, 2), "arbitro": arb}
        for k in MERCADOS:
            fila[f"mod_{k}"] = round(mod[k], 4)
            fila[f"mkt_{k}"] = round(mk[k], 4) if k in mk else None
        registro.append(fila)

        def linea(cat, k_si, txt_si, txt_no, lado_si, lado_no):
            si = fin[k_si] >= 0.5
            pf = fin[k_si] if si else 1 - fin[k_si]
            pm = mod[k_si] if si else 1 - mod[k_si]
            pk = (mk[k_si] if si else 1 - mk[k_si]) if k_si in mk else None
            m = info.get(k_si, {}).get(lado_si if si else lado_no, {})
            return (cat, txt_si if si else txt_no, pf, pm, pk, m)
        filas = []
        k1 = max(("1", "X", "2"), key=lambda k: fin[k])
        m1 = info.get(k1, {}).get({"1": "Home", "X": "Draw", "2": "Away"}[k1], {})
        filas.append(("1X2", {"1": f"gana {loc}", "X": "empate", "2": f"gana {vis}"}[k1], fin[k1], mod[k1],
                      mk.get(k1), m1))
        filas.append(linea("Más/menos 2.5", "mas_2.5", "más de 2.5 goles", "menos de 2.5 goles", "Over", "Under"))
        filas.append(linea("Ambos marcan", "btts", "ambos marcan: sí", "ambos marcan: no", "Yes", "No"))
        for l in ("3.5", "4.5"):
            filas.append(linea("Tarjetas", f"tarjetas_mas_{l}", f"más de {l} tarjetas", f"menos de {l} tarjetas",
                               "Over", "Under"))
        for l in ("8.5", "9.5"):
            filas.append(linea("Córners", f"corners_mas_{l}", f"más de {l} córners", f"menos de {l} córners",
                               "Over", "Under"))
        filas.append(linea("Goles", "mas_1.5", "más de 1.5 goles", "menos de 1.5 goles", "Over", "Under"))
        filas.append(linea("Goles", "primero_local", f"{loc} marca primero", f"{vis} marca primero", "Home", "Away"))

        L += [f"## {partido} ({str(fecha)[:16].replace('T', ' ')} UTC)", "",
              f"Goles esperados {lam[0]:.2f} - {lam[1]:.2f}, marcador más probable "
              f"{gm['marcador'][0]}-{gm['marcador'][1]}. Córners esperados {cor:.1f}. Amarillas esperadas "
              f"{tar:.1f} (árbitro {arb or '?'}, {n_arb} partidos en nuestras ligas, x{r_arb:.2f}). "
              f"Forma del once: {loc} {fl:+.2f}, {vis} {fv:+.2f}.", "",
              "| mercado | pronóstico | final | modelo | mercado | cuota mínima | cuota mediana | mejor cuota | casas |",
              "|---|---|---|---|---|---|---|---|---|"]
        for cat, txt, pf, pm, pk, m in filas:
            pk_txt = f"{pk*100:.0f}%" if pk is not None else "-"
            L.append(f"| {cat} | **{txt}** | {pf*100:.0f}% | {pm*100:.0f}% | {pk_txt} | {1/pf:.2f} | "
                     f"{m.get('mediana', float('nan')):.2f} | {m.get('mejor', float('nan')):.2f} | {m.get('casas', 0)} |")
        L += ["", f"Once {fila['fuente_once']} {loc}: " + ", ".join(ol.jugador),
              f"Once {ov.fuente_once.iloc[0] if len(ov) else '-'} {vis}: " + ", ".join(ov.jugador), ""]
        print(f"{partido}: goles {lam[0]:.2f}-{lam[1]:.2f}  1X2 final {fin['1']*100:.0f}/{fin['X']*100:.0f}/"
              f"{fin['2']*100:.0f}  ambos {fin['btts']*100:.0f}%  once {fila['fuente_once']}")
    L += ["## Cuánto fiarse", "",
          "- Pesos de la mezcla modelo/mercado: " + ", ".join(f"{k} {v:.2f}" for k, v in w.items() if v) +
          " (el resto 0 = manda el mercado). Se reaprenden en `evaluacion.md` con los partidos jugados.",
          "- Tarjetas: pocas casas y probablemente cuentan distinto (roja = 2); el modelo cuenta amarillas.",
          "- El ajuste de forma (nota justa) está puesto a mano (B_FORMA = 0.5).", ""]
    open(SALIDA, "w").write("\n".join(L) + "\n")
    if registro:
        r = pd.DataFrame(registro)
        if os.path.exists(RUTA_REGISTRO):
            r = pd.concat([pd.read_csv(RUTA_REGISTRO), r])
        r.to_csv(RUTA_REGISTRO, index=False)


if __name__ == "__main__":
    main()
