"""
Corre cada 15 minutos. Busca partidos que empiezan en los próximos 90
minutos, y si tienen alineación YA confirmada (variable 7 y 8 aplicables)
y no se han refinado todavía, recalcula la predicción con datos definitivos
y actualiza el registro.

Reutiliza las funciones del pipeline principal en vez de duplicar código.
"""
import os
import pandas as pd
from datetime import datetime, timedelta
from pipeline_diario import (obtener_proximos_partidos, obtener_alineacion, obtener_cuotas,
                              recalcular_parametros, predecir_goles, predecir_tarjetas, RUTA_HISTORICO)

RUTA_REGISTRO = "data/registro_predicciones.csv"
RUTA_REFINADOS = "data/partidos_refinados.md"


def main():
    if not os.path.exists(RUTA_HISTORICO):
        print("Sin histórico todavía -- nada que refinar")
        return

    historico = pd.read_csv(RUTA_HISTORICO)
    params = recalcular_parametros(historico)

    registro = pd.read_csv(RUTA_REGISTRO) if os.path.exists(RUTA_REGISTRO) else pd.DataFrame()
    if "refinado" not in registro.columns:
        registro["refinado"] = False

    proximos = obtener_proximos_partidos(dias=2)
    ahora = datetime.utcnow()
    refinados_esta_vez = []

    for p in proximos:
        fecha_partido = datetime.fromisoformat(p["date"].replace("Z", "+00:00")).replace(tzinfo=None)
        minutos_para_empezar = (fecha_partido - ahora).total_seconds() / 60
        if not (0 <= minutos_para_empezar <= 90):
            continue

        ya_refinado = not registro[(registro["match_id"] == p["id"]) & (registro["refinado"] == True)].empty
        if ya_refinado:
            continue

        local, visitante = p["homeTeam"]["name"], p["awayTeam"]["name"]
        alineacion, es_confirmada = obtener_alineacion(p["id"], p["date"])
        if not (alineacion and es_confirmada):
            continue  # todavía no hay alineación real -- se reintenta en 15 min

        cuotas = obtener_cuotas(p["id"])
        pred_goles = predecir_goles(local, visitante, params)
        pred_tarjetas = predecir_tarjetas(local, visitante, None, params,
                                           alineacion=alineacion, es_alineacion_confirmada=True)

        nueva_fila = {"match_id": p["id"], "fecha": p["date"], "equipo_local": local, "equipo_visitante": visitante,
                       "prob_local": pred_goles["prob_local"], "prob_empate": pred_goles["prob_empate"],
                       "prob_visitante": pred_goles["prob_visitante"], "prob_over_tarjetas": pred_tarjetas["prob_over"],
                       "generado_el": datetime.utcnow().isoformat(), "refinado": True}

        # La fila se sustituye entera, así que hay que arrastrar la probabilidad
        # de mercado que ya hubiera: es la que permite comparar después modelo
        # contra casa, y aquí no se recalcula. Sin esto, refinar un partido
        # borraba justamente el dato que sirve para medir si ganamos al mercado.
        anterior = registro[registro["match_id"] == p["id"]]
        if not anterior.empty and "prob_mercado_over_tarjetas" in anterior.columns:
            nueva_fila["prob_mercado_over_tarjetas"] = anterior.iloc[0]["prob_mercado_over_tarjetas"]

        registro = registro[registro["match_id"] != p["id"]]  # se sustituye la predicción anterior por la refinada
        registro = pd.concat([registro, pd.DataFrame([nueva_fila])], ignore_index=True)
        refinados_esta_vez.append({**nueva_fila, "tiene_cuotas": bool(cuotas)})
        print(f"[refinado] {local} vs {visitante} -- alineación real aplicada")

    registro.to_csv(RUTA_REGISTRO, index=False)

    if refinados_esta_vez:
        with open(RUTA_REFINADOS, "a", encoding="utf-8") as f:
            f.write(f"\n## Refinado el {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n")
            for r in refinados_esta_vez:
                f.write(f"- **{r['equipo_local']} vs {r['equipo_visitante']}**: "
                        f"1X2 {r['prob_local']*100:.0f}/{r['prob_empate']*100:.0f}/{r['prob_visitante']*100:.0f}% | "
                        f"Tarjetas over {r['prob_over_tarjetas']*100:.0f}% | Cuotas: {'sí' if r['tiene_cuotas'] else 'no'}\n")
        print(f"{len(refinados_esta_vez)} partido(s) refinado(s)")
    else:
        print("Ningún partido para refinar en esta pasada")


if __name__ == "__main__":
    main()
