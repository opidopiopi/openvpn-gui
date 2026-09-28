class Command:
    def __init__(self, command: str, payload: str):
        self.command: str = command
        self.payload: str = payload


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


def state_last():
    return Command('state', '1')


def state_on():
    return Command('state', 'on')


def needstr(type: str, message: str):
    return Command('needstr', f"'{type}' '{message}'")


def password(type: str, password: str):
    return Command('password', f"'{type}' '{password}'")


def hold_release():
    return Command('hold', 'release')


def hold_on():
    return Command('hold', 'on')


def sighup():
    return Command('signal', 'SIGHUP')
