"""
¿Se apartan las casas que cosechamos del cierre afinado, y se gana
apostando donde se apartan? (25/09/2026)

Pista de cuota_como_variable.py: el precio cosechado de Highlightly es más
blando que el cierre de Pinnacle/Betfair. La estrategia clásica es no usar
modelo: tomar el precio afinado (sin margen) como probabilidad verdadera y
apostar en la casa que pague MÁS de lo justo.

  valor esperado = cuota_casa * p_afinada - 1   (> 0: la casa paga de más)

Referencia afinada: cierre de football-data, SOLO Pinnacle o Betfair
Exchange (se excluye "media": no es afinada). Pinnacle no está entre las 53
casas cosechadas.

Qué es lo cosechado (spec de /odds): la última cuota PREVIA de cada casa,
refrescada "varias veces al día". Se cosecha días después del partido, así
que es la última foto antes del pitido, pero NO se sabe a qué hora se tomó.
Si la foto de la casa es de horas antes y el cierre se movió después,
"valor" puede ser solo una cuota vieja que ya no estaba disponible: el
mismo fallo que el "29% de arbitraje" de CLAUDE.md. Por eso se mira el
beneficio REAL, no solo el esperado: si el valor es real, el beneficio real
se parece al esperado; si es un espejismo, no.

Errores agrupados por partido (las apuestas de un mismo partido ganan y
pierden juntas).
"""
import sys
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import evaluar_mercados as EM

UMBRALES = (0.0, 0.02, 0.05, 0.10)


def main():
    for sufijo, nombre in (("", "CIERRE (se conoce en el pitido)"),
                           ("_previa", "PREVIA (días antes; sin mirar al futuro)")):
        print("=" * 90 + f"\nREFERENCIA: {nombre}\n" + "=" * 90)
        analizar(sufijo)
    cuando_se_cosecha()


