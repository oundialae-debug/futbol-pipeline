"""
El modelo de juegos en directo APRENDE de todo lo recogido (30/09-01/10/2026, petición del usuario).

Cada línea de total de juegos del registro de 5 minutos con el partido ya terminado es un ejemplo.
Variables: la casa (prob. sin margen), el modelo de siempre, el modelo "con el saque de hoy", cuántos
juegos faltan hasta la línea ((línea − jugados)/10) y el nivel (ITF, Challenger/125, WTA).
    p = sig(a + b·logit(casa) + c·logit(modelo) + d·logit(directo) + e·faltan + f·itf + g·chall + h·wta)

Lección del 01/10: la primera versión (sin la casa como punto de partida) aprendió "todo es menos",
avisó 101 veces en un día y acertó lo mismo que ya decía la casa (61% vs 60%, −5,5%). Ahora:
- el punto de partida es FIARSE DE LA CASA (b=1, el resto 0) y la regularización tira hacia ahí:
  solo se aparta de la casa si los datos lo sostienen;
- cada partido pesa igual (sus líneas y pasadas ganan y pierden juntas);
- se mide como se usaría: por DÍAS (walk_forward): para cada día, se aprende solo con los días
  anteriores y se "apuesta" en papel donde lo aprendido se separa de la casa >= UMBRAL.
Resultado en data/tenis/api_tennis/calibracion_juegos.json; el vigilante lo lee al arrancar.
"""
import glob
import json
import os

import numpy as np
import pandas as pd

SAL = "data/tenis/api_tennis/calibracion_juegos.json"
MIN_PARTIDOS = 30
UMBRAL = 0.05
NOMBRES = ["const", "casa", "modelo", "directo", "faltan", "itf", "challenger", "wta"]


def _logit(p):
    p = np.clip(np.asarray(p, float), 0.01, 0.99)
    return np.log(p / (1 - p))


def _sig(z):
    return 1 / (1 + np.exp(-z))


def datos():
    regs = [pd.read_csv(f) for f in sorted(glob.glob("data/tenis/api_tennis/registro/*.csv"))]
    res = [pd.read_csv(f) for f in sorted(glob.glob("data/tenis/api_tennis/resultados/*.csv"))]
    if not regs or not res:
        return pd.DataFrame()
    res = pd.concat(res).drop_duplicates("event_key", keep="last")
    res = res[res.estado == "Finished"]
    d = pd.concat(regs)
    d = d[d.mercado == "total_juegos"].dropna(subset=["prob_mercado", "prob_modelo"])
    d = d.merge(res[["event_key", "juegos_totales"]], on="event_key")
    d = d.dropna(subset=["juegos_totales"])
    for c in ("prob_modelo_directo", "jugados", "saque_tot1", "saque_tot2"):
        if c not in d:
            d[c] = np.nan
    d["prob_modelo_directo"] = d.prob_modelo_directo.fillna(d.prob_modelo)
    # juegos ya jugados: columna propia desde el 01/10; antes, estimados por los puntos al saque (~6,2 por juego)
    d["jugados"] = pd.to_numeric(d.jugados, errors="coerce").fillna(
        (pd.to_numeric(d.saque_tot1, errors="coerce") + pd.to_numeric(d.saque_tot2, errors="coerce")) / 6.2)
    d = d.dropna(subset=["jugados"])
    d["linea"] = d.linea.astype(float)
    d["y"] = (d.juegos_totales.astype(float) > d.linea).astype(float)
    d["w"] = 1 / d.groupby("event_key").event_key.transform("size")
    d["dia"] = d.hora.astype(str).str[:10]
    return d


def X(d):
    t = d.tipo.astype(str).str.lower()
    return np.column_stack([_logit(d.prob_mercado), _logit(d.prob_modelo), _logit(d.prob_modelo_directo),
                            (d.linea.astype(float) - d.jugados.astype(float)) / 10,
                            t.str.contains("itf").astype(float), t.str.contains("challenger").astype(float),
                            (t.str.contains("wta") | t.str.contains("women")).astype(float)])


PREVIA = np.array([0, 1, 0, 0, 0, 0, 0, 0], float)     # punto de partida: la casa tal cual


def _ajustar(Xm, y, w, l2=2.0, it=60):
    Xm = np.column_stack([np.ones(len(Xm)), Xm])
    b = PREVIA.copy()
    R = l2 * np.diag(np.r_[0.0, np.ones(len(b) - 1)])
    for _ in range(it):
        p = _sig(Xm @ b)
        g = Xm.T @ (w * (p - y)) + R @ (b - PREVIA)
        H = (Xm * (w * p * (1 - p))[:, None]).T @ Xm + R
        b -= np.linalg.solve(H, g)
    return b


