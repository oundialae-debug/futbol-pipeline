"""
Partidos de la UEFA Nations League de un día y sus cuotas (26/09/2026).

Petición del usuario, tema APARTE del proyecto de ambos marcan (ver
modelos/ambos_marcan/CLAUDE.md "PUNTO DE RETORNO"). No usa ningún modelo:
lista partidos (hora de España) y cuotas de 1X2, más/menos 2.5 y ambos
marcan, por casa. Por mercado y lado: mejor cuota, mediana, nº de casas,
probabilidad sin margen de la mediana y margen medio.

Liga: UEFA Nations League, id 5039 (CLAUDE.md, sondeo del 24/09).
~1 + nº de partidos llamadas. Escribe nations_league_hoy.md.
"""
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
import pandas as pd

API_KEY = os.environ["HIGHLIGHTLY_API_KEY"]
HEADERS = {"x-rapidapi-key": API_KEY}   # nunca se imprime
BASE_URL = "https://soccer.highlightly.net"
LIGA = 5039
MADRID = ZoneInfo("Europe/Madrid")
FECHA = os.environ.get("FECHA") or datetime.now(MADRID).date().isoformat()
MERCADOS = {"Full Time Result": ["Home", "Draw", "Away"],
            "Total Goals 2.5": ["Over", "Under"],
            "Both Teams To Score": ["Yes", "No"]}


def pedir(path, params=None):
    for intento in range(3):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
        except Exception:
            time.sleep(2 * (intento + 1)); continue
        if r.status_code == 429:
            time.sleep(5); continue
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] {path}")
            return None
        try:
            return r.json()
        except Exception:
            return None
    return None


def lista(d):
    if isinstance(d, dict):
        for k in ("data", "records", "results"):
            if isinstance(d.get(k), list):
                return d[k]
        return [d]
    return d or []


def main():
    j = pedir("/matches", {"leagueId": LIGA, "date": FECHA, "timezone": "Europe/Madrid"})
    partidos = [p for p in lista(j) if isinstance(p, dict) and p.get("id")]
    lineas = [f"# UEFA Nations League, {FECHA} (hora de España)\n",
              "Cuotas prematch de la API. Tema aparte del proyecto; sin modelo.\n"]
    print(f"{len(partidos)} partidos el {FECHA}")
    filas_resumen = []
    for p in sorted(partidos, key=lambda x: str(x.get("date"))):
        loc = (p.get("homeTeam") or {}).get("name", "?")
        vis = (p.get("awayTeam") or {}).get("name", "?")
        try:
            hora = datetime.fromisoformat(str(p.get("date")).replace("Z", "+00:00")).astimezone(MADRID).strftime("%H:%M")
        except Exception:
            hora = "?"
        estado = ((p.get("state") or {}).get("description")) if isinstance(p.get("state"), dict) else p.get("state")
        lineas.append(f"\n## {hora}  {loc} - {vis}  ({estado})\n")
        print(f"\n{hora}  {loc} - {vis}  ({estado})")
        o = pedir("/odds", {"matchId": p["id"], "oddsType": "prematch"})
        filas = []
        for b in lista(o):
            for c in (b.get("odds") or []) if isinstance(b, dict) else []:
                if c.get("market") in MERCADOS:
                    for v in c.get("values") or []:
                        try:
                            filas.append({"mercado": c["market"], "casa": c.get("bookmakerName"),
                                          "lado": str(v.get("value")), "cuota": float(v.get("odd"))})
                        except (TypeError, ValueError):
                            pass
        d = pd.DataFrame(filas)
        if d.empty:
            lineas.append("Sin cuotas todavía en la API para estos mercados.\n")
            print("  sin cuotas")
            continue
        for mercado, lados in MERCADOS.items():
            m = d[(d.mercado == mercado) & d.lado.isin(lados)]
            if m.empty:
                continue
            piv = m.pivot_table(index="casa", columns="lado", values="cuota", aggfunc="last").dropna()
            piv = piv[[l for l in lados if l in piv.columns]]
            if piv.empty or piv.shape[1] != len(lados):
                continue
            med = piv.median()
            inv = 1 / med
            prob = inv / inv.sum()
            margen = ((1 / piv).sum(axis=1) - 1).mean()
            lineas += [f"**{mercado}** ({len(piv)} casas, margen medio {margen*100:.1f}%)\n",
                       "| lado | mejor cuota (casa) | mediana | prob. sin margen |", "|---|---|---|---|"]
            for l in lados:
                mejor = piv[l].max(); casa = piv[l].idxmax()
                lineas.append(f"| {l} | {mejor:.2f} ({casa}) | {med[l]:.2f} | {prob[l]*100:.1f}% |")
                filas_resumen.append({"hora": hora, "partido": f"{loc} - {vis}", "mercado": mercado,
                                      "lado": l, "mejor": mejor, "casa_mejor": casa,
                                      "mediana": med[l], "prob": prob[l], "casas": len(piv)})
            lineas.append("")
            print(f"  {mercado}: " + "  ".join(f"{l} {med[l]:.2f} (mejor {piv[l].max():.2f})" for l in lados)
                  + f"  [{len(piv)} casas]")
    open("nations_league_hoy.md", "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    pd.DataFrame(filas_resumen).to_csv("data/nations_league_hoy.csv", index=False)
    print("\nEscrito nations_league_hoy.md y data/nations_league_hoy.csv")


if __name__ == "__main__":
    main()
