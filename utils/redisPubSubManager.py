from abc import abstractmethod
import redis
import redis.asyncio as aioredis
from redis.asyncio.client import PubSub
from typing import Any, Optional

try:
    from ..config import REDIS_HOST, REDIS_PORT, REDIS_DB_STORAGE
except ImportError:
    from config import REDIS_HOST, REDIS_PORT, REDIS_DB_STORAGE

# Custom types
PubSubMessage = Optional[dict[str, Any]]


class RedisPubSubManager:
    def __init__(self):
        self.redis_connection = None
        self.pubsub = None

    @abstractmethod
    def _get_redis_connection(self) -> None:
        """
        Establishes a connection to Redis.
        """
        raise NotImplementedError

    @abstractmethod
    def connect(self) -> None:
        """
        Connects to the Redis server and initializes the pubsub client.
        """
        raise NotImplementedError

    @abstractmethod
    def publish(self, channel: str, message: str) -> None:
        """
        Publishes a message to a specific Redis channel.

        Args:
            channel (str): Channel.
            message (str): Message to be published.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_message(self) -> PubSubMessage:
        """
        Get the next message in subscribed topic(s) if one is available, otherwise None.

        Returns:
            PubSubMessage: Message published to subscribed topic(s).
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, channel: str) -> PubSub:
        """
        Subscribes to a Redis channel.

        Args:
            channel (str): Channel to subscribe to.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribes from a Redis channel.

        Args:
            channel (str): Channel to unsubscribe from.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnects from the Redis server and unsubscribes from all channels.
        """
        raise NotImplementedError


class RedisPubSubManagerAsync(RedisPubSubManager):
    async def _get_redis_connection(self) -> aioredis.Redis:
        self.redis_connection = await aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB_STORAGE,
            auto_close_connection_pool=False
        )

    async def connect(self) -> None:
        await self._get_redis_connection()
        self.pubsub = self.redis_connection.pubsub()

    async def publish(self, channel: str, message: str) -> None:
        await self.redis_connection.publish(channel, message)

    async def get_message(self) -> PubSubMessage:
        return await self.pubsub.get_message(ignore_subscribe_messages=True)

    async def subscribe(self, channel: str) -> None:
        await self.pubsub.subscribe(channel)

    async def unsubscribe(self, channel: str) -> None:
        await self.pubsub.unsubscribe(channel)

    async def disconnect(self) -> None:
        await self.pubsub.unsubscribe()
        self.pubsub = None


class RedisPubSubManagerSync(RedisPubSubManager):
    def _get_redis_connection(self) -> None:
        self.redis_connection = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB_STORAGE
        )

    def connect(self) -> None:
        self._get_redis_connection()
        self.pubsub = self.redis_connection.pubsub()

    def publish(self, channel: str, message: str) -> None:
        self.redis_connection.publish(channel, message)

    def get_message(self) -> PubSubMessage:
        return self.pubsub.get_message(ignore_subscribe_messages=True)

    def subscribe(self, channel: str) -> None:
        self.pubsub.subscribe(channel)

    def unsubscribe(self, channel: str) -> None:
        self.pubsub.unsubscribe(channel)

    def disconnect(self) -> None:
        self.pubsub.unsubscribe()
        self.pubsub = None
