import argparse
import logging
from nicegui import ui, app, Event
from management import OpenVPNConnection
from connection import State
import bandwidth
import dialogs
import commands


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


def show_log(level: str, message: str, log: ui.log):
    if 'F' in level:
        log.push(message, classes='text-red')
    if 'W' in level:
        log.push(message, classes='text-orange')
    else:
        log.push(message)


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
        client_storage['connection'] = OpenVPNConnection(port=arguments.port)

    connection = client_storage['connection']

    _ = ui.colors(primary='#ea7e20', brandorange='#ea7e20',
                  brandblue='#003366')
    ui.dark_mode().enable()

    with ui.grid(columns=2).classes('w-full h-full'):

        state = Event[State]()

        with ui.card().classes('w-full bg-brandorange'):
            _ = ui.label('Your private IP:').classes('font-bold')
            local_address = ui.label('IPv4:\nIPv6:').classes(
                'whitespace-pre-line')

        with ui.card().classes('w-full bg-brandblue'):
            _ = ui.label('Remote server IP:').classes(
                'font-bold text-white')
            remote_address = ui.label('Address:\nPort:').classes(
                'whitespace-pre-line text-white')

        state_overview = ui.label('Initializing...').classes(
            'font-bold col-span-full')

        def update_state(new_state: State):
            if new_state.connected():
                switch.value = True

            state_overview.text = new_state.timestamp.strftime('%H:%M:%S')
            state_overview.text += f': {new_state.state}'
            if new_state.description:
                state_overview.text += f' ({new_state.description})'

            local_address.text = f'IPv4: {new_state.local_ipv4}\n'
            local_address.text += f'IPv6: {new_state.local_ipv6}'

            remote_address.text = f'Address: {new_state.remote_address}\n'
            remote_address.text += f'Port: {new_state.remote_port}'

        state.subscribe(update_state)

        connection.set_state_change_callback(lambda s: state.emit(s))

        async def toggle_connection() -> None:
            if switch.value:
                await connection.client_connect()
                switch.text = 'Connected'
                _ = switch.props('color=green')
            else:
                await connection.client_disconnect()
                switch.text = 'Disconnected'
                _ = switch.props('color=grey')

        switch = ui.switch('Connect', on_change=toggle_connection)

        with ui.row():
            _ = ui.label('Loglevel:')
            loglevel = ui.slider(min=0, max=11, value=3).props(
                'label').classes('w-30')
            _ = loglevel.on('update:model-value',
                            lambda e: connection.loglevel(e.args), throttle=1.0)

        bandwidth_graph = bandwidth.BandwidthGraph(60)

        connection.set_bytecount_callback(bandwidth_graph.update_graph)

        log = ui.log().classes('col-span-full')

    def log_callback(level, message): return show_log(level, message, log)
    connection.set_log_callback(log_callback)

    token_dialog = dialogs.TokenDialog()
    connection.set_pkcs11_id_callback(token_dialog.show_dialog)

    password_dialog = dialogs.PasswordDialog()
    connection.set_password_callback(password_dialog.show_dialog)


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
