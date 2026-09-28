import re
from dataclasses import dataclass


def parse_from(message: str) -> PKCS_11_Token:
    message_pattern = r"'(\d)', ID:'(?P<id>[^']+)', BLOB:'(?P<blob>[^']+)'"

    match = re.match(message_pattern, message)
    return PKCS_11_Token(match.group('id'))


@dataclass
class PKCS_11_Token:
    name: str
