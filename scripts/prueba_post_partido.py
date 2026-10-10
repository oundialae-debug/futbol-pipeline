"""Prueba SIN RED de scripts/post_partido.py: respuestas falsas de la API, sin git, en una carpeta temporal.
Caso real de calendario: Real Madrid - Villarreal (2026-10-10 19:00 UTC) y RB Leipzig - Frankfurt (16:30 UTC).
  1) 17:00 UTC: los dos antes de la ventana -> 0 llamadas.
  2) 20:50 UTC: Madrid en juego -> 1 llamada y sigue; Leipzig pasado saque+4h -> marca "abandonado", 0 llamadas.
  3) 21:00 UTC: Madrid terminado -> 2 llamadas, fila en el histórico, marca "datos_listos" (sin vídeo ni Buffer: eso es Live).
  4) 21:05 UTC: la marca impide repetir -> 0 llamadas, sin fila duplicada.
  5) tope: con 30 llamadas ya gastadas hoy -> no se llama.
  6) bucle: en juego -> el mismo job espera 5 min (reloj falso) y vuelve a sondear hasta terminar.
  7) bucle: nunca termina -> 1 llamada por sondeo y pasado saque+4h se deja (≤30 llamadas/día).
  8) bucle: con 20 llamadas ya gastadas hoy -> para al llegar a 30.
Uso: python3 scripts/prueba_post_partido.py   (sale con error si algo falla)"""
import json, os, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import post_partido as P  # noqa: E402

RM, RB = 1336420545, 1340476411


def partido(estado, marcador):
    return [{"id": RM, "date": "2026-10-10T19:00:00.000Z", "round": "Regular Season - 9",
             "league": {"id": 119924, "name": "La Liga"},
             "homeTeam": {"id": 461175, "name": "Real Madrid"}, "awayTeam": {"id": 454367, "name": "Villarreal"},
             "state": {"description": estado, "score": {"current": marcador}}}]


def stats(tid, xg, on, off, blk):
    return {"team": {"id": tid}, "statistics": [
        {"displayName": "Expected Goals", "value": xg}, {"displayName": "Shots on target", "value": on},
        {"displayName": "Shots off target", "value": off}, {"displayName": "Blocked shots", "value": blk},
        {"displayName": "Possession", "value": 0.55}, {"displayName": "Corners", "value": 6}]}


def copiar_historico(base):
    """El histórico real SIN el partido de la prueba (desde el 10/10 ya lleva el Madrid - Villarreal de verdad)."""
    with open(RAIZ / "data/historico_partidos.csv", encoding="utf-8") as f, \
            open(base / "data/historico_partidos.csv", "w", encoding="utf-8") as g:
        g.writelines(x for x in f if not x.startswith(f"{RM},"))


def P_salida(f):
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        f()
    return buf.getvalue().splitlines()


def pasada(base, hora):
    os.environ["AHORA"] = f"2026-10-10T{hora}:00+00:00"
    return P.main()


