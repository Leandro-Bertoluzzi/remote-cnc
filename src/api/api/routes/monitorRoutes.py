import asyncio

import redis.asyncio as aioredis
from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT
from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from api.middleware.authMiddleware import GetUserDep

monitorRoutes = APIRouter(prefix="/monitor", tags=["Monitor"])

# Allowed PubSub channels that clients can subscribe to.
_ALLOWED_CHANNELS = {"grbl_status", "grbl_messages", "cnc:events"}


@monitorRoutes.get("/stream/{channel}")
async def stream(channel: str, user: GetUserDep, req: Request):
    """SSE endpoint — subscribe to a Gateway PubSub channel.

    Streams real-time CNC status, GRBL messages, or lifecycle events
    depending on the *channel* parameter.
    """
    if channel not in _ALLOWED_CHANNELS:
        raise HTTPException(400, detail=f"Canal no permitido: {channel}")

    async def subscribe():
        conn = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB_STORAGE,
            auto_close_connection_pool=False,
        )
        pubsub = conn.pubsub()
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
                    data: bytes = message["data"]
                    yield {"event": channel, "data": data.decode()}
                else:
                    await asyncio.sleep(0.05)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await conn.aclose()

    return EventSourceResponse(subscribe())
