import argparse
import logging

from nicegui import ui, app, Event

from .openvpn.management import OpenVPNConnection
from .openvpn.connection import State

from .gui import BytecountGraph, PasswordDialog, TokenDialog, StateWidget
from .gui import Logview, AwaitConnection


logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(prog="OpenVPN-GUI")

connection_group = parser.add_mutually_exclusive_group(required=True)
_ = connection_group.add_argument("-p", "--port", type=int)
_ = connection_group.add_argument("-s", "--socket", type=str)
_ = parser.add_argument(
    "-n", "--native", help="show native window", action="store_true"
)
_ = parser.add_argument("-v", "--verbose", action="store_true")
_ = parser.add_argument("-vv", "--very_verbose", action="store_true")

arguments = parser.parse_args()

if arguments.very_verbose:
    logging.basicConfig(level=logging.DEBUG)
elif arguments.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)


@ui.page("/")
def page():
    ui.add_head_html("""
        <style>
        .body--dark {
          background: #0f1117;
        }
        </style>
    """)

    client_storage = app.storage.client

    if "connection" not in client_storage:
        client_storage["connection"] = OpenVPNConnection()

    connection: OpenVPNConnection = client_storage["connection"]

    _ = ui.colors(primary="#ED7F22", brandorange="#ED7F22", brandblue="#1652B8")

    with (
        ui.left_drawer(value=False).props("bordered") as left_drawer,
        ui.column().classes("h-full"),
    ):
        _ = ui.space()
        with ui.row():
            dark_mode_switch = ui.switch("Dark mode:", value=True).props("left-label")
            ui.dark_mode().bind_value(dark_mode_switch, "value")

    with ui.header():
        _ = ui.button(icon="menu", on_click=lambda e: left_drawer.toggle())

    state: Event[State] = Event[State]()
    new_route: Event[str] = Event[str]()

    state_widget = StateWidget()
    state.subscribe(state_widget.update)
    new_route.subscribe(state_widget.add_route)

    with ui.grid(columns=2).classes("w-full h-full"):

        async def toggle_connection() -> None:
            if switch.value:
                await connection.client_connect()
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

        switch = ui.switch("Connect", on_change=toggle_connection)

        with ui.row():
            _ = ui.label("Loglevel:")
            loglevel = ui.slider(min=0, max=11, value=3).props("label").classes("w-30")
            _ = loglevel.on(
                "update:model-value",
                lambda e: connection.loglevel(e.args),
                throttle=1.0,
            )

        bandwidth_graph = BytecountGraph(60)

        log_view = Logview()

    token_dialog = TokenDialog(connection)
    password_dialog = PasswordDialog()
    await_management_connection = AwaitConnection()

    connection.callback_state_change = state.emit
    connection.callback_bytecount = bandwidth_graph.update_graph
    connection.callback_log = log_view.append
    connection.callback_password_input = password_dialog.trigger_dialog
    connection.callback_pkcs11_id_selection = token_dialog.trigger_selection
    connection.callback_add_route = new_route.emit
    connection.callback_management_connected = await_management_connection.dispose

    logger.debug("Page loaded")


async def close_connection():
    client_storage = app.storage.client

    if "connection" in client_storage:
        await client_storage["connection"].management_disconnect()


async def check_connection():
    client_storage = app.storage.client

    connection: OpenVPNConnection = client_storage["connection"]

    while not connection.management_connected():
        try:
            if arguments.socket:
                await connection.connect_to_socket(arguments.socket)
            elif arguments.port:
                await connection.connect_to_port(arguments.port)
        except Exception as e:
            logger.error(f"Failed to connect to management client: {e}")

            with ui.dialog() as dialog, ui.card():
                _ = ui.label(f"Failed to connect to management interface: {e}")
                with ui.row():
                    _ = ui.button(
                        "Reconnect", color="green", on_click=lambda: dialog.close()
                    )
                    _ = ui.button("Exit", color="red", on_click=app.shutdown)
            await dialog


app.on_connect(check_connection)
app.on_disconnect(close_connection)
ui.run(
    native=arguments.native,
    host="127.0.0.1",
    title="OpenVPN Client",
    favicon="images/openvpn-icon.svg",
)
