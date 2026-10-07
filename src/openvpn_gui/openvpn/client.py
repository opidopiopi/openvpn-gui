from abc import ABC, abstractmethod
from collections.abc import Callable, Awaitable

from . import omi
from . import connection


class VPNClient(ABC):
    @abstractmethod
    def on_token_input(
        self, message: str, callback: Callable[[str], Awaitable[omi.OmiCommandResult]]
    ) -> None:
        pass

    @abstractmethod
    def on_password_input(
        self, callback: Callable[[str], Awaitable[omi.OmiCommandResult]]
    ) -> None:
        pass

    @abstractmethod
    def on_username_input(
        self, callback: Callable[[str], Awaitable[omi.OmiCommandResult]]
    ) -> None:
        pass

    @abstractmethod
    def on_bytecount(self, bytecount: connection.Bytecount) -> None:
        pass

    @abstractmethod
    def on_state(self, state: connection.State) -> None:
        pass

    @abstractmethod
    def on_log(self, timestamp: str, flag: str, message: str) -> None:
        pass
