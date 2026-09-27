import pytest
from unittest.mock import MagicMock
import asyncio
from . import omi


pytestmark = pytest.mark.anyio


@pytest.fixture
async def protocol() -> omi.OmiProtocol:
    future: asyncio.Future[bool] = asyncio.Future()
    transport = MagicMock()

    protocol = omi.OmiProtocol(future, omi.ConnectionProperties(''))
    protocol.connection_made(transport)
    return protocol


async def test_pkcs11_id_count(protocol: omi.OmiProtocol):
    result = protocol.queue_command('pkcs11-id-count')

    response = 'PKCS11ID-COUNT:1'
    protocol.data_received(f'>{response}\r\n'.encode())

    await result
    assert result.result().status_text == response


async def test_pkcs11_id_get(protocol: omi.OmiProtocol):
    result = protocol.queue_command('pkcs11-id-get 0')

    response = "PKCS11ID-ENTRY:'0', ID:'...', BLOB:'Hello there!'"
    protocol.data_received(f'>{response}\r\n'.encode())

    await result
    assert result.result().status_text == response
