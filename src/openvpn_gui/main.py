import argparse
import logging
import uuid

from multiprocessing import freeze_support
from nicegui import ui, app, native

from openvpn_gui.controller import Controller
from openvpn_gui.pages import root


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
