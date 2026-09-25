"""
¿Ayuda entrenar también con la temporada 2024/25?

Motivo (24/09/2026): el modelo pierde toda su ventaja al empezar la
temporada 2026/27 (-0.60% sobre predecir la media) y el entrenamiento no
tenía ningún cambio de temporada. El backfill trajo 1.743 partidos de
2024/25 de las 5 grandes (sin Segunda todavía).

Ojo: 2024/25 casi no trae xG (5%) ni centros (18%), y aún no tiene árbitro,
alineaciones (calidad_plantilla) ni h2h profundo. XGBoost acepta huecos
(NaN) de serie, así que esas filas se usan con lo que tengan.

Comparación limpia: mismos rasgos, mismos partidos de prueba (posteriores
al 24/04/2026, con todos los rasgos completos), y SOLO cambia qué filas
entran en el entrenamiento:
  A: como hasta ahora -- 2025/26 anterior al 24/04 con todos los rasgos
  B: A + todas las filas de 2024/25 (con sus huecos)
Brier emparejado partido a partido, 5 semillas, por tramo de la prueba.
"""
import sys, time
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

t0 = time.time()
hist = M.cargar()
bc = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
fechas = pd.to_datetime(bc.fecha, utc=True)
CORTE = pd.Timestamp('2026-04-24', tz='UTC')
INICIO_2526 = pd.Timestamp('2025-07-01', tz='UTC')
INICIO_2627 = pd.Timestamp('2026-07-01', tz='UTC')
grupos = rasgos.grupos_rasgo(bc)

CONFIGS = {
    'base+Elo': grupos['base'] + grupos['elo'],
    'conjunto propio (base+Elo+calidad+arbitro+h2h)': rasgos.columnas_rasgo_default(bc),
}

def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))

def predecir(cols, ent, val):
    y = ent['ambos_marcan'].values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s),
                                     val[cols].values, 2)[:, 1] for s in EM.SEMILLAS], axis=0)

INICIO_2425 = pd.Timestamp('2024-07-01', tz='UTC')
cuotas = EM.cargar_cuotas_crudas()
for nombre, cols in CONFIGS.items():
    completo = bc[cols].notna().all(axis=1)
    ent_a = bc[completo & (fechas >= INICIO_2526) & (fechas <= CORTE)]
    hay_y = bc['ambos_marcan'].notna()
    ent = {'A': ent_a,
           'B': pd.concat([bc[hay_y & (fechas >= INICIO_2425) & (fechas < INICIO_2526)], ent_a]),
           'C': pd.concat([bc[hay_y & (fechas < INICIO_2526)], ent_a])}
    prueba = bc[completo & (fechas > CORTE)]
    y = prueba['ambos_marcan'].values.astype(int)
    b = {k: 2 * (predecir(cols, e, prueba) - y) ** 2 for k, e in ent.items()}
    bmedia = 2 * (ent_a['ambos_marcan'].mean() - y) ** 2   # predecir siempre la tasa base
    print(f"\n== {nombre} ({len(cols)} rasgos) ==")
    print(f"entrenamiento A {len(ent['A'])} (2025/26) | B {len(ent['B'])} (+2024/25) | "
          f"C {len(ent['C'])} (+2024/25 +2023/24 parcial)")
    print(f"{'tramo de prueba':16s} {'n':>4s} {'B vs A':>8s} {'C vs A':>8s} {'C vs B':>8s} "
          f"{'A/media':>8s} {'B/media':>8s} {'C/media':>8s}")
    fp = pd.to_datetime(prueba.fecha, utc=True).values
    for tramo, m in (('final 2025/26', fp < INICIO_2627.to_datetime64()),
                     ('inicio 2026/27', fp >= INICIO_2627.to_datetime64()),
                     ('todo', np.ones(len(y), bool))):
        mej = {k: (1 - b[k][m].mean() / bmedia[m].mean()) * 100 for k in b}
        print(f"{tramo:16s} {m.sum():4d} {sig(b['A'][m]-b['B'][m]):+7.2f}s {sig(b['A'][m]-b['C'][m]):+7.2f}s "
              f"{sig(b['B'][m]-b['C'][m]):+7.2f}s {mej['A']:+7.2f}% {mej['B']:+7.2f}% {mej['C']:+7.2f}%")
    # contra el mercado, y robustez: ¿lo empujan unos pocos partidos?
    pmer = EM.mercado_por_partido(cuotas, EM.MERCADOS['ambos_marcan'])
    cc = prueba.match_id.isin(pmer.index).values
    bm = 2 * (pmer.loc[prueba.match_id[cc]].values - y[cc]) ** 2
    print(f"contra el mercado ({cc.sum()} con cuota): " +
          "   ".join(f"{k} {sig(bm-b[k][cc]):+.2f}s" for k in b))
    for k in ('B', 'C'):
        d = np.sort(bm - b[k][cc])[::-1]
        rng = np.random.default_rng(0)
        medias = np.array([rng.choice(d, len(d)).mean() for _ in range(5000)])
        print(f"  {k}: sin sus k mejores partidos " +
              "  ".join(f"k={q}: {sig(d[q:]):+.2f}s" for q in (1, 3, 5, 10)) +
              f" | bootstrap peor que el mercado en el {np.mean(medias <= 0)*100:.0f}%")
print(f"\n({time.time()-t0:.0f}s)  positivo en 'X vs Y' = X mejora a Y")
