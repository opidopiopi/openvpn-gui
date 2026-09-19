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
        self.pksc11_ids: list[str] = []


class OpenVPNConnection:
    def __init__(self, host: str, port: int):
        self.host: str = host
        self.port: int = port
        self.task_queue: asyncio.Queue[commands.Command] = asyncio.Queue()
        self.incoming_commands = {
            'INFO': self._incoming_info,
            'NEED-STR': self._need_string,
            'PKCS11ID-COUNT': self._set_pkcs11id_count,
            'PKCS11ID-ENTRY': self._set_pkcs11id_entry,
            'LOG': self._log,
        }
        self.state: State = State()
        self.log_listeners = [lambda level, message: logger.debug(message)]
        self.pkcs11_id_selectors = []
        self.outgoing_task = None
        self.incoming_task = None

    async def management_connect(self):
        logger.debug(f'Connecting to {self.host}:{self.port}')
        reader, writer = await asyncio.open_connection(self.host, self.port)
        logger.debug('Connected!')

        self.outgoing_task = asyncio.create_task(self._outgoing_worker(writer))
        self.incoming_task = asyncio.create_task(self._incoming_worker(reader))

        self.task_queue.put_nowait(commands.bytecount_on(1))
        self.task_queue.put_nowait(commands.state_on())
        self.task_queue.put_nowait(commands.log_on())

    async def management_disconnect(self):
        if self.outgoing_task is None or self.incoming_task is None:
            return

        self.task_queue.put_nowait(commands.exit())
        await self.task_queue.join()
        await self.outgoing_task
        await self.incoming_task

    def management_connected(self):
        if self.outgoing_task is None or self.incoming_task is None:
            return False

        return not self.outgoing_task.done() and not self.incoming_task.done()

    def add_pkcs11_id_selector(self, selector):
        logger.debug('BLUB')
        self.pkcs11_id_selectors.append(selector)

    def add_log_listener(self, listener):
        self.log_listeners.append(listener)

    def remove_log_listener(self, listener):
        self.log_listeners.remove(listener)

    def loglevel(self, level: int):
        logger.debug(f'Set verbosity to {level}')
        self.task_queue.put_nowait(commands.verbosity(level))

    def _incoming_info(self, message: str):
        logger.info(message)

    def _need_string(self, message: str):
        if 'pkcs11-id-request' in message:
            self.task_queue.put_nowait(commands.pkcs11_id_count())

    def _log(self, message: str):
        message_pattern = r"\d+,(?P<flag>[IFNWD]+),(?P<message>.*)"

        match = re.match(message_pattern, message)
        if match is not None:
            for listener in self.log_listeners:
                listener(match.group('flag'), match.group('message'))

    def _set_pkcs11id_count(self, message: str):
        if not message.isdigit():
            logger.error(f'Invalid pkcs11id count: {message}')
            return

        self.state.pkcs11_id_count = int(message)

        for id in range(self.state.pkcs11_id_count):
            logger.debug(f'Getting pkcs11-id #{id}')
            self.task_queue.put_nowait(commands.pkcs11_id_get(id))

    def _set_pkcs11id_entry(self, message: str):
        message_pattern = r"'(?P<index>\d)', ID:'(?P<id>[^']+)', BLOB:'(?P<blob>[^']+)'"

        match = re.match(message_pattern, message)

        if match is not None:
            index: int = int(match.group('index'))
            token_id: str = match.group('id')

            logger.debug(f'Set pkcs11id {token_id}: {index}')
            self.state.pksc11_ids.append(token_id)

            if (index + 1) == self.state.pkcs11_id_count:
                for selector in self.pkcs11_id_selectors:
                    logger.debug(f'Selecting one of the following tokens: {self.state.pksc11_ids}')
                    selector(self.state.pksc11_ids, lambda token: self.task_queue.put_nowait(
                        commands.needstr('pkcs11-id-request', token)))

    async def _outgoing_worker(self, writer: asyncio.StreamWriter):
        logger.debug('Starting outgoing worker')
        while True:
            command: commands.Command = await self.task_queue.get()

            logger.debug(f'Sending: {command.command} {command.payload}')

            writer.write(
                f'{command.command} {command.payload}'.rstrip().encode('utf-8'))
            writer.write('\n'.encode('utf-8'))
            await writer.drain()

            self.task_queue.task_done()

            if command.command == 'exit':
                break

        writer.close()
        logger.debug('Stopping outgoing worker')

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

                command = self.incoming_commands.get(
                    command, self._incoming_info)(message)

        logger.debug('Stopping incoming worker')
