from nicegui import ui


class TokenDialog:
    def __init__(self):
        self._last_selection: str = ''

        with ui.dialog() as dialog, ui.card():
            _ = dialog.props('persistent')
            _ = ui.label('Please select one of the following Tokens:')
            with ui.row():
                selector = ui.select([])
                _ = ui.button(
                    'ok', on_click=lambda: dialog.submit(selector.value))
                self._selector = selector
                self._dialog = dialog

    async def show_dialog(self, tokens: list[str]) -> str:
        self._selector.set_options(tokens,
                                   value=self._last_selection if self._last_selection else tokens[0])

        while True:
            result = await self._dialog
            if result is not None and len(result) > 0:
                self._last_selection = result
                return result


class PasswordDialog:
    def __init__(self):
        with ui.dialog() as password_dialog, ui.card():
            self._password_dialog = password_dialog
            _ = password_dialog.props('persistent')
            self._password_label = ui.label('Please enter the password for:')
            self._password_input = ui.input(password=True, password_toggle_button=True).on(
                'keydown.enter', password_dialog.close)
            _ = ui.button('Submit', on_click=lambda: password_dialog.close())

    async def show_dialog(self, password_name: str) -> str:
        self._password_label.text = f"Please enter the password for: '{password_name}'"
        await self._password_dialog
        password, self._password_input.value = self._password_input.value, ''
        return password
