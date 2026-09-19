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
    with ui.row():
        _ = ui.label('Loglevel:')
        loglevel = ui.slider(min=0, max=11, value=3).props(
            'label').classes('w-30')
        _ = loglevel.on('update:model-value',
                        lambda e: connection.loglevel(e.args), throttle=1.0)

    log = ui.log().classes('w-full h-100')

    def logger(level, message): return show_log(level, message, log)
    connection.add_log_listener(logger)
    ui.context.client.on_disconnect(
        lambda: connection.remove_log_listener(logger))


async def open_connection():
    try:
        await connection.management_connect()
    except:
        logger.error(f'Failed to connect to {host}:{port}')


async def close_connection():
    await connection.management_disconnect()


async def check_connection():
    while not connection.management_connected():
        with ui.dialog() as dialog, ui.card():
            _ = ui.label(f'Failed to connect to {host}:{port}')
            _ = ui.label('Reconnect?')
            with ui.row():
                _ = ui.button('Yes', color='green',
                              on_click=lambda: dialog.submit(True))
                _ = ui.button('No', color='red',
                              on_click=lambda: dialog.submit(False))
        if await dialog:
            await open_connection()
        else:
            break


app.on_startup(open_connection)
app.on_shutdown(close_connection)
app.on_connect(check_connection)
ui.run(native=True)
