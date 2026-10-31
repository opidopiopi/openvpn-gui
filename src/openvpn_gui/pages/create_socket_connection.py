import uuid
from nicegui import ui
from openvpn_gui.controller import Controller


async def create_socket_connection(connection_label: ui.label, controller: Controller):
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
