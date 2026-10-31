from nicegui import ui

from openvpn_gui.controller import Controller


def landing_page(controller: Controller) -> None:
    with ui.grid(columns=2).classes("w-full"):
        for id, connection in controller.connection_configs().items():
            with ui.card().classes("w-full bg-brandblue"):
                _ = ui.label(connection["name"]).classes("font-bold")

                if "port" in connection:
                    _ = ui.label(f"Port: {connection['port']}").classes("font-bold")
                elif "socket" in connection:
                    _ = ui.label(f"Socket: {connection['socket']}").classes("font-bold")

                _ = ui.button(
                    "Connect",
                    on_click=lambda id=id: ui.navigate.to(f"/connection/{id}"),
                )
