import iofree
import random
import pytest
from datetime import datetime


@iofree.parser
def http_response():
    parser = yield from iofree.get_parser()
    first_line = yield from iofree.read_until(b"\r\n")
    ver, code, status = first_line[:-2].split()
    assert ver == b"HTTP/1.1"
    assert code == b"200"
    assert status == b"OK"
    header_lines = yield from iofree.read_until(b"\r\n\r\n", return_tail=False)
    headers = header_lines.split(b"\r\n")
    data = yield from iofree.read(4)
    assert data == b"haha"
    (number,) = yield from iofree.read_struct("!H")
    assert number == 8 * 256 + 8
    number = yield from iofree.read_int(3)
    assert number == int.from_bytes(b"\x11\x11\x11", "big")
    assert (yield from iofree.peek(2)) == b"co"
    assert (yield from iofree.read(7)) == b"content"
    yield from iofree.write(b"abc")
    parser.write(b"def")
    yield from iofree.wait()
    assert len((yield from iofree.read_more(5))) >= 5
    yield from iofree.read()
    return headers


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
        b"haha\x08\x08\x11\x11\x11content extra"
    )
    while response:
        n = random.randrange(1, 30)
        data = response[:n]
        del response[:n]
        parser.send(data)
    parser.send()
    parser.read(1) == b"a"
    parser.read() == b"bc"
    assert parser.has_result
    headers = parser.get_result()
    assert len(headers) == 6
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
