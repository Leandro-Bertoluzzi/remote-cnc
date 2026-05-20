"""Shared port abstractions for all modules.

See DR-0007 for the architectural rationale.
"""

from core.ports.gateway_client import IGatewayClient
from core.ports.redis_client import RedisClient

__all__ = ["IGatewayClient", "RedisClient"]
