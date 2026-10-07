from nicegui import ui, Event


class UsernameDialog:
    def __init__(self):
        self._event: Event[bool] = Event()
        self._event.subscribe(self.show_dialog)

        with ui.dialog() as self._username_dialog, ui.card():
            _ = self._username_dialog.props("persistent")
            self._username_label: ui.label = ui.label("Please enter your username:")
            self._username_input: ui.input = ui.input().on("keydown.enter", self._username_dialog.close)
            _ = ui.button("Submit", on_click=lambda: self._username_dialog.close())

    def trigger_dialog(self, callback):
        self._callback = callback
        self._event.emit(True)

    async def show_dialog(self) -> None:
        await self._username_dialog
        username = self._username_input.value
        self._callback(username)
