import enum
import socket
from struct import Struct
from iofree import schema, read_raw_struct


class IPv4(schema.Unit):
    def __init__(self):
        self._struct = Struct("4s")

    def get_value(self, namespace):
        result, = yield from read_raw_struct(self._struct)
        return socket.inet_ntoa(result)

    def __call__(self, obj: str) -> bytes:
        return self._struct.pack(socket.inet_aton(obj))


class IPv6(schema.Unit):
    def __init__(self):
        self._struct = Struct("16s")

    def get_value(self, namespace):
        result, = yield from read_raw_struct(self._struct)
        return socket.inet_ntop(socket.AF_INET6, result)

    def __call__(self, obj: str) -> bytes:
        return self._struct.pack(socket.inet_pton(socket.AF_INET6, obj))


ipv4 = IPv4()
ipv6 = IPv6()


class Hostname(schema.BinarySchema):
    name: str = schema.LengthPrefixedString(schema.uint8, "ascii")


class Addr(schema.BinarySchema):
    atyp: int = schema.uint8
    host: schema.BinarySchema = schema.Switch("atyp", {1: ipv4, 4: ipv6, 3: Hostname})
    port: int = schema.uint16be


class AuthMethod(enum.IntEnum):
    no_auth = 0
    gssapi = 1
    user_auth = 2
    no_acceptable_method = 255


class Cmd(enum.IntEnum):
    connect = 1
    bind = 2
    associate = 3


class Rep(enum.IntEnum):
    succeeded = 0
    general_failure = 1
    not_allowed = 2
    network_unreachable = 3
    host_unreachable = 4
    connection_refused = 5
    ttl_expired = 6
    command_not_supported = 7
    address_type_not_supported = 8


class Socks5Handshake(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    methods = schema.LengthPrefixedBytes(schema.uint8)


class Socks5ClientRequest(schema.BinarySchema):
    auth_ver = schema.MustEqual(schema.uint8, 1)
    username = schema.LengthPrefixedString(schema.uint8)
    password = schema.LengthPrefixedString(schema.uint8)
    ver = schema.MustEqual(schema.uint8, 5)
    cmd = schema.SizedIntEnum(schema.uint8, Cmd)
    rsv = schema.MustEqual(schema.uint8, 0)
    addr = Addr


class Socks5Reply(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    rep = schema.SizedIntEnum(schema.uint8, Rep)
    rsv = schema.MustEqual(schema.uint8, 0)
    bind_addr = Addr


class Socks5ServerSelection(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    method = schema.SizedIntEnum(schema.uint8, AuthMethod)


class Socks5UDPRelay(schema.BinarySchema):
    rsv = schema.MustEqual(schema.Bytes(2), b"\x00\x00")
    flag = schema.uint8
    addr = Addr
    data = schema.Bytes(-1)
