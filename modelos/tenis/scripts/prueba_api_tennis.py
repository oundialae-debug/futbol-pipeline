"""
Prueba de API-Tennis (una llamada a get_livescore y otra a get_live_odds), para
comprobar que los campos reales coinciden con lo que espera api_tennis.estado().
Guarda data/tenis/api_tennis/prueba.md: campos recibidos, un ejemplo de partido
(sin la clave: la clave nunca va en la respuesta) y el marcador traducido de
cada partido individual en juego. Corre en GitHub Actions (prueba_api_tennis.yml).
"""
import json
import os
import sys

sys.path.insert(0, "modelos/tenis/scripts")
import api_tennis as A  # noqa: E402

SALIDA = "data/tenis/api_tennis"


def main():
    os.makedirs(SALIDA, exist_ok=True)
    lin = ["# Prueba de API-Tennis\n"]
    try:
        vivos = A.marcadores()
    except RuntimeError as e:
        lin.append(f"get_livescore: ERROR: {e}")
        open(f"{SALIDA}/prueba.md", "w").write("\n".join(lin) + "\n")
        print("\n".join(lin))
        sys.exit(1)
    lin.append(f"get_livescore: {len(vivos)} partidos en juego.")
    campos = sorted({k for p in vivos for k in p})
    lin.append(f"Campos: {', '.join(campos)}\n")
    tipos = {}
    for p in vivos:
        tipos[p.get("event_type_type")] = tipos.get(p.get("event_type_type"), 0) + 1
    lin.append(f"Tipos: {tipos}\n")
    if vivos:
        ej = {k: v for k, v in vivos[0].items() if k not in ("pointbypoint", "statistics")}
        lin += ["Ejemplo (sin punto a punto ni estadísticas):", "```", json.dumps(ej, ensure_ascii=False, indent=1)[:3000], "```"]
        pbp = vivos[0].get("pointbypoint") or []
        lin += ["Punto a punto, primeros elementos:", "```", json.dumps(pbp[:2], ensure_ascii=False)[:1500], "```"]
    lin += ["\n| partido | tipo | estado bruto | marcador traducido |", "|---|---|---|---|"]
    for p in vivos:
        if A.circuito(p) is None:
            continue
        bruto = f"{p.get('event_status')} / {p.get('event_game_result')} / saca {p.get('event_serve')} / " \
                f"{[(s.get('score_set'), s.get('score_first'), s.get('score_second')) for s in p.get('scores') or []]}"
        lin.append(f"| {p.get('event_first_player')} vs {p.get('event_second_player')} | {p.get('event_type_type')} | "
                   f"{bruto} | {A.estado(p)} |")
    try:
        odds = A.cuotas_directo()
        lin.append(f"\nget_live_odds: {type(odds).__name__} con {len(odds)} elementos.")
        primero = odds[0] if isinstance(odds, list) and odds else (next(iter(odds.values())) if isinstance(odds, dict) and odds else None)
        lin += ["Ejemplo:", "```", json.dumps(primero, ensure_ascii=False, indent=1)[:3000], "```"]
    except RuntimeError as e:
        lin.append(f"\nget_live_odds: ERROR: {e}")
    open(f"{SALIDA}/prueba.md", "w").write("\n".join(lin) + "\n")
    print("\n".join(lin[:6]))


if __name__ == "__main__":
    main()
