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
import os
import numpy as np
import pandas as pd
from scipy.stats import nbinom, poisson

RUTA_POR_LIGA = "data/historico_por_liga.csv"
# Ficheros del ajuste antiguo, solo España. Se conservan como respaldo por si
# el nuevo no estuviera generado todavía.
RUTA_HISTORICO = "data/historico_completo_2025_26.csv"
RUTA_EVENTOS = "data/eventos_tarjetas_jugadores_2025_26.csv"

LAMBDA_MINIMA = 0.8   # suelo: nunca suponer que ya no van a salir tarjetas
LIGA_DESCONOCIDA = "(otras)"


def preparar_datos(ruta_por_liga=RUTA_POR_LIGA,
                    ruta_historico=RUTA_HISTORICO, ruta_eventos=RUTA_EVENTOS):
    """Un partido por fila: tarjetas al descanso, en la segunda parte y liga.

    Prefiere el histórico por liga, que reconstruye el reparto a partir del
    MINUTO de cada tarjeta en seis ligas distintas. El anterior salía de
    cruzar dos ficheros de La Liga y solo de La Liga, y eso resultó ser el
    fallo de fondo del modelo: predecía 3.2 tarjetas en la segunda parte para
    todo el mundo cuando la Ligue 1 tiene 2.02, un 65% de más."""
    if os.path.exists(ruta_por_liga):
        d = pd.read_csv(ruta_por_liga)
        base = pd.DataFrame({
            "ht": d["tarjetas_ht"].astype(int),
            "sh": d["tarjetas_2a"].astype(int),
            "liga": d["liga"].astype(str),
        })
        return base.reset_index(drop=True)

    h = pd.read_csv(ruta_historico)
    e = pd.read_csv(ruta_eventos)
    h["total"] = (h.amarillas_local + h.rojas_local +
                  h.amarillas_visitante + h.rojas_visitante)
    e["minuto"] = pd.to_numeric(e["minuto"], errors="coerce")
    e = e.dropna(subset=["minuto"])
    con_eventos = set(e["match_id"].unique())
    base = h[h["match_id"].isin(con_eventos)].copy()
    al_descanso = e[e["minuto"] <= 45].groupby("match_id").size()
    base["ht"] = base["match_id"].map(al_descanso).fillna(0).astype(int)
    base["sh"] = base["total"] - base["ht"]
    base["liga"] = "La Liga"
    return base[["ht", "sh", "liga"]].reset_index(drop=True)


def ajustar(base):
    """Devuelve (interceptos_por_liga, b, phi).

    INTERCEPTO POR LIGA, PENDIENTE COMPARTIDA. Las ligas se diferencian sobre
    todo en el NIVEL -- de 2.02 tarjetas en la segunda parte en la Ligue 1 a
    3.10 en Segunda, un 53% -- y eso hay que recogerlo o el modelo se equivoca
    de liga en liga.

    La pendiente se comparte a propósito. Ajustada por separado sale -0.28 en
    la Ligue 1 y +0.10 en la Premier, pero con 35-91 partidos por liga esas
    diferencias no son distinguibles del ruido (p ~ 0.17 en las dos mayores).
    Darle una pendiente propia a cada liga sería ajustar ruido.

    Conviene saber lo que dice esa pendiente compartida: sale en torno a
    -0.03, o sea prácticamente cero. La hipótesis de la que nació este modelo
    -- que un primer tiempo bronco anuncia una segunda parte más tranquila --
    se sostenía en un -0.289 sacado de un fichero de solo La Liga. Con las
    seis ligas juntas, ese efecto no aparece.
    """
    ligas = sorted(base["liga"].unique())
    X = np.zeros((len(base), len(ligas) + 1))
    for i, l in enumerate(ligas):
        X[:, i] = (base["liga"] == l).astype(float)
    X[:, -1] = base["ht"]
    coef = np.linalg.lstsq(X, base["sh"], rcond=None)[0]

    interceptos = {l: float(coef[i]) for i, l in enumerate(ligas)}
    # Para una liga que no esté en el ajuste -- MLS, Brasil, lo que aparezca
    # en directo -- se usa la media de las conocidas. Es una suposición, y
    # por eso lleva nombre propio en vez de esconderse.
    interceptos[LIGA_DESCONOCIDA] = float(np.mean(list(interceptos.values())))
    b_coef = float(coef[-1])

    esperado = np.maximum(LAMBDA_MINIMA,
                          base["liga"].map(interceptos).fillna(
                              interceptos[LIGA_DESCONOCIDA]) + b_coef * base["ht"])
    residuos = base["sh"] - esperado
    phi = max(1.01, float(residuos.var()) / max(float(base["sh"].mean()), 0.01))
    return interceptos, b_coef, float(phi)


def lambda_de(k, a, b, liga=None):
    """`a` puede ser un número (un solo nivel) o el diccionario de interceptos
    por liga. Lo segundo es lo que devuelve ajustar() ahora."""
    if isinstance(a, dict):
        a = a.get(liga, a.get(LIGA_DESCONOCIDA, np.mean(list(a.values()))))
    return max(LAMBDA_MINIMA, a + b * k)


