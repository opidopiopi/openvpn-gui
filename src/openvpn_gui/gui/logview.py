from nicegui import ui


class Logview:
    def __init__(self):
        self._log: ui.log = ui.log().classes("col-span-full")

    def append(self, level: str, message: str) -> None:
        if "F" in level:
            self._log.push(message, classes="text-red")
        if "W" in level:
            self._log.push(message, classes="text-orange")
        else:
            self._log.push(message)
