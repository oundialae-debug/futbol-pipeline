"""
Pronósticos de Inglaterra-España y Chequia-Croacia (Nations League,
26/09/2026): 1X2, más/menos 2.5, ambos marcan, tarjetas, córners y goles.
Tema APARTE del proyecto de ambos marcan.

Fuentes de probabilidad, por mercado:
  mercado   mediana de casas sin margen (data/selecciones/cuotas_hoy.csv,
            modelos/selecciones/previa_hoy.py). En todo este proyecto nada ha batido al
            precio: es la referencia principal.
  modelo    modelo_selecciones.py (Poisson de selecciones, 71 partidos desde
            2025) + ajuste de forma del once con la nota justa
            (notas_jugadores.csv) + árbitro en tarjetas (sus tarjetas en
            nuestras ligas frente a la media de su liga, encogido con 10
            partidos).
Prueba hacia delante del modelo (48 partidos desde oct-2025, cada uno
pronosticado con los anteriores), contra la tasa previa:
  1X2 +1.91s y ambos marcan +1.28s: algo sabe.
  más/menos goles, córners y tarjetas: PEOR que la tasa previa (-0.3s a
  -2.6s). En totales el modelo no aporta; ahí manda el mercado.
Pronóstico = el resultado más probable según el mercado (la cuota más baja),
con la opinión del modelo al lado y la cuota mínima (1/p) por debajo de la
cual no compensa apostarlo.
"""
import sys
import json
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_selecciones as S

B_FORMA = 0.5           # 0.1 puntos de nota del once -> ~5% de goles (a mano, sin calibrar)
K_ARBITRO = 10
DISPERSION = {"corners": 1.18, "amarillas": 1.67}   # de la prueba hacia delante
LINEAS = {"goles": "Total Goals 2.5", "corners": "Total Corners 9.5", "tarjetas": "Total Cards 4.5"}


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
    j = json.load(open(f"{S.CARPETA}/raw/partido_hoy_{mid}.json"))
    j = j[0] if isinstance(j, list) else j
    nombre = (j.get("referee") or {}).get("name")
    h = pd.read_csv("data/historico_partidos.csv").merge(
        pd.read_csv("data/historico_arbitro_clima.csv")[["match_id", "arbitro"]], on="match_id")
    h["tarj"] = h.l_yellow_cards + h.v_yellow_cards
    h = h[h.tarj.notna()]
    h["media_liga"] = h.groupby(["liga", "temporada"]).tarj.transform("mean")
    g = h[h.arbitro == nombre]
    if g.empty:
        return nombre, 1.0, 0
    m = g.media_liga.mean()
    return nombre, (g.tarj.sum() + K_ARBITRO * m) / (g.media_liga.sum() + K_ARBITRO * m), len(g)


def forma(notas, equipo):
    n = notas[notas.seleccion == equipo]
    o, h = n[n.once_probable], n[n.once_habitual]
    return float(o.nota.mean() - h.sel_nota_bruta.fillna(h.nota).mean()), o


