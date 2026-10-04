import asyncio
import logging
from collections.abc import Callable, Awaitable

from . import commands
from . import connection
from . import omi_adapter
from . import client
from . import omi
from . import pkcs11_token

logger = logging.getLogger(__name__)


class OpenVPNConnection(client.VPNClient):
    def __init__(self):
        super().__init__()
        self._connection: omi_adapter.OmiAdapter
        self._connection_closed: asyncio.Future[bool] = asyncio.Future()
        self._connection_closed.set_result(True)

    async def management_connect(self):
        logger.debug('Connecting...')

        self._connection, self._connection_closed = await omi_adapter.connect_to_port('/tmp/openvpn-connection', self)
        await self._connection.management_ready()
        self.callback_management_connected()

        logger.debug('Connected!')

        await self.send_command(commands.bytecount_on(1))
        await self.send_command(commands.state_on())
        result = await self._connection.queue_command(commands.state_last())
        self.callback_state_change(connection.parse_status(result.result[0]))
        await self.send_command(commands.log_on())

    async def management_disconnect(self):
        _ = self._connection.queue_command(commands.exit())
        await self._connection_closed

    def management_connected(self):
        return not self._connection_closed.done()

    async def client_connect(self):
        await self.send_command(commands.hold_release())

    async def client_disconnect(self):
        await self.send_command(commands.hold_on())
        await self.send_command(commands.sighup())

    async def loglevel(self, level: int):
        logger.debug(f'Set verbosity to {level}')
        await self.send_command(commands.verbosity(level))

    async def send_command(self, command: str):
        _ = await self._connection.queue_command(command)

    async def pkcs11_tokens(self) -> list[pkcs11_token.PKCS_11_Token]:
        result = await self._connection.queue_command(commands.pkcs11_id_count())

        token_count = int(result.status_text)
        logger.debug(f'token count: {token_count}')

        tokens = [commands.pkcs11_id_get(i) for i in range(token_count)]
        tokens = await asyncio.gather(*[self._connection.queue_command(command) for command in tokens])
        return list(map(lambda result: pkcs11_token.parse_from(result.status_text), tokens))

    def on_token_input(self, message: str, callback: Callable[[str], Awaitable[omi.OmiCommandResult]]) -> None:
        self.callback_pkcs11_id_selection(message, callback)

    def on_password_input(self, callback: Callable[[str], Awaitable[omi.OmiCommandResult]]) -> None:
        self.callback_password_input(callback)

    def on_bytecount(self, bytecount: connection.Bytecount) -> None:
        self.callback_bytecount(bytecount)

    def on_state(self, state: connection.State) -> None:
        self.callback_state_change(state)

    def on_log(self, timestamp, flag: str, message: str) -> None:
        if message.startswith('net_route_v4_add'):
            route = message.split(':')[1]
            self.callback_add_route(route)

        message = f'{timestamp}: {message}'
        self.callback_log(flag, message)
