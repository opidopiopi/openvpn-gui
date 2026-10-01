import re
from dataclasses import dataclass
from cryptography import x509
import base64


def parse_from(message: str) -> PKCS_11_Token:
    message_pattern = r"'(\d)', ID:'(?P<id>[^']+)', BLOB:'(?P<blob>[^']+)'"

    match = re.match(message_pattern, message)
    certificate = match.group('blob')
    token_id = match.group('id')

    split_name = token_id.encode().decode('unicode-escape').split('/')

    name = f'{split_name[3]} Slot: {split_name[4]}'

    return PKCS_11_Token(name,
                         token_id,
                         x509.load_der_x509_certificate(base64.b64decode(certificate)))


@dataclass
class PKCS_11_Token:
    name: str
    token_id: str
    certificate: x509.Certificate
