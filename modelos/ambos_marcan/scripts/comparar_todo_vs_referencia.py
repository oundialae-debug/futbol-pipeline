"""
Todas las comparaciones de ambos_marcan de la sesión del 24/09, rehechas
como Brier EMPAREJADO modelo contra modelo, sobre TODOS los partidos de
validación -- no solo los que tienen cuota.

Las comparaciones originales medían cada variante contra el MERCADO, y eso
exige cuota: 194-212 partidos (cosecha desde el 24/08/2026). Pero para
decidir si una variable mejora el modelo basta con comparar el modelo con
y sin ella, partido a partido, y eso no necesita cuota: ~560 partidos de
validación (521 cuando interviene "localía", que recorta la muestra).

Cada comparación usa los MISMOS partidos para variante y referencia (la
unión de columnas no nulas de las dos), así que el recorte de localía
nunca cruza muestras distintas.
"""
import sys, time, itertools
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd

t0 = time.time()
# construcción de las 6 variables del barrido (todo lo anterior a su bucle)
fuente = open('scripts/experimentos_combinaciones.py', encoding='utf-8').read()
exec(fuente.split('print(f"Carga y preparacion')[0])

arb_v10 = calcular_arbitro_ventana(hist, ventana=10).rename(columns=lambda c: c.replace('arbitrov20', 'arbitrov10'))
bc = bc.merge(arb_v10, on='match_id', how='left')
bc['poisson_lambda_local'] = (bc['loc_m_goles'] + bc['vis_m_goles_contra']) / 2
bc['poisson_lambda_visit'] = (bc['vis_m_goles'] + bc['loc_m_goles_contra']) / 2
bc['poisson_p_btts'] = ((1 - np.exp(-bc['poisson_lambda_local'].clip(lower=0))) *
                        (1 - np.exp(-bc['poisson_lambda_visit'].clip(lower=0))))

nucleo = sum((grupos[g] for g in ['base', 'elo']), [])
g = lambda *ns: sum((grupos[n] for n in ns), [])
PROD = nucleo + g('arbitro', 'h2h', 'h2h_profundo', 'tabla', 'calidad_plantilla')
PROD_SIN_ARB = nucleo + g('h2h', 'h2h_profundo', 'tabla', 'calidad_plantilla')
PROD_SIN_H2HP = nucleo + g('arbitro', 'h2h', 'tabla', 'calidad_plantilla')
ARB10 = ['arbitrov10_tarjetas_media', 'arbitrov10_goles_media', 'arbitrov10_partidos_previos']
POISSON = ['poisson_lambda_local', 'poisson_lambda_visit', 'poisson_p_btts']
BTTS = grupos['btts']

# (nombre, columnas variante, columnas referencia, nombre referencia)
COMPARACIONES = []
SUELTAS = [('btts_tasa', BTTS), ('poisson_btts', POISSON), ('arbitro_v10', ARB10)] + \
          [(NOMBRES[v], VARS[v]) for v in range(1, 7)]
for nombre, cols in SUELTAS:
    COMPARACIONES.append((f'{nombre} (sola)', nucleo + cols, nucleo, 'base+elo'))
for nombre, cols in SUELTAS:
    if nombre in ('arbitro_v10', 'arbitro_v20'):
        COMPARACIONES.append((f'{nombre} (sustituye arbitro)', PROD_SIN_ARB + cols, PROD, 'produccion'))
    elif nombre == 'h2h_reciente':
        COMPARACIONES.append((f'{nombre} (sustituye h2h_profundo)', PROD_SIN_H2HP + cols, PROD, 'produccion'))
    else:
        COMPARACIONES.append((f'{nombre} (anadida)', PROD + cols, PROD, 'produccion'))
todas6 = sum((VARS[v] for v in range(1, 7)), [])
COMPARACIONES.append(('las 6 juntas (sola)', nucleo + todas6, nucleo, 'base+elo'))
for tam in (3, 4, 5, 6):
    for combo in itertools.combinations(range(1, 7), tam):
        cols = PROD_SIN_ARB + sum((VARS[v] for v in combo), [])
        COMPARACIONES.append(('combo ' + '+'.join(NOMBRES[v] for v in combo), cols, PROD, 'produccion'))

print(f"Preparación: {time.time()-t0:.0f}s. {len(COMPARACIONES)} comparaciones.\n")

cache = {}
def predecir(cols, clave_base, ent, val):
    clave = (tuple(cols), clave_base)
    if clave not in cache:
        y_ent = ent['ambos_marcan'].values.astype(int)
        ps = [M.probabilidades(M.entrenar(ent[cols].values, y_ent, 2, semilla=s),
                               val[cols].values, 2)[:, 1] for s in EM.SEMILLAS]
        cache[clave] = np.mean(ps, axis=0)
    return cache[clave]

filas = []
for i, (nombre, cols_v, cols_r, ref) in enumerate(COMPARACIONES):
    todas = sorted(set(cols_v) | set(cols_r))
    base = bc[bc[todas].notna().all(axis=1)].reset_index(drop=True)   # bc ya viene ordenado por fecha
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent, val = base.iloc[:corte], base.iloc[corte:]
    clave_base = hash(tuple(base.match_id))
    y = val['ambos_marcan'].values.astype(int)
    d = 2 * (predecir(cols_r, clave_base, ent, val) - y) ** 2 - 2 * (predecir(cols_v, clave_base, ent, val) - y) ** 2
    sigmas = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    filas.append({'comparacion': nombre, 'referencia': ref, 'n_validacion': len(val), 'sigmas': sigmas})
    print(f"[{i+1}/{len(COMPARACIONES)}] {nombre:70s} vs {ref:10s} n={len(val)}  {sigmas:+.2f}s", flush=True)

tabla = pd.DataFrame(filas)
tabla.to_csv('data/comparar_todo_vs_referencia.csv', index=False)
print(f"\nEscrito data/comparar_todo_vs_referencia.csv ({time.time()-t0:.0f}s)")
print("\nTop 10 combos vs produccion:")
combos = tabla[tabla.comparacion.str.startswith('combo')].sort_values('sigmas', ascending=False)
print(combos.head(10).to_string(index=False))
print(f"\nCombos que mejoran a produccion: {(combos.sigmas > 0).sum()} de {len(combos)}; "
      f"por encima de +2s: {(combos.sigmas >= 2).sum()}")
