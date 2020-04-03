import pytest
from iofree import schema


def check_schema(schema):
    str(schema)
    repr(schema)
    str(schema.__class__)
    schema2 = schema.__class__.parse(schema.binary)
    assert schema == schema2


def test_number():
    assert schema.uint16be.parse(b"\x00\x03") == 3
    with pytest.raises(schema.ParseError):
        schema.uint8.parse(b"\x03\x04", strict=True)


def test_length_prefixed_bytes():
    some_bytes = schema.LengthPrefixedBytes(schema.uint8)
    str(some_bytes)


def test_basic():
    class Content(schema.BinarySchema):
        first_line = schema.EndWith(b"\r\n")
        string = schema.String(5, encoding="ascii")

    content = Content(b"GET / HTTP/1.1", "abcde")
    assert content != 3
    content2 = Content(b"POST", "xyz")
    assert content != content2
    with pytest.raises(ValueError):
        Content(b"PUT")
    check_schema(content)

    with pytest.raises(schema.ParseError):
        Content.parse(b"abc\r\n" + "中文".encode())


def test_equal():
    class Content(schema.BinarySchema):
        name = schema.MustEqual(schema.Bytes(3), b"abc")
        name2 = schema.LengthPrefixedObject(schema.uint8, schema.Bytes(1))

    with pytest.raises(schema.ParseError):
        Content.parse(b"abb")

    with pytest.raises(schema.ParseError):
        Content.parse(b"abc\x02abc")


def test_group():
    Group = schema.Group(a=schema.uint8, b=schema.uint32be)
    check_schema(Group(1, 3))
    Group2 = schema.Group(a=schema.uint16, b=schema.uint16be)
    check_schema(Group2(1, 3))


def test_group2():
    class Dynamic(schema.BinarySchema):
        a = schema.uint8
        b = schema.Group(c=schema.uint16, d=schema.uint16be)

    dynamic = Dynamic(1, Dynamic.b(2, 3))
    check_schema(dynamic)
