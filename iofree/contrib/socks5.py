import enum
from .. import schema
from .common import Addr


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
