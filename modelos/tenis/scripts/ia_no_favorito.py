"""
¿Puede una IA predecir CUÁNDO el no favorito gana más de lo que paga bet365? (10/10/2026, usuario:
"ajustar la IA para que prediga cuándo se equivoca la casa y apostar con Stake medido").
bet365 hace de casa blanda parecida a Stake. tennis-data 2020-2025, ATP+WTA, cierre (B365 y Pinnacle).

Prueba limpia, por años: para cada año Y (2021-2025), la IA se entrena SOLO con los años anteriores y
apuesta en papel en Y. Una apuesta por partido, al no favorito de bet365, a cuota de bet365, si
p_IA × cuota − 1 > umbral. Variables (todas conocidas antes del partido): prob. sin margen de bet365 y de
Pinnacle del no favorito y su diferencia, mejor cuota del mercado / bet365, ranking y puntos de ambos,
superficie, nivel, ronda, al mejor de 5, WTA. Controles: siempre al no favorito, y "Pinnacle dice que bet365
paga de más" sin IA. Retiradas: gana quien avanza (como liquidan casi todas); walkovers fuera.
Escribe data/tenis/ia_no_favorito.md.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, "modelos/tenis/scripts")
import cruce_fuentes as C  # noqa: E402

SAL = "data/tenis/ia_no_favorito.md"
NIVEL = {"Grand Slam": 3, "Masters 1000": 2, "Masters Cup": 2, "ATP500": 1, "ATP250": 0,
         "WTA1000": 2, "WTA500": 1, "WTA250": 0, "Tour Championships": 2}
RONDA = {"1st Round": 1, "2nd Round": 2, "3rd Round": 3, "4th Round": 4, "Quarterfinals": 5, "Semifinals": 6,
         "The Final": 7, "Round Robin": 4}


def datos():
    partes = []
    for circ in ("atp", "wta"):
        t = C.cargar_td(circ)
        t = t[~t.Comment.astype(str).str.contains("Walkover|w/o", case=False)]
        for c in ("B365W", "B365L", "PSW", "PSL", "MaxW", "MaxL", "WRank", "LRank", "WPts", "LPts"):
            t[c] = pd.to_numeric(t[c], errors="coerce")
        t = t.dropna(subset=["B365W", "B365L", "PSW", "PSL"])
        t = t[(t.B365W > 1) & (t.B365L > 1) & (t.PSW > 1) & (t.PSL > 1)]
        ud_es_ganador = t.B365W > t.B365L                 # el no favorito de bet365 ganó
        g = lambda a, b: np.where(ud_es_ganador, t[a], t[b])  # noqa: E731  (dato del no favorito)
        f = lambda a, b: np.where(ud_es_ganador, t[b], t[a])  # noqa: E731  (dato del favorito)
        d = pd.DataFrame({"anio": t.Date.astype(str).str[:4].astype(int), "y": ud_es_ganador.astype(int),
                          "c_ud": g("B365W", "B365L"), "c_fav": f("B365W", "B365L"),
                          "ps_ud": g("PSW", "PSL"), "ps_fav": f("PSW", "PSL"),
                          "max_ud": g("MaxW", "MaxL"), "rk_ud": g("WRank", "LRank"), "rk_fav": f("WRank", "LRank"),
                          "pt_ud": g("WPts", "LPts"), "pt_fav": f("WPts", "LPts"),
                          "sup": t.Surface.astype(str), "nivel": t.get("Series", t.get("Tier")).map(NIVEL),
                          "ronda": t.Round.map(RONDA), "bo5": (pd.to_numeric(t["Best of"], errors="coerce") == 5).astype(int),
                          "wta": int(circ == "wta")})
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    d["p365"] = (1 / d.c_ud) / (1 / d.c_ud + 1 / d.c_fav)
    d["pps"] = (1 / d.ps_ud) / (1 / d.ps_ud + 1 / d.ps_fav)
    d["dif_ps"] = d.pps - d.p365
    d["max_rel"] = d.max_ud / d.c_ud
    d["log_rk"] = np.log(d.rk_ud.clip(1)) - np.log(d.rk_fav.clip(1))
    d["log_pt"] = np.log(d.pt_ud.clip(1)) - np.log(d.pt_fav.clip(1))
    for s in ("Hard", "Clay", "Grass"):
        d[f"sup_{s}"] = (d.sup == s).astype(int)
    return d


X = ["p365", "pps", "dif_ps", "max_rel", "log_rk", "log_pt", "sup_Hard", "sup_Clay", "sup_Grass", "nivel", "ronda",
     "bo5", "wta"]


def resumen(nombre, g):
    if len(g) < 2:
        return f"| {nombre} | {len(g)} | | | | |"
    b = np.where(g.y == 1, g.c_ud - 1, -1.0)
    return (f"| {nombre} | {len(g)} | {g.y.mean():.1%} | {np.mean(1 / g.c_ud):.1%} | {b.mean():+.1%} | "
            f"{b.mean() / (b.std(ddof=1) / np.sqrt(len(b))):+.2f} |")


def main():
    d = datos()
    pruebas = []
    for y in range(2021, 2026):
        tr, te = d[d.anio < y], d[d.anio == y].copy()
        m = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, l2_regularization=1.0,
                                           min_samples_leaf=200, random_state=0).fit(tr[X], tr.y)
        te["p_ia"] = m.predict_proba(te[X])[:, 1]
        pruebas.append(te)
    t = pd.concat(pruebas)
    t["ve"] = t.p_ia * t.c_ud - 1
    t["ve_ps"] = t.pps * t.c_ud - 1
    lin = ["# IA para el no favorito contra bet365 (tennis-data, por años: aprende con los anteriores)\n",
           f"{len(t):,} partidos de prueba (2021-2025, ATP+WTA). Una apuesta por partido al no favorito, cuota de bet365 al cierre.\n",
           "| regla | apuestas | aciertos | hace falta | beneficio | sigmas |", "|---|---|---|---|---|---|",
           resumen("siempre al no favorito (control)", t),
           resumen("Pinnacle dice que bet365 paga de más (sin IA)", t[t.ve_ps > 0]),
           resumen("IA: valor > 0%", t[t.ve > 0]),
           resumen("IA: valor > 3%", t[t.ve > .03]),
           resumen("IA: valor > 8%", t[t.ve > .08])]
    lin += ["", "IA con valor > 3%, año a año:", "", "| año | apuestas | aciertos | hace falta | beneficio | sigmas |",
            "|---|---|---|---|---|---|"]
    for y, g in t[t.ve > .03].groupby("anio"):
        lin.append(resumen(str(y), g))
    lin += ["", "Calibración de la IA en prueba (no favorito):", "", "| la IA dice | pasa | bet365 dice | partidos |", "|---|---|---|---|"]
    t["tramo"] = pd.cut(t.p_ia, [0, .15, .25, .35, .45, .55])
    for k, g in t.groupby("tramo", observed=True):
        lin.append(f"| {k} | {g.y.mean():.1%} | {g.p365.mean():.1%} | {len(g)} |")
    open(SAL, "w").write("\n".join(lin) + "\n")
    print("\n".join(lin))


if __name__ == "__main__":
    main()
