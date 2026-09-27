"""
Modelo propio para el mercado SIN EMPATE (Draw No Bet = Asian Handicap 0) de
selecciones (27/09/2026). Tema aparte del proyecto de ambos marcan.

Petición del usuario: reentrenar con partidos anteriores SOLO para "gana o
pierde sin empate", sin tocar cómo se pronostican los demás mercados.

Sin empate se decide solo entre los partidos que NO acaban en empate (si hay
empate se devuelve la apuesta). Así que se entrena solo con esos:

  P(gana el local | no empate) = sigmoide(fuerza_A - fuerza_B + casa*h + b*(calidad_A - calidad_B))

Bradley-Terry con encogimiento ridge (C), peso por recencia (vida media 365
días, la misma que el modelo de goles) y la misma "calidad" de plantilla.
Los partidos contra rivales sin jugadores en la API se descartan igual que en
modelo_selecciones.cargar().

La alternativa, que es lo que salía hasta hoy si se pedía, es DERIVARLO del
modelo de goles: P1 / (P1 + P2) del Poisson. `python3 sin_empate.py` hace la
prueba hacia delante de las dos (cada partido solo con los anteriores) contra
la tasa base, y escribe modelos/selecciones/sin_empate.md.
"""
import sys
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, "modelos/selecciones")
import modelo_selecciones as S

C_RIDGE = 1.0          # fijado ANTES de mirar la prueba; 0.3 y 3 se enseñan como control
DESDE = "2025-10-01"   # mismo inicio que la prueba hacia delante del modelo de goles
SALIDA = "modelos/selecciones/sin_empate.md"
warnings.filterwarnings("ignore")


def ajustar_sin_empate(p, q, C=C_RIDGE):
    """p: partidos de cargar() (con w). Devuelve f(local, visitante, casa) -> P(gana local | no empate)."""
    d = p[p.goles_l != p.goles_v]
    equipos = sorted(set(d.local_id) | set(d.visitante_id))
    idx = {t: i for i, t in enumerate(equipos)}
    n = len(idx)

    def matriz(loc, vis, casa):
        X = np.zeros((len(loc), n + 2))
        for k, (a, b) in enumerate(zip(loc, vis)):
            if a in idx:
                X[k, idx[a]] = 1
            if b in idx:
                X[k, idx[b]] = -1
        X[:, n] = casa
        X[:, n + 1] = [10 * (q.get(a, 0) - q.get(b, 0)) for a, b in zip(loc, vis)]
        return X

    y = (d.goles_l > d.goles_v).astype(int)
    m = LogisticRegression(C=C, fit_intercept=False, max_iter=5000)
    m.fit(matriz(d.local_id, d.visitante_id, d.casa), y, sample_weight=d.w)
    return lambda loc, vis, casa: float(m.predict_proba(matriz([loc], [vis], [casa]))[0, 1])


def derivado_goles(f_gol, loc, vis, casa, am):
    lam = (np.mean([f(loc, vis, casa, am) for f in f_gol]), np.mean([f(vis, loc, 0.0, am) for f in f_gol]))
    g = S.goles(*lam)
    return g["1"] / (g["1"] + g["2"])


def prueba(p, q):
    filas = []
    for f in sorted(p.fecha[p.fecha >= DESDE].unique()):
        ent = p[p.fecha < f].copy()
        ent["w"] = 0.5 ** ((pd.Timestamp(f) - pd.to_datetime(ent.fecha)).dt.days / S.VIDA_MEDIA)
        hoy = p[(p.fecha == f) & (p.goles_l != p.goles_v)]
        if hoy.empty:
            continue
        f_gol = [S.ajustar(ent[ent[f"{o}_l"].notna()], q, o) for o in ("goles", "xg")]
        fs = {C: ajustar_sin_empate(ent, q, C) for C in (0.3, C_RIDGE, 3.0)}
        ne = ent[ent.goles_l != ent.goles_v]
        base_casa = np.average(ne.goles_l > ne.goles_v, weights=ne.w)   # sin empate, gana el de casa
        for _, r in hoy.iterrows():
            fila = {"match_id": r.match_id, "fecha": f, "local": r.local, "visitante": r.visitante,
                    "y": float(r.goles_l > r.goles_v), "casa": r.casa,
                    "derivado": derivado_goles(f_gol, r.local_id, r.visitante_id, r.casa, r.amistoso),
                    "base": base_casa if r.casa else 0.5}
            for C, g in fs.items():
                fila[f"propio_C{C}"] = g(r.local_id, r.visitante_id, r.casa)
            filas.append(fila)
    return pd.DataFrame(filas)


def sigmas(a, b, y):
    """+ = a mejor que b (Brier), emparejado por partido."""
    dif = (b - y) ** 2 - (a - y) ** 2
    return dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif)))


def main():
    p, q, _, _ = S.cargar()
    t = prueba(p, q)
    t.to_csv("data/selecciones/sin_empate_prueba.csv", index=False)
    y = t.y.values
    cols = ["derivado"] + [c for c in t if c.startswith("propio_")] + ["base"]
    brier = {c: ((t[c] - y) ** 2).mean() for c in cols}
    acierto = {c: ((t[c] > 0.5) == (y == 1)).mean() for c in cols}
    elegido = f"propio_C{C_RIDGE}"
    L = ["# Sin empate (Draw No Bet): modelo propio contra el derivado del modelo de goles", "",
         f"Prueba hacia delante: {len(t)} partidos SIN empate desde {DESDE}, cada uno pronosticado solo con "
         "los anteriores (los empates no cuentan: en este mercado se devuelve la apuesta). Brier: más bajo "
         "es mejor. Sigmas emparejadas por partido; hace falta +2 para creérselo.", "",
         "| modelo | Brier | acierto | contra el derivado | contra la tasa base |", "|---|---|---|---|---|"]
    for c in cols:
        s_d = "-" if c == "derivado" else f"{sigmas(t[c].values, t.derivado.values, y):+.2f}s"
        s_b = "-" if c == "base" else f"{sigmas(t[c].values, t.base.values, y):+.2f}s"
        if c == "derivado":
            nombre = "derivado del modelo de goles (P1/(P1+P2))"
        elif c == "base":
            nombre = "tasa base (sin empate, gana el de casa)"
        else:
            nombre = f"propio, ridge C={c.split('C')[1]}" + (" (el elegido de antemano)" if c == elegido else " (control)")
        L.append(f"| {nombre} | {brier[c]:.4f} | {acierto[c]:.0%} | {s_d} | {s_b} |")
    L += ["", "Por tramos de tiempo (Brier, propio elegido contra derivado):", "",
          "| tramo | n | propio | derivado |", "|---|---|---|---|"]
    t["tramo"] = pd.to_datetime(t.fecha).dt.to_period("Q").astype(str)
    for tr, g in t.groupby("tramo"):
        L.append(f"| {tr} | {len(g)} | {((g[elegido]-g.y)**2).mean():.4f} | {((g.derivado-g.y)**2).mean():.4f} |")
    open(SALIDA, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
