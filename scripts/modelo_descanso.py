"""
MODELO DE TARJETAS AL DESCANSO.

Dado el número de tarjetas mostradas al llegar el descanso, estima la
probabilidad de que el total del partido supere cada línea.

OJO: EL MODELO SOLO VALE EN EL DESCANSO
---------------------------------------
lambda(k) está ajustado sobre "cuántas tarjetas caen DESDE EL MINUTO 45
hasta el final". Aplicarlo en el minuto 22, con 68 minutos por delante en
vez de 45, subestima lo que queda y da números sin sentido. Quien llame a
esto debe asegurarse de que el partido está de verdad en el descanso.

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


def _parametros_nb(media, phi):
    """(r, p) de la binomial negativa, o None si no hay sobredispersión."""
    varianza = phi * media
    if varianza <= media:
        return None
    r = media * media / (varianza - media)
    return r, r / (r + media)


def prob_over(k, linea, a, b, phi):
    """P(total del partido > linea | k tarjetas al descanso).

    Si k ya supera la línea el mercado está resuelto: se devuelve 1.0, pero
    quien llame debe tratarlo como 'ya decidido', no como una apuesta con
    valor -- la casa habrá cerrado ese mercado."""
    faltan = linea - k
    if faltan < 0:
        return 1.0
    media = lambda_de(k, a, b)
    umbral = int(np.floor(faltan))
    nb = _parametros_nb(media, phi)
    if nb is None:
        return float(1 - poisson.cdf(umbral, media))
    return float(1 - nbinom.cdf(umbral, nb[0], nb[1]))


def prob_push(k, linea, a, b, phi):
    """P(total == linea), que es cuando la casa devuelve la apuesta.

    Solo puede pasar en líneas enteras (3.0, 4.0...). En las de .5 es cero.
    Ignorarlo infravalora el Over en las enteras, porque cuenta el empate
    como derrota."""
    if float(linea) != int(linea):
        return 0.0
    faltan = int(linea) - k
    if faltan < 0:
        return 0.0
    media = lambda_de(k, a, b)
    nb = _parametros_nb(media, phi)
    if nb is None:
        return float(poisson.pmf(faltan, media))
    return float(nbinom.pmf(faltan, nb[0], nb[1]))


def valor_esperado(k, linea, cuota, a, b, phi):
    """Valor esperado de apostar 1 unidad al Over, contando el push.

    En una línea entera: gana cuota-1 si supera, recupera la unidad si
    empata, pierde 1 si no llega."""
    if not cuota or cuota <= 1:
        return None
    p_over = prob_over(k, linea, a, b, phi)
    p_push = prob_push(k, linea, a, b, phi)
    return p_over * cuota + p_push * 1.0 - 1.0


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
    for k in range(0, 7):
        print(f"  {k:>2d}  " + "  ".join(
            (f"{prob_over(k, l, a, b, phi)*100:5.1f}%" if not ya_resuelto(k, l) else "  YA  ")
            for l in lineas))
    print("\nEfecto del push en lineas enteras (k=2, cuota 1.80):")
    for l in (3.0, 3.5, 4.0, 4.5):
        sin_push = prob_over(2, l, a, b, phi) * 1.80 - 1
        con_push = valor_esperado(2, l, 1.80, a, b, phi)
        print(f"  linea {l}: sin push {sin_push*100:+.1f}%  con push {con_push*100:+.1f}%")
