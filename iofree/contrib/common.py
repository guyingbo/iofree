import socket
from struct import Struct
from .. import schema, read_raw_struct


class IPv4(schema.Unit):
    def __init__(self):
        self._struct = Struct("4s")

    def get_value(self):
        (result,) = yield from read_raw_struct(self._struct)
        return socket.inet_ntoa(result)

    def __call__(self, obj: str) -> bytes:
        return self._struct.pack(socket.inet_aton(obj))


class IPv6(schema.Unit):
    def __init__(self):
        self._struct = Struct("16s")

    def get_value(self):
        (result,) = yield from read_raw_struct(self._struct)
        return socket.inet_ntop(socket.AF_INET6, result)

    def __call__(self, obj: str) -> bytes:
        return self._struct.pack(socket.inet_pton(socket.AF_INET6, obj))


ipv4 = IPv4()
ipv6 = IPv6()


class Addr(schema.BinarySchema):
    atyp: int = schema.uint8
    host: str = schema.Switch(
        "atyp",
        {1: ipv4, 4: ipv6, 3: schema.LengthPrefixedString(schema.uint8, "ascii")},
    )
    port: int = schema.uint16be
