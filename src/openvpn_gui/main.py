import argparse
import logging
import uuid

from multiprocessing import freeze_support
from nicegui import ui, app, Event, native

from openvpn_gui.openvpn.management import OpenVPNConnection
from openvpn_gui.openvpn.connection import State

from openvpn_gui.gui import BytecountGraph, PasswordDialog, TokenDialog, StateWidget
from openvpn_gui.gui import Logview, AwaitConnection, UsernameDialog


# prevent infinite process glitch
freeze_support()


logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(prog="OpenVPN-GUI")

_ = parser.add_argument("-p", "--port", type=int, action="append", default=[])
_ = parser.add_argument("-s", "--socket", type=str, action="append", default=[])
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


commandline_configs = dict()

for port in arguments.port:
    commandline_configs[str(uuid.uuid4())] = {"port": port, "name": f"Port {port}"}

for socket in arguments.socket:
    commandline_configs[str(uuid.uuid4())] = {
        "socket": socket,
        "name": f"Socket: {socket}",
    }


def active_connection() -> OpenVPNConnection:
    if "connection" not in app.storage.client:
        app.storage.client["connection"] = OpenVPNConnection()

    return app.storage.client["connection"]


def connection_configs():
    if commandline_configs:
        logger.info(f"commandline_config: {commandline_configs}")
        return commandline_configs

    if "connections" not in app.storage.general:
        app.storage.general["connections"] = dict()

    return app.storage.general["connections"]


def root():
    ui.add_head_html("""
        <style>
        .body--dark {
          background: #0f1117;
        }
        </style>
    """)
    _ = ui.colors(primary="#ED7F22", brandorange="#ED7F22", brandblue="#1652B8")

    with (
        ui.left_drawer(value=False).props("bordered") as left_drawer,
        ui.column().classes("h-full").classes("w-full"),
    ):
        for id, connection in connection_configs().items():
            _ = ui.button(
                connection["name"],
                on_click=lambda id=id: ui.navigate.to("/connection/" + id),
            ).classes("w-full")

        _ = ui.separator()

        with ui.button_group():
            _ = ui.button(
                "Port",
                on_click=lambda: ui.navigate.to("/connection/create/port"),
            )
            _ = ui.button(
                "Socket",
                on_click=lambda: ui.navigate.to("/connection/create/socket"),
            ).classes("w-full bg-brandblue")

        _ = ui.space()

        with ui.row():
            dark_mode_switch = (
                ui.switch(
                    "Dark mode:", value=app.storage.general.get("dark_mode", True)
                )
                .props("left-label")
                .bind_value(app.storage.general, "dark_mode")
            )
            ui.dark_mode().bind_value(dark_mode_switch, "value")

    with ui.header():
        _ = ui.button(icon="menu", on_click=lambda e: left_drawer.toggle())

    _ = ui.sub_pages(
        {
            "/": landing_page,
            "/connection/{name}": show_connection,
            "/connection/create/port": create_port_connection,
            "/connection/create/socket": create_socket_connection,
        }
    ).classes("w-full")


def landing_page():
    pass
    if connection_configs():
        ui.navigate.to("/connection/" + list(connection_configs().keys())[0])


def create_socket_connection():
    _ = ui.label("Create a new socket connection:")

    def check_name(value: str):
        return value not in connection_configs()

    name = ui.input(
        label="Enter connection name",
        validation={"Name invalid or already existing": check_name},
    )

    socket = ui.input(
        label="Enter a socket path",
    )

    def create():
        id = str(uuid.uuid4())
        connection_configs()[id] = {"socket": socket.value, "name": str(name.value)}
        ui.navigate.to(f"/connection/{id}")

    _ = ui.button("Create connection", on_click=create)


def create_port_connection():
    _ = ui.label("Create a new port connection:")

    def check_name(value: str):
        return value not in connection_configs()

    name = ui.input(
        label="Enter connection name",
        validation={"Name invalid or already existing": check_name},
    )

    def check_port(value: str):
        return value.isdigit() and int(value) >= 1 and int(value) <= 65535

    port = ui.input(
        label="Enter port number",
        validation={"Input a nuber between 1 and 65535": check_port},
    )

    def create():
        id = str(uuid.uuid4())
        connection_configs()[id] = {"port": int(port.value), "name": str(name.value)}
        ui.navigate.to(f"/connection/{id}")

    _ = ui.button("Create connection", on_click=create)


async def show_connection(name: str):
    logger.info(f"Connecting to: {name}")

    await close_connection()
    connection = active_connection()

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
        username_dialog = UsernameDialog()

        if not connection.management_connected():
            await_management_connection = AwaitConnection()
            connection.callback_management_connected = (
                await_management_connection.dispose
            )

    connection.callback_state_change = state.emit
    connection.callback_bytecount = bandwidth_graph.update_graph
    connection.callback_log = log_view.append
    connection.callback_password_input = password_dialog.trigger_dialog
    connection.callback_username_input = username_dialog.trigger_dialog
    connection.callback_pkcs11_id_selection = token_dialog.trigger_selection
    connection.callback_add_route = new_route.emit

    logger.debug("Page loaded")

    await check_connection(name)


async def close_connection():
    logger.debug(f"Disconnecting...")
    await active_connection().management_disconnect()


async def check_connection(name: str):
    if name not in connection_configs():
        ui.navigate.to("/")

    connection: OpenVPNConnection = active_connection()

    connection_config = connection_configs()[name]
    logger.debug(f"connect to {name} using: {connection_config}")

    while not connection.management_connected():
        try:
            if "socket" in connection_config:
                await connection.connect_to_socket(connection_config["socket"])
            elif "port" in connection_config:
                await connection.connect_to_port(connection_config["port"])
        except Exception as e:
            logger.error(f"Failed to connect to management client: {e}")

            with ui.dialog() as dialog, ui.card():
                _ = ui.label(f"Failed to connect to management interface: {e}")
                with ui.row():
                    _ = ui.button(
                        "Reconnect", color="green", on_click=lambda: dialog.close()
                    )
                    _ = ui.button(
                        "Cancel", color="red", on_click=lambda e: ui.navigate.to("/")
                    )
            await dialog


app.on_disconnect(close_connection)

ui.run(
    root,
    reload=True,
    native=arguments.native,
    host="127.0.0.1",
    title="OpenVPN Client",
    favicon="images/openvpn-icon.svg",
    port=native.find_open_port(),
)
