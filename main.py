import logging
from nicegui import ui, app
from management import OpenVPNConnection

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


host, port = ('127.0.0.1', 8888)
connection = OpenVPNConnection(host, port)


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
    connection.add_log_listener(logger)
    # connection.add_pkcs11_id_selector(show_pkcs11_dialog)
    ui.context.client.on_disconnect(
        lambda: connection.remove_log_listener(logger))


def show_pkcs11_dialog(tokens: list[str], callback):
    logger.debug('Show token selection dialog')
    with ui.dialog() as dialog, ui.card():
        _ = ui.label('Please select one of the following Tokens:')
        selector = ui.select(tokens)


async def close_connection():
    await connection.management_disconnect()


async def check_connection():
    while not connection.management_connected():
        try:
            await connection.management_connect()
        except:
            logger.error(f'Failed to connect to {host}:{port}')

            with ui.dialog() as dialog, ui.card():
                _ = ui.label(f'Failed to connect to {host}:{port}')
                _ = ui.label('Reconnect?')
                with ui.row():
                    _ = ui.button('Yes', color='green',
                                  on_click=lambda: dialog.close())
                    _ = ui.button('No', color='red',
                                  on_click=lambda: dialog.close())
            await dialog


app.on_connect(check_connection)
app.on_disconnect(close_connection)
ui.run()
