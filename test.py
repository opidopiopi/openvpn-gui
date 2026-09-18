import asyncio
import sys
import re
import logging
from nicegui import ui, app
from management import OpenVPNConnection

logging.basicConfig(level=logging.DEBUG)

ui.label('Hello there!')
ui.button('BUTTON', on_click=lambda: ui.notify('button was pressed'))


loglevel = ui.slider(min=0, max=11, value=3).props('label')


async def open_connection():
    host, port = ('127.0.0.1', 8888)
    connection = OpenVPNConnection(host, port)
    app.storage.client['vpn_connection'] = connection

    while True:
        try:
            await connection.connect()
        except:
            with ui.dialog() as dialog, ui.card():
                ui.label(f'Failed to connect to {host}:{port}')
                ui.label('Reconnect?')
                with ui.row():
                  ui.button('Yes', color='green', on_click=lambda: dialog.submit(True))
                  ui.button('No', color='red', on_click=lambda: dialog.submit(False))

            retry = await dialog
            if not retry:
                break


async def close_connection():
    if app.storage.client['vpn_connection']:
        await app.storage.client['vpn_connection'].close()

app.on_connect(open_connection)
app.on_disconnect(close_connection)
ui.run()
