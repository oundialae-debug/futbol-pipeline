"""
Selección de variables de mas_2_5 con las variables diseñadas por el usuario
(24/09/2026), y prueba final limpia. Mismo protocolo que
modelos/ambos_marcan/scripts/seleccion_y_prueba_limpia.py, con dos cambios:

  - BÚSQUEDA EXHAUSTIVA en vez de hacia delante: con 6 grupos candidatos son
    64 combinaciones por núcleo, cabe probarlas todas. Dos núcleos: la base
    casa/fuera pedida por el usuario (`base_cf`) y la base clásica (sin
    amarillas, para que lo único distinto sea el casa/fuera) -> 128 configs.
  - El ENTRENAMIENTO incluye 2024/25 (con sus huecos: sin alineaciones, casi
    sin xG). En ambos_marcan eso mejoró el inicio de temporada +2.8s.

Tres tramos por fecha. Los partidos de selección y de prueba son un conjunto
FIJO (2025/26 en adelante, con alineaciones y con las dos bases completas),
para que ninguna comparación cruce muestras:
  - entrenamiento: todo lo anterior al tramo de selección (incluye 2024/25)
  - selección: último 25% de los partidos fijos antes del 24/04/2026
  - prueba final: partidos fijos después del 24/04/2026, mirada UNA vez,
    reentrenando con todo lo anterior al 24/04

Se elige por el Brier medio del tramo de selección. La prueba no participa.
"""
import sys, time, itertools, io, contextlib, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
import rasgos, rasgos_mas25 as R, modelo_xgboost as M, evaluar_mercados as EM

t0 = time.time()
with contextlib.redirect_stdout(io.StringIO()):
    hist = M.cargar()
js = pd.read_csv("data/historico_jugador_stats.csv")
h2 = pd.read_csv("data/historico_h2h_profundo.csv")
bc = R.construir(hist, js, h2)
G = R.grupos(bc)
print(f"Rasgos construidos ({time.time()-t0:.0f}s)")

OBJ = "mas_2_5"
NUCLEOS = ["base_cf", "base_clasica"]
EXTRAS = ["elo", "tabla", "cp_ataque", "cp_defensa", "cp_minutos", "h2h_reciente"]
CORTE = pd.Timestamp("2026-04-24", tz="UTC")
INICIO_2526 = pd.Timestamp("2025-07-01", tz="UTC")
INICIO_2627 = pd.Timestamp("2026-07-01", tz="UTC")

fechas = pd.to_datetime(bc.fecha, utc=True)
con_obj = bc["goles_l"].notna() & bc["goles_v"].notna()
fijo = (con_obj & (fechas >= INICIO_2526)
        & (bc.loc_cp_conocidos > 0) & (bc.vis_cp_conocidos > 0)
        & bc[G["base_cf"]].notna().all(axis=1) & bc[G["base_clasica"]].notna().all(axis=1))
antes = bc[fijo & (fechas <= CORTE)]
prueba = bc[fijo & (fechas > CORTE)]
n_sel = int(len(antes) * 0.25)
sel = antes.iloc[-n_sel:]
ini_sel = pd.to_datetime(sel.fecha.min(), utc=True)
ent_sel = bc[con_obj & (fechas < ini_sel)]
ent_fin = bc[con_obj & (fechas <= CORTE)]
print(f"Partidos fijos: {fijo.sum()}")
print(f"  entrenamiento (selección) {len(ent_sel)} filas, {str(ent_sel.fecha.min())[:10]} a {str(ent_sel.fecha.max())[:10]} (incluye 2024/25)")
print(f"  selección     {len(sel)} ({str(sel.fecha.min())[:10]} a {str(sel.fecha.max())[:10]})")
print(f"  prueba final  {len(prueba)} ({str(prueba.fecha.min())[:10]} a {str(prueba.fecha.max())[:10]}), "
      f"entrenando con {len(ent_fin)} filas\n")


def cols_de(nucleo, extras):
    return list(dict.fromkeys(G[nucleo] + sum((G[e] for e in extras), [])))


def predecir(cols, ent, val):
    y = ent[OBJ].values.astype(int)
    return np.mean([M.probabilidades(M.entrenar(ent[cols].values, y, 2, semilla=s),
                                     val[cols].values, 2)[:, 1] for s in EM.SEMILLAS], axis=0)


def brier_partido(p, val):
    return 2 * (p - val[OBJ].values.astype(int)) ** 2


def sig(d):
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))


# ---------- 1. las 128 combinaciones, mirando SOLO el tramo de selección ----------
filas, bs = [], {}
for nucleo in NUCLEOS:
    for k in range(len(EXTRAS) + 1):
        for extras in itertools.combinations(EXTRAS, k):
            nombre = "+".join((nucleo,) + extras)
            b = brier_partido(predecir(cols_de(nucleo, extras), ent_sel, sel), sel)
            bs[nombre] = b
            filas.append({"config": nombre, "nucleo": nucleo, "n_extras": k,
                          "n_rasgos": len(cols_de(nucleo, extras)), "brier_sel": b.mean()})
    print(f"  {nucleo}: 64 combinaciones hechas ({time.time()-t0:.0f}s)")

