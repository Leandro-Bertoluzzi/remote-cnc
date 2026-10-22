import asyncio
from unittest.mock import AsyncMock, MagicMock

from manager.adapters.api.routes.monitorRoutes import stream

from apps.api.tests.fakes import FakeAsyncPubSubClient


def test_invalid_monitor_channel_is_rejected(client, user_headers):
    response = client.get("/monitor/stream/not-allowed", headers=user_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Canal no permitido: not-allowed"


def test_stream_uses_injected_pubsub():
    pubsub = FakeAsyncPubSubClient([b'{"state": "Idle"}'])
    request = MagicMock()
    request.is_disconnected = AsyncMock(side_effect=[False, True])

    async def run():
        response = await stream("grbl_status", MagicMock(), pubsub, request)
        return [event async for event in response.body_iterator]

    chunks = asyncio.run(run())

    assert "grbl_status" in str(chunks) and '{"state": "Idle"}' in str(chunks)
    assert pubsub.handles[0].closed