def main():
    p, q, roto, sinq = S.cargar()
    eq = json.load(open(f"{S.CARPETA}/equipos.json"))
    ids = eq["equipos"]
    notas = pd.read_csv(f"{S.CARPETA}/notas_jugadores.csv")
    c = pd.read_csv(f"{S.CARPETA}/cuotas_hoy.csv")
    L = ["# Pronósticos Nations League, 26/09/2026", "",
         "Tema aparte del proyecto de ambos marcan. **Pronóstico = lo más probable según el mercado** "
         "(mediana de casas sin margen), que es lo único que nada ha batido en este proyecto. Al lado, "
         "nuestro modelo de selecciones con la nota justa de los jugadores y el árbitro. "
         "**Cuota mínima** = 1/probabilidad: por debajo no compensa.", "",
         f"Datos: {len(p)} partidos de las 4 selecciones desde 2025 (descartados {sinq} contra rivales sin "
         f"jugadores en la API y {roto} xG roto).", ""]
    for loc, vis, mid in eq["cruces"]:
        partido = f"{loc} - {vis}"
        lam = S.esperados(p, q, ["goles", "xg"], ids[loc], ids[vis])
        fl, ol = forma(notas, loc)
        fv, ov = forma(notas, vis)
        lam = (lam[0] * np.exp(B_FORMA * fl - 0.5 * B_FORMA * fv), lam[1] * np.exp(B_FORMA * fv - 0.5 * B_FORMA * fl))
        gm = S.goles(*lam)
        cor = sum(S.esperados(p[p.corners_l.notna()], q, ["corners"], ids[loc], ids[vis]))
        tar = sum(S.esperados(p[p.amarillas_l.notna()], q, ["amarillas"], ids[loc], ids[vis]))
        arb, r_arb, n_arb = arbitro(mid)
        tar_arb = tar * r_arb

        filas = []   # (categoría, apuesta, p_mercado, mediana, mejor, casas, p_modelo)
        def poner(cat, nombre_mercado, etiquetas, p_modelo):
            mk = mercado(c, partido, nombre_mercado)
            if not mk:
                return
            lado = max(mk, key=lambda l: mk[l]["p"])
            filas.append((cat, etiquetas[lado], mk[lado], p_modelo.get(lado)))
        poner("1X2", "Full Time Result", {"Home": f"gana {loc}", "Draw": "empate", "Away": f"gana {vis}"},
              {"Home": gm["1"], "Draw": gm["X"], "Away": gm["2"]})
        poner("Más/menos 2.5", "Total Goals 2.5", {"Over": "más de 2.5 goles", "Under": "menos de 2.5 goles"},
              {"Over": gm["mas_2.5"], "Under": 1 - gm["mas_2.5"]})
        poner("Ambos marcan", "Both Teams To Score", {"Yes": "ambos marcan: sí", "No": "ambos marcan: no"},
              {"Yes": gm["btts"], "No": 1 - gm["btts"]})
        for linea in ("3.5", "4.5"):
            pm = S.prob_mas(tar_arb, float(linea), DISPERSION["amarillas"])
            poner("Tarjetas", f"Total Cards {linea}", {"Over": f"más de {linea} tarjetas",
                                                       "Under": f"menos de {linea} tarjetas"},
                  {"Over": pm, "Under": 1 - pm})
        for linea in ("8.5", "9.5"):
            pm = S.prob_mas(cor, float(linea), DISPERSION["corners"])
            poner("Córners", f"Total Corners {linea}", {"Over": f"más de {linea} córners",
                                                        "Under": f"menos de {linea} córners"},
                  {"Over": pm, "Under": 1 - pm})
        poner("Goles", "Total Goals 1.5", {"Over": "más de 1.5 goles", "Under": "menos de 1.5 goles"},
              {"Over": gm["mas_1.5"], "Under": 1 - gm["mas_1.5"]})
        poner("Goles", "First Team To Score", {"Home": f"{loc} marca primero", "Away": f"{vis} marca primero"},
              {"Home": gm["primero_local"] / (1 - gm["sin_goles"]),
               "Away": gm["primero_visitante"] / (1 - gm["sin_goles"])})

        L += [f"## {partido}", "",
              f"Modelo: goles esperados {lam[0]:.2f} - {lam[1]:.2f}, marcador más probable "
              f"{gm['marcador'][0]}-{gm['marcador'][1]}. Córners esperados {cor:.1f}. Tarjetas amarillas "
              f"esperadas {tar:.1f}; árbitro {arb} ({n_arb} partidos en nuestras ligas, x{r_arb:.2f}) -> "
              f"{tar_arb:.1f}. Forma del once: {loc} {fl:+.2f}, {vis} {fv:+.2f}.", "",
              "| mercado | pronóstico | prob. mercado | prob. modelo | cuota mínima | cuota mediana | mejor cuota (sin atípicos) | casas |",
              "|---|---|---|---|---|---|---|---|"]
        for cat, apuesta, mk, pmod in filas:
            pm_txt = f"{pmod*100:.0f}%" if pmod is not None else "-"
            L.append(f"| {cat} | **{apuesta}** | {mk['p']*100:.0f}% | {pm_txt} | {1/mk['p']:.2f} | "
                     f"{mk['mediana']:.2f} | {mk['mejor']:.2f} | {mk['casas']} |")
        L += ["", f"Once {ol.fuente_once.iloc[0]} {loc}: " + ", ".join(ol.jugador),
              f"Once {ov.fuente_once.iloc[0]} {vis}: " + ", ".join(ov.jugador), ""]
        print(f"\n== {partido} ==  goles {lam[0]:.2f}-{lam[1]:.2f}  córners {cor:.1f}  "
              f"tarjetas {tar:.1f} -> {tar_arb:.1f} ({arb} x{r_arb:.2f}, n={n_arb})")
        for cat, apuesta, mk, pmod in filas:
            print(f"  {cat:14s} {apuesta:28s} mercado {mk['p']*100:4.0f}%  modelo "
                  f"{(pmod or np.nan)*100:4.0f}%  mín {1/mk['p']:.2f}  mediana {mk['mediana']:.2f}  "
                  f"mejor {mk['mejor']:.2f} ({mk['casas']} casas)")
    L += ["## Cuánto fiarse", "",
          "Prueba hacia delante del modelo de selecciones: 48 partidos desde oct-2025, cada uno pronosticado "
          "solo con los anteriores, contra la tasa de los partidos previos:", "",
          "- 1X2: +1.91s (acierta el 65%). Ambos marcan: +1.28s. Algo saben, pero no se pueden medir contra "
          "el mercado (no hay cuotas históricas de selecciones).",
          "- Más/menos goles (-0.7 a -1.2s), córners (-0.3 a -1.5s; se queda corto, 8.9 predichos contra 9.9 "
          "reales) y tarjetas (+0.1 a -2.6s): **peor que la tasa previa**. En totales, el modelo no aporta.",
          "- Tarjetas: solo 1 casa cotiza cada línea (precio poco fiable). El árbitro, en el proyecto de "
          "clubes, no mejoró el mercado de tarjetas.",
          "- Ajuste de forma (nota justa) puesto a mano. Las cuotas se cogieron a las 16:54 UTC; "
          "pueden moverse con las alineaciones.", ""]
    open("modelos/selecciones/pronosticos.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
