from nicegui import ui

from openvpn_gui.controller import Controller


def landing_page(controller: Controller) -> None:
    if controller.connection_configs():
        ui.navigate.to("/connection/" + list(controller.connection_configs().keys())[0])
