from nicegui import ui, Event


class TokenDialog:
    def __init__(self, vpn_connection):
        self._vpn_connection = vpn_connection
        self._last_selection: str = ''
        self._show_dialog: Event[bool] = Event()
        self._show_dialog.subscribe(self.show_dialog)

        with ui.dialog() as dialog, ui.card():
            _ = dialog.props('persistent')
            self._label = ui.label('Please select one of the following Tokens:')
            with ui.row():
                selector = ui.select([])
                _ = ui.button(
                    'ok', on_click=lambda: dialog.submit(selector.value))
                self._selector = selector
                self._dialog = dialog

    async def show_warning(self):
        with ui.dialog() as dialog, ui.card():
            _ = ui.label('No pkcs11 ids found, please insert your smartcard')
            _ = ui.button('ok', on_click=lambda: dialog.close())
            await dialog


    def trigger_selection(self, message: str, callback) -> None:
        self._label.set_text(message)
        self._callback = callback
        self._show_dialog.emit(True)

    async def show_dialog(self) -> None:
        while True:
            tokens = await self._vpn_connection.pkcs11_tokens()

            if len(tokens) > 0:
                break

            await self.show_warning()

        selection = {i: token.name for i, token in enumerate(tokens)}

        self._selector.set_options(selection,
                                   value=self._last_selection if self._last_selection else 0)

        result = await self._dialog
        if result is not None:
            self._last_selection = result
            self._callback(tokens[result].name)
