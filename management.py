import asyncio
import sys
import re
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

command_pattern = r'^>([^:]+):(.*)$'


class Command:
    command = ''
    payload = ''

    def __init__(self, command, payload):
        self.command = command
        self.payload = payload


class OpenVPNConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.task_queue = asyncio.Queue()
        self.incoming_commands = {
            'INFO': self.incoming_info,
            'NEED-STR': self.need_string,
            'PKCS11ID-COUNT': self.set_pkcs11id_count,
            'PKCS11ID-ENTRY': self.set_pkcs11id_entry,
        }


    async def connect(self):
        logger.debug(f'Connecting to {self.host}:{self.port}')
        reader, writer = await asyncio.open_connection(self.host, self.port)
        logger.debug(f'Connected!')

        asyncio.create_task(self.outgoing_worker(writer)),
        asyncio.create_task(self.incoming_worker(reader))
        

    async def close(self):
        self.task_queue.put_nowait(Command('exit', ''))

    def incoming_info(self, message: str):
        logger.info(message)


    def need_string(self, message: str):
        if 'pkcs11-id-request' in message:
            self.task_queue.put_nowait(Command('pkcs11-id-count', ''))


    def set_pkcs11id_count(self, message: str):
        if not message.isdigit():
            logger.error(f'Invalid pkcs11id count: {message}')
            return
        
        for id in range(int(message)):
            logger.debug(f'Getting pkcs11-id #{id}')
            self.task_queue.put_nowait(Command('pkcs11-id-get', str(id)))


    def set_pkcs11id_entry(self, message: str):
        message_pattern = r"'(?P<index>\d)', ID:'(?P<id>[^']+)', BLOB:'(?P<blob>[^']+)'"

        match = re.match(message_pattern, message)

        logger.debug(f'Set pkcs11id {match.group('index')}: {match.group('id')}')


    async def outgoing_worker(self, writer):
        logger.debug('Starting outgoing worker')
        while True:
            command = await self.task_queue.get()

            logger.debug(f'Sending: {command.command} {command.payload}')

            writer.write(f'{command.command} {command.payload}'.rstrip().encode('utf-8'))
            writer.write('\n'.encode('utf-8'))
            await writer.drain()

            self.task_queue.task_done()

            if command.command == 'exit':
                break

        writer.close()
        logger.debug('Stopping outgoing worker')

    async def incoming_worker(self, reader):
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

                command = self.incoming_commands.get(command, self.incoming_info)(message)

        logger.debug('Stopping incoming worker')
