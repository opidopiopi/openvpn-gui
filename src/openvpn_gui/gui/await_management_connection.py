from nicegui import ui, Event


class AwaitConnection:
    def __init__(self):
        self.management_connected: Event[bool] = Event()
        with ui.dialog().props("persistent") as is_connecting_overlay:
            _ = ui.spinner(size="lg")
            label = ui.label(
                "Connecting to management interface...\n"
                + "Make sure no other clients are connected!"
            )
            _ = label.classes("whitespace-pre-line")
            _ = is_connecting_overlay.open()
            self.management_connected.subscribe(lambda e: is_connecting_overlay.close())

    def dispose(self):
        self.management_connected.emit(True)
