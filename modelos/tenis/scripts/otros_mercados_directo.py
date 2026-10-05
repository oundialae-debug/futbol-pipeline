"""
Ganador y resultado en sets EN DIRECTO, en papel (05/10/2026, pregunta del usuario: "¿solo has apostado a
juegos?"). Usa el registro de cada 5 minutos (data/tenis/api_tennis/registro/) y los resultados finales.
Reglas probadas: modelo (o modelo con el saque de hoy) por encima de la casa 5/10 puntos, y seguir al
favorito de la casa. Una apuesta por partido (primera pasada que cumple). Sets: solo pasadas con TODOS
los resultados aún posibles cotizados; si falta uno (suspendido), la prob. sin margen de la casa se
infla (Ryser: 2:1 "al 56%" a cuota 101) y salía un falso +12,9%.
Escribe data/tenis/otros_mercados_directo.md.
"""
import glob, numpy as np, pandas as pd
d = pd.concat(pd.read_csv(f, low_memory=False) for f in sorted(glob.glob('data/tenis/api_tennis/registro/*.csv')))
r = pd.concat(pd.read_csv(f) for f in glob.glob('data/tenis/api_tennis/resultados/*.csv')).drop_duplicates('event_key', keep='last')
r = r[r.estado == 'Finished'].copy()
s = r.sets.astype(str).str.split('-', expand=True)
r['s1'] = pd.to_numeric(s[0], errors='coerce'); r['s2'] = pd.to_numeric(s[1], errors='coerce')
r = r.dropna(subset=['s1', 's2'])
d = d.merge(r[['event_key', 's1', 's2']], on='event_key')
if 'prob_modelo_directo' not in d: d['prob_modelo_directo'] = np.nan
d['prob_modelo_directo'] = d.prob_modelo_directo.fillna(d.prob_modelo)
for c in ('cuota', 'cuota_rival', 'prob_mercado', 'prob_modelo', 'prob_modelo_directo'): d[c] = pd.to_numeric(d[c], errors='coerce')
d = d.sort_values('hora')

def res(nombre, g):
    if len(g) < 2: print(f'{nombre:45s} n={len(g)}'); return
    m, sd = g.b.mean(), g.b.std(ddof=1)
    print(f'{nombre:45s} n={len(g):4d} acierto {g.y.mean():.0%} benef {m:+.1%} ({m/(sd/np.sqrt(len(g))):+.2f}s) casa decía {g.pc.mean():.0%}')

# ---- GANADOR
g = d[d.mercado == 'ganador'].dropna(subset=['prob_mercado', 'prob_modelo']).copy()
g['y1'] = (g.s1 > g.s2).astype(float)
w = g.groupby('event_key').size()
print(f'GANADOR en directo: {g.event_key.nunique()} partidos, {len(g)} pasadas')
wt = 1 / g.groupby('event_key').event_key.transform('size')
for c in ('prob_modelo', 'prob_modelo_directo', 'prob_mercado'):
    print(f'  Brier {c}: {np.sum(wt * (g[c] - g.y1) ** 2) / wt.sum():.4f}')
def apuestas_g(cond_lado, nombre):
    out = []
    for k, x in g.groupby('event_key'):
        for row in x.itertuples():
            lado = cond_lado(row)
            if lado is None: continue
            p1 = lado == 1
            cuota = row.cuota if p1 else row.cuota_rival
            y = row.y1 if p1 else 1 - row.y1
            out.append({'y': y, 'b': cuota - 1 if y else -1, 'pc': row.prob_mercado if p1 else 1 - row.prob_mercado}); break
    res(nombre, pd.DataFrame(out))
for col in ('prob_modelo', 'prob_modelo_directo'):
    for u in (0.05, 0.10):
        apuestas_g(lambda r, col=col, u=u: 1 if getattr(r, col) - r.prob_mercado >= u else (2 if r.prob_mercado - getattr(r, col) >= u else None), f'ganador: {col} > casa +{u:.0%}')
for u in (0.65, 0.75, 0.85):
    apuestas_g(lambda r, u=u: 1 if r.prob_mercado >= u else (2 if 1 - r.prob_mercado >= u else None), f'ganador: favorito de la casa >= {u:.0%}')
apuestas_g(lambda r: 1 if r.prob_mercado <= 0.35 else (2 if r.prob_mercado >= 0.65 else None), 'ganador: el que va perdiendo (casa <=35%)')

st = d[d.mercado == 'sets'].dropna(subset=['prob_mercado', 'prob_modelo']).copy()
lab = st.linea.astype(str).str.split(':', expand=True)
st['a'], st['b_'] = pd.to_numeric(lab[0]), pd.to_numeric(lab[1])
st = st[(st.a.isin([0, 1, 2])) & (st.b_.isin([0, 1, 2]))]          # solo al mejor de 3
st['y'] = ((st.a == st.s1) & (st.b_ == st.s2)).astype(float)
ss = st.sets.astype(str).str.split('-', expand=True); st['sa'], st['sb'] = pd.to_numeric(ss[0]), pd.to_numeric(ss[1])
posibles = {(0, 0): 4, (1, 0): 3, (0, 1): 3, (1, 1): 2}
n = st.groupby(['event_key', 'hora']).linea.transform('size')
st = st[[n_ == posibles.get((a, b), -1) for n_, a, b in zip(n, st.sa, st.sb)]]      # pasada con TODOS los resultados posibles
st = st[st.cuota.astype(float) < 50]
print(f'SETS (al mejor de 3, pasadas completas): {st.event_key.nunique()} partidos, {len(st)} filas')
wt = 1 / st.groupby('event_key').event_key.transform('size')
for c in ('prob_modelo', 'prob_modelo_directo', 'prob_mercado'):
    print(f'  Brier {c}: {np.sum(wt * (st[c] - st.y) ** 2) / wt.sum():.4f}')
def res(nombre, g):
    if len(g) < 2: print(nombre, len(g)); return
    m, sd = g.b.mean(), g.b.std(ddof=1)
    print(f'{nombre:45s} n={len(g):4d} acierto {g.y.mean():.0%} benef {m:+.1%} ({m/(sd/np.sqrt(len(g))):+.2f}s) casa decía {g.pc.mean():.0%}')
def una_por_partido(cond, nombre):
    out = []
    for k, x in st.sort_values('hora').groupby('event_key'):
        for row in x.itertuples():
            if cond(row):
                out.append({'y': row.y, 'b': row.cuota - 1 if row.y else -1, 'pc': row.prob_mercado}); break
    res(nombre, pd.DataFrame(out))
for u in (0.05, 0.10):
    una_por_partido(lambda r, u=u: r.prob_modelo - r.prob_mercado >= u, f'sets: modelo > casa +{u:.0%}')
    una_por_partido(lambda r, u=u: r.prob_modelo_directo - r.prob_mercado >= u, f'sets: directo > casa +{u:.0%}')
una_por_partido(lambda r: r.prob_mercado >= 0.5, 'sets: favorito de la casa (>=50%)')
una_por_partido(lambda r: r.prob_mercado >= 0.7, 'sets: favorito de la casa (>=70%)')