def _parametros_nb(media, phi):
    """(r, p) de la binomial negativa, o None si no hay sobredispersión."""
    varianza = phi * media
    if varianza <= media:
        return None
    r = media * media / (varianza - media)
    return r, r / (r + media)


def prob_over(k, linea, a, b, phi, liga=None):
    """P(total del partido > linea | k tarjetas al descanso).

    Si k ya supera la línea el mercado está resuelto: se devuelve 1.0, pero
    quien llame debe tratarlo como 'ya decidido', no como una apuesta con
    valor -- la casa habrá cerrado ese mercado."""
    faltan = linea - k
    if faltan < 0:
        return 1.0
    media = lambda_de(k, a, b, liga)
    umbral = int(np.floor(faltan))
    nb = _parametros_nb(media, phi)
    if nb is None:
        return float(1 - poisson.cdf(umbral, media))
    return float(1 - nbinom.cdf(umbral, nb[0], nb[1]))


def prob_push(k, linea, a, b, phi, liga=None):
    """P(total == linea), que es cuando la casa devuelve la apuesta.

    Solo puede pasar en líneas enteras (3.0, 4.0...). En las de .5 es cero.
    Ignorarlo infravalora el Over en las enteras, porque cuenta el empate
    como derrota."""
    if float(linea) != int(linea):
        return 0.0
    faltan = int(linea) - k
    if faltan < 0:
        return 0.0
    media = lambda_de(k, a, b, liga)
    nb = _parametros_nb(media, phi)
    if nb is None:
        return float(poisson.pmf(faltan, media))
    return float(nbinom.pmf(faltan, nb[0], nb[1]))


def valor_esperado(k, linea, cuota, a, b, phi, liga=None):
    """Valor esperado de apostar 1 unidad al Over, contando el push.

    En una línea entera: gana cuota-1 si supera, recupera la unidad si
    empata, pierde 1 si no llega."""
    if not cuota or cuota <= 1:
        return None
    p_over = prob_over(k, linea, a, b, phi, liga)
    p_push = prob_push(k, linea, a, b, phi, liga)
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
        tasa_base = float(((entrena["ht"] + entrena["sh"]) > linea).mean())
        for _, fila in test.iterrows():
            real = 1.0 if (fila["ht"] + fila["sh"]) > linea else 0.0
            err_modelo.append(
                (prob_over(fila["ht"], linea, a, b, phi, fila.get("liga")) - real) ** 2)
            err_base.append((tasa_base - real) ** 2)
    bm, bb = float(np.mean(err_modelo)), float(np.mean(err_base))
    return bm, bb, (bb - bm) / bb * 100 if bb else 0.0


if __name__ == "__main__":
    base = preparar_datos()
    a, b, phi = ajustar(base)
    print(f"Partidos usados: {len(base)} de {base['liga'].nunique()} ligas")
    print(f"pendiente compartida: {b:+.3f} por tarjeta al descanso   phi = {phi:.2f}")
    print("nivel base de cada liga (tarjetas esperadas en la 2a parte con k=0):")
    for liga, v in sorted(a.items(), key=lambda x: -x[1]):
        n = int((base["liga"] == liga).sum())
        print(f"   {liga:20} {v:5.2f}" + (f"   ({n} partidos)" if n else "   (media de las demas)"))
    r = base[["ht", "sh"]].corr().iloc[0, 1]
    print(f"\ncorrelacion descanso vs 2a parte, TODAS juntas: {r:+.3f}")
    print("por liga:")
    for liga, g in base.groupby("liga"):
        if len(g) >= 30:
            print(f"   {liga:20} {g[['ht','sh']].corr().iloc[0,1]:+.3f}  ({len(g)} partidos)")
    bm, bb, mejora = validar(base)
    print(f"\nValidacion out-of-sample (linea 4.5):")
    print(f"  Brier modelo {bm:.4f} | tasa base {bb:.4f} | mejora {mejora:+.1f}%")
    print("\nTABLA P(Over | tarjetas al descanso)")
    lineas = (2.5, 3.5, 4.5, 5.5, 6.5, 7.5)
    print("  HT  " + "  ".join(f"{l:>6.1f}" for l in lineas))
    for k in range(0, 7):
        print(f"  {k:>2d}  " + "  ".join(
            (f"{prob_over(k, l, a, b, phi, 'La Liga')*100:5.1f}%" if not ya_resuelto(k, l) else "  YA  ")
            for l in lineas))
    print("\nEfecto del push en lineas enteras (k=2, cuota 1.80):")
    for l in (3.0, 3.5, 4.0, 4.5):
        sin_push = prob_over(2, l, a, b, phi) * 1.80 - 1
        con_push = valor_esperado(2, l, 1.80, a, b, phi)
        print(f"  linea {l}: sin push {sin_push*100:+.1f}%  con push {con_push*100:+.1f}%")
