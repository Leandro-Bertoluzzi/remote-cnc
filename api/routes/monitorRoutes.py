import asyncio  # noqa: F401
from fastapi import APIRouter, Request
from middleware.authMiddleware import GetUserDep
from middleware.pubSubMiddleware import GetPubSub
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

monitorRoutes = APIRouter(prefix="/monitor", tags=["Monitor"])


class PubSubMessageModel(BaseModel):
    message: str


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
    request: PubSubMessageModel,
    redis: GetPubSub,
    user: GetUserDep
):
    await redis.publish(channel, request.message)
