import datetime
from dataclasses import dataclass


@dataclass
class State:
    timestamp: datetime.datetime
    state: str
    description: str
    local_ipv4: str
    remote_address: str
    remote_port: str
    local_address: str
    local_port: str
    local_ipv6: str


def parse_status(message: str) -> State:
    split: list[str] = message.split(',')
    # this will be up to 9 values but
    # only 2 parts are mandatory, the rest is optional
    # so we just add some emtpy space
    split += [''] * 7

    timestamp: datetime.datetime = datetime.datetime.fromtimestamp(
        int(split[0]))

    return State(timestamp,
                 split[1],
                 split[2],
                 split[3],
                 split[4],
                 split[5],
                 split[6],
                 split[7],
                 split[8])
