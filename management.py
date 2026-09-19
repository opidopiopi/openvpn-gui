import asyncio
import logging
import re

import commands

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

command_pattern = r'^>([^:]+):(.*)$'


class State:
    def __init__(self):
        self.pkcs11_id_count: int = 0
        self.pkcs11_ids: list[str] = []


class OpenVPNConnection:
    def __init__(self, host: str, port: int):
        self.host: str = host
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
        self.log_listeners = [lambda level, message: logger.debug(message)]
        self.pkcs11_id_selectors = []
        self.password_selectors = []
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

    def add_pkcs11_id_selector(self, selector):
        logger.debug('BLUB')
        self.pkcs11_id_selectors.append(selector)

    def add_log_listener(self, listener):
        self.log_listeners.append(listener)

    def remove_log_listener(self, listener):
        self.log_listeners.remove(listener)

    def add_password_selector(self, selector):
        self.password_selectors.append(selector)

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
            for listener in self.log_listeners:
                listener(match.group('flag'), match.group('message'))

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
            for selector in self.password_selectors:
                password: str = await selector(match.group('password_name'))
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
                for selector in self.pkcs11_id_selectors:
                    logger.debug(
                        f'Selecting one of the following tokens: {self.state.pkcs11_ids}')
                    token: str = await selector(self.state.pkcs11_ids)
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
