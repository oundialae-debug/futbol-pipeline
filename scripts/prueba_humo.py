"""Prueba de humo SIN red: ejercita las rutas de formato que py_compile no ve."""
import sys, os
sys.path.insert(0, "scripts")
os.environ.setdefault("HIGHLIGHTLY_API_KEY", "prueba")
import descanso_en_vivo as dv

base = dv.preparar_datos()
a, b, phi = dv.ajustar(base)
print(f"ajuste: {len(a)} niveles, pendiente {b:+.3f}")

# la linea que rompio en produccion
print(f"Modelo sobre {len(base)} partidos de {base['liga'].nunique()} ligas: "
      f"pendiente {b:+.3f}, phi={phi:.2f}")
print("  niveles: " + ", ".join(f"{l} {v:.2f}" for l, v in sorted(a.items(), key=lambda x: -x[1])))

# escribir_informe con un bloque falso, que es donde estan los demas formatos
info = {"match_id": 1, "partido": "A vs B", "liga": "Ligue 1", "minuto": 45,
        "estado": "Half time", "liga_modelo": "Ligue 1", "marcador": "0 - 0",
        "tarjetas_ht": 2, "faltas_ht": 11.0, "corners_ht": 3.0,
        "minutos_tarjetas": ["20", "40"], "lambda_restante": 1.96}
filas = [{"match_id": 1, "partido": "A vs B", "liga": "Ligue 1", "minuto": 45,
          "estado": "Half time", "tarjetas_ht": 2, "faltas_ht": 11.0,
          "corners_ht": 3.0, "liga_modelo": "Ligue 1", "linea": 4.0,
          "prob_modelo": 0.31, "prob_push": 0.17, "prob_mercado": 0.40,
          "casas": 2, "mejor_cuota": 2.5, "mejor_casa": "X", "ev": -0.05,
          "resuelto": False, "momento": "2026-09-20T17:00:00+00:00"}]
dv.RUTA_INFORME = "/tmp/claude-0/informe_prueba.md"
dv.escribir_informe([(info, filas)], [("C vs D", 30)], a, b, phi, base)
print("\nescribir_informe: OK")
