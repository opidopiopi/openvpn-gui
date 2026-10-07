class Command:
    def __init__(self, command: str, payload: str):
        self.command: str = command
        self.payload: str = payload


def exit():
    return "exit"


def pkcs11_id_count():
    return "pkcs11-id-count"


def pkcs11_id_get(index: int):
    return f"pkcs11-id-get {str(index)}"


def bytecount_on(seconds: int):
    return f"bytecount {str(seconds)}"


def log_on():
    return "log on"


def verbosity(level: int):
    return f"verb {str(level)}"


def state_last():
    return "state 1"


def state_on():
    return "state on"


def needstr(type: str, message: str) -> str:
    return f"needstr '{type}' '{message}'"


def password(type: str, password: str) -> str:
    return f"password '{type}' '{password}'"


def username(type: str, username: str) -> str:
    return f"username '{type}' '{username}'"


def hold_release():
    return "hold release"


def hold_on():
    return "hold on"


def sighup():
    return "signal SIGHUP"
