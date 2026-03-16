from typing import Any, Optional, Protocol

import redis
import redis.asyncio as aioredis

from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT

# Custom types
PubSubMessage = Optional[dict[str, Any]]


# ---------------------------------------------------------------------------
# Protocols – define the contracts without mixing sync/async signatures
# ---------------------------------------------------------------------------


class PubSubPublisher(Protocol):
    """Minimal publish interface (sync or async callers import the concrete class)."""

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...


# ---------------------------------------------------------------------------
# Async implementation
# ---------------------------------------------------------------------------


class RedisPubSubManagerAsync:
    """Async Redis PubSub manager (for use with FastAPI / asyncio)."""

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB_STORAGE,
    ):
        self._host = host
        self._port = port
        self._db = db
        self.redis_connection: aioredis.Redis | None = None
        self.pubsub: aioredis.client.PubSub | None = None

    async def connect(self) -> None:
        self.redis_connection = aioredis.Redis(
            host=self._host,
            port=self._port,
            db=self._db,
            auto_close_connection_pool=False,
        )
        self.pubsub = self.redis_connection.pubsub()

    async def publish(self, channel: str, message: str) -> None:
        assert self.redis_connection is not None, "Call connect() first"
        await self.redis_connection.publish(channel, message)

    async def get_message(self) -> PubSubMessage:
        assert self.pubsub is not None, "Call connect() first"
        return await self.pubsub.get_message(ignore_subscribe_messages=True)

    async def subscribe(self, channel: str) -> None:
        assert self.pubsub is not None, "Call connect() first"
        await self.pubsub.subscribe(channel)

    async def unsubscribe(self, channel: str) -> None:
        assert self.pubsub is not None, "Call connect() first"
        await self.pubsub.unsubscribe(channel)

    async def disconnect(self) -> None:
        if self.pubsub is not None:
            await self.pubsub.unsubscribe()
            self.pubsub = None
        if self.redis_connection is not None:
            await self.redis_connection.aclose()
            self.redis_connection = None


# ---------------------------------------------------------------------------
# Sync implementation
# ---------------------------------------------------------------------------


class RedisPubSubManagerSync:
    """Synchronous Redis PubSub manager (for use in workers / desktop)."""

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB_STORAGE,
    ):
        self._host = host
        self._port = port
        self._db = db
        self.redis_connection: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None

    def connect(self) -> None:
        self.redis_connection = redis.Redis(host=self._host, port=self._port, db=self._db)
        self.pubsub = self.redis_connection.pubsub()

    def publish(self, channel: str, message: str) -> None:
        assert self.redis_connection is not None, "Call connect() first"
        self.redis_connection.publish(channel, message)

    def get_message(self) -> PubSubMessage:
        assert self.pubsub is not None, "Call connect() first"
        return self.pubsub.get_message(ignore_subscribe_messages=True)

    def subscribe(self, channel: str) -> None:
        assert self.pubsub is not None, "Call connect() first"
        self.pubsub.subscribe(channel)

    def unsubscribe(self, channel: str) -> None:
        assert self.pubsub is not None, "Call connect() first"
        self.pubsub.unsubscribe(channel)

    def disconnect(self) -> None:
        if self.pubsub is not None:
            self.pubsub.unsubscribe()
            self.pubsub = None
        if self.redis_connection is not None:
            self.redis_connection.close()
            self.redis_connection = None
