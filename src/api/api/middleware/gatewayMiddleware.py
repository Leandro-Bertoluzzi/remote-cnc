"""FastAPI dependency for the CNC GatewayClient singleton."""

from typing import Annotated

from core.utilities.gateway.gatewayClient import GatewayClient
from fastapi import Depends

_gateway_client: GatewayClient | None = None


def get_gateway_client() -> GatewayClient:
    """Return a shared GatewayClient instance (lazy-initialised)."""
    global _gateway_client  # noqa: PLW0603
    if _gateway_client is None:
        _gateway_client = GatewayClient()
    return _gateway_client


# Type alias for FastAPI dependency injection
GetGateway = Annotated[GatewayClient, Depends(get_gateway_client)]
