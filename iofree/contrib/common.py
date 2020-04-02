import socket
from .. import schema

ipv4 = schema.Convert(schema.Bytes(4), encode=socket.inet_aton, decode=socket.inet_ntoa)
ipv6 = schema.Convert(
    schema.Bytes(16),
    encode=lambda x: socket.inet_pton(socket.AF_INET6, x),
    decode=lambda x: socket.inet_ntop(socket.AF_INET6, x),
)


class Addr(schema.BinarySchema):
    atyp: int = schema.uint8
    host: str = schema.Switch(
        "atyp", {1: ipv4, 4: ipv6, 3: schema.LengthPrefixedString(schema.uint8)}
    )
    port: int = schema.uint16be
