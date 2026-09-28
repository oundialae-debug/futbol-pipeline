"""
Edad media y valor de mercado medio del once, para ambos marcan (petición del
usuario, 28/09/2026; la edad es la prioritaria). Datos de
backfill_perfil_jugador.py. Variantes FIJADAS ANTES de tener los datos:

  A  edad    edad media de los 10 titulares de CAMPO el día del partido (el
             portero es siempre el primer id del once: 9.957 de 9.958
             comprobados). loc_/vis_/dif_edad_campo.
  B  valor   valor de mercado medio de los 11 titulares, en millones, con la
             última valoración ANTERIOR al partido (nunca la de hoy).
             loc_/vis_/dif_valor_once.
  C  las dos juntas.

Mínimo 7 jugadores con dato por equipo; si no, hueco (el modelo entrena con
huecos). Solo titulares: los cambios no se conocen antes del pitido.

Misma prueba mes a mes que el modelo oficial (modelo_ambos_marcan.predecir_mes,
5 semillas), en los meses con el rasgo en al menos la mitad de los partidos.
Brier emparejado. Con 3 intentos el listón honesto es ~+2.4s; si solo se
mira A, +2s.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import numpy as np
import pandas as pd
import modelo_ambos_marcan as A

MINIMO = 7


def once_largo():
    """Una fila por titular: match_id, lado, orden (0 = portero), jugador_id, fecha."""
    lu = pd.read_csv("data/historico_lineups.csv")
    h = pd.read_csv("data/historico_partidos.csv", usecols=["match_id", "fecha"])
    filas = [(r.match_id, lado, k, int(j))
             for r in lu.itertuples() for lado in ("local", "visitante")
             if isinstance(getattr(r, f"{lado}_ids"), str)
             for k, j in enumerate(x for x in getattr(r, f"{lado}_ids").split("|") if x.strip().isdigit())]
    t = pd.DataFrame(filas, columns=["match_id", "lado", "orden", "jugador_id"]).merge(h, on="match_id")
    t["fecha"] = pd.to_datetime(t.fecha, utc=True).dt.tz_localize(None)
    return t


def rasgos(t=None):
    t = once_largo() if t is None else t
    per = pd.read_csv("data/jugador_perfil.csv")
    per = per[per.nacimiento.notna()].assign(nacimiento=lambda d: pd.to_datetime(d.nacimiento, errors="coerce"))
    t = t.merge(per[["jugador_id", "nacimiento"]], on="jugador_id", how="left")
    t["edad"] = (t.fecha - t.nacimiento).dt.days / 365.25
    # valor: última valoración anterior al partido (merge_asof hacia atrás, estricto)
    v = pd.read_csv("data/jugador_valor_mercado.csv")
    v = v.assign(fecha_v=pd.to_datetime(v.fecha, errors="coerce"),
                 valor=pd.to_numeric(v.valor, errors="coerce") / 1e6).dropna(subset=["fecha_v", "valor"])
    t = pd.merge_asof(t.sort_values("fecha"), v[["jugador_id", "fecha_v", "valor"]].sort_values("fecha_v"),
                      left_on="fecha", right_on="fecha_v", by="jugador_id",
                      direction="backward", allow_exact_matches=False)
    campo = t[t.orden > 0].groupby(["match_id", "lado"]).edad.agg(["mean", "count"])
    once = t.groupby(["match_id", "lado"]).valor.agg(["mean", "count"])
    g = pd.DataFrame({"edad_campo": campo["mean"].where(campo["count"] >= MINIMO),
                      "valor_once": once["mean"].where(once["count"] >= MINIMO)}).reset_index()
    out = None
    for lado, pre in (("local", "loc"), ("visitante", "vis")):
        x = g[g.lado == lado].drop(columns="lado").rename(columns={c: f"{pre}_{c}" for c in ("edad_campo", "valor_once")})
        out = x if out is None else out.merge(x, on="match_id", how="outer")
    for c in ("edad_campo", "valor_once"):
        out[f"dif_{c}"] = out[f"loc_{c}"] - out[f"vis_{c}"]
    return out


VARIANTES = {
    "A edad": ["loc_edad_campo", "vis_edad_campo", "dif_edad_campo"],
    "B valor": ["loc_valor_once", "vis_valor_once", "dif_valor_once"],
}
VARIANTES["C edad+valor"] = VARIANTES["A edad"] + VARIANTES["B valor"]


def main():
    bt, cols = A.preparar()
    r = rasgos()
    bt = bt.merge(r, on="match_id", how="left")
    print(f"Cobertura: edad {bt.loc_edad_campo.notna().mean():.0%}, valor {bt.loc_valor_once.notna().mean():.0%} "
          f"de {len(bt)} partidos. Edad media {bt.loc_edad_campo.mean():.1f} años; "
          f"valor medio {bt.loc_valor_once.median():.1f} M (mediana)")
    cob = bt.groupby("mes").loc_edad_campo.apply(lambda s: s.notna().mean())
    meses = [m for m, n in bt.mes.value_counts().sort_index().items() if n >= 20 and cob.get(m, 0) >= 0.5]
    print(f"Meses de prueba: {meses[0]}..{meses[-1]} ({len(meses)})")
    base = pd.concat([A.predecir_mes(bt, cols, m) for m in meses])
    y = base[A.OBJETIVO].values
    filas = []
    for nombre, extra in VARIANTES.items():
        v = pd.concat([A.predecir_mes(bt, cols, m, extra=extra) for m in meses])
        d = (base.p_ambos.values - y) ** 2 - (v.p_ambos.values - y) ** 2
        pos = sum(((base[base.mes == m].p_ambos - base[base.mes == m][A.OBJETIVO]) ** 2).mean() >
                  ((v[v.mes == m].p_ambos - v[v.mes == m][A.OBJETIVO]) ** 2).mean() for m in meses)
        ini = (base.mes >= "2026-08").values
        di = d[ini]
        s = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
        print(f"{nombre:13s} vs oficial {s:+.2f}s  (Brier {((v.p_ambos.values - y)**2).mean():.4f} vs "
              f"{((base.p_ambos.values - y)**2).mean():.4f}; mejora en {pos}/{len(meses)} meses; "
              f"arranque 2026/27: {di.mean()*100:+.2f} pts en {len(di)} partidos)", flush=True)
        filas.append({"variante": nombre, "sigmas": round(s, 2), "meses_mejor": pos, "meses": len(meses)})
    pd.DataFrame(filas).to_csv("data/experimento_edad_valor.csv", index=False)


if __name__ == "__main__":
    main()
