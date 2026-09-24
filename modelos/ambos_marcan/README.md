# Ambos Marcan

Offshoot del pipeline principal ([`futbol-pipeline`](../..)), enfocado solo
en el mercado **Both Teams To Score**. Ver `CLAUDE.md` en esta misma
carpeta para el contexto completo antes de tocar nada.

## Uso rápido

```bash
cd modelos/ambos_marcan
python3 scripts/prueba_humo.py       # sin red, comprueba que todo funciona
python3 scripts/evaluar_mercados.py  # entrena y compara contra el mercado
```

Los datos ya están en `data/` (históricos completos + cuotas filtradas a
Both Teams To Score). No hace falta clave de API para nada de lo anterior.
