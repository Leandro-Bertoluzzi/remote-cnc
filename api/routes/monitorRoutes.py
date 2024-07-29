import asyncio  # noqa: F401
from config import GRBL_LOGS_FILE
from core.utils.logs import LogsInterpreter
from fastapi import APIRouter, Request
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.pubSubMiddleware import GetPubSub
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from typing import Optional

monitorRoutes = APIRouter(prefix="/monitor", tags=["Monitor"])


class LogResponseModel(BaseModel):
    datetime: str
    level: str
    type: Optional[str]
    message: str


class PubSubMessageModel(BaseModel):
    message: str


@monitorRoutes.get('/logs')
def get_logs(
    admin: GetAdminDep
) -> list[LogResponseModel]:
    logs = []
    log_sets = LogsInterpreter().interpret_file(GRBL_LOGS_FILE)

    for datetime, level, type, message in log_sets:
        log_dict = {
            'datetime': datetime,
            'level': level,
            'type': type,
            'message': message,
        }
        logs.append(log_dict)

    return logs


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
