"""
Cruza las cuotas históricas de football-data.co.uk con nuestros partidos
(24/09/2026). La API borra las cuotas a los 28 días; esta fuente las guarda
de temporadas enteras: media de casas (Avg), máxima (Max), Bet365, Pinnacle
(P) antes del partido, y las de cierre (sufijo C).

Cruce: misma liga, fecha a ±1 día, mismo marcador, y el par de nombres más
parecido (los nombres no coinciden entre fuentes: "Man City" / "Manchester
City"). Se exige similitud mínima; lo dudoso se descarta y se cuenta.
Salida: data/cuotas_football_data.csv (match_id + cuotas Más/Menos 2.5).
"""
import glob, difflib, unicodedata, re
import numpy as np, pandas as pd

DIV = {"E0": "Premier League", "SP1": "La Liga", "SP2": "Segunda", "I1": "Serie A",
       "D1": "Bundesliga", "F1": "Ligue 1"}
COLS = ["B365>2.5", "B365<2.5", "P>2.5", "P<2.5", "Max>2.5", "Max<2.5", "Avg>2.5", "Avg<2.5",
        "PC>2.5", "PC<2.5", "AvgC>2.5", "AvgC<2.5", "MaxC>2.5", "MaxC<2.5"]


ALIAS = {"ath bilbao": "athletic club", "m'gladbach": "borussia monchengladbach",
         "paris sg": "paris saint germain", "celta b": "celta de vigo ii"}


def norm(s):
    s = ALIAS.get(str(s).strip().lower(), s)
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(fc|cf|ac|afc|sc|ssc|as|us|rc|cd|ud|sd|ca|club|de|1\.|vfb|vfl|tsg|sv|bsc|fsv|rcd|ogc|stade|olympique)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


fd = []
for f in sorted(glob.glob("data/football_data/*.csv")):
    d = pd.read_csv(f, encoding="utf-8-sig", on_bad_lines="skip")
    d = d.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    d["liga"] = DIV[f.split("/")[-1].split("_")[0]]
    d["fecha"] = pd.to_datetime(d["Date"], dayfirst=True, errors="coerce")
    fd.append(d[["liga", "fecha", "HomeTeam", "AwayTeam", "FTHG", "FTAG"] + [c for c in COLS if c in d.columns]])
fd = pd.concat(fd, ignore_index=True)

h = pd.read_csv("data/historico_partidos.csv").dropna(subset=["goles_l", "goles_v"])
h["dia"] = pd.to_datetime(h.fecha, format="mixed", utc=True).dt.tz_localize(None).dt.normalize()

filas, dudosos, sin_par = [], 0, 0
por_clave = {k: g for k, g in fd.groupby(["liga", "FTHG", "FTAG"])}
for r in h.itertuples(index=False):
    g = por_clave.get((r.liga, r.goles_l, r.goles_v))
    if g is None:
        sin_par += 1; continue
    g = g[(g.fecha - r.dia).abs() <= pd.Timedelta(days=1)]
    if g.empty:
        sin_par += 1; continue
    s = g.apply(lambda x: min(sim(x.HomeTeam, r.local), sim(x.AwayTeam, r.visitante)), axis=1)
    if s.max() < 0.6:
        dudosos += 1; continue
    x = g.loc[s.idxmax()]
    filas.append({"match_id": r.match_id, "fd_local": x.HomeTeam, "fd_visit": x.AwayTeam,
                  "sim": round(s.max(), 2), **{c: x.get(c, np.nan) for c in COLS}})
out = pd.DataFrame(filas)
dup = out.match_id.duplicated().sum()
out.to_csv("data/cuotas_football_data.csv", index=False)
print(f"{len(h)} partidos nuestros | cruzados {len(out)} ({len(out)/len(h)*100:.1f}%) | "
      f"sin candidato {sin_par} | dudosos (nombre < 0.6) {dudosos} | duplicados {dup}")
print("Similitud más baja aceptada (revisar a ojo):")
print(out.sort_values("sim").head(8)[["fd_local", "fd_visit", "sim"]].merge(
    h[["match_id", "local", "visitante"]], left_index=False, right_index=False, how="left",
    left_on=out.sort_values("sim").head(8).match_id.values, right_on="match_id").to_string(index=False))
print(f"con Avg>2.5: {out['Avg>2.5'].notna().sum()}, con Pinnacle cierre: {out['PC>2.5'].notna().sum()}")
