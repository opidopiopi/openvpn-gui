import argparse
import logging
import uuid

from multiprocessing import freeze_support
from nicegui import ui, app, Event, native

from openvpn_gui.openvpn.management import OpenVPNConnection
from openvpn_gui.openvpn.connection import State

from openvpn_gui.gui import BytecountGraph, PasswordDialog, TokenDialog, StateWidget
from openvpn_gui.gui import Logview, AwaitConnection, UsernameDialog

from openvpn_gui.controller import Controller


# prevent infinite process glitch
freeze_support()


logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(prog="OpenVPN-GUI")

_ = parser.add_argument(
    "-p",
    "--port",
    type=str,
    action="append",
    default=[],
    metavar="[NAME=]PORT",
    help="define a management connection using a port on localhost",
)
_ = parser.add_argument(
    "-s",
    "--socket",
    type=str,
    action="append",
    default=[],
    metavar="[NAME=]SOCKET",
    help="define a management connection using a unix socket",
)
_ = parser.add_argument(
    "-n", "--native", help="show native window", action="store_true"
)
_ = parser.add_argument("-v", "--verbose", action="store_true", help="show info log")
_ = parser.add_argument(
    "-vv", "--very_verbose", action="store_true", help="show debug log"
)
_ = parser.add_argument(
    "-d", "--debug", action="store_true", help="Debug mode enables refresh"
)

arguments = parser.parse_args()

if arguments.very_verbose:
    logging.basicConfig(level=logging.DEBUG)
elif arguments.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)


commandline_configs = dict()


def split_argument(argument: str, prefix: str):
    split = argument.split("=")

    if len(split) == 2:
        return split[1], split[0]
    else:
        return argument, prefix + argument


for port in arguments.port:
    port, name = split_argument(port, "Port: ")
    commandline_configs[str(uuid.uuid4())] = {
        "port": port,
        "name": name,
    }

for socket in arguments.socket:
    socket, name = split_argument(socket, "Socket: ")
    commandline_configs[str(uuid.uuid4())] = {
        "socket": socket,
        "name": name,
    }

controller = Controller(commandline_configs)


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
        for id, connection in controller.connection_configs().items():
            _ = ui.button(
                connection["name"],
                on_click=lambda id=id: ui.navigate.to("/connection/" + id),
            ).classes("w-full")

        _ = ui.separator()

        if not controller.is_static_config():
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
        connection_label = (
            ui.label("Connection").classes("text-bold").style("font-size: 200%")
        )

    _ = ui.context.client.page_container.default_slot.children[0].props(
        ':style-fn="o => ({ height: `calc(100vh - ${o}px)` })"'
    )
    _ = ui.context.client.content.classes("h-full")

    _ = ui.sub_pages(
        {
            "/": landing_page,
            "/connection/{name}": show_connection,
            "/connection/create/port": create_port_connection,
            "/connection/create/socket": create_socket_connection,
        },
        data={"connection_label": connection_label},
    ).classes("w-full h-full")


def landing_page():
    pass
    if controller.connection_configs():
        ui.navigate.to("/connection/" + list(controller.connection_configs().keys())[0])


async def create_socket_connection(connection_label: ui.label):
    await controller.disconnect()
    connection_label.text = "new socket connection"
    _ = ui.label("Create a new socket connection:")

    def check_name(value: str):
        return value not in controller.connection_configs()

    name = ui.input(
        label="Enter connection name",
        validation={"Name invalid or already existing": check_name},
    )

    socket = ui.input(
        label="Enter a socket path",
    )

    def create():
        id = str(uuid.uuid4())
        controller.connection_configs()[id] = {
            "socket": socket.value,
            "name": str(name.value),
        }
        ui.navigate.to(f"/connection/{id}")

    _ = ui.button("Create connection", on_click=create)


async def create_port_connection(connection_label: ui.label):
    await controller.disconnect()
    connection_label.text = "new port connection"
    _ = ui.label("Create a new port connection:")

    def check_name(value: str):
        return value not in controller.connection_configs()

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
        controller.connection_configs()[id] = {
            "port": int(port.value),
            "name": str(name.value),
        }
        ui.navigate.to(f"/connection/{id}")

    _ = ui.button("Create connection", on_click=create)


async def show_connection(name: str, connection_label: ui.label):
    logger.info(f"Connecting to: {name}")

    await controller.disconnect()
    connection = controller.active_connection()

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


app.on_disconnect(controller.disconnect)

app.native.window_args["text_select"] = True

ui.run(
    root,
    reload=arguments.debug,
    native=arguments.native,
    host="127.0.0.1",
    title="OpenVPN Client",
    favicon="images/openvpn-icon.svg",
    port=native.find_open_port(),
)
