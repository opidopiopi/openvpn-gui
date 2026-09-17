import asyncio
import urllib.parse
import sys
import re
import logging

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

command_pattern = r'^>([^:]+):(.*)$'



def incoming_info(message: str, task_queue):
    logger.info(message)


def need_string(message: str, task_queue):
    if 'pkcs11-id-request' in message:
        task_queue.put_nowait(Command('pkcs11-id-count', ''))


def set_pkcs11id_count(message: str, task_queue):
    if not message.isdigit():
        logger.error(f'Invalid pkcs11id count: {message}')
        return
    
    for id in range(int(message)):
        logger.debug(f'Getting pkcs11-id #{id}')
        task_queue.put_nowait(Command('pkcs11-id-get', str(id)))


def set_pkcs11id_entry(message: str, task_queue):
    message_pattern = r"'(?P<index>\d)', ID:'(?P<id>[^']+)', BLOB:'(?P<blob>[^']+)'"

    match = re.match(message_pattern, message)

    logger.debug(f'Set pkcs11id {match.group('index')}: {match.group('id')}')


incoming_commands = {
        'INFO': incoming_info,
        'NEED-STR': need_string,
        'PKCS11ID-COUNT': set_pkcs11id_count,
        'PKCS11ID-ENTRY': set_pkcs11id_entry,
        }


class Command:
    command = ''
    payload = ''

    def __init__(self, command, payload):
        self.command = command
        self.payload = payload


async def outgoing_worker(out_queue, writer):
    logger.debug('Starting outgoing worker')
    while True:
        command = await out_queue.get()

        logger.debug(f'Sending: {command.command} {command.payload}')

        writer.write(f'{command.command} {command.payload}'.rstrip().encode('utf-8'))
        writer.write('\n'.encode('utf-8'))
        await writer.drain()

        out_queue.task_done()


async def main(host, port):
    reader, writer = await asyncio.open_connection(host, port)

    logger.debug(f'Connected to {host}:{port}')

    queue = asyncio.Queue()

    asyncio.create_task(outgoing_worker(queue, writer))

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

            command = incoming_commands.get(command, incoming_info)(message, queue)

    # Ignore the body, close the socket
    writer.close()
    await writer.wait_closed()

asyncio.run(main('localhost', 8888))
