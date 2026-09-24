"""
Combo vs produccion, partido a partido, en los MISMOS partidos.

El barrido de 42 combinaciones (experimentos_combinaciones.py) compara cada
combo contra el MERCADO. Para saber si un combo es mejor que la PRODUCCION
hace falta la diferencia emparejada de Brier entre los dos modelos sobre
los mismos partidos de validacion -- y cuidado con elegir el mejor de 42:
el mejor de 42 siempre parece bueno por azar. Por eso se miran los 5 mejores
de la submuestra de localia, no solo el primero.
"""
import sys
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd

# reutiliza la construccion de las 6 variables del barrido (todo lo anterior al bucle)
fuente = open('scripts/experimentos_combinaciones.py', encoding='utf-8').read()
exec(fuente.split('print(f"Carga y preparacion')[0])

cfgm = EM.MERCADOS['ambos_marcan']
pmer_todos = EM.mercado_por_partido(cuotas, cfgm)
nucleo = sum((grupos[g] for g in ['base','elo']), [])
prod_sin_arb = sum((grupos[g] for g in ['h2h','h2h_profundo','tabla','calidad_plantilla']), [])

CONFIGS = {
    'produccion (arbitro original)': nucleo + prod,
    'arb_v20+h2h_rec+tabla_goles+localia': nucleo + prod_sin_arb + VARS[1]+VARS[2]+VARS[3]+VARS[5],
    'arb_v20+h2h_rec+localia': nucleo + prod_sin_arb + VARS[1]+VARS[2]+VARS[5],
    'arb_v20+h2h_rec+tabla_goles+localia+mom5': nucleo + prod_sin_arb + VARS[1]+VARS[2]+VARS[3]+VARS[5]+VARS[6],
    'arb_v20+tabla_goles+localia+mom5': nucleo + prod_sin_arb + VARS[1]+VARS[3]+VARS[5]+VARS[6],
    'arb_v20+tabla_goles+localia': nucleo + prod_sin_arb + VARS[1]+VARS[3]+VARS[5],
}

todas = sorted(set(sum(CONFIGS.values(), [])))
base = bc[bc[todas].notna().all(axis=1)].sort_values('fecha').reset_index(drop=True)
corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
ent = base.iloc[:corte]
fecha_corte = pd.to_datetime(ent.fecha.max())
# Dos validaciones distintas, cada una con su muestra correcta:
# - combo vs PRODUCCION no necesita cuota -> todos los partidos de validacion
# - modelo vs MERCADO solo donde hay cuota (cosecha desde el 24/08/2026)
val = base[pd.to_datetime(base.fecha) > fecha_corte]
con_cuota = val.match_id.isin(pmer_todos.index).values
y = val['ambos_marcan'].values.astype(int)
y_ent = ent['ambos_marcan'].values.astype(int)
print(f"{len(base)} partidos, mismos para todas las configs. Validacion: {len(val)} "
      f"(de ellos {con_cuota.sum()} con cuota)\n")

b_mercado = 2 * (pmer_todos.loc[val.match_id[con_cuota]].values - y[con_cuota]) ** 2
b = {}
for nombre, cols in CONFIGS.items():
    preds = []
    for s in EM.SEMILLAS:
        m = M.entrenar(ent[cols].values, y_ent, 2, semilla=s)
        preds.append(M.probabilidades(m, val[cols].values, 2)[:, 1])
    b[nombre] = 2 * (np.mean(preds, axis=0) - y) ** 2

def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))

ref = b['produccion (arbitro original)']
print(f"{'config':45s} {'vs produccion':>14s} {'vs mercado':>11s}")
for nombre, bb in b.items():
    vs_prod = sig(ref - bb) if nombre != 'produccion (arbitro original)' else 0.0
    vs_merc = sig(b_mercado - bb[con_cuota])
    print(f"{nombre:45s} {vs_prod:+13.2f}s {vs_merc:+10.2f}s")
