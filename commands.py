
class Command:
    command = ''
    payload = ''

    def __init__(self, command, payload):
        self.command = command
        self.payload = payload

def exit():
    return Command('exit', '')

def pkcs11_id_count():
    return Command('pkcs11-id-count', '')

def pkcs11_id_get(index: int):
    return Command('pkcs11-id-get', str(index))

def bytecount_on(seconds: int):
    return Command('bytecount', str(seconds))

def log_on():
    return Command('log', 'on')

def verbosity(level: int):
    return Command('verb', str(level))

def status():
    return Command('status', 'on')
