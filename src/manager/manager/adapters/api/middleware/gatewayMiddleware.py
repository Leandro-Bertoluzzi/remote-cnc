"""FastAPI dependency for the CNC GatewayClient singleton."""

from functools import lru_cache
from typing import Annotated

from core.adapters.gateway.gateway_client import GatewayClient
from core.ports.gateway_client import IGatewayClient
from fastapi import Depends


@lru_cache(maxsize=1)
def get_gateway_client() -> IGatewayClient:
    """Return a shared GatewayClient instance (created once, cached)."""
    return GatewayClient.from_config()


# Type alias for FastAPI dependency injection
GetGateway = Annotated[IGatewayClient, Depends(get_gateway_client)]
