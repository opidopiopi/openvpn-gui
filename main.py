import sys
import argparse
import logging
from nicegui import ui, app
from management import OpenVPNConnection

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


parser = argparse.ArgumentParser(prog='OpenVPN-GUI')
_ = parser.add_argument('-p', '--port', type=int)
_ = parser.add_argument(
    '-n', '--native', help='show native window', action="store_true")

arguments = parser.parse_args()

connection = OpenVPNConnection(port=arguments.port)


def show_log(level: str, message: str, log: ui.log):
    if 'F' in level:
        log.push(message, classes='text-red')
    if 'W' in level:
        log.push(message, classes='text-orange')
    else:
        log.push(message)


@ui.page('/')
def page():
    with ui.column().classes('w-full'):
        _ = ui.label('Initializing...')

        _ = ui.space()
        with ui.row():
            _ = ui.label('Loglevel:')
            loglevel = ui.slider(min=0, max=11, value=3).props(
                'label').classes('w-30')
            _ = loglevel.on('update:model-value',
                            lambda e: connection.loglevel(e.args), throttle=1.0)

        log = ui.log()  # .classes('w-full h-100')

    def logger(level, message): return show_log(level, message, log)
    connection.set_log_callback(logger)

    with ui.dialog() as dialog, ui.card():
        _ = dialog.props('persistent')
        _ = ui.label('Please select one of the following Tokens:')
        selector = ui.select([], on_change=lambda e: dialog.submit(e.value))

    async def show_pkcs11_dialog(tokens: list[str]) -> str:
        selector.set_options(tokens)

        while True:
            result = await dialog
            if result is not None and len(result) > 0:
                return str(result)

    connection.set_pkcs11_id_callback(show_pkcs11_dialog)

    with ui.dialog() as password_dialog, ui.card():
        _ = password_dialog.props('persistent')
        password_label = ui.label('Please enter the password for:')
        password_input = ui.input(password=True, password_toggle_button=True).on(
            'keydown.enter', password_dialog.close)
        _ = ui.button('Submit', on_click=lambda: password_dialog.close())

    async def show_password_dialog(password_name: str):
        password_label.text = f"Please enter the password for: '{password_name}'"
        await password_dialog
        return password_input.value

    connection.set_password_callback(show_password_dialog)

    ui.context.client.on_disconnect(connection.reset_log_callback)
    ui.context.client.on_disconnect(connection.reset_pkcs11_id_callback)
    ui.context.client.on_disconnect(connection.reset_password_callback)


async def close_connection():
    await connection.management_disconnect()


async def check_connection():
    while not connection.management_connected():
        try:
            await connection.management_connect()
        except:
            logger.error(f'Failed to connect to management client')

            with ui.dialog() as dialog, ui.card():
                _ = ui.label(f'Failed to connect to management')
                _ = ui.label('Reconnect?')
                with ui.row():
                    _ = ui.button('Yes', color='green',
                                  on_click=lambda: dialog.close())
                    _ = ui.button('No', color='red',
                                  on_click=lambda: dialog.close())
            await dialog


app.on_connect(check_connection)
app.on_disconnect(close_connection)
ui.run(native=arguments.native)
