import uuid
from nicegui import ui
from openvpn_gui.controller import Controller


async def create_port_connection(connection_label: ui.label, controller: Controller):
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
