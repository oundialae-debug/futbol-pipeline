"""Envío a Buffer (copiado de Live: scripts/enviar_cola.py, origin/main del 10/10/2026; mismas llamadas GraphQL).
Solo stdlib. Necesita BUFFER_API_KEY. Lo usa scripts/post_partido.py."""
import json, os, urllib.request

CANAL = {"instagram": "6ac3c8166a5c39ccb620dd8a", "tiktok": "6ac3c8456a5c39ccb620dec4"}
Q = "mutation($i:CreatePostInput!){createPost(input:$i){__typename ... on PostActionSuccess{post{id}} ... on MutationError{message}}}"


def gql(q, v):
    rq = urllib.request.Request(os.environ.get("BUFFER_URL", "https://api.buffer.com"),
                                json.dumps({"query": q, "variables": v}).encode(),
                                {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["BUFFER_API_KEY"]})
    return json.load(urllib.request.urlopen(rq, timeout=60))


def entrada(x, due):
    """Igual que Live/enviar_cola.entrada: con "video" -> automático (IG reel al feed); con imágenes -> recordatorio."""
    video = "video" in x
    if x["red"] == "instagram":
        tipo = "reel" if video else ("carousel" if len(x.get("imagenes", [])) > 1 else "post")
        meta = {"instagram": {"type": tipo, "shouldShareToFeed": True}}
        # primer comentario: NO, Buffer lo reserva al plan de pago
    else:
        meta = {"tiktok": {"title": x.get("titulo", x["text"].split("\n")[0])[:90]}}
    assets = [{"video": {"url": x["video"]}}] if video else [{"image": {"url": u}} for u in x["imagenes"]]
    return {"channelId": CANAL[x["red"]], "text": x["text"], "assets": assets, "metadata": meta, "mode": "customScheduled",
            "dueAt": due.isoformat(timespec="seconds"),
            "schedulingType": "notification" if x.get("recordatorio", not video) else "automatic"}


def enviar(x, due):
    """Devuelve (buffer_id | None, respuesta resumida)."""
    r = gql(Q, {"i": entrada(x, due)})
    d = (r.get("data") or {}).get("createPost") or {}
    if d.get("__typename") == "PostActionSuccess":
        return d["post"]["id"], "ok"
    return None, json.dumps(r)[:300]
