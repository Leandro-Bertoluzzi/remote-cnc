import asyncio  # noqa: F401
from fastapi import APIRouter, Request
from api.middleware.authMiddleware import GetUserDep
from api.middleware.pubSubMiddleware import GetPubSub
from schemas.general import PubSubMessage
from sse_starlette.sse import EventSourceResponse

monitorRoutes = APIRouter(prefix="/monitor", tags=["Monitor"])


@monitorRoutes.get("/stream/{channel}")
async def stream(
    channel: str,
    redis: GetPubSub,
    user: GetUserDep,
    req: Request
):
    async def subscribe(channel: str, redis: GetPubSub):
        await redis.subscribe(channel)
        while True:
            if await req.is_disconnected():
                break
            message = await redis.get_message()
            if message is not None and 'data' in message.keys():
                data: bytes = message['data']
                yield {"event": channel, "data": data.decode()}

    event_generator = subscribe(channel, redis)
    return EventSourceResponse(event_generator)


@monitorRoutes.post("/messages/{channel}")
async def push_message(
    channel: str,
    request: PubSubMessage,
    redis: GetPubSub,
    user: GetUserDep
):
    await redis.publish(channel, request.message)
