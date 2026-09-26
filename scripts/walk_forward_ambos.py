"""
Ambos marcan mes a mes: entrenar, probar el mes siguiente, ajustarse, seguir
(26/09/2026, petición del usuario).

"Es una IA, debe ser capaz de ajustarse a sí misma y no usar siempre las
mismas variables con el mismo peso." Evaluación de origen móvil, sin mirar
nunca al futuro. Para cada mes de prueba M (sep-2024 ... hoy):

  1. ELEGIR VARIABLES: 6 conjuntos candidatos. Cada uno se entrena con lo
     anterior a los 2 meses previos a M y se puntúa (Brier) en esos 2
     meses. Gana el mejor. Todo anterior a M.
  2. REENTRENAR el elegido con TODO lo anterior a M (máximos partidos: el
     histórico empieza en ago-2023). XGBoost reparte de nuevo el peso de
     cada variable en cada reentreno.
  3. CORREGIR FALLOS: las predicciones que el modelo ya hizo en meses de
     prueba ANTERIORES y sus resultados reales se usan para recalibrar
     (regresión logística sobre el logit de la probabilidad: si venía
     diciendo 60% y pasaba el 52%, lo baja). Solo con meses ya jugados.
  4. PREDECIR M, que nunca ha visto.

Tres brazos para separar qué ayuda:
  estático      conjunto fijo (producción + precio previo), entrenado UNA vez
                con lo anterior a sep-2024 y congelado
  reentreno     el mismo conjunto fijo, reentrenado cada mes
  adaptativo    elige conjunto cada mes + reentrena + recalibra

Precio previo = previa de Pinnacle/Betfair de football-data (días antes del
partido), nunca el cierre (ver "Casas contra el precio afinado").

Métricas: Brier por mes contra la tasa base (media de lo anterior), y en
los meses con cuotas reales de ambos marcan (ago-sep 2026) el beneficio de
apostar con la regla VE > 0 contra la mediana de casas y bet365.
"""
import sys, time
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import rasgos, modelo_xgboost as M, evaluar_mercados as EM
from apuesta_ambos_marcan import rasgos_mercado
from cuota_como_variable import MKT

PRIMER_MES = "2024-09"
MIN_PARTIDOS_MES = 20
SEMILLAS_SELECCION = (0, 1, 2)
SEMILLAS_FINAL = (0, 1, 2, 3, 4)
MIN_PARA_RECALIBRAR = 300
OBJ = "ambos_marcan"


def predecir(ent, val, cols, semillas):
    y = ent[OBJ].values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s),
                                     val[cols].values, 2)[:, 1] for s in semillas], axis=0)


def brier(p, y):
    return 2 * (p - y) ** 2


def logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def main():
    t0 = time.time()
    hist = M.cargar()
    bt = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    g = rasgos.grupos_rasgo(bt)
    prod = rasgos.columnas_rasgo_default(bt)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    bt = bt.merge(rasgos_mercado(fd, "_previa"), on="match_id", how="left")
    bt = bt[bt.goles_l.notna()].reset_index(drop=True)
    bt["mes"] = pd.to_datetime(bt.fecha, utc=True).dt.strftime("%Y-%m")
    en = lambda *gs: [c for gr in gs for c in g[gr] if c in bt.columns]
    CANDIDATOS = {
        "base+elo": en("base", "elo"),
        "produccion": prod,
        "produccion+precio": prod + MKT,
        "base+elo+precio": en("base", "elo") + MKT,
        "propio_ambos+precio": en("base", "elo", "calidad_plantilla", "arbitro", "h2h") + MKT,
        "solo precio": MKT,
    }
    FIJO = "produccion+precio"

    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if n >= MIN_PARTIDOS_MES]
    prueba = [m for m in meses if m >= PRIMER_MES]
    print(f"{len(bt)} partidos ({bt.mes.min()} a {bt.mes.max()}). Meses de prueba: {len(prueba)} "
          f"({prueba[0]} a {prueba[-1]})\n")

    ent0 = bt[bt.mes < PRIMER_MES]
    modelos_estaticos = [M.entrenar(ent0[CANDIDATOS[FIJO]].values, ent0[OBJ].values.astype(int), 2, semilla=s)
                         for s in SEMILLAS_FINAL]

    historial = []      # predicciones fuera de muestra ya jugadas (para recalibrar)
    filas = []
    for mes in prueba:
        pasado = bt[bt.mes < mes]
        test = bt[bt.mes == mes]
        y = test[OBJ].values.astype(int)
        base_rate = pasado[OBJ].mean()

        # 1. elegir conjunto en los 2 meses anteriores con datos
        previos = [m for m in meses if m < mes][-2:]
        sel = pasado[pasado.mes.isin(previos)]
        ent_sel = pasado[pasado.mes < previos[0]]
        puntos = {k: brier(predecir(ent_sel, sel, c, SEMILLAS_SELECCION), sel[OBJ].values).mean()
                  for k, c in CANDIDATOS.items()}
        elegido = min(puntos, key=puntos.get)

        # 2. reentrenar y predecir
        p_fijo = predecir(pasado, test, CANDIDATOS[FIJO], SEMILLAS_FINAL)
        p_elegido = predecir(pasado, test, CANDIDATOS[elegido], SEMILLAS_FINAL)
        p_estatico = np.mean([M.probabilidades(m, test[CANDIDATOS[FIJO]].values, 2)[:, 1]
                              for m in modelos_estaticos], axis=0)

        # 3. recalibrar con los errores de meses ya jugados
        p_adapt = p_elegido
        if len(historial) >= MIN_PARA_RECALIBRAR:
            hp = np.array([h[0] for h in historial]); hy = np.array([h[1] for h in historial])
            lr = LogisticRegression(C=1.0).fit(logit(hp).reshape(-1, 1), hy)
            p_adapt = lr.predict_proba(logit(p_elegido).reshape(-1, 1))[:, 1]
        historial += list(zip(p_elegido, y))

        b0 = brier(np.full(len(y), base_rate), y).mean()
        fila = {"mes": mes, "n": len(y), "elegido": elegido, "tasa_real": y.mean(),
                "brier_base": b0}
        for k, p in (("estatico", p_estatico), ("reentreno", p_fijo), ("adaptativo", p_adapt)):
            fila[f"mejora_{k}"] = (1 - brier(p, y).mean() / b0) * 100
        filas.append(fila)
        for k, p in (("estatico", p_estatico), ("reentreno", p_fijo), ("adaptativo", p_adapt)):
            test = test.assign(**{f"p_{k}": p})
        test.to_csv(f"/tmp/wf_{mes}.csv", index=False)
        print(f"{mes}  n={len(y):3d}  elegido={elegido:22s}  sobre la tasa base: "
              f"estático {fila['mejora_estatico']:+5.2f}%  reentreno {fila['mejora_reentreno']:+5.2f}%  "
              f"adaptativo {fila['mejora_adaptativo']:+5.2f}%   ({time.time()-t0:.0f}s)", flush=True)

    t = pd.DataFrame(filas)
    t.to_csv("data/walk_forward_ambos.csv", index=False)
    todos = pd.concat([pd.read_csv(f"/tmp/wf_{m}.csv") for m in prueba])
    y = todos[OBJ].values.astype(int)
    print("\nTOTAL (todos los meses de prueba, emparejado partido a partido):")
    for a, b in (("reentreno", "estatico"), ("adaptativo", "reentreno"), ("adaptativo", "estatico")):
        d = brier(todos[f"p_{b}"].values, y) - brier(todos[f"p_{a}"].values, y)
        print(f"  {a:10s} vs {b:10s}: {d.mean()/(d.std(ddof=1)/np.sqrt(len(d))):+.2f}s  (n={len(d)})")
    print("  conjunto elegido por mes:", t.elegido.value_counts().to_dict())

    # apuestas en los meses con cuotas reales de ambos marcan
    c = EM.cargar_cuotas_crudas()
    b_ = c[c.familia == "Both Teams To Score"]
    piv = b_.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
    piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
    precios = {"mediana de casas": piv.groupby("match_id")[["yes", "no"]].median(),
               "bet365": piv[piv.casa == "bet365"].set_index("match_id")[["yes", "no"]]}
    print("\nAPUESTAS (regla VE > 0, 1 unidad, un lado por partido):")
    for fuente, pr in precios.items():
        v = todos.merge(pr, left_on="match_id", right_index=True)
        for k in ("estatico", "reentreno", "adaptativo"):
            p = v[f"p_{k}"]; yy = v[OBJ].values
            ve_si, ve_no = p * v.yes - 1, (1 - p) * v.no - 1
            si = ve_si >= ve_no
            ve = np.where(si, ve_si, ve_no)
            ben = np.where(si, np.where(yy == 1, v.yes - 1, -1.0), np.where(yy == 0, v.no - 1, -1.0))[ve > 0]
            if len(ben) > 5:
                print(f"  {fuente:16s} {k:10s} {len(ben):3d} apuestas  real {ben.mean()*100:+6.1f}%  "
                      f"({ben.mean()/(ben.std(ddof=1)/np.sqrt(len(ben))):+.2f}s)  "
                      f"sin 5 mejores {np.sort(ben)[:-5].mean()*100:+.1f}%")
    print(f"\n({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
