from nicegui import app, ui
import logging

from openvpn_gui.openvpn.management import OpenVPNConnection

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, static_config: dict[str, str]):
        self._static_config: dict[str, str] = static_config

    def is_static_config(self) -> bool:
        return len(self._static_config) > 0

    async def disconnect(self) -> None:
        await self.active_connection().management_disconnect()

    async def connect(self, name: str) -> None:
        if name not in self.connection_configs():
            ui.navigate.to("/")

        connection: OpenVPNConnection = self.active_connection()

        connection_config = self.connection_configs()[name]
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
                            "Cancel",
                            color="red",
                            on_click=lambda e: ui.navigate.to("/"),
                        )
                await dialog

    def active_connection(self) -> OpenVPNConnection:
        if "connection" not in app.storage.client:
            app.storage.client["connection"] = OpenVPNConnection()

        return app.storage.client["connection"]

    def connection_configs(self) -> dict[str, str]:
        if self.is_static_config():
            return self._static_config

        if "connections" not in app.storage.general:
            app.storage.general["connections"] = dict()

        return app.storage.general["connections"]
