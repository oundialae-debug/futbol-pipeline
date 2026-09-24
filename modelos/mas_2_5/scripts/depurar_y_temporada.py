"""
Depuración de variables + aprender el salto de temporada (24/09/2026).

Punto de partida: base_clasica+elo+cp_ataque (73 rasgos), el mejor hasta hoy.

1. DEPURAR: eliminación hacia atrás por MEDIDA (cada medida = loc/vis/dif
   de la media propia y la del rival), además de elo y cp_ataque. En cada paso
   se quita el bloque cuya ausencia más baja el Brier del tramo de selección;
   se para cuando quitar cualquiera lo sube. La prueba final no participa.
2. SALTO DE TEMPORADA: grupo `jornada` = partidos jugados por cada equipo EN
   ESTA temporada (loc/vis/dif_tabla_pj). Con él el modelo puede aprender que
   en las primeras jornadas sus medias de 8 partidos aún son del año pasado.
3. SOLIDEZ, en tres sitios:
   - final de 2025/26 (abr-jun): sin cuotas (la API las borra a los 28 días),
     solo contra la media y entre modelos
   - inicio de 2026/27 (ago-sep): también contra el mercado
   - réplica independiente: entrenar SOLO con 2024/25 y probar en el arranque
     de 2025/26 (ago-oct 2025). Sin cp_ataque (2024/25 no tiene alineaciones).
"""
import sys, io, contextlib, time, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np, pandas as pd
t0 = time.time()
src = open("scripts/seleccion_combinaciones.py", encoding="utf-8").read().split("# ---------- 1.")[0]
with contextlib.redirect_stdout(io.StringIO()):
    exec(src)

MEDIDAS = {"goles": ["m_goles", "m_goles_contra"],
           "xg": ["m_expected_goals", "m_contra_expected_goals"],
           "tiros_puerta": ["m_shots_on_target", "m_contra_shots_on_target"],
           "tiros_fuera": ["m_shots_off_target", "m_contra_shots_off_target"],
           "corners": ["m_corners", "m_contra_corners"],
           "faltas": ["m_fouls", "m_contra_fouls"],
           "posesion": ["m_possession", "m_contra_possession"],
           "pases": ["m_total_passes", "m_contra_total_passes"],
           "centros": ["m_crosses", "m_contra_crosses"],
           "puntos": ["m_puntos"],
           "previos_descanso": ["partidos_previos", "descanso"]}
B = {k: [f"{p}_{c}" for c in v for p in ("loc", "vis", "dif")] for k, v in MEDIDAS.items()}
B["elo"], B["cp_ataque"] = G["elo"], G["cp_ataque"]
B["jornada"] = ["loc_tabla_pj", "vis_tabla_pj", "dif_tabla_pj"]
assert set(sum((B[k] for k in MEDIDAS), [])) | {"liga_id"} == set(G["base_clasica"]), "bloques != base_clasica"

cols = lambda bl: ["liga_id"] + sum((B[b] for b in bl), [])
b_sel = lambda bl: brier_partido(predecir(cols(bl), ent_sel, sel), sel)

# ---------- 1. depuración hacia atrás ----------
actual = list(MEDIDAS) + ["elo", "cp_ataque"]
b_act = b_sel(actual)
print(f"Inicio: {len(cols(actual))} rasgos, Brier selección {b_act.mean():.4f}")
while len(actual) > 1:
    prueba_q = {b: b_sel([x for x in actual if x != b]) for b in actual}
    mejor = min(prueba_q, key=lambda b: prueba_q[b].mean())
    if prueba_q[mejor].mean() >= b_act.mean():
        print(f"  quitar cualquiera empeora (lo menos malo: {mejor}). Fin.")
        break
    actual.remove(mejor); b_act = prueba_q[mejor]
    print(f"  - {mejor:17s} -> {len(cols(actual))} rasgos, Brier {b_act.mean():.4f}")