def _pred(b, d):
    return _sig(np.column_stack([np.ones(len(d)), X(d)]) @ b)


def walk_forward(d):
    """Apuestas en papel día a día: se aprende con los días anteriores; en el día siguiente, en la línea
    principal de cada partido (la más cercana al 50%), PRIMERA pasada en que lo aprendido se separa de la
    casa >= UMBRAL, se apuesta ese lado a la cuota de la API. Un partido, una apuesta."""
    out = []
    dias = sorted(d.dia.unique())
    for i, dia in enumerate(dias[1:], 1):
        tr, te = d[d.dia < dia], d[d.dia == dia].copy()
        if tr.event_key.nunique() < MIN_PARTIDOS or te.empty:
            continue
        b = _ajustar(X(tr), tr.y.values, tr.w.values)
        te["p"] = _pred(b, te)
        te["dist"] = (te.prob_mercado.astype(float) - 0.5).abs()
        te = te.sort_values(["hora", "dist"]).groupby(["hora", "event_key"]).head(1)
        te["dif"] = te.p - te.prob_mercado.astype(float)
        sen = te[te.dif.abs() >= UMBRAL].sort_values("hora").groupby("event_key").head(1)
        for r in sen.itertuples():
            mas = r.dif > 0
            cuota = float(r.cuota if mas else r.cuota_rival)
            gana = (r.juegos_totales > r.linea) if mas else (r.juegos_totales < r.linea)
            out.append({"dia": dia, "event_key": r.event_key, "lado": "más" if mas else "menos", "cuota": cuota,
                        "p_aprendida": r.p if mas else 1 - r.p, "p_casa": r.prob_mercado if mas else 1 - r.prob_mercado,
                        "gana": bool(gana), "benef": cuota - 1 if gana else -1.0})
    return pd.DataFrame(out)


def ajustar():
    d = datos()
    ev = d.event_key.unique() if len(d) else []
    info = {"partidos": int(len(ev)), "filas": int(len(d)), "activo": False, "coef": None, "variables": NOMBRES}
    if len(ev) >= 10:
        rng = np.random.default_rng(0)
        bloque = dict(zip(ev, rng.permutation(len(ev)) % 5))
        d["bloque"] = d.event_key.map(bloque)
        cal = np.zeros(len(d))
        for k in range(5):
            tr, te = (d.bloque != k).values, (d.bloque == k).values
            b = _ajustar(X(d[tr]), d.y.values[tr], d.w.values[tr])
            cal[te] = _pred(b, d[te])
        w = d.w.values / d.w.sum()

        def brier(p):
            return float(np.sum(w * (np.asarray(p, float) - d.y.values) ** 2))
        info["brier_modelo"] = brier(d.prob_modelo)
        info["brier_casa"] = brier(d.prob_mercado)
        info["brier_modelo_directo"] = brier(d.prob_modelo_directo)
        info["brier_recalibrado_cv"] = brier(cal)
        info["sesgo_modelo_mas"] = float(np.sum(w * (d.prob_modelo.astype(float) - d.y.values)))
        b = _ajustar(X(d), d.y.values, d.w.values)
        info["coef"] = [float(x) for x in b]
        info["activo"] = bool(len(ev) >= MIN_PARTIDOS and info["brier_recalibrado_cv"] < info["brier_casa"])
        wf = walk_forward(d)
        if len(wf):
            info["papel_por_dias"] = {"apuestas": int(len(wf)), "aciertos": float(wf.gana.mean()),
                                      "beneficio_medio": float(wf.benef.mean()),
                                      "sigmas": float(wf.benef.mean() / (wf.benef.std(ddof=1) / np.sqrt(len(wf))))
                                      if len(wf) > 1 else None}
    os.makedirs(os.path.dirname(SAL), exist_ok=True)
    json.dump(info, open(SAL, "w"), indent=1)
    return info


def cargar():
    try:
        return json.load(open(SAL))
    except (OSError, ValueError):
        return {"activo": False}


def aplicar(info, fila):
    """Prob. aprendida del 'más' para una línea (fila: dict con prob_mercado, prob_modelo,
    prob_modelo_directo, linea, jugados, tipo). Sin coeficientes válidos: la casa tal cual."""
    if not info.get("coef") or len(info["coef"]) != len(NOMBRES):
        return float(fila["prob_mercado"])
    return float(_pred(np.array(info["coef"]), pd.DataFrame([fila]))[0])


if __name__ == "__main__":
    print(json.dumps(ajustar(), indent=1))
