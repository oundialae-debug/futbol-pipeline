"""
Selección de variables SOLO para ambos_marcan + prueba final limpia.

Dos problemas detectados el 24/09 (ver CLAUDE.md, "Aviso de contaminación"):
  1. El conjunto de producción se eligió por la suma de los 5 mercados --
     un compromiso que, por ejemplo, empeora tarjetas. Aquí se elige solo
     por el Brier de ambos_marcan.
  2. Toda la sesión midió contra los MISMOS partidos (posteriores al
     24/04/2026). Elegir repetidamente el mejor sobre ellos infla el
     resultado.

Tres tramos por fecha, sobre un conjunto FIJO de partidos (los que tienen
todas las candidatas, para que ninguna comparación cruce muestras):
  - entrenamiento: lo más antiguo
  - selección: el último 25% ANTES del 24/04 -- en toda la sesión solo se
    usó para entrenar, nunca para evaluar
  - prueba final: DESPUÉS del 24/04 -- la selección no lo ve; se mira una
    sola vez, al final, reentrenando con entrenamiento+selección

Selección hacia delante: se parte de base+Elo y en cada paso se añade el
grupo que más baja el Brier medio en el tramo de selección. Se para
cuando ninguno lo baja.

Contaminación residual que NO se puede quitar con partidos ya jugados: la
LISTA de candidatas se construyó el 24/09 mirando resultados posteriores
al 24/04. La elección entre ellas sí es limpia; la lista, no del todo.
"""
import sys, time
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd

t0 = time.time()
fuente = open('scripts/experimentos_combinaciones.py', encoding='utf-8').read()
exec(fuente.split('print(f"Carga y preparacion')[0])

bc['poisson_lambda_local'] = (bc['loc_m_goles'] + bc['vis_m_goles_contra']) / 2
bc['poisson_lambda_visit'] = (bc['vis_m_goles'] + bc['loc_m_goles_contra']) / 2
bc['poisson_p_btts'] = ((1 - np.exp(-bc['poisson_lambda_local'].clip(lower=0))) *
                        (1 - np.exp(-bc['poisson_lambda_visit'].clip(lower=0))))

NUCLEO = grupos['base'] + grupos['elo']
CANDIDATAS = {
    'arbitro': grupos['arbitro'], 'h2h': grupos['h2h'], 'h2h_profundo': grupos['h2h_profundo'],
    'tabla': grupos['tabla'], 'calidad_plantilla': grupos['calidad_plantilla'],
    'btts': grupos['btts'], 'rotacion': grupos['rotacion'], 'forma_reciente': grupos['forma_reciente'],
    'poisson': ['poisson_lambda_local', 'poisson_lambda_visit', 'poisson_p_btts'],
    **{NOMBRES[v]: VARS[v] for v in range(1, 7)},
}
PRODUCCION = ['arbitro', 'h2h', 'h2h_profundo', 'tabla', 'calidad_plantilla']
CORTE_PRUEBA = pd.Timestamp('2026-04-24', tz='UTC')   # la validación usada toda la sesión empieza aquí

todas = NUCLEO + sum(CANDIDATAS.values(), [])
base = bc[bc[todas].notna().all(axis=1)].reset_index(drop=True)    # bc ya viene ordenado por fecha
fechas = pd.to_datetime(base.fecha, utc=True)
antes = base[fechas <= CORTE_PRUEBA]
prueba = base[fechas > CORTE_PRUEBA]
n_sel = int(len(antes) * 0.25)
ent, sel = antes.iloc[:-n_sel], antes.iloc[-n_sel:]
print(f"{len(base)} partidos con todas las candidatas (sin clima).")
print(f"  entrenamiento {len(ent)} ({str(ent.fecha.min())[:10]} a {str(ent.fecha.max())[:10]})")
print(f"  selección     {len(sel)} ({str(sel.fecha.min())[:10]} a {str(sel.fecha.max())[:10]})")
print(f"  prueba final  {len(prueba)} ({str(prueba.fecha.min())[:10]} a {str(prueba.fecha.max())[:10]})\n")

def cols_de(grupos_elegidos):
    return NUCLEO + sum((CANDIDATAS[g] for g in grupos_elegidos), [])

def predecir(cols, ent, val):
    y_ent = ent['ambos_marcan'].values.astype(int)
    ps = [M.probabilidades(M.entrenar(ent[cols].values, y_ent, 2, semilla=s), val[cols].values, 2)[:, 1]
          for s in EM.SEMILLAS]
    return np.mean(ps, axis=0)

def brier_partido(p, val):
    return 2 * (p - val['ambos_marcan'].values.astype(int)) ** 2

def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))

# ---------- 1. selección hacia delante, mirando SOLO el tramo de selección ----------
elegidas = []
b_actual = brier_partido(predecir(cols_de(elegidas), ent, sel), sel)
print(f"Paso 0: base+Elo  Brier selección {b_actual.mean():.4f}")
paso = 0
while True:
    paso += 1
    resultados = {}
    for g in CANDIDATAS:
        if g in elegidas:
            continue
        resultados[g] = brier_partido(predecir(cols_de(elegidas + [g]), ent, sel), sel)
    if not resultados:
        break
    mejor = min(resultados, key=lambda g: resultados[g].mean())
    b_mejor = resultados[mejor]
    if b_mejor.mean() >= b_actual.mean():
        print(f"Paso {paso}: ninguna candidata baja el Brier (la mejor, {mejor}, da "
              f"{b_mejor.mean():.4f}). Fin.")
        break
    print(f"Paso {paso}: + {mejor:18s} Brier selección {b_mejor.mean():.4f}  "
          f"({sig(b_actual - b_mejor):+.2f}s sobre el paso anterior)")
    elegidas.append(mejor)
    b_actual = b_mejor

print(f"\nConjunto elegido para ambos_marcan: base+Elo + {elegidas}")
print(f"({time.time()-t0:.0f}s)\n")

# ---------- 2. prueba final, una sola vez, reentrenando con entrenamiento+selección ----------
cfgm = EM.MERCADOS['ambos_marcan']
pmer = EM.mercado_por_partido(cuotas, cfgm)
con_cuota = prueba.match_id.isin(pmer.index).values
b_merc = 2 * (pmer.loc[prueba.match_id[con_cuota]].values - prueba['ambos_marcan'].values[con_cuota].astype(int)) ** 2

finales = {
    'elegido (solo ambos_marcan)': elegidas,
    'produccion (suma 5 mercados)': PRODUCCION,
    'base+Elo': [],
}
b_fin = {n: brier_partido(predecir(cols_de(g), antes, prueba), prueba) for n, g in finales.items()}
ref = b_fin['elegido (solo ambos_marcan)']
print(f"PRUEBA FINAL: {len(prueba)} partidos ({con_cuota.sum()} con cuota)\n")
print(f"{'modelo':32s} {'Brier':>7s} {'elegido vs este':>16s} {'vs mercado':>11s}")
for n, bb in b_fin.items():
    vs = sig(bb - ref) if n != 'elegido (solo ambos_marcan)' else 0.0
    print(f"{n:32s} {bb.mean():7.4f} {vs:+15.2f}s {sig(b_merc - bb[con_cuota]):+10.2f}s")
print(f"\n(positivo en 'elegido vs este' = el elegido es mejor que ese modelo)")
