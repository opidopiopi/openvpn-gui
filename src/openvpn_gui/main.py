import argparse
import logging
import uuid
import os
from pathlib import Path

from multiprocessing import freeze_support

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
    "-m",
    "--mock",
    type=str,
    action="append",
    default=[],
    metavar="[NAME=]MOCK",
    help="define a mock connection",
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
_ = parser.add_argument("-c", "--config", help="Config directory")

arguments = parser.parse_args()

if arguments.very_verbose:
    logging.basicConfig(level=logging.DEBUG)
elif arguments.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)


commandline_configs = dict()

config_directory = (
    Path(os.getenv("XDG_STATE_HOME", default=Path.home() / ".local" / "state"))
    / "openvpn-gui"
)
if arguments.config:
    path = Path(arguments.config)

    if path.exists() and not path.is_dir():
        logger.error("The given config directory is a file!")

    config_directory = path

config_directory.mkdir(exist_ok=True)

# hacky override of the nicegui default
os.environ["NICEGUI_STORAGE_PATH"] = str(config_directory)
logger.info("Using configuration in %s", config_directory)


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

for mock in arguments.mock:
    mock, name = split_argument(mock, "Mock: ")
    commandline_configs[str(uuid.uuid4())] = {
        "mock": mock,
        "name": name,
    }


# We need to override 'NICEGUI_STORAGE_PATH' before module import...
from nicegui import ui, app, native

from openvpn_gui.controller import Controller
from openvpn_gui.pages import root


controller = Controller(commandline_configs)


app.on_disconnect(controller.disconnect)

app.native.window_args["text_select"] = True

ui.run(
    lambda: root(controller),
    reload=arguments.debug,
    native=arguments.native,
    host="127.0.0.1",
    title="OpenVPN Client",
    favicon="images/openvpn-icon.svg",
    port=native.find_open_port(),
)
