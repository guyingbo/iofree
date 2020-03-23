import pytest
from iofree import schema


def check_schema(schema):
    str(schema)
    repr(schema)
    str(schema.__class__)
    schema2 = schema.__class__.parse(schema.binary)
    assert schema == schema2


def test_basic():
    class Content(schema.BinarySchema):
        first_line = schema.EndWith(b"\r\n")
        string = schema.String(5)

    content = Content(b"GET / HTTP/1.1", "abcde")
    assert content != 3
    content2 = Content(b"POST", "xyz")
    assert content != content2
    with pytest.raises(ValueError):
        Content(b"PUT")
    check_schema(content)