depurado = actual
print(f"DEPURADO: {depurado} ({len(cols(depurado))} rasgos)  ({time.time()-t0:.0f}s)\n")

# ---------- 2-3. prueba final por tramos ----------
A = list(MEDIDAS) + ["elo", "cp_ataque"]
cfg = {"A: base_clasica+elo+g/a": A, "A + jornada": A + ["jornada"],
       "DEPURADO": depurado, "DEPURADO + jornada": depurado + ["jornada"]}
y = prueba[OBJ].values.astype(int)
pmer = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS[OBJ])
pm = pmer.reindex(prueba.match_id).values
cc = ~np.isnan(pm)
bm = 2 * (pm - y) ** 2
ini = (pd.to_datetime(prueba.fecha, utc=True) >= INICIO_2627).values
bmed = 2 * (ent_fin[OBJ].mean() - y) ** 2
P = {n: predecir(cols(bl), ent_fin, prueba) for n, bl in cfg.items()}
Bf = {n: 2 * (p - y) ** 2 for n, p in P.items()}
ref = Bf["A: base_clasica+elo+g/a"]
print(f"PRUEBA: final 2025/26 n={(~ini).sum()} | inicio 2026/27 n={ini.sum()} ({cc.sum()} con cuota)")
print(f"{'modelo':26s} {'rasgos':>6s} | {'final: vs media':>15s} {'vs A':>7s} | "
      f"{'inicio: vs media':>16s} {'vs A':>7s} {'vs mercado':>11s} {'acierto':>8s}")
for n, b in Bf.items():
    vsA = lambda m: sig(ref[m] - b[m]) if b is not ref else 0.0
    print(f"{n:26s} {len(cols(cfg[n])):6d} | "
          f"{(1-b[~ini].mean()/bmed[~ini].mean())*100:+14.2f}% {vsA(~ini):+6.2f}s | "
          f"{(1-b[ini].mean()/bmed[ini].mean())*100:+15.2f}% {vsA(ini):+6.2f}s "
          f"{sig(bm[cc]-b[cc]):+10.2f}s {((P[n][cc]>.5)==y[cc]).mean()*100:7.1f}%")
print(f"{'mercado':26s} {'':6s} | {'':15s} {'':7s} | {(1-bm[cc].mean()/bmed[cc].mean())*100:+15.2f}% "
      f"{'':7s} {'':11s} {((pm[cc]>.5)==y[cc]).mean()*100:7.1f}%")

# ---------- réplica: arranque de 2025/26 entrenando solo con 2024/25 ----------
f_all = pd.to_datetime(bc.fecha, utc=True)
ent_r = bc[con_obj & (f_all < INICIO_2526)]
val_r = bc[con_obj & (f_all >= INICIO_2526) & (f_all < pd.Timestamp("2025-11-01", tz="UTC"))]
yr = val_r[OBJ].values.astype(int)
bmed_r = 2 * (ent_r[OBJ].mean() - yr) ** 2
sin_cp = lambda bl: [b for b in bl if b != "cp_ataque"]
print(f"\nRÉPLICA arranque 2025/26 (ago-oct 2025, n={len(val_r)}), entrenando solo con 2024/25 "
      f"({len(ent_r)} filas), sin g/a:")
Rb = {}
for n, bl in (("A", sin_cp(A)), ("A + jornada", sin_cp(A) + ["jornada"]),
              ("DEPURADO", sin_cp(depurado)), ("DEPURADO + jornada", sin_cp(depurado) + ["jornada"])):
    Rb[n] = 2 * (predecir(cols(bl), ent_r, val_r) - yr) ** 2
for n, b in Rb.items():
    print(f"  {n:20s} vs media {(1-b.mean()/bmed_r.mean())*100:+.2f}%  vs A {sig(Rb['A']-b) if n!='A' else 0:+.2f}s")
print(f"\n({time.time()-t0:.0f}s)")
