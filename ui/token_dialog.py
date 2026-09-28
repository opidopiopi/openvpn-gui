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
