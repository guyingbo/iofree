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


class NameType(enum.IntEnum):
    host_name = 0


class SignatureScheme(enum.IntEnum):
    # RSASSA-PKCS1-v1_5 algorithms
    rsa_pkcs1_sha256 = 0x0401
    rsa_pkcs1_sha384 = 0x0501
    rsa_pkcs1_sha512 = 0x0601
    # ECDSA algorithms
    ecdsa_secp256r1_sha256 = 0x0403
    ecdsa_secp384r1_sha384 = 0x0503
    ecdsa_secp521r1_sha512 = 0x0603
    # RSASSA-PSS algorithms with public key OID rsaEncryption
    rsa_pss_rsae_sha256 = 0x0804
    rsa_pss_rsae_sha384 = 0x0805
    rsa_pss_rsae_sha512 = 0x0806
    # EdDSA algorithms
    ed25519 = 0x0807
    ed448 = 0x0808
    # RSASSA-PSS algorithms with public key OID RSASSA-PSS
    rsa_pss_pss_sha256 = 0x0809
    rsa_pss_pss_sha384 = 0x080a
    rsa_pss_pss_sha512 = 0x080b
    # Legacy algorithms
    rsa_pkcs1_sha1 = 0x0201
    ecdsa_sha1 = 0x0203
    # Reserved Code Points
    # private_use(0xFE00..0xFFFF)


class NamedGroup(enum.IntEnum):
    # Elliptic Curve Groups (ECDHE)
    secp256r1 = 0x0017
    secp384r1 = 0x0018
    secp521r1 = 0x0019
    x25519 = 0x001D
    x448 = 0x001E
    # Finite Field Groups (DHE)
    ffdhe2048 = 0x0100
    ffdhe3072 = 0x0101
    ffdhe4096 = 0x0102
    ffdhe6144 = 0x0103
    ffdhe8192 = 0x0104
    # Reserved Code Points
    # ffdhe_private_use(0x01FC..0x01FF)
    # ecdhe_private_use(0xFE00..0xFEFF)


class PskKeyExchangeMode(enum.IntEnum):
    psk_ke = 0
    psk_dhe_ke = 1


class CipherSuite(enum.IntEnum):
    TLS_AES_128_GCM_SHA256 = 0x1301
    TLS_AES_256_GCM_SHA384 = 0x1302
    TLS_CHACHA20_POLY1305_SHA256 = 0x1303
    TLS_AES_128_CCM_SHA256 = 0x1304
    TLS_AES_128_CCM_8_SHA256 = 0x1305


cipher_suite = schema.SizedIntEnum(schema.uint16be, CipherSuite)


class ServerName(schema.BinarySchema):
    name_type = schema.MustEqual(
        schema.SizedIntEnum(schema.uint8, NameType), NameType.host_name
    )
    name = schema.Switch(
        "name_type", {NameType.host_name: schema.LengthPrefixedString(schema.uint16be)}
    )


class Extension(schema.BinarySchema):
    ext_type = schema.SizedIntEnum(schema.uint16be, ExtensionType)
    ext_data = schema.Switch(
        "ext_type",
        {
            ExtensionType.server_name: schema.LengthPrefixedObject(
                schema.uint16be,
                schema.LengthPrefixedObjectList(schema.uint16be, ServerName),
            ),
            ExtensionType.supported_versions: schema.LengthPrefixedObject(
                schema.uint16be,
                schema.LengthPrefixedObjectList(schema.uint8, schema.Bytes(2)),
            ),
            ExtensionType.signature_algorithms: schema.LengthPrefixedObject(
                schema.uint16be,
                schema.LengthPrefixedObjectList(
                    schema.uint16be,
                    schema.SizedIntEnum(schema.uint16be, SignatureScheme),
                ),
            ),
            ExtensionType.supported_groups: schema.LengthPrefixedObject(
                schema.uint16be,
                schema.LengthPrefixedObjectList(
                    schema.uint16be, schema.SizedIntEnum(schema.uint16be, NamedGroup)
                ),
            ),
            ExtensionType.key_share: schema.LengthPrefixedObject(
                schema.uint16be,
                schema.LengthPrefixedObjectList(
                    schema.uint16be, schema.LengthPrefixedBytes(schema.uint16be)
                ),
            ),
            ExtensionType.psk_key_exchange_modes: schema.LengthPrefixedObject(
                schema.uint16be,
                schema.LengthPrefixedObjectList(
                    schema.uint8, schema.SizedIntEnum(schema.uint8, PskKeyExchangeMode)
                ),
            ),
            ExtensionType.early_data: schema.LengthPrefixedObject(
                schema.uint16be, schema.LengthPrefixedBytes(schema.uint16be)
            ),
        },
    )

    @classmethod
    def server_name(cls, name):
        return cls(ExtensionType.server_name, [ServerName(..., name)])

    @classmethod
    def supported_versions(cls, *versions):
        return cls(ExtensionType.supported_versions, versions)

    @classmethod
    def signature_algorithms(cls, schemes):
        return cls(ExtensionType.signature_algorithms, schemes)

    @classmethod
    def supported_groups(cls, groups):
        return cls(ExtensionType.supported_groups, groups)

    @classmethod
    def key_share(cls, key_exchanges):
        return cls(ExtensionType.key_share, key_exchanges)

    @classmethod
    def psk_key_exchange_modes(cls, modes):
        return cls(ExtensionType.psk_key_exchange_modes, modes)

    @classmethod
    def early_data(cls, data):
        return cls(ExtensionType.early_data, data)


class ClientHello(schema.BinarySchema):
    legacy_version = schema.MustEqual(schema.Bytes(2), b"\x03\x03")
    rand = schema.Bytes(32)
    legacy_session_id = schema.LengthPrefixedBytes(schema.uint8)
    cipher_suites = schema.LengthPrefixedObjectList(schema.uint16be, cipher_suite)
    legacy_compression_methods = schema.MustEqual(schema.Bytes(2), b"\x01\x00")
    extensions = schema.LengthPrefixedObjectList(schema.uint16be, Extension)


class ServerHello(schema.BinarySchema):
    legacy_version = schema.MustEqual(schema.Bytes(2), b"\x03\x03")
    rand = schema.Bytes(32)
    legacy_session_id_echo = schema.LengthPrefixedBytes(schema.uint8)
    cipher_suites = schema.LengthPrefixedObjectList(schema.uint16be, cipher_suite)
    legacy_compression_method = schema.MustEqual(schema.uint8, 0)
    extensions = schema.LengthPrefixedObjectList(schema.uint16be, Extension)


class Handshake(schema.BinarySchema):
    msg_type = schema.SizedIntEnum(schema.uint8, HandshakeType)
    msg = schema.LengthPrefixedObject(
        schema.uint24be,
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
    fragment = schema.LengthPrefixedBytes(schema.uint16be)

    @classmethod
    def pack(cls, content_type: ContentType, data: bytes) -> bytes:
        if not data:
            raise ValueError("need data")
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
    encrypted_record = schema.LengthPrefixedBytes(schema.uint16be)
