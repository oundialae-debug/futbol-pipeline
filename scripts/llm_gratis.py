"""
LLM gratuito para tareas MECÁNICAS (resumir, clasificar, redactar en bloque).
Nunca para análisis del modelo ni decisiones. Solo datos públicos: lo que se
manda sale a un tercero.

Las claves NO están aquí: son credenciales del entorno (ajustes del entorno ->
API credentials, tipo Bearer) y el proxy las añade solo a las peticiones a su
dominio. Por eso no se envía cabecera Authorization.

Probado el 05/10/2026: Groq y Cerebras responden; Mistral acepta la clave pero
devuelve 429 en todo (plan gratuito de la API sin activar del todo).

Uso:
    from llm_gratis import preguntar
    texto = preguntar("Resume en una línea: ...", max_tokens=300)
o desde la terminal:
    python3 scripts/llm_gratis.py "pregunta"
"""
import json
import sys
import urllib.error
import urllib.request

# (nombre, base, modelo), en orden de preferencia. Si uno falla, se prueba el siguiente.
PROVEEDORES = [
    ("groq", "https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),
    ("cerebras", "https://api.cerebras.ai/v1", "gpt-oss-120b"),
    ("mistral", "https://api.mistral.ai/v1", "mistral-small-latest"),
]


def preguntar(prompt, max_tokens=500, temperatura=0.2, proveedores=PROVEEDORES):
    errores = []
    for nombre, base, modelo in proveedores:
        cuerpo = json.dumps({"model": modelo, "max_tokens": max_tokens, "temperature": temperatura,
                             "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(f"{base}/chat/completions", data=cuerpo,
                                     headers={"Content-Type": "application/json",
                                              # con el "Python-urllib" por defecto, Groq y Cerebras dan 403
                                              "User-Agent": "futbol-pipeline/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
            texto = (d["choices"][0]["message"].get("content") or "").strip()
            if texto:
                return texto
            errores.append(f"{nombre}: respuesta vacía (sube max_tokens)")
        except urllib.error.HTTPError as e:
            errores.append(f"{nombre}: HTTP {e.code}")
        except Exception as e:  # red caída, tiempo agotado...
            errores.append(f"{nombre}: {type(e).__name__}")
    raise RuntimeError("Ningún LLM gratuito respondió: " + "; ".join(errores))


if __name__ == "__main__":
    print(preguntar(" ".join(sys.argv[1:]) or "Responde solo con: hola"))
