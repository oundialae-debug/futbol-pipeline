"""
Inventario de mercados de tenis YA CERRADOS en Kalshi (API pública, sin
clave; aprobado por el usuario el 30/09/2026). Solo lectura de datos.

Mercados liquidados desde el corte (01/08/2026) en /markets y los anteriores en
/historical/markets.

Guarda data/tenis/kalshi/mercados_<serie>.csv con una fila por mercado
(cada partido tiene dos: uno por jugador) y data/tenis/kalshi/inventario.md.
"""
import json
import os
import sys
import time

import pandas as pd
import requests

API = "https://api.elections.kalshi.com/trade-api/v2"
SALIDA = "data/tenis/kalshi"
SERIES = ["KXATPMATCH", "KXWTAMATCH", "KXATPCHALLENGERMATCH", "KXCHALLENGERMATCH", "KXWTACHALLENGERMATCH",
          "KXITFMATCH", "KXITFWMATCH", "KXATPGAMETOTAL", "KXATPGTOTAL", "KXWTAGTOTAL",
          "KXATPGAMESPREAD", "KXATPGSPREAD"]
CAMPOS = ["ticker", "event_ticker", "title", "yes_sub_title", "no_sub_title", "result", "status", "open_time",
          "close_time", "occurrence_datetime", "expected_expiration_time", "settlement_ts", "volume_fp",
          "open_interest_fp", "rules_primary", "floor_strike", "cap_strike", "strike_type", "custom_strike"]


def pedir(url, params):
    for intento in range(5):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 429:
                time.sleep(2 ** intento)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  reintento {intento + 1}: {e}", file=sys.stderr)
            time.sleep(2 ** intento)
    raise RuntimeError(f"sin respuesta de {url} {params}")


def main():
    os.makedirs(SALIDA, exist_ok=True)
    series = sys.argv[1:] or SERIES
    lineas = ["# Kalshi: mercados de tenis cerrados\n", "| serie | mercados | partidos (eventos) | primer cierre | último cierre |",
              "|---|---|---|---|---|"]
    for s in series:
        filas = []
        # /markets solo da lo liquidado desde el corte (/historical/cutoff, 01/08/2026);
        # lo anterior está en /historical/markets. Se piden los dos y se quitan duplicados.
        for ruta, extra in (("markets", {"status": "settled"}), ("historical/markets", {})):
            cursor = None
            while True:
                p = {"series_ticker": s, "limit": 1000, **extra}
                if cursor:
                    p["cursor"] = cursor
                d = pedir(f"{API}/{ruta}", p)
                for m in d.get("markets", []):
                    fila = {c: (json.dumps(m[c]) if isinstance(m.get(c), (dict, list)) else m.get(c)) for c in CAMPOS}
                    fila["origen"] = ruta
                    filas.append(fila)
                cursor = d.get("cursor")
                if not cursor or not d.get("markets"):
                    break
        df = pd.DataFrame(filas, columns=CAMPOS + ["origen"]).drop_duplicates("ticker")
        df.to_csv(f"{SALIDA}/mercados_{s}.csv", index=False)
        if len(df):
            lineas.append(f"| {s} | {len(df)} | {df['event_ticker'].nunique()} | {df['close_time'].min()[:10]} | "
                          f"{df['close_time'].max()[:10]} |")
        else:
            lineas.append(f"| {s} | 0 | 0 | | |")
        print(lineas[-1], flush=True)
    open(f"{SALIDA}/inventario.md", "w").write("\n".join(lineas) + "\n")


if __name__ == "__main__":
    main()