def analizar(sufijo):
    fd = pd.read_csv("data/cuotas_historicas_fd.csv").set_index("match_id")
    h = pd.read_csv("data/historico_partidos.csv").set_index("match_id")
    c = EM.cargar_cuotas_crudas()
    c = c[c.match_id.isin(h.index) & c.match_id.isin(fd.index)]

    piezas = []
    # 1X2
    r = c[c.familia == "Full Time Result"].copy()
    r = r[r.match_id.map(fd["fuente" + sufijo + ("_1x2" if sufijo else "_1x2")] if not sufijo else fd.fuente_previa_1x2).isin(["pinnacle", "betfair"])]
    col = {"home": "p_local", "draw": "p_empate", "away": "p_visitante"}
    r = r[r.lado.isin(col)]
    r["p_afinada"] = [fd.at[m, col[l] + sufijo] for m, l in zip(r.match_id, r.lado)]
    gl, gv = r.match_id.map(h.goles_l), r.match_id.map(h.goles_v)
    real = np.select([gl > gv, gl == gv], ["home", "draw"], "away")
    r["gana"] = (r.lado.values == real)
    r["mercado_x"] = "1X2"
    piezas.append(r)
    # más/menos 2.5
    o = c[(c.familia == "Total Goals") & (c.mercado == "Total Goals 2.5")].copy()
    fte = fd.fuente_previa_mas_2_5 if sufijo else fd.fuente_mas_2_5
    o = o[o.match_id.map(fte).isin(["pinnacle", "betfair"]) & o.lado.isin(["over", "under"])]
    pov = o.match_id.map(fd["p_mas_2_5" + sufijo])
    o["p_afinada"] = np.where(o.lado == "over", pov, 1 - pov)
    tot = o.match_id.map(h.goles_l) + o.match_id.map(h.goles_v)
    o["gana"] = np.where(o.lado == "over", tot > 2.5, tot < 2.5)
    o["mercado_x"] = "mas/menos 2.5"
    piezas.append(o)

    d = pd.concat(piezas, ignore_index=True)
    d = d[(d.cuota > 1) & d.p_afinada.notna()]
    d["ve"] = d.cuota * d.p_afinada - 1
    d["beneficio"] = np.where(d.gana, d.cuota - 1, -1.0)
    print(f"{d.match_id.nunique()} partidos, {d.casa.nunique()} casas, {len(d)} cuotas con referencia afinada.")
    print(f"Fuente de la referencia: {d.match_id.map(fd.fuente_previa_1x2 if sufijo else fd.fuente_1x2).value_counts().to_dict()}")
    fe = pd.to_datetime(d.match_id.map(h.fecha), format="mixed", utc=True)
    print(f"Fechas: {str(fe.min())[:10]} a {str(fe.max())[:10]}\n")

    # comprobación de signo con un caso concreto
    ej = d.sort_values("ve").iloc[len(d) // 2]
    print(f"Caso concreto (signo): {ej.casa} {ej.mercado_x} {ej.lado} cuota {ej.cuota} , "
          f"p_afinada {ej.p_afinada:.3f} -> justa {1/ej.p_afinada:.2f} -> VE {ej.ve*100:+.1f}%\n")

    def resumen(sel, etiqueta):
        if sel.empty:
            print(f"  {etiqueta:44s} sin apuestas")
            return
        pm = sel.groupby("match_id").agg(b=("beneficio", "sum"), n=("beneficio", "size"))
        roi = pm.b.sum() / pm.n.sum()
        x = pm.b.values - roi * pm.n.values          # residuo por partido
        ee = np.sqrt((x ** 2).sum()) / pm.n.sum()
        print(f"  {etiqueta:44s} {len(sel):5d} apuestas {len(pm):4d} partidos  "
              f"VE medio {sel.ve.mean()*100:+5.1f}%  real {roi*100:+6.1f}%  ({roi/ee:+.2f}s)")

    for mx in ("1X2", "mas/menos 2.5"):
        s = d[d.mercado_x == mx]
        print(f"== {mx} ==")
        resumen(s, "todas las cuotas (a ciegas)")
        mejor = s.loc[s.groupby(["match_id", "lado"]).cuota.idxmax()]
        resumen(mejor, "mejor cuota de cada lado (a ciegas)")
        for u in UMBRALES:
            resumen(s[s.ve > u], f"cualquier casa con VE > {u*100:.0f}%")
            resumen(mejor[mejor.ve > u], f"mejor cuota con VE > {u*100:.0f}%")
        sel = mejor[mejor.ve > 0]
        pm = sel.groupby("match_id").beneficio.sum().sort_values(ascending=False)
        for k in (1, 3, 5):
            resumen(sel[~sel.match_id.isin(pm.index[:k])], f"  mejor VE>0% sin sus {k} mejores partidos")
        grande = sel[sel.cuota >= 5]
        resumen(grande, "  mejor VE>0%, solo cuotas >= 5")
        resumen(sel[sel.cuota < 5], "  mejor VE>0%, solo cuotas < 5")
        print()

    if sufijo:
        return
    print("Casas que más veces pagan por encima del cierre (1X2 + 2.5, VE > 2%):")
    t = d.groupby("casa").agg(cuotas=("ve", "size"), pct_valor=("ve", lambda v: (v > 0.02).mean() * 100),
                              ve_medio=("ve", lambda v: v.mean() * 100))
    print(t.sort_values("pct_valor", ascending=False).head(10).round(1).to_string())
    d.to_csv("data/casas_contra_cierre.csv", index=False)


def cuando_se_cosecha():
    """
    ¿A qué hora es la foto cosechada? Si el precio mediano cosechado acierta
    igual que el cierre, es una foto de cerca del pitido; si acierta como la
    previa, es de días antes. Brier emparejado, 1X2, mismos partidos.
    """
    fd = pd.read_csv("data/cuotas_historicas_fd.csv").set_index("match_id")
    h = pd.read_csv("data/historico_partidos.csv").set_index("match_id")
    pm = EM.mercado_por_partido(EM.cargar_cuotas_crudas(), EM.MERCADOS["resultado"])
    ids = [m for m in pm.index if m in fd.index and m in h.index and pd.notna(fd.at[m, "p_local_previa"])]
    gl, gv = h.loc[ids, "goles_l"].values, h.loc[ids, "goles_v"].values
    y = np.select([gl > gv, gl == gv], [0, 1], 2)
    B = lambda p: EM.brier(p, y, 3)
    cos = B(pm.loc[ids][["p_home", "p_draw", "p_away"]].values)
    cie = B(fd.loc[ids, ["p_local", "p_empate", "p_visitante"]].values)
    pre = B(fd.loc[ids, ["p_local_previa", "p_empate_previa", "p_visitante_previa"]].values)
    s_ = lambda d: d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    dist = lambda a, b: np.abs(a - b).mean() * 100
    P = lambda cols, df: df.loc[ids, cols].values
    pc = pm.loc[ids][["p_home", "p_draw", "p_away"]].values
    print("\n¿Cuándo es la foto cosechada? (1X2, %d partidos)" % len(ids))
    print(f"  Brier  previa {pre.mean():.4f}   cosechado {cos.mean():.4f}   cierre {cie.mean():.4f}")
    print(f"  cierre mejor que cosechado: {s_(cos - cie):+.2f}s   cosechado mejor que previa: {s_(pre - cos):+.2f}s")
    print(f"  distancia media (puntos): cosechado-cierre {dist(pc, P(['p_local','p_empate','p_visitante'], fd)):.2f}  "
          f"cosechado-previa {dist(pc, P(['p_local_previa','p_empate_previa','p_visitante_previa'], fd)):.2f}  "
          f"previa-cierre {dist(P(['p_local_previa','p_empate_previa','p_visitante_previa'], fd), P(['p_local','p_empate','p_visitante'], fd)):.2f}")


if __name__ == "__main__":
    main()
