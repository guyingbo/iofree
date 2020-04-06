import iofree
import socket
import pytest
import threading
from time import sleep


@iofree.parser
def example():
    parser = yield from iofree.get_parser()
    while True:
        data = yield from iofree.read(1)
        if data == b"\x10":
            parser.respond(data=b"done", exc=Exception())
        elif data == b"\x20":
            parser.respond(close=True, result=10)


def write_data(sock, n):
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
