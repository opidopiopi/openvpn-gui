from . import omi, commands, connection, client
from .omi_adapter import OmiAdapter

from datetime import datetime
import asyncio
import logging
import random
from typing import override

logger = logging.getLogger(__name__)


PKCS11_ID_REQUEST: str = "pkcs11-id-request"


class MockConnection(OmiAdapter):
    async def async_bytecount(self):
        in_count = 16
        out_count = 16
        while True:
            self.recv_line(f">BYTECOUNT:{in_count},{out_count}")
            await asyncio.sleep(1)
            in_count += random.randint(0, 1024 * 1024 * 1024)
            out_count += random.randint(0, 1024 * 1024 * 1024)

    def __init__(
        self, finish_future: asyncio.Future[bool], vpn_client: client.VPNClient
    ):
        self._vpn_client: client.VPNClient = vpn_client

        super().__init__(finish_future, vpn_client)

        self.recv_line(
            ">INFO:OpenVPN Management Interface Version 6 -- type 'help' for more info"
        )

        self._async_task = None

    @override
    def queue_command(self, command: str) -> asyncio.Future[omi.OmiCommandResult]:

        logger.info(f"Intercepting: {command}")

        result = omi.OmiCommandResult(command, [], True, "")

        if command == commands.hold_release():
            self.recv_line(
                ">NEED-STR:Need 'pkcs11-id-request' string MSG:Please specify PKCS#11 id to use"
            )
        elif command == commands.state_last():
            result.result = ["1795353946,CONNECTING,,,,,,"]
        elif command.startswith("needstr"):
            self.recv_line(">PASSWORD:Need 'localhost token' password")
        elif command.startswith("password"):
            self.recv_line(
                ">STATE:1795355979,CONNECTED,SUCCESS,192.168.55.2,127.0.0.1,1194,,"
            )
            self._async_task = asyncio.create_task(self.async_bytecount())
        elif command == commands.pkcs11_id_count():
            result.status_text = "1"
        elif command == commands.pkcs11_id_get(0):
            result.status_text = "'0', ID:'piv_II/PKCS\x2315\x20emulated/a856b2494a34e42f/localhost/03', BLOB:'MIIDUzCCAjugAwIBAgIQTEqmr1kZM59lUgOOaayRyjANBgkqhkiG9w0BAQsFADAUMRIwEAYDVQQDDAkxMjcuMC4wLjEwHhcNMjYwOTE3MTkyNTM2WhcNMjgxMjIwMTkyNTM2WjAUMRIwEAYDVQQDDAlsb2NhbGhvc3QwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDi5doMl8GoqBluqDJyYzmz7w00VBH3ZRF5weiqcXVwcXzJb9DQW/ARIlQEF3Qe0J0k+k8jhdIpb2Lqvroyn345S/7boRlJWAWqBgNZJ1B6ZoqUQA4gM+DjbOMIDIi7WI0wcl/hM7QC90Xb0m+90wnvCT52rf7lpdgmhDTviarDFRhlx9W9uadGxIHZXGMlgTO90Y97sui5eYhOlwRyBfyGeqlKntsZlQp6oxtlWA/bv2pb45aZTlm/SV8pPhCELy7aGqSghGg9rqfqmbjJn9MejqAChKPHrHz+9UIL9DG7wqK+c7XqNn85t+uMK7n1+tS8yNPuK8bCOcXiawmVVTOZAgMBAAGjgaAwgZ0wCQYDVR0TBAIwADAdBgNVHQ4EFgQUZbd3jaIHJH4XKy5l1oDOtL4c0q4wTwYDVR0jBEgwRoAU8wFpvCKExRwQjesU+StqbWTNycShGKQWMBQxEjAQBgNVBAMMCTEyNy4wLjAuMYIUMHF/5eCajjrEVCxfbugKYc2wRPYwEwYDVR0lBAwwCgYIKwYBBQUHAwIwCwYDVR0PBAQDAgeAMA0GCSqGSIb3DQEBCwUAA4IBAQBtsoHUw8F+uaGVmPh6uEY7PL1ohcQXhVyeggjfC+NetMcLlHa5Mx5povrBWYvpMK3rMeiy0M8csB9FDz0FFqmmwp529GuwUCOmsiWnvMSMlVV5qQAQDvgtu+Z1fCX6BQZenJPpHVnMOQPU1kcw7s7rtsyi1LrGdA5Q5zuut2De08M9Zuk09EuHQ1ehumNWbXanJJm22JGyDVlp+S5dGnWxWwu/QErFZcUFk9VEMuca/k7B3VhsCXKr+8+XAXB1f5fpjLGRplhHtzZZPPLpulJdnMHvheBm9c3Af4w/BWmGBkHtOkaSWom5fIp23lZAnClroBF95xD+RSEkwRCkP+cx'"

        future = asyncio.Future()
        future.set_result(result)
        return future


async def connect_to_mock(
    vpn_client: client.VPNClient,
) -> tuple[OmiAdapter, asyncio.Future[bool]]:

    loop = asyncio.get_running_loop()
    finish_future = loop.create_future()
    protocol = MockConnection(finish_future, vpn_client)

    return protocol, finish_future
