from nicegui import ui
from openvpn.connection import State


class StateWidget:
    def __init__(self):
        with ui.grid(columns=2).classes('w-full h-full'):
            with ui.card().classes('w-full bg-brandorange'):
                _ = ui.label('Your private IP:').classes('font-bold')
                self._local_address: ui.label = ui.label('IPv4:\nIPv6:').classes(
                    'whitespace-pre-line')

            with ui.card().classes('w-full bg-brandblue'):
                _ = ui.label('Remote server IP:').classes(
                    'font-bold text-white')
                self._remote_address: ui.label = ui.label('Address:\nPort:').classes(
                    'whitespace-pre-line text-white')

            self._state_overview: ui.label = ui.label('Initializing...').classes(
                'font-bold col-span-full')

    def update(self, new_state: State):
        self._state_overview.text = new_state.timestamp.strftime('%H:%M:%S')
        self._state_overview.text += f': {new_state.state}'
        if new_state.description:
            self._state_overview.text += f' ({new_state.description})'

        self._local_address.text = f'IPv4: {new_state.local_ipv4}\n'
        self._local_address.text += f'IPv6: {new_state.local_ipv6}'

        self._remote_address.text = f'Address: {new_state.remote_address}\n'
        self._remote_address.text += f'Port: {new_state.remote_port}'
