import socket

from .. import schema


class Addr(schema.BinarySchema):
    atyp: int = schema.uint8
    host: str = schema.Switch(
        "atyp",
        {
            1: schema.Convert(
                schema.Bytes(4), encode=socket.inet_aton, decode=socket.inet_ntoa
            ),
            4: schema.Convert(
                schema.Bytes(16),
                encode=lambda x: socket.inet_pton(socket.AF_INET6, x),
                decode=lambda x: socket.inet_ntop(socket.AF_INET6, x),
            ),
            3: schema.LengthPrefixedString(schema.uint8),
        },
    )
    port: int = schema.uint16be

    @classmethod
    def from_tuple(cls, addr):
        try:
            return cls(1, *addr)
        except OSError:
            try:
                return cls(4, *addr)
            except OSError:
                return cls(3, *addr)
