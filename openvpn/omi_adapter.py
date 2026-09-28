from . import omi, commands, connection, client

from datetime import datetime
import asyncio
import logging
from typing import override

logger = logging.getLogger(__name__)


async def connect_to_port(socket: str, vpn_client: client.VPNClient) -> tuple[OmiAdapter, asyncio.Future[bool]]:
    loop = asyncio.get_running_loop()
    finish_future = loop.create_future()

    _, protocol = await loop.create_unix_connection(
            lambda: OmiAdapter(finish_future, vpn_client), socket)

    return protocol, finish_future


PKCS11_ID_REQUEST: str = 'pkcs11-id-request'


class OmiAdapter(omi.OmiProtocol):
    '''
    The grandmother adapter
    '''

    def __init__(self, finish_future: asyncio.Future[bool],
                 vpn_client: client.VPNClient):
        self._vpn_client = vpn_client

        connection_properties = omi.ConnectionProperties(password='')
        super().__init__(finish_future, connection_properties)

    def on_token_input(self, callback) -> None:
        self._on_token_input = callback

    @override
    def recv_notify_INFO(self, args: str):
        logger.info(f'Info from management: {args}')

    def recv_notify_NEED_STR(self, args: str) -> None:
        if PKCS11_ID_REQUEST in args:
            message: str = args.split('MSG:')[1]
            self._trigger_token_selection(message)

    def recv_notify_PASSWORD(self, args: str):
        password_name: str = args.split("'")[1]

        self._trigger_password_input(password_name)

    @override
    def recv_notify_LOG(self, args: str):
        timestamp, flag, message = args.split(',', 2)

        if message.startswith('MANAGEMENT'):
            return

        timestamp = datetime.fromtimestamp(int(timestamp)).strftime('%H:%M:%S')
        self._vpn_client.on_log(timestamp, flag, message)

    def recv_notify_STATE(self, args: str):
        self._vpn_client.on_state(connection.parse_status(args))

    @override
    def recv_notify_BYTECOUNT(self, args: str):
        bytes_in, bytes_out = args.split(',', 1)
        self._vpn_client.on_bytecount(connection.Bytecount(int(bytes_in), int(bytes_out)))

    def _trigger_token_selection(self, message: str):
        def token_callback(token: str):
            return self.queue_command(commands.needstr(PKCS11_ID_REQUEST,
                                                       token))

        self._vpn_client.on_token_input(message, token_callback)

    def _trigger_password_input(self, password_name: str):
        def password_callback(password: str):
            return self.queue_command(commands.password(password_name, password))

        self._vpn_client.on_password_input(password_callback)
