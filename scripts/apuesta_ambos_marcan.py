"""
¿Se gana DINERO apostando a ambos marcan con el mejor modelo? (26/09/2026)

El +1.32s de cuota_como_variable.py mide Brier contra el precio SIN margen.
Apostar es otra cosa: se cobra con cuotas CON margen (5-7% en ambos marcan),
y el modelo usaba el precio de CIERRE de Pinnacle/Betfair, que no se conoce
al apostar (la trampa de casas_contra_cierre.py: +16% contra el cierre,
-1.2% contra la previa).

Versión honesta:
  - rasgos de mercado de la PREVIA de football-data (Pinnacle/Betfair días
    antes del partido), incluido el ambos marcan implícito recalculado sobre
    esa previa. Nada del cierre.
  - modelo = producción + esos 7 rasgos, entrenamiento con huecos (M.partir),
    5 semillas.
  - apuestas contra las cuotas REALES de ambos marcan cosechadas de las
    casas (31 casas, 219 partidos de validación con cuota).
  - regla: se apuesta 1 unidad al lado (sí/no) con p_modelo x cuota - 1 >
    umbral. Como mucho una apuesta por partido.
  - tres formas de elegir cuota: mejor cuota entre casas (optimista: puede
    ser una foto vieja), mediana entre casas (realista), una sola casa grande
    (bet365).
Beneficio real, error por partido, y sin los k partidos que más aportan.
Además, el control: el mismo modelo con el CIERRE (para ver cuánto del
número venía de mirar al futuro).
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM
from btts_implicito import ajustar
from cuota_como_variable import MKT, predecir

UMBRALES = (0.0, 0.02, 0.05, 0.10)
CASA_UNICA = "bet365"


def rasgos_mercado(fd, sufijo):
    """Los 7 rasgos mkt_ a partir del cierre (sufijo '') o de la previa ('_previa')."""
    d = pd.DataFrame({"match_id": fd.match_id,
                      "mkt_p_local": fd["p_local" + sufijo],
                      "mkt_p_empate": fd["p_empate" + sufijo],
                      "mkt_p_visitante": fd["p_visitante" + sufijo],
                      "mkt_p_mas_2_5": fd["p_mas_2_5" + sufijo]})
    if sufijo == "":
        d["mkt_lambda_l"], d["mkt_lambda_v"] = fd.lambda_l, fd.lambda_v
    else:
        lam = [ajustar(a, b, c, e) if not np.isnan([a, b, c]).any() else (np.nan, np.nan)
               for a, b, c, e in zip(d.mkt_p_local, d.mkt_p_empate, d.mkt_p_visitante, d.mkt_p_mas_2_5)]
        d["mkt_lambda_l"], d["mkt_lambda_v"] = zip(*lam)
    d["mkt_p_btts_implicito"] = (1 - np.exp(-d.mkt_lambda_l)) * (1 - np.exp(-d.mkt_lambda_v))
    return d


def resumen(ap, etiqueta):
    if ap.empty:
        print(f"    {etiqueta:34s} sin apuestas")
        return
    roi = ap.beneficio.mean()
    ee = ap.beneficio.std(ddof=1) / np.sqrt(len(ap))       # 1 apuesta por partido
    orden = ap.beneficio.sort_values(ascending=False)
    sin = "  ".join(f"sin {k}: {orden.iloc[k:].mean()*100:+.1f}%" for k in (1, 3, 5) if len(orden) > k + 5)
    print(f"    {etiqueta:34s} {len(ap):3d} apuestas  VE medio {ap.ve.mean()*100:+5.1f}%  "
          f"real {roi*100:+6.1f}% ({roi/ee:+.2f}s)  | {sin}")


def main():
    hist = M.cargar()
    base_todo = rasgos.construir(hist).sort_values("fecha").reset_index(drop=True)
    prod = rasgos.columnas_rasgo_default(base_todo)
    fd = pd.read_csv("data/cuotas_historicas_fd.csv")
    cuotas = EM.cargar_cuotas_crudas()
    b = cuotas[cuotas.familia == "Both Teams To Score"]
    piv = b.pivot_table(index=["match_id", "casa"], columns="lado", values="cuota", aggfunc="last").dropna()
    piv = piv[(piv.yes > 1) & (piv.no > 1)].reset_index()
    precios = {
        "mejor cuota": piv.groupby("match_id")[["yes", "no"]].max(),
        "mediana de casas": piv.groupby("match_id")[["yes", "no"]].median(),
        CASA_UNICA: piv[piv.casa == CASA_UNICA].set_index("match_id")[["yes", "no"]],
    }
    margen = (1 / piv.yes + 1 / piv.no - 1).mean()
    print(f"Ambos marcan cosechado: {piv.match_id.nunique()} partidos, {piv.casa.nunique()} casas, "
          f"margen medio {margen*100:.1f}%\n")

    for sufijo, nombre in (("_previa", "PREVIA (lo que se sabe al apostar)"),
                           ("", "CIERRE (control: mira al futuro)")):
        bt = base_todo.merge(rasgos_mercado(fd, sufijo), on="match_id", how="left")
        cols = prod + MKT
        base, ent, fecha_corte = M.partir(bt, prod)
        ent = ent[ent[M.ORIGEN_OBJETIVO["ambos_marcan"]].notna()]
        val = base[(pd.to_datetime(base.fecha) > fecha_corte) & base.match_id.isin(precios["mediana de casas"].index)]
        p = predecir(ent, val, cols, "ambos_marcan", 2)
        y = val.ambos_marcan.values.astype(int)
        print(f"== Modelo con precio de la {nombre}: {len(val)} partidos con cuota ==")
        for fuente, pr in precios.items():
            v = val.assign(p=p, y=y).merge(pr, left_on="match_id", right_index=True)
            ve_si = v.p * v.yes - 1
            ve_no = (1 - v.p) * v.no - 1
            lado_si = ve_si >= ve_no
            v = v.assign(ve=np.where(lado_si, ve_si, ve_no),
                         beneficio=np.where(lado_si, np.where(v.y == 1, v.yes - 1, -1.0),
                                            np.where(v.y == 0, v.no - 1, -1.0)))
            print(f"  cuota: {fuente} ({len(v)} partidos)")
            for u in UMBRALES:
                resumen(v[v.ve > u], f"apostar si VE > {u*100:.0f}%")
        # control del signo con un caso concreto
        ej = val.assign(p=p).merge(precios["mediana de casas"], left_on="match_id", right_index=True).iloc[0]
        print(f"  (signo: p_modelo(sí)={ej.p:.3f}, cuota sí {ej.yes:.2f} -> VE sí "
              f"{(ej.p*ej.yes-1)*100:+.1f}%; justa sería {1/ej.p:.2f})\n")


if __name__ == "__main__":
    main()
