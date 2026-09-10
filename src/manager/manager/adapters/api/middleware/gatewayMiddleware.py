"""FastAPI dependency for the shared CNC GatewayClient."""

from typing import Annotated

from core.ports.gateway_client import IGatewayClient
from fastapi import Depends
from manager.adapters.api.context import AppContext
from manager.adapters.api.middleware.contextMiddleware import get_app_context


def get_gateway_client(context: Annotated[AppContext, Depends(get_app_context)]) -> IGatewayClient:
    return context.gateway


# Type alias for FastAPI dependency injection
GetGateway = Annotated[IGatewayClient, Depends(get_gateway_client)]
