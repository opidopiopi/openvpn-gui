from nicegui import ui, Event
from collections.abc import Callable

from openvpn_gui.openvpn.management import OpenVPNConnection
from openvpn_gui.openvpn.pkcs11_token import PKCS_11_Token


class TokenDialog:
    def __init__(self, vpn_connection: OpenVPNConnection):
        self._vpn_connection: OpenVPNConnection = vpn_connection
        self._last_selection: int = 0
        self._show_dialog: Event[bool] = Event()
        self._show_dialog.subscribe(self.show_dialog)
        self._tokens: list[PKCS_11_Token] = []
        self._callback: Callable[[str], None] = lambda s: None

        with ui.dialog() as dialog, ui.card():
            _ = dialog.props("persistent")
            self._label: ui.label = ui.label(
                "Please select one of the following Tokens:"
            )

            with ui.card():
                self._issuer: ui.label = ui.label()
                self._subject: ui.label = ui.label()
                self._valid_until: ui.label = ui.label()

            with ui.row():
                selector = (
                    ui.select([], on_change=lambda e: self.show_token_info(e.value))
                    .on("keydown.enter", lambda: dialog.submit(selector.value))
                    .props("autofocus")
                )
                _ = ui.button("ok", on_click=lambda: dialog.submit(selector.value))
                self._selector: ui.select = selector
                self._dialog: ui.dialog = dialog

    async def show_warning(self):
        with ui.dialog() as dialog, ui.card():
            _ = ui.label("No pkcs11 ids found, please insert your smartcard!")
            _ = ui.button("ok", on_click=lambda: dialog.close())
            await dialog

    def trigger_selection(self, message: str, callback: Callable[[str], None]) -> None:
        _ = self._label.set_text(message)
        self._callback = callback
        self._show_dialog.emit(True)

    def show_token_info(self, token_index: int) -> None:
        cert = self._tokens[token_index].certificate
        self._issuer.text = f"Issuer: {cert.issuer.rfc4514_string()}"
        self._subject.text = f"Subject: {cert.subject.rfc4514_string()}"
        valid_until: str = cert.not_valid_after_utc.strftime("%d.%m.%Y %H:%M:%S")
        self._valid_until.text = f"Valid until: {valid_until}"

    async def show_dialog(self) -> None:
        while True:
            self._tokens = await self._vpn_connection.pkcs11_tokens()

            if len(self._tokens) > 0:
                break

            await self.show_warning()

        selection = {i: token.name for i, token in enumerate(self._tokens)}

        _ = self._selector.set_options(selection, value=self._last_selection)

        if len(self._tokens) == 1:
            result = 0
        else:
            result = await self._dialog

        if result is not None:
            self._last_selection = result
            self._callback(self._tokens[result].token_id)
