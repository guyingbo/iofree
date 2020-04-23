# references:
# rfc1928(SOCKS Protocol Version 5): https://www.ietf.org/rfc/rfc1928.txt
# rfc1929(Username/Password Authentication for SOCKS V5):
# https://tools.ietf.org/html/rfc1929
# handshake                                   server selection
# +----+----------+----------+                +----+--------+
# |VER | NMETHODS | METHODS  |                |VER | METHOD |
# +----+----------+----------+                +----+--------+
# | 1  |    1     | 1 to 255 |                | 1  |   1    |
# +----+----------+----------+                +----+--------+
# Username/Password Authentication            auth reply
# +----+------+----------+------+----------+  +----+--------+
# |VER | ULEN |  UNAME   | PLEN |  PASSWD  |  |VER | STATUS |
# +----+------+----------+------+----------+  +----+--------+
# | 1  |  1   | 1 to 255 |  1   | 1 to 255 |  | 1  |   1    |
# +----+------+----------+------+----------+  +----+--------+
# request
# +----+-----+-------+------+----------+----------+
# |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
# +----+-----+-------+------+----------+----------+
# | 1  |  1  | X'00' |  1   | Variable |    2     |
# +----+-----+-------+------+----------+----------+
# reply
# +----+-----+-------+------+----------+----------+
# |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
# +----+-----+-------+------+----------+----------+
# | 1  |  1  | X'00' |  1   | Variable |    2     |
# +----+-----+-------+------+----------+----------+
# udp relay request and reply
# +----+------+------+----------+----------+----------+
# |RSV | FRAG | ATYP | DST.ADDR | DST.PORT |   DATA   |
# +----+------+------+----------+----------+----------+
# | 2  |  1   |  1   | Variable |    2     | Variable |
# +----+------+------+----------+----------+----------+
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


class Handshake(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    methods = schema.LengthPrefixedObjectList(
        schema.uint8, schema.SizedIntEnum(schema.uint8, AuthMethod)
    )


class ServerSelection(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    method = schema.SizedIntEnum(schema.uint8, AuthMethod)


class UsernameAuth(schema.BinarySchema):
    auth_ver = schema.MustEqual(schema.uint8, 1)
    username = schema.LengthPrefixedString(schema.uint8)
    password = schema.LengthPrefixedString(schema.uint8)


class UsernameAuthReply(schema.BinarySchema):
    auth_ver = schema.MustEqual(schema.uint8, 1)
    status = schema.MustEqual(schema.uint8, 0)


class ClientRequest(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    cmd = schema.SizedIntEnum(schema.uint8, Cmd)
    rsv = schema.MustEqual(schema.uint8, 0)
    addr = Addr


class Reply(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    rep = schema.SizedIntEnum(schema.uint8, Rep)
    rsv = schema.MustEqual(schema.uint8, 0)
    bind_addr = Addr


class UDPRelay(schema.BinarySchema):
    rsv = schema.MustEqual(schema.Bytes(2), b"\x00\x00")
    flag = schema.uint8
    addr = Addr
    data = schema.Bytes(-1)
