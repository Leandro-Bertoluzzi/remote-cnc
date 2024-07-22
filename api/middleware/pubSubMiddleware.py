from core.utils.redisPubSubManager import RedisPubSubManagerAsync
from fastapi import Depends
from typing import Annotated


async def get_pubsub():
    redis = RedisPubSubManagerAsync()
    await redis.connect()
    try:
        yield redis
    finally:
        await redis.disconnect()


# Type definitions
GetPubSub = Annotated[RedisPubSubManagerAsync, Depends(get_pubsub)]
