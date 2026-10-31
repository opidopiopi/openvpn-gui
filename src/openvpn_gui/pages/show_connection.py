import logging

from nicegui import ui, Event

from openvpn_gui.controller import Controller
from openvpn_gui.gui import AwaitConnection
from openvpn_gui.gui import BytecountGraph
from openvpn_gui.gui import Logview
from openvpn_gui.gui import PasswordDialog
from openvpn_gui.gui import StateWidget
from openvpn_gui.gui import TokenDialog
from openvpn_gui.gui import UsernameDialog
from openvpn_gui.openvpn.connection import State
from openvpn_gui.openvpn.management import OpenVPNConnection


logger = logging.getLogger(__name__)


async def show_connection(
    name: str, connection_label: ui.label, controller: Controller
):
    logger.info(f"Connecting to: {name}")

    await controller.disconnect()
    connection: OpenVPNConnection = controller.active_connection()

    config = controller.connection_configs()[name]
    connection_label.text = config["name"]

    state: Event[State] = Event[State]()
    new_route: Event[str] = Event[str]()

    state_widget = StateWidget()
    state.subscribe(state_widget.update)
    new_route.subscribe(state_widget.add_route)

    with ui.grid(columns=2).classes("w-full"):

        async def toggle_connection() -> None:
            if switch.value is None:
                switch.text = "Connecting..."
                await connection.client_connect()
                switch.enabled = False
            elif switch.value:
                switch.enabled = True
                switch.text = "Connected"
                _ = switch.props("color=green")
            else:
                state_widget.clear_routes()
                await connection.client_disconnect()
                switch.text = "Disconnected"
                _ = switch.props("color=grey")

        def update_switch(new_state):
            if new_state.connected():
                switch.value = True

        state.subscribe(update_switch)

        switch = ui.switch("Connect", on_change=toggle_connection).props(
            "toggle-indeterminate"
        )

        with ui.row():
            _ = ui.label("Loglevel:")
            loglevel = ui.slider(min=0, max=7, value=3).props("label").classes("w-30")
            _ = loglevel.on(
                "update:model-value",
                lambda e: connection.loglevel(e.args),
                throttle=1.0,
            )

        bandwidth_graph = BytecountGraph(60)

    log_view = Logview()

    token_dialog = TokenDialog(connection)
    password_dialog = PasswordDialog()
    username_dialog = UsernameDialog()

    if not connection.management_connected():
        await_management_connection = AwaitConnection()
        connection.callback_management_connected = await_management_connection.dispose

    connection.callback_state_change = state.emit
    connection.callback_bytecount = bandwidth_graph.update_graph
    connection.callback_log = log_view.append
    connection.callback_password_input = password_dialog.trigger_dialog
    connection.callback_username_input = username_dialog.trigger_dialog
    connection.callback_pkcs11_id_selection = token_dialog.trigger_selection
    connection.callback_add_route = new_route.emit

    logger.debug("Page loaded")

    await controller.connect(name)
