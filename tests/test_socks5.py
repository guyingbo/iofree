import os

import pytest

from iofree.contrib import socks5


def check_schema(schema):
    str(schema)
    repr(schema)
    str(schema.__class__)
    parser = schema.__class__.get_parser()
    schema2 = parser.parse(schema.binary)
    assert schema == schema2


def test_handshake():
    handshake = socks5.Handshake(
        ..., [socks5.AuthMethod.no_auth, socks5.AuthMethod.user_auth]
    )
    check_schema(handshake)
    with pytest.raises(ValueError):
        socks5.Handshake(6, [])


def test_client_request():
    auth = socks5.UsernameAuth(..., "username", "password")
    check_schema(auth)

    request = socks5.ClientRequest(
        ..., socks5.Cmd.connect, 0, socks5.Addr(1, "127.0.0.1", 8000)
    )
    check_schema(request)


def test_reply():
    reply = socks5.Reply(5, socks5.Rep.succeeded, 0, socks5.Addr(4, "::1", 8080))
    check_schema(reply)


def test_udp_reply():
    udp_reply = socks5.UDPRelay(
        ..., 32, socks5.Addr.from_tuple(("google.com", 80)), os.urandom(64)
    )
    check_schema(udp_reply)
