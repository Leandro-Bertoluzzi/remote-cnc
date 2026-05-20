"""FastAPI dependency for the CNC GatewayClient singleton."""

from typing import Annotated

from core.adapters.gateway.gateway_client import GatewayClient
from core.ports.gateway_client import IGatewayClient
from fastapi import Depends

_gateway_client: IGatewayClient | None = None


def get_gateway_client() -> IGatewayClient:
    """Return a shared GatewayClient instance (lazy-initialised)."""
    global _gateway_client  # noqa: PLW0603
    if _gateway_client is None:
        _gateway_client = GatewayClient.from_config()
    return _gateway_client


# Type alias for FastAPI dependency injection
GetGateway = Annotated[IGatewayClient, Depends(get_gateway_client)]
