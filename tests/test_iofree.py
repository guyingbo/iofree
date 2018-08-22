import iofree
import random
import pytest
from datetime import datetime


def http_response_reader():
    first_line = yield from iofree.read_until(b"\r\n")
    ver, code, status = first_line[:-2].split()
    assert ver == b"HTTP/1.1"
    assert code == b"200"
    assert status == b"OK"
    header_lines = yield from iofree.read_until(b"\r\n\r\n", return_tail=False)
    headers = header_lines.split(b"\r\n")
    data = yield from iofree.read(4)
    assert data == b"haha"
    number, = yield from iofree.read_struct("!H")
    assert number == 8 * 256 + 8
    assert (yield from iofree.peek(2)) == b"co"
    assert (yield from iofree.read(7)) == b"content"
    yield from iofree.write(b"abc")
    yield from iofree.wait()
    assert len((yield from iofree.read_more(5))) >= 5
    yield from iofree.read()
    return headers


def test_http_parser():
    parser = iofree.Parser(http_response_reader())
    response = bytearray(
        b"HTTP/1.1 200 OK\r\n"
        b"Connection: keep-alive\r\n"
        b"Content-Encoding: gzip\r\n"
        b"Content-Type: text/html\r\n"
        b"Date: "
        + datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT").encode()
        + b"\r\nServer: nginx\r\n"
        b"Vary: Accept-Encoding\r\n\r\n"
        b"haha\x08\x08content extra"
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


def simple_reader():
    yield from iofree.read(1)
    raise Exception("special")


def bad_reader():
    yield from iofree.wait()
    yield "bad"


def test_exception():
    parser = iofree.Parser(simple_reader())
    with pytest.raises(Exception) as exc_info:
        parser.send(b"haha")
    assert exc_info.value.args[0] == "special"
    with pytest.raises(iofree.NoResult):
        parser.get_result()


def test_bad():
    parser = iofree.Parser(bad_reader())
    with pytest.raises(RuntimeError):
        parser.send(b"haha")
