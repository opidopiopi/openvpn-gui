from nicegui import ui, app

from .create_port_connection import create_port_connection
from .create_socket_connection import create_socket_connection
from .landing_page import landing_page
from .show_connection import show_connection
from openvpn_gui.controller import Controller


def root(controller: Controller):
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

        _ = ui.button(
            "Github",
            icon="web",
            on_click=lambda: ui.navigate.to(
                "https://github.com/opidopiopi/openvpn-gui"
            ),
        )

        with ui.row():
            dark_mode_switch = (
                ui.switch(
                    "Dark mode:", value=app.storage.general.get("dark_mode", True)
                )
                .props("left-label")
                .bind_value(app.storage.general, "dark_mode")
            )
            _ = ui.dark_mode().bind_value(dark_mode_switch, "value")

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
        data={"connection_label": connection_label, "controller": controller},
    ).classes("w-full h-full")
