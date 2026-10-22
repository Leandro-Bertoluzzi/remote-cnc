import asyncio

from fastapi import APIRouter, HTTPException, Request
from manager.adapters.api.middleware.authMiddleware import GetUserDep
from manager.adapters.api.middleware.contextMiddleware import GetPubSub
from sse_starlette.sse import EventSourceResponse

monitorRoutes = APIRouter(prefix="/monitor", tags=["Monitor"])

# Allowed PubSub channels that clients can subscribe to.
_ALLOWED_CHANNELS = {"grbl_status", "grbl_messages", "cnc:events"}


@monitorRoutes.get("/stream/{channel}")
async def stream(channel: str, user: GetUserDep, pubsub_client: GetPubSub, req: Request):
    """SSE endpoint — subscribe to a Gateway PubSub channel.

    Streams real-time CNC status, GRBL messages, or lifecycle events
    depending on the *channel* parameter.
    """
    if channel not in _ALLOWED_CHANNELS:
        raise HTTPException(400, detail=f"Canal no permitido: {channel}")

    async def subscribe():
        pubsub = pubsub_client.pubsub()
        await pubsub.subscribe(channel)
        try:
            while True:
                if await req.is_disconnected():
                    break
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is not None and "data" in message:
                    data = message["data"]
                    text = data.decode() if isinstance(data, bytes) else str(data)
                    yield {"event": channel, "data": text}
                else:
                    await asyncio.sleep(0.05)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    return EventSourceResponse(subscribe())
