import enum
from .. import schema


class ExtensionType(enum.IntEnum):
    server_name = 0
    max_fragment_length = 1
    status_request = 5
    supported_groups = 10
    signature_algorithms = 13
    use_srtp = 14
    heartbeat = 15
    application_layer_protocol_negotiation = 16
    signed_certificate_timestamp = 18
    client_certificate_type = 19
    server_certificate_type = 20
    padding = 21
    pre_shared_key = 41
    early_data = 42
    supported_versions = 43
    cookie = 44
    psk_key_exchange_modes = 45
    certificate_authorities = 47
    oid_filters = 48
    post_handshake_auth = 49
    signature_algorithms_cert = 50
    key_share = 51


class HandshakeType(enum.IntEnum):
    client_hello = 1
    server_hello = 2
    new_session_ticket = 4
    end_of_early_data = 5
    encrypted_extensions = 8
    certificate = 11
    certificate_request = 13
    certificate_verify = 15
    finished = 20
    key_update = 24
    message_hash = 254


class ContentType(enum.IntEnum):
    invalid = 0
    change_cipher_spec = 20
    alert = 21
    handshake = 22
    application_data = 23


class CipherSuite(enum.IntEnum):
    TLS_AES_128_GCM_SHA256 = 0x1301
    TLS_AES_256_GCM_SHA384 = 0x1302
    TLS_CHACHA20_POLY1305_SHA256 = 0x1303
    TLS_AES_128_CCM_SHA256 = 0x1304
    TLS_AES_128_CCM_8_SHA256 = 0x1305


cipher_suite = schema.SizedIntEnum(schema.uint16, CipherSuite)


class Extension(schema.BinarySchema):
    ext_type = schema.SizedIntEnum(schema.uint16, ExtensionType)
    ext_data = schema.LengthPrefixedBytes(schema.uint16)


class ClientHello(schema.BinarySchema):
    legacy_version = schema.MustEqual(schema.Bytes(2), b"\x03\x03")
    rand = schema.Bytes(32)
    legacy_session_id = schema.LengthPrefixedBytes(schema.uint8)
    cipher_suites = schema.LengthPrefixedObjectList(schema.uint16, cipher_suite)
    legacy_compression_methods = schema.MustEqual(schema.Bytes(2), b"\x01\x00")
    extensions = schema.LengthPrefixedObjectList(schema.uint16, Extension)


class ServerHello(schema.BinarySchema):
    legacy_version = schema.MustEqual(schema.Bytes(2), b"\x03\x03")
    rand = schema.Bytes(32)
    legacy_session_id_echo = schema.LengthPrefixedBytes(schema.uint8)
    cipher_suites = schema.LengthPrefixedObjectList(schema.uint16, cipher_suite)
    legacy_compression_method = schema.MustEqual(schema.uint8, 0)
    extensions = schema.LengthPrefixedObjectList(schema.uint16, Extension)


class Handshake(schema.BinarySchema):
    msg_type = schema.SizedIntEnum(schema.uint8, HandshakeType)
    msg = schema.LengthPrefixedObject(
        schema.uint24,
        schema.Switch(
            "msg_type",
            {
                HandshakeType.client_hello: ClientHello,
                HandshakeType.server_hello: ServerHello,
            },
        ),
    )


class TLSPlaintext(schema.BinarySchema):
    content_type = schema.SizedIntEnum(schema.uint8, ContentType)
    legacy_record_version = schema.Bytes(2)
    fragment = schema.LengthPrefixedBytes(schema.uint16)

    @classmethod
    def pack(cls, content_type: ContentType, data: bytes) -> bytes:
        assert len(data) > 0, "need data"
        data = memoryview(data)
        fragments = []
        while True:
            if len(data) > 16384:
                fragments.append(data[:16384])
                data = data[16384:]
            else:
                fragments.append(data)
                break
        is_handshake = content_type is ContentType.handshake
        return b"".join(
            cls(
                content_type,
                b"\x03\x01" if i == 0 and is_handshake else b"\x03\x03",
                frg,
            )
            for i, frg in enumerate(fragments)
        )


class TLSInnerPlaintext(schema.BinarySchema):
    content = schema.Bytes(-1)
    content_type = schema.SizedIntEnum(schema.uint8, ContentType)
    # padding = schema.Padding(b"\x00")


class TLSCiphertext(schema.BinarySchema):
    opaque_type = schema.MustEqual(
        schema.SizedIntEnum(schema.uint8, ContentType), ContentType.application_data
    )
    legacy_record_version = schema.MustEqual(schema.Bytes(2), b"\x03\x03")
    encrypted_record = schema.LengthPrefixedBytes(schema.uint16)
