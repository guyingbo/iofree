import random
from datetime import datetime

import pytest

import iofree
from iofree import schema


class HTTPResponse(schema.BinarySchema):
    head = schema.EndWith(b"\r\n\r\n")

    def __post_init__(self):
        first_line, *header_lines = self.head.split(b"\r\n")
        self.ver, self.code, *status = first_line.split(None, 2)
        self.status = status[0] if status else b""
        self.header_lines = header_lines


@iofree.parser
def http_response():
    response = yield from HTTPResponse
    assert response.ver == b"HTTP/1.1"
    assert response.code == b"200"
    assert response.status == b"OK"
    yield from iofree.read_until(b"\n", return_tail=True)
    data = yield from iofree.read(4)
    assert data == b"haha"
    (number,) = yield from iofree.read_struct("!H")
    assert number == 8 * 256 + 8
    number = yield from iofree.read_int(3)
    assert number == int.from_bytes(b"\x11\x11\x11", "big")
    assert (yield from iofree.peek(2)) == b"co"
    assert (yield from iofree.read(7)) == b"content"
    yield from iofree.wait()
    assert len((yield from iofree.read_more(5))) >= 5
    yield from iofree.read()
    yield from iofree.wait_event()
    return b"\r\n".join(response.header_lines)


def test_http_parser():
    parser = http_response.parser()
    response = bytearray(
        b"HTTP/1.1 200 OK\r\n"
        b"Connection: keep-alive\r\n"
        b"Content-Encoding: gzip\r\n"
        b"Content-Type: text/html\r\n"
        b"Date: "
        + datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT").encode()
        + b"\r\nServer: nginx\r\n"
        b"Vary: Accept-Encoding\r\n\r\n"
        b"a line\nhaha\x08\x08\x11\x11\x11content extra"
    )
    while response:
        n = random.randrange(1, 30)
        data = response[:n]
        del response[:n]
        parser.send(data)
    parser.send()
    parser.send_event(0)
    assert parser.has_result
    parser.get_result()
    parser.read_output_bytes()
    parser.send(b"redundant")
    assert parser.readall().endswith(b"redundant")


def test_http_parser2():
    for i in range(100):
        test_http_parser()


@iofree.parser
def simple():
    parser = yield from iofree.get_parser()
    yield from iofree.read(1)
    assert parser.has_more_data()
    assert not parser.finished()
    raise Exception("special")


@iofree.parser
def bad_reader():
    with pytest.raises(ValueError):
        yield from iofree.read_more(-1)
    with pytest.raises(ValueError):
        yield from iofree.peek(-1)
    with pytest.raises(ValueError):
        yield from iofree.read_int(-1)

    yield from iofree.wait()
    yield "bad"


def test_exception():
    parser = simple.parser()
    with pytest.raises(iofree.ParseError):
        parser.send(b"haha")
    with pytest.raises(iofree.NoResult):
        parser.get_result()


def test_bad():
    parser = bad_reader.parser()
    with pytest.raises(RuntimeError):
        parser.send(b"haha")
