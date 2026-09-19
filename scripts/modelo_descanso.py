"""
MODELO DE TARJETAS AL DESCANSO.

Dado el número de tarjetas mostradas al llegar el descanso, estima la
probabilidad de que el total del partido supere cada línea.

EL HALLAZGO QUE DEFINE EL MODELO
--------------------------------
La correlación entre tarjetas al descanso y tarjetas en la segunda parte es
NEGATIVA (-0.171 sobre 427 partidos):

    tarjetas al descanso:   0     1     2     3     4
    media en 2a parte:    3.79  3.11  3.29  2.86  2.65

Es decir: un primer tiempo bronco NO anticipa un segundo tiempo bronco. Toda
la señal del descanso viene de las tarjetas que ya están en el banco, no de
un ritmo elevado que vaya a continuar. Modelar esto al revés -- que es lo
intuitivo -- sobreestimaría los Over sistemáticamente.

CÓMO SE MODELA
--------------
Total final = tarjetas del descanso (conocidas) + tarjetas de la 2a parte.
La segunda parte se modela como binomial negativa:

    media   lambda(k) = a + b*k    (b negativo, por lo de arriba)
    varianza = phi * lambda        (phi ~ 1.24, por encima de Poisson)

La binomial negativa, y no Poisson, porque la varianza observada supera
claramente a la media. Usar Poisson daría colas demasiado finas y por tanto
exceso de confianza en las líneas extremas.

Los coeficientes se recalculan desde los CSV en cada ejecución, así que el
modelo se afina solo conforme se acumulan jornadas.
"""
import numpy as np
import pandas as pd
from scipy.stats import nbinom, poisson

RUTA_HISTORICO = "data/historico_completo_2025_26.csv"
RUTA_EVENTOS = "data/eventos_tarjetas_jugadores_2025_26.csv"

LAMBDA_MINIMA = 0.8   # suelo: nunca suponer que ya no van a salir tarjetas


def preparar_datos(ruta_historico=RUTA_HISTORICO, ruta_eventos=RUTA_EVENTOS):
    """Cruza histórico y eventos para sacar, por partido, cuántas tarjetas
    hubo al descanso y cuántas en la segunda parte."""
    h = pd.read_csv(ruta_historico)
    e = pd.read_csv(ruta_eventos)
    h["total"] = (h.amarillas_local + h.rojas_local +
                  h.amarillas_visitante + h.rojas_visitante)
    e["minuto"] = pd.to_numeric(e["minuto"], errors="coerce")
    e = e.dropna(subset=["minuto"])

    # solo partidos de los que tenemos los eventos completos; si no, un partido
    # sin eventos registrados parecería tener 0 tarjetas al descanso
    con_eventos = set(e["match_id"].unique())
    base = h[h["match_id"].isin(con_eventos)].copy()
    al_descanso = e[e["minuto"] <= 45].groupby("match_id").size()
    base["ht"] = base["match_id"].map(al_descanso).fillna(0).astype(int)
    base["sh"] = base["total"] - base["ht"]
    return base.reset_index(drop=True)


def ajustar(base):
    """Devuelve (a, b, phi) del modelo de la segunda parte."""
    b_coef, a_coef = np.polyfit(base["ht"], base["sh"], 1)
    esperado = np.maximum(LAMBDA_MINIMA, a_coef + b_coef * base["ht"])
    residuos = base["sh"] - esperado
    phi = max(1.01, float(residuos.var()) / max(float(base["sh"].mean()), 0.01))
    return float(a_coef), float(b_coef), float(phi)


def lambda_de(k, a, b):
    return max(LAMBDA_MINIMA, a + b * k)


def prob_over(k, linea, a, b, phi):
    """P(total del partido > linea | k tarjetas al descanso).

    Si k ya supera la línea el mercado está resuelto: se devuelve 1.0, pero
    quien llame debe tratarlo como 'ya decidido', no como una apuesta con
    valor -- la casa habrá cerrado ese mercado."""
    faltan = linea - k
    if faltan < 0:
        return 1.0
    media = lambda_de(k, a, b)
    varianza = phi * media
    umbral = int(np.floor(faltan))
    if varianza <= media:   # sin sobredispersión, Poisson
        return float(1 - poisson.cdf(umbral, media))
    r = media * media / (varianza - media)
    p = r / (r + media)
    return float(1 - nbinom.cdf(umbral, r, p))


def ya_resuelto(k, linea):
    return k > linea


def validar(base, linea=4.5, bloques=5, semilla=7):
    """Validación fuera de muestra contra la tasa base. Devuelve
    (brier_modelo, brier_base, mejora_relativa)."""
    indices = np.arange(len(base))
    np.random.default_rng(semilla).shuffle(indices)
    particiones = np.array_split(indices, bloques)
    err_modelo, err_base = [], []
    for i in range(bloques):
        test = base.iloc[particiones[i]]
        entrena = base.iloc[np.concatenate([particiones[j] for j in range(bloques) if j != i])]
        a, b, phi = ajustar(entrena)
        tasa_base = float((entrena["total"] > linea).mean())
        for _, fila in test.iterrows():
            real = 1.0 if fila["total"] > linea else 0.0
            err_modelo.append((prob_over(fila["ht"], linea, a, b, phi) - real) ** 2)
            err_base.append((tasa_base - real) ** 2)
    bm, bb = float(np.mean(err_modelo)), float(np.mean(err_base))
    return bm, bb, (bb - bm) / bb * 100 if bb else 0.0


def tabla(a, b, phi, lineas=(2.5, 3.5, 4.5, 5.5, 6.5, 7.5), maximo_ht=6):
    """Tabla legible P(Over | tarjetas al descanso), para el informe."""
    filas = []
    for k in range(maximo_ht + 1):
        filas.append((k, {l: prob_over(k, l, a, b, phi) for l in lineas}))
    return filas


if __name__ == "__main__":
    base = preparar_datos()
    a, b, phi = ajustar(base)
    print(f"Partidos usados: {len(base)}")
    print(f"lambda(k) = max({LAMBDA_MINIMA}, {a:.3f} {b:+.3f}*k)   phi = {phi:.2f}")
    print(f"correlacion descanso vs 2a parte: {base[['ht','sh']].corr().iloc[0,1]:+.3f}")
    bm, bb, mejora = validar(base)
    print(f"\nValidacion out-of-sample (linea 4.5):")
    print(f"  Brier modelo {bm:.4f} | tasa base {bb:.4f} | mejora {mejora:+.1f}%")
    print("\nTABLA P(Over | tarjetas al descanso)")
    lineas = (2.5, 3.5, 4.5, 5.5, 6.5, 7.5)
    print("  HT  " + "  ".join(f"{l:>6.1f}" for l in lineas))
    for k, probs in tabla(a, b, phi):
        marca = lambda l: "  YA " if ya_resuelto(k, l) else ""
        print(f"  {k:>2d}  " + "  ".join(
            (f"{probs[l]*100:5.1f}%" if not ya_resuelto(k, l) else "  YA  ") for l in lineas))
