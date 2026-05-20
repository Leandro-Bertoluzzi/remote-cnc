"""Application context for the Desktop application.

``AppContext`` is the composition root: it holds all infrastructure dependencies.

Views and helpers receive ``AppContext`` (or just the ports they need)
via constructor arguments — never by importing singletons directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.adapters.gateway.gateway_client import GatewayClient
from core.ports.gateway_client import IGatewayClient


@dataclass
class AppContext:
    """Container for shared infrastructure dependencies."""

    gateway: IGatewayClient = field(default_factory=GatewayClient.from_config)


def create_app_context() -> AppContext:
    """Build the production ``AppContext`` from environment config."""
    return AppContext(gateway=GatewayClient.from_config())
