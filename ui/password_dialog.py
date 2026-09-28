from nicegui import ui


class PasswordDialog:
    def __init__(self):
        with ui.dialog() as password_dialog, ui.card():
            self._password_dialog: ui.dialog = password_dialog
            _ = password_dialog.props('persistent')
            self._password_label: ui.label = ui.label('Please enter the password for:')
            self._password_input: ui.input = ui.input(password=True,
                                                      password_toggle_button=True).on('keydown.enter', password_dialog.close)
            _ = ui.button('Submit', on_click=lambda: password_dialog.close())

    async def show_dialog(self, password_name: str) -> str:
        self._password_label.text = f"Please enter the password for: '{password_name}'"
        await self._password_dialog
        password, self._password_input.value = self._password_input.value, ''
        return password if password else ''
