import redis.asyncio as aioredis
from redis.asyncio.client import PubSub

try:
    from ..config import REDIS_HOST, REDIS_PORT, REDIS_DB_STORAGE
except ImportError:
    from config import REDIS_HOST, REDIS_PORT, REDIS_DB_STORAGE


class RedisPubSubManager:
    def __init__(self):
        self.pubsub = None

    async def _get_redis_connection(self) -> aioredis.Redis:
        """
        Establishes a connection to Redis.

        Returns:
            aioredis.Redis: Redis connection object.
        """
        return aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB_STORAGE,
            auto_close_connection_pool=False
        )

    async def connect(self) -> None:
        """
        Connects to the Redis server and initializes the pubsub client.
        """
        self.redis_connection = await self._get_redis_connection()
        self.pubsub = self.redis_connection.pubsub()

    async def _publish(self, channel: str, message: str) -> None:
        """
        Publishes a message to a specific Redis channel.

        Args:
            channel (str): Channel.
            message (str): Message to be published.
        """
        await self.redis_connection.publish(channel, message)

    async def subscribe(self, channel: str) -> PubSub:
        """
        Subscribes to a Redis channel.

        Args:
            channel (str): Channel to subscribe to.

        Returns:
            PubSub: PubSub object for the subscribed channel.
        """
        await self.pubsub.subscribe(channel)
        return self.pubsub

    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribes from a Redis channel.

        Args:
            channel (str): Channel to unsubscribe from.
        """
        await self.pubsub.unsubscribe(channel)

    async def disconnect(self) -> None:
        """
        Disconnects from the Redis server and unsubscribes from all channels.
        """
        await self.pubsub.unsubscribe()
        self.pubsub = None
