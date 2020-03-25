import os
from iofree.contrib import tls13 as tls


def check_schema(schema):
    str(schema)
    repr(schema)
    str(schema.__class__)
    parser = schema.__class__.get_parser()
    schema2 = parser.parse(schema.binary)
    assert schema == schema2


def test_handshake():
    client_hello = tls.ClientHello(
        b"\x03\x03",
        os.urandom(32),
        b"=" * 32,
        [
            tls.CipherSuite.TLS_AES_128_CCM_8_SHA256,
            tls.CipherSuite.TLS_AES_128_GCM_SHA256,
        ],
        b"\x01\x00",
        [tls.Extension(tls.ExtensionType.early_data, b"some data")],
    )
    handshake = tls.Handshake(tls.HandshakeType.client_hello, client_hello)
    check_schema(handshake)