tabla = pd.DataFrame(filas).sort_values("brier_sel").reset_index(drop=True)
ref_sel = bs["base_clasica+elo"]
tabla["vs_clasica_elo_sel"] = [sig(ref_sel - bs[c]) for c in tabla.config]
tabla.to_csv("data/seleccion_combinaciones.csv", index=False)
print("\nTop 10 en el tramo de selección (positivo = mejor que base_clasica+elo):")
print(tabla.head(10).to_string(index=False, float_format=lambda x: f"{x:.4f}"))
for nucleo in NUCLEOS:
    t = tabla[tabla.nucleo == nucleo]
    print(f"  mejor con {nucleo}: {t.config.iloc[0]}  Brier {t.brier_sel.iloc[0]:.4f}")
# ¿qué grupo aparece en las mejores? (la cabeza sola está inflada por selección)
top = tabla.head(16)
print("\nPresencia de cada grupo en las 16 mejores (de 128):")
for e in EXTRAS:
    print(f"  {e:14s} {top.config.str.contains(e).sum():2d}/16")
print(f"  núcleo base_cf {(top.nucleo=='base_cf').sum():2d}/16")

elegido = tabla.config.iloc[0]
nucleo_e, *extras_e = elegido.split("+")
print(f"\nELEGIDO: {elegido}  ({len(cols_de(nucleo_e, extras_e))} rasgos)\n")

# ---------- 2. prueba final, UNA vez ----------
finales = {
    f"ELEGIDO ({elegido})": cols_de(nucleo_e, extras_e),
    "todo lo pedido (base_cf+las 6)": cols_de("base_cf", EXTRAS),
    "base_cf+elo": cols_de("base_cf", ["elo"]),
    "base_clasica+elo": cols_de("base_clasica", ["elo"]),
    "produccion repo padre (99 rasgos)": rasgos.columnas_rasgo_default(bc),
}
y = prueba[OBJ].values.astype(int)
pf = {n: predecir(c, ent_fin, prueba) for n, c in finales.items()}
bf = {n: 2 * (p - y) ** 2 for n, p in pf.items()}
ref = bf[f"ELEGIDO ({elegido})"]
pmer = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS[OBJ])
cc = prueba.match_id.isin(pmer.index).values
pm = pmer.loc[prueba.match_id[cc]].values
bm = 2 * (pm - y[cc]) ** 2
fp = pd.to_datetime(prueba.fecha, utc=True)
ini = (fp >= INICIO_2627).values
bmedia = 2 * (ent_fin[OBJ].mean() - y) ** 2

print(f"PRUEBA FINAL: {len(prueba)} partidos ({cc.sum()} con cuota; "
      f"{(~ini).sum()} final 2025/26, {ini.sum()} inicio 2026/27)\n")
print(f"{'modelo':44s} {'Brier':>7s} {'elegido vs':>11s} {'vs media':>9s} "
      f"{'vs mercado':>11s} {'acierto':>8s}")
for n, b in bf.items():
    vs = sig(b - ref) if b is not ref else 0.0
    ac = ((pf[n][cc] > 0.5) == y[cc]).mean() * 100
    print(f"{n:44s} {b.mean():7.4f} {vs:+10.2f}s {(1-b.mean()/bmedia.mean())*100:+8.2f}% "
          f"{sig(bm - b[cc]):+10.2f}s {ac:7.1f}%")
print(f"{'mercado':44s} {bm.mean():7.4f} {'':>11s} {'':>9s} {'':>11s} "
      f"{((pm > 0.5) == y[cc]).mean()*100:7.1f}%")
print("(positivo en 'elegido vs' = el elegido es mejor; 'acierto' sobre los partidos con cuota)")

print("\nPor tramo, elegido:")
for tramo, m in (("final 2025/26", ~ini), ("inicio 2026/27", ini)):
    print(f"  {tramo:16s} n={m.sum():4d}  vs media {(1-ref[m].mean()/bmedia[m].mean())*100:+.2f}%  "
          f"vs base_clasica+elo {sig(bf['base_clasica+elo'][m] - ref[m]):+.2f}s")

d = np.sort(bm - ref[cc])[::-1]
print(f"\nElegido contra el mercado: {sig(d):+.2f}s. Sin sus k mejores partidos: " +
      "  ".join(f"k={k}: {sig(d[k:]):+.2f}s" for k in (1, 3, 5, 10)))
rng = np.random.default_rng(0)
medias = np.array([rng.choice(d, len(d)).mean() for _ in range(5000)])
print(f"Bootstrap: peor que el mercado en el {np.mean(medias <= 0)*100:.0f}% de remuestreos")
print(f"\n({time.time()-t0:.0f}s)")
