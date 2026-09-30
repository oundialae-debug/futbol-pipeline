"""
El modelo de juegos en directo APRENDE de lo que se va recogiendo (30/09/2026, petición del usuario).

Cada línea de total de juegos del registro de 5 minutos (data/tenis/api_tennis/registro/) con el
partido ya terminado (resultados/) es un ejemplo: prob. del modelo, prob. de la casa (sin margen)
y si hubo más juegos que la línea. Con eso se ajusta una recalibración logística:
    p_nueva = sigmoide(a + b·logit(p_modelo) + c·logit(p_casa))
que corrige el sesgo conocido (el modelo exagera el "más") y aprende cuánto fiarse de la casa.

Disciplina (CLAUDE.md): cada partido pesa lo mismo (sus líneas y pasadas ganan y pierden juntas),
y la recalibración solo se ACTIVA si, validada por partidos que no vio (5 bloques por partido),
mejora el Brier del modelo crudo y hay al menos MIN_PARTIDOS partidos. Si no, el vigilante sigue
con el modelo crudo. Se reajusta cada hora (registro_directo.py -> evaluar_juegos.py) y el
vigilante la lee al arrancar cada ejecución. Resultado en data/tenis/api_tennis/calibracion_juegos.json.
"""
import glob
import json
import os

import numpy as np
import pandas as pd

SAL = "data/tenis/api_tennis/calibracion_juegos.json"
MIN_PARTIDOS = 30


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
    d["y"] = (d.juegos_totales.astype(float) > d.linea.astype(float)).astype(float)
    d["w"] = 1 / d.groupby("event_key").event_key.transform("size")
    return d


def _ajustar(X, y, w, l2=1.0, it=50):
    X = np.column_stack([np.ones(len(X)), X])
    b = np.zeros(X.shape[1])
    b[1] = 1.0                                         # parte de "fiarse del modelo tal cual"
    for _ in range(it):
        p = _sig(X @ b)
        g = X.T @ (w * (p - y)) + l2 * np.r_[0, b[1:] - np.r_[1, np.zeros(len(b) - 2)]]
        H = (X * (w * p * (1 - p))[:, None]).T @ X + l2 * np.diag(np.r_[0, np.ones(len(b) - 1)])
        b -= np.linalg.solve(H, g)
    return b


def _X(d):
    return np.column_stack([_logit(d.prob_modelo), _logit(d.prob_mercado)])


def ajustar():
    d = datos()
    ev = d.event_key.unique() if len(d) else []
    info = {"partidos": int(len(ev)), "filas": int(len(d)), "activo": False, "coef": None}
    if len(ev) >= 10:
        rng = np.random.default_rng(0)
        bloque = dict(zip(ev, rng.permutation(len(ev)) % 5))
        d["bloque"] = d.event_key.map(bloque)
        cal = np.zeros(len(d))
        for k in range(5):
            tr, te = (d.bloque != k).values, (d.bloque == k).values
            b = _ajustar(_X(d[tr]), d.y.values[tr], d.w.values[tr])
            cal[te] = _sig(np.column_stack([np.ones(te.sum()), _X(d[te])]) @ b)
        w = d.w.values / d.w.sum()

        def brier(p):
            return float(np.sum(w * (np.asarray(p, float) - d.y.values) ** 2))
        info["brier_modelo"] = brier(d.prob_modelo)
        info["brier_casa"] = brier(d.prob_mercado)
        info["brier_recalibrado_cv"] = brier(cal)
        info["sesgo_modelo_mas"] = float(np.sum(w * (d.prob_modelo.astype(float) - d.y.values)))
        b = _ajustar(_X(d), d.y.values, d.w.values)
        info["coef"] = [float(x) for x in b]
        info["activo"] = bool(len(ev) >= MIN_PARTIDOS and info["brier_recalibrado_cv"] < info["brier_modelo"])
    os.makedirs(os.path.dirname(SAL), exist_ok=True)
    json.dump(info, open(SAL, "w"), indent=1)
    return info


def cargar():
    try:
        return json.load(open(SAL))
    except (OSError, ValueError):
        return {"activo": False}


def aplicar(info, p_modelo, p_casa):
    """Prob. del 'más' recalibrada; si la recalibración no está activa, la del modelo tal cual."""
    if not info.get("activo") or not info.get("coef"):
        return p_modelo
    a, b, c = info["coef"]
    return float(_sig(a + b * _logit(p_modelo) + c * _logit(p_casa)))


if __name__ == "__main__":
    print(ajustar())