def main():
    ok = True

    def check(cond, txt):
        nonlocal ok
        print(("OK   " if cond else "FALLO") + " " + txt)
        ok &= bool(cond)

    with tempfile.TemporaryDirectory() as tmp:
        base, api = Path(tmp) / "repo", Path(tmp) / "api"
        (base / "data").mkdir(parents=True)
        api.mkdir()
        copiar_historico(base)
        filas0 = sum(1 for _ in open(base / "data/historico_partidos.csv"))
        P.usar_rutas(base)
        P.OPC.update(simular=str(api), git=False)

        # respaldo: solo a saque+2h05 (4 pasadas del principal sin marca); Madrid saca a las 19:00 UTC
        os.environ["AHORA"] = "2026-10-10T20:44:00+00:00"
        check(not P.hay_respaldo(), "respaldo: a saque+1h44 del Madrid no se activa")
        os.environ["AHORA"] = "2026-10-10T21:04:00+00:00"
        check(not any("Real Madrid" in l for l in P_salida(lambda: P.hay_respaldo())), "respaldo: a saque+2h04 todavía no")
        os.environ["AHORA"] = "2026-10-10T21:06:00+00:00"
        check(P.hay_respaldo(), "respaldo: a saque+2h06 sin marca SÍ se activa")

        out, n = pasada(base, "17:00")
        check(out.get(RM) == "pronto" and out.get(RB) == "pronto" and n == 0, f"antes de la ventana: {out}, {n} llamadas")

        (api / f"matches_{RM}.json").write_text(json.dumps(partido("Second half", "1 - 1")))
        out, n = pasada(base, "20:50")
        check(out.get(RM) == "en_juego" and n == 1, f"en juego: {out.get(RM)}, {n} llamada")
        mb = json.loads((base / f"data/redes/post_partido/{RB}.json").read_text())
        check(out.get(RB) == "abandonado" and mb["estado"] == "abandonado", "Leipzig pasado saque+4h: abandonado")

        (api / f"matches_{RM}.json").write_text(json.dumps(partido("Finished", "2 - 1")))
        (api / f"statistics_{RM}.json").write_text(json.dumps([stats(461175, 2.1, 7, 6, 4), stats(454367, 0.9, 3, 4, 2)]))
        out, n = pasada(base, "21:00")
        filas = sum(1 for _ in open(base / "data/historico_partidos.csv"))
        check(out.get(RM) == "datos_listos" and n == 2, f"terminado: {out.get(RM)}, {n} llamadas")
        check(filas == filas0 + 1, "una fila nueva en historico_partidos.csv")
        check(not (base / "media").exists(), "sin imágenes ni vídeo en futbol-pipeline")
        m = json.loads((base / f"data/redes/post_partido/{RM}.json").read_text())
        claves = {"match_id", "local", "visitante", "liga", "fecha", "saque_utc", "resultado", "estado"}
        check(claves <= set(m) and m["estado"] == "datos_listos" and m["resultado"] == "2-1" and m["llamadas"] == 3
              and m["local"] == "Real Madrid" and m["saque_utc"].startswith("2026-10-10T19:00"), f"marca: {m}")

        out, n = pasada(base, "21:05")
        filas2 = sum(1 for _ in open(base / "data/historico_partidos.csv"))
        check(out.get(RM) == "ya_hecho" and n == 0 and filas2 == filas, "la marca impide repetir (0 llamadas)")
        consumo = json.loads((base / "data/redes/post_partido_consumo.json").read_text())
        check(consumo["dias"]["2026-10-10"] == 3, f"consumo del día: {consumo['dias']}")

        (base / f"data/redes/post_partido/{RM}.json").unlink()
        copiar_historico(base)
        consumo["dias"]["2026-10-10"] = 30
        (base / "data/redes/post_partido_consumo.json").write_text(json.dumps(consumo))
        out, n = pasada(base, "21:10")
        check(n == 0 and out.get(RM) == "tope", f"tope de 30/día: {out.get(RM)}, {n} llamadas")

    # 6) bucle: en juego a las 20:50, el mismo job duerme 5 min (reloj falso) y a las 20:55 ya está terminado
    with tempfile.TemporaryDirectory() as tmp:
        base, api = Path(tmp) / "repo", Path(tmp) / "api"
        (base / "data").mkdir(parents=True)
        api.mkdir()
        copiar_historico(base)
        P.usar_rutas(base)
        P.OPC.update(simular=str(api), git=False)
        (api / f"matches_{RM}.json").write_text(json.dumps(partido("Second half", "1 - 0")))
        os.environ["AHORA"] = "2026-10-10T20:50:00+00:00"
        sueños = []

        def dormir(seg):
            sueños.append(seg)
            os.environ["AHORA"] = "2026-10-10T20:55:00+00:00"
            (api / f"matches_{RM}.json").write_text(json.dumps(partido("Finished", "1 - 0")))
            (api / f"statistics_{RM}.json").write_text(json.dumps([stats(461175, 0.9, 5, 4, 3), stats(454367, 0.6, 2, 3, 1)]))
        out = P.bucle(dormir)
        m = json.loads((base / f"data/redes/post_partido/{RM}.json").read_text())
        check(sueños == [300] and out.get(RM) == "datos_listos" and m["llamadas"] == 3,
              f"bucle: {len(sueños)} espera de {sueños}, {out.get(RM)}, {m['llamadas']} llamadas")

    # 7) y 8) bucle que nunca termina: abandona a saque+4h; con el tope, para a las 30 del día
    for usadas, esperado in ((0, "abandonado"), (20, "tope")):
        with tempfile.TemporaryDirectory() as tmp:
            base, api = Path(tmp) / "repo", Path(tmp) / "api"
            (base / "data/redes").mkdir(parents=True)
            api.mkdir()
            copiar_historico(base)
            (base / "data/redes/post_partido_consumo.json").write_text(
                json.dumps({"dias": {"2026-10-10": usadas}, "partidos": {}}))
            P.usar_rutas(base)
            P.OPC.update(simular=str(api), git=False)
            (api / f"matches_{RM}.json").write_text(json.dumps(partido("Second half", "0 - 0")))
            reloj = [datetime(2026, 10, 10, 20, 50, tzinfo=timezone.utc)]
            os.environ["AHORA"] = reloj[0].isoformat()
            sueños = []

            def dormir(seg):
                sueños.append(seg)
                reloj[0] += timedelta(seconds=seg)
                os.environ["AHORA"] = reloj[0].isoformat()
            out = P.bucle(dormir)
            dias = json.loads((base / "data/redes/post_partido_consumo.json").read_text())["dias"]
            c = sum(dias.values())     # a las 22:00 UTC ya es día 11 en Madrid: el consumo sigue en el día nuevo
            # 19:00 UTC + 4h = 23:00 UTC, ya "ayer" en Madrid: se deja sin marca ("fuera"), igual que "abandonado"
            fin_ok = out.get(RM) in (("abandonado", "fuera") if esperado == "abandonado" else ("tope",))
            check(fin_ok and max(dias.values()) <= 30 and (dias["2026-10-10"] == 30 if esperado == "tope" else c == len(sueños)),
                  f"bucle sin final (ya gastadas {usadas}): {out.get(RM)}, {len(sueños)} esperas, {c} llamadas en el día")

    print("\nTODO BIEN" if ok else "\nHAY FALLOS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
