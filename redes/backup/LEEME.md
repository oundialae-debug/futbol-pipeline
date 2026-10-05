# Backup de publicación sin Claude (2yellow)

Publica solo, con reglas fijas, si Claude no puede ejecutarse (p. ej. sin suscripción). Apagado por defecto.

## Activarlo (2 pasos, una vez)
1. Buffer → https://publish.buffer.com/settings/api → crea una clave de API. En GitHub: repo `futbol-pipeline` → Settings → Secrets and variables → Actions → **Secrets** → New secret `BUFFER_API_KEY` = la clave.
2. Mismo sitio → pestaña **Variables** → New variable `BACKUP_REDES` = `on`.
Para apagarlo: pon `BACKUP_REDES` en `off` (o bórrala). Si Claude vuelve a funcionar, apágalo para no duplicar posts.
Prueba manual: Actions → redes_backup → Run workflow (fase `manana`).

## Qué hace
- 05:45 UTC: elige los 2 partidos de hoy con más peso (puntos FIFA), genera las 6 plantillas, monta el vídeo (música rotada y variante del bandido en `live/scripts/aprender.py`), programa el previo (≥4 h antes del saque, nunca <20 min) y el vídeo del día.
- Cada 20 min (14:00–01:59 UTC): si un partido ya terminó y sus datos están actualizados, genera las 5 de post-partido y publica al momento.
- Registro en `redes/backup/publicaciones_backup.csv` (misma estructura de variante que `redes/publicaciones.csv` de Live).

## Límites (a propósito, sin criterio de Claude)
- Solo selecciones/Nations League por ahora; las ligas necesitan su calendario en `partidos_hoy()`.
- El post-partido depende de que el workflow de datos haya actualizado el resultado; si no, se publica en cuanto lo haga o caduca a las 14 h.
- No revisa métricas ni cambia reglas; no sustituye a Claude, solo mantiene el ritmo.
