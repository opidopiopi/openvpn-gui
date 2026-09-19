import logging
from nicegui import ui, app
from management import OpenVPNConnection

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ui.label('Disconnected')
ui.button('BUTTON', on_click=lambda: ui.notify('button was pressed'))


loglevel = ui.slider(min=0, max=11, value=3).props('label')

host, port = ('127.0.0.1', 8888)
connection = OpenVPNConnection(host, port)


async def open_connection():
    try:
        await connection.connect()
    except:
        logger.error(f'Failed to connect to {host}:{port}')


async def close_connection():
    await connection.close()


async def check_connection():
    while not connection.connected():
        with ui.dialog() as dialog, ui.card():
            ui.label(f'Failed to connect to {host}:{port}')
            ui.label('Reconnect?')
            with ui.row():
                ui.button('Yes', color='green',
                          on_click=lambda: dialog.submit(True))
                ui.button('No', color='red',
                          on_click=lambda: dialog.submit(False))
        if await dialog:
            await open_connection()
        else:
            break


app.on_startup(open_connection)
app.on_shutdown(close_connection)
app.on_connect(check_connection)
ui.run()
