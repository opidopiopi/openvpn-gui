from nicegui import ui, Event


class PasswordDialog:
    def __init__(self):
        self._event: Event[bool] = Event()
        self._event.subscribe(self.show_dialog)

        with ui.dialog() as password_dialog, ui.card():
            self._password_dialog: ui.dialog = password_dialog
            _ = password_dialog.props('persistent')
            self._password_label: ui.label = ui.label('Please enter the password for:')
            self._password_input: ui.input = ui.input(password=True,
                                                      password_toggle_button=True).on('keydown.enter', password_dialog.close)
            _ = ui.button('Submit', on_click=lambda: password_dialog.close())

    def trigger_dialog(self, callback):
        self._callback = callback
        self._event.emit(True)

    async def show_dialog(self) -> None:
        self._password_label.text = "Please enter the password: "
        await self._password_dialog
        password, self._password_input.value = self._password_input.value, ''
        self._callback(password)
