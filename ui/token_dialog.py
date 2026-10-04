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

            with ui.card():
                self._issuer = ui.label()
                self._subject = ui.label()
                self._valid_until = ui.label()

            with ui.row():
                selector = ui.select([], on_change=lambda e: self.show_token_info(e.value))
                _ = ui.button(
                    'ok', on_click=lambda: dialog.submit(selector.value))
                self._selector = selector
                self._dialog = dialog

    async def show_warning(self):
        with ui.dialog() as dialog, ui.card():
            _ = ui.label('No pkcs11 ids found, please insert your smartcard!')
            _ = ui.button('ok', on_click=lambda: dialog.close())
            await dialog


    def trigger_selection(self, message: str, callback) -> None:
        self._label.set_text(message)
        self._callback = callback
        self._show_dialog.emit(True)

    def show_token_info(self, token_index):
        cert = self._tokens[token_index].certificate
        self._issuer.text = f'Issuer: {cert.issuer.rfc4514_string()}'
        self._subject.text = f'Subject: {cert.subject.rfc4514_string()}'
        valid_until: str = cert.not_valid_after_utc.strftime('%d.%m.%Y %H:%M:%S')
        self._valid_until.text = f'Valid until: {valid_until}'

    async def show_dialog(self) -> None:
        while True:
            self._tokens = await self._vpn_connection.pkcs11_tokens()

            if len(self._tokens) > 0:
                break

            await self.show_warning()

        selection = {i: token.name for i, token in enumerate(self._tokens)}

        self._selector.set_options(selection,
                                   value=self._last_selection if self._last_selection else 0)

        result = await self._dialog
        if result is not None:
            self._last_selection = result
            self._callback(self._tokens[result].token_id)
