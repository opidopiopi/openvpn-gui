import argparse
import logging
from nicegui import ui, app, Event
from openvpn.management import OpenVPNConnection
from openvpn.connection import State

from ui import BandwidthGraph, PasswordDialog, TokenDialog, StateWidget, Logview


logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(prog='OpenVPN-GUI')
_ = parser.add_argument('-p', '--port', type=int)
_ = parser.add_argument(
    '-n', '--native', help='show native window', action="store_true")
_ = parser.add_argument('-v', '--verbose', action="store_true")
_ = parser.add_argument('-vv', '--very_verbose', action="store_true")

arguments = parser.parse_args()

if arguments.very_verbose:
    logging.basicConfig(level=logging.DEBUG)
elif arguments.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)


@ui.page('/')
def page():
    ui.add_head_html('''
        <style>
        .body--dark {
          background: #0f1117;
        }
        </style>
    ''')

    ui.page_title('OpenVPN Client')

    client_storage = app.storage.client

    if 'connection' not in client_storage:
        client_storage['connection'] = OpenVPNConnection()

    connection: OpenVPNConnection = client_storage['connection']

    _ = ui.colors(primary='#ea7e20', brandorange='#ea7e20',
                  brandblue='#003366')
    ui.dark_mode().enable()

    state: Event[State] = Event[State]()
    new_route: Event[str] = Event[str]()

    state_widget = StateWidget()
    state.subscribe(state_widget.update)
    new_route.subscribe(state_widget.add_route)

    with ui.grid(columns=2).classes('w-full h-full'):
        async def toggle_connection() -> None:
            if switch.value:
                await connection.client_connect()
                switch.text = 'Connected'
                _ = switch.props('color=green')
            else:
                state_widget.clear_routes()
                await connection.client_disconnect()
                switch.text = 'Disconnected'
                _ = switch.props('color=grey')

        def update_switch(new_state):
            if new_state.connected():
                switch.value = True

        state.subscribe(update_switch)

        switch = ui.switch('Connect', on_change=toggle_connection)

        with ui.row():
            _ = ui.label('Loglevel:')
            loglevel = ui.slider(min=0, max=11, value=3).props(
                'label').classes('w-30')
            _ = loglevel.on('update:model-value',
                            lambda e: connection.loglevel(e.args), throttle=1.0)

        bandwidth_graph = BandwidthGraph(60)

        log_view = Logview()

    token_dialog = TokenDialog(connection)

    password_dialog = PasswordDialog()

    connection.callback_state_change = state.emit
    connection.callback_bytecount = bandwidth_graph.update_graph
    connection.callback_log = log_view.append
    connection.callback_password_input = password_dialog.trigger_dialog
    connection.callback_pkcs11_id_selection = token_dialog.trigger_selection
    connection.callback_add_route = new_route.emit

    logger.debug('Page loaded')


async def close_connection():
    client_storage = app.storage.client

    if 'connection' in client_storage:
        await client_storage['connection'].management_disconnect()


async def check_connection():
    client_storage = app.storage.client

    connection: OpenVPNConnection = client_storage['connection']

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
