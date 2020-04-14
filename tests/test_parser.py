import iofree
import socket
import pytest
import threading
from time import sleep
from iofree import schema
from iofree.contrib.common import Addr


@iofree.parser
def example():
    parser = yield from iofree.get_parser()
    yield from Addr
    while True:
        n = yield from schema.uint8
        if n == 16:
            parser.respond(data=b"done", exc=Exception())
        elif n == 32:
            parser.respond(close=True, result=10)


def write_data(sock, n):
    sock.sendall(Addr.from_tuple(("google.com", 8080)).binary)
    for i in range(n):
        sock.sendall(i.to_bytes(1, "big"))
        sleep(0.001)
    sock.shutdown(socket.SHUT_WR)


def test_parser():
    parser = example.parser()
    rsock, wsock = socket.socketpair()
    thread = threading.Thread(target=write_data, args=(wsock, 0x21))
    thread.start()
    with pytest.raises(Exception):
        r = parser.run(rsock)
    r = parser.run(rsock)
    assert r == 10
    thread.join()


def test_parser2():
    parser = example.parser()
    rsock, wsock = socket.socketpair()
    thread = threading.Thread(target=write_data, args=(wsock, 5))
    thread.start()
    with pytest.raises(iofree.ParseError):
        parser.run(rsock)
    thread.join()


@iofree.parser
def first():
    parser = yield from iofree.get_parser()
    for i in range(10):
        a = yield from schema.Group(x=schema.uint8, y=schema.uint16be)
        parser.respond(result=a.binary[1:] + a.binary[:1])
    return b""


@iofree.parser
def second():
    parser = yield from iofree.get_parser()
    for i in range(10):
        a = yield from schema.Group(x=schema.uint16be, y=schema.uint8)
        parser.respond(result=a)


def test_parser_chain():
    p = iofree.ParserChain(first.parser(), second.parser())
    p.send(b"")
    for i in range(10):
        p.send(schema.Group(x=schema.uint8, y=schema.uint16be)(30, 512).binary)
    list(p)
