import asyncio
import logging
import re

import commands

logger = logging.getLogger(__name__)

command_pattern = r'^>([^:]+):(.*)$'


class State:
    def __init__(self):
        self.pkcs11_id_count: int = 0
        self.pkcs11_ids: list[str] = []


def default_log(level: str, message: str):
    logger.info(f'{level} {message}')


def default_pkcs11_selection(tokens: list[str]):
    logger.info(f'Select token: {tokens}')


def default_password_input(name: str):
    logger.info(f'Enter password {name}')


class OpenVPNConnection:
    def __init__(self, port: int):
        self.host: str = '127.0.0.1'
        self.port: int = port

        self.incoming_commands = {
            'INFO': self._incoming_info,
            'NEED-STR': self._need_string,
            'PKCS11ID-COUNT': self._set_pkcs11id_count,
            'PKCS11ID-ENTRY': self._set_pkcs11id_entry,
            'PASSWORD': self._ask_password,
            'LOG': self._log,
        }
        self.state: State = State()
        self.callback_log = default_log
        self.callback_pkcs11_id_selection = default_pkcs11_selection
        self.callback_password_input = default_password_input
        self.incoming_task = None
        self.writer = None

    async def management_connect(self):
        logger.debug(f'Connecting to {self.host}:{self.port}')
        reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logger.debug('Connected!')

        self.incoming_task = asyncio.create_task(self._incoming_worker(reader))

        await self.send_command(commands.bytecount_on(1))
        await self.send_command(commands.state_on())
        await self.send_command(commands.log_on())

    async def management_disconnect(self):
        if self.incoming_task is None:
            return

        await self.send_command(commands.exit())
        await self.incoming_task

    def management_connected(self):
        if self.incoming_task is None:
            return False

        return not self.incoming_task.done()

    async def client_connect(self):
        await self.send_command(commands.hold_release())

    async def client_disconnect(self):
        await self.send_command(commands.hold_on())
        await self.send_command(commands.sighup())

    def set_log_callback(self, listener):
        self.callback_log = listener

    def reset_log_callback(self):
        self.callback_log = default_log

    def set_pkcs11_id_callback(self, selector):
        self.callback_pkcs11_id_selection = selector

    def reset_pkcs11_id_callback(self):
        self.callback_pkcs11_id_selection = default_pkcs11_selection

    def set_password_callback(self, selector):
        self.callback_password_input = selector

    def reset_password_callback(self):
        self.callback_password_input = default_password_input

    async def loglevel(self, level: int):
        logger.debug(f'Set verbosity to {level}')
        await self.send_command(commands.verbosity(level))

    async def _incoming_info(self, message: str):
        logger.info(message)

    async def _need_string(self, message: str):
        if 'pkcs11-id-request' in message:
            await self.send_command(commands.pkcs11_id_count())

    async def _log(self, message: str):
        message_pattern = r"\d+,(?P<flag>[IFNWD]+),(?P<message>.*)"

        match = re.match(message_pattern, message)
        if match is not None:
            self.callback_log(match.group('flag'), match.group('message'))

    async def _set_pkcs11id_count(self, message: str):
        if not message.isdigit():
            logger.error(f'Invalid pkcs11id count: {message}')
            return

        self.state.pkcs11_id_count = int(message)
        self.state.pkcs11_ids = ['loading'] * self.state.pkcs11_id_count

        for id in range(self.state.pkcs11_id_count):
            logger.debug(f'Getting pkcs11-id #{id}')
            await self.send_command(commands.pkcs11_id_get(id))

    async def _ask_password(self, message: str):
        message_pattern = r"[^']+'(?P<password_name>[^']+)'[^']+"

        match = re.match(message_pattern, message)

        if match is not None:
            logger.debug(f'Requesting password {match.group('password_name')}')
            password: str = await self.callback_password_input(match.group('password_name'))
            await self.send_command(commands.password(match.group('password_name'), password))

    async def _set_pkcs11id_entry(self, message: str):
        message_pattern = r"'(?P<index>\d)', ID:'(?P<id>[^']+)', BLOB:'(?P<blob>[^']+)'"

        match = re.match(message_pattern, message)

        if match is not None:
            index: int = int(match.group('index'))
            token_id: str = match.group('id')

            logger.debug(f'Set pkcs11id {token_id}: {index}')
            self.state.pkcs11_ids[index] = token_id

            if (index + 1) == self.state.pkcs11_id_count:
                logger.debug(
                    f'Selecting one of the following tokens: {self.state.pkcs11_ids}')
                token: str = await self.callback_pkcs11_id_selection(self.state.pkcs11_ids)
                await self.send_command(commands.needstr('pkcs11-id-request', token))

    async def send_command(self, command: commands.Command):
        if self.writer is None:
            return

        logger.debug(f'Sending: {command.command} {command.payload}')

        self.writer.write(
            f'{command.command} {command.payload}'.rstrip().encode('utf-8'))
        self.writer.write('\n'.encode('utf-8'))
        await self.writer.drain()

    async def _incoming_worker(self, reader: asyncio.StreamReader):
        logger.debug('Starting incoming worker')
        while True:
            line = await reader.readline()
            if not line:
                break

            line = line.decode('utf-8').rstrip()
            logger.debug(f'{line}')

            match = re.match(command_pattern, line)
            if line and match:
                command, message = match.groups()
                logger.debug(f'CMD: {command}, MSG: {message}')

                await self.incoming_commands.get(command, self._incoming_info)(message)

        logger.debug('Stopping incoming worker')
