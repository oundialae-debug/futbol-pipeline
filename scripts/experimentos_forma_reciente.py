import sys
sys.path.insert(0, 'scripts')
import numpy as np, pandas as pd
import rasgos, modelo_xgboost as M, evaluar_mercados as EM

hist = M.cargar()
base_completa = rasgos.construir(hist).sort_values('fecha').reset_index(drop=True)
grupos = rasgos.grupos_rasgo(base_completa)
cuotas = EM.cargar_cuotas_crudas()
print(f"forma_reciente: {len(grupos['forma_reciente'])} columnas\n")

def evaluar(nombre_cfg, extra_grupos):
    cols = sum((grupos[g] for g in ['base','elo'] + extra_grupos), [])
    base = base_completa[base_completa[cols].notna().all(axis=1)].reset_index(drop=True)
    corte = int(len(base) * (1 - M.PROPORCION_VALIDACION))
    ent = base.iloc[:corte]
    fecha_corte = pd.to_datetime(ent.fecha.max())
    print(f"=== {nombre_cfg} ({len(cols)} rasgos, {len(base)} partidos utilizables) ===")
    suma_sigmas = suma_acierto = 0.0
    for nombre, cfg in EM.MERCADOS.items():
        r = EM.evaluar_uno(nombre, cfg, base, cols, ent, fecha_corte, cuotas)
        if not r["evaluable"]:
            print(f"  {nombre:20s} NO EVALUABLE -- {r['motivo']}")
            continue
        pmer_todos = EM.mercado_por_partido(cuotas, cfg)
        val = base[pd.to_datetime(base.fecha) > fecha_corte]
        val = val[val.match_id.isin(pmer_todos.index)]
        y = val[nombre].values.astype(int)
        y_ent = ent[nombre].values.astype(int)
        preds = []
        for s in EM.SEMILLAS:
            modelo = M.entrenar(ent[cols].values, y_ent, cfg['n_clases'], semilla=s)
            p = M.probabilidades(modelo, val[cols].values, cfg['n_clases'])
            preds.append(p if cfg['n_clases']==3 else p[:,1])
        pn = np.mean(preds, axis=0)
        if cfg['n_clases'] == 3:
            pm = pmer_todos.loc[val.match_id][[f'p_{l}' for l in cfg['lados']]].values
            acierto_modelo = (pn.argmax(axis=1) == y).mean()
            acierto_mercado = (pm.argmax(axis=1) == y).mean()
        else:
            pm = pmer_todos.loc[val.match_id].values
            acierto_modelo = ((pn > 0.5).astype(int) == y).mean()
            acierto_mercado = ((pm > 0.5).astype(int) == y).mean()
        ad = acierto_modelo - acierto_mercado
        suma_sigmas += r['sigmas']
        suma_acierto += ad
        print(f"  {nombre:20s} n={r['partidos']:4d}  {r['sigmas']:+.2f}s  acierto {acierto_modelo*100:5.1f}% vs {acierto_mercado*100:5.1f}% ({ad*100:+.1f}pp)")
    print(f"  SUMA sigmas: {suma_sigmas:+.2f}   SUMA acierto_dif: {suma_acierto*100:+.1f}pp\n")

evaluar("base+elo", [])
evaluar("base+elo+forma_reciente (sola)", ['forma_reciente'])
evaluar("produccion actual (arbitro+h2h+h2h_profundo+tabla+calidad)", ['arbitro','h2h','h2h_profundo','tabla','calidad_plantilla'])
evaluar("produccion + forma_reciente", ['arbitro','h2h','h2h_profundo','tabla','calidad_plantilla','forma_reciente'])
