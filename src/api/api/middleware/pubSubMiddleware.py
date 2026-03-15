from typing import Annotated

from core.utilities.redisPubSubManager import RedisPubSubManagerAsync
from fastapi import Depends


async def get_pubsub():
    redis = RedisPubSubManagerAsync()
    await redis.connect()
    try:
        yield redis
    finally:
        await redis.disconnect()


# Type definitions
GetPubSub = Annotated[RedisPubSubManagerAsync, Depends(get_pubsub)]
