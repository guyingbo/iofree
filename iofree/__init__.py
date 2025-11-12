"""`iofree` is an easy-to-use and powerful library \
to help you implement network protocols and binary parsers."""

import sys
import typing
from collections import deque
from enum import IntEnum, auto
from socket import SocketType
from struct import Struct

from .exceptions import NoResult, ParseError

__version__ = "0.2.5"
_wait = object()
_no_result = object()


class Traps(IntEnum):
    _read = auto()
    _read_more = auto()
    _read_until = auto()
    _read_struct = auto()
    _read_int = auto()
    _wait = auto()
    _peek = auto()
    _wait_event = auto()
    _get_parser = auto()


class State(IntEnum):
    _state_wait = auto()
    _state_next = auto()
    _state_end = auto()


class Parser:
    def __init__(self, gen: typing.Generator):
        self.gen = gen
        self._input = bytearray()
        self._input_events: typing.Deque = deque()
        self._output_events: typing.Deque = deque()
        self._res = _no_result
        self._mapping_stack: typing.Deque = deque()
        self._next_value = None
        self._last_trap: typing.Optional[tuple] = None
        self._pos = 0
        self._state: State = State._state_wait
        self._process()

    def __repr__(self):
        return f"<{self.__class__.__qualname__}({self.gen})>"

    def __iter__(self):
        return self

    def __next__(self) -> typing.Any:
        if self._output_events:
            return self._output_events.popleft()
        raise StopIteration

    def parse(self, data: bytes, *, strict: bool = True) -> typing.Any:
        """
        parse bytes
        """
        self.send(data)
        if strict and self.has_more_data():
            raise ParseError("redundant data left")
        return self.get_result()

    def send(self, data: bytes = b"") -> None:
        """
        send data for parsing
        """
        self._input.extend(data)
        self._process()

    def read_output_bytes(self) -> bytes:
        buf = []
        for to_send, close, exc, result in self:
            buf.append(result)
        return b"".join(buf)

    def respond(
        self,
        *,
        data: bytes = b"",
        close: bool = False,
        exc: typing.Optional[Exception] = None,
        result: typing.Any = _no_result,
    ) -> None:
        """produce some event data to interact with a stream:
        data:   bytes to send to the peer
        close:  whether the socket should be closed
        exc:    raise an exception to break the loop
        result: result to return
        """
        self._output_events.append((data, close, exc, result))

    def run(self, sock: SocketType) -> typing.Any:
        "reference implementation of how to deal with socket"
        self.send(b"")
        while True:
            for to_send, close, exc, result in self:
                if to_send:
                    sock.sendall(to_send)
                if close:
                    sock.close()
                if exc:
                    raise exc
                if result is not _no_result:
                    return result
            data = sock.recv(1024)
            if not data:
                raise ParseError("need data")
            self.send(data)

    @property
    def has_result(self) -> bool:
        return self._res is not _no_result

    def get_result(self) -> typing.Any:
        """
        raises *NoResult* exception if no result has been set
        """
        self._process()
        if not self.has_result:
            raise NoResult("no result")
        return self._res

    def set_result(self, result) -> None:
        self._res = result
        self.respond(result=result)

    def finished(self) -> bool:
        return self._state is State._state_end

    def _process(self) -> None:
        if self._state is State._state_end:
            return
        self._state = State._state_next
        while self._state is State._state_next:
            self._next_state()

    def _next_state(self) -> None:
        if self._last_trap is None:
            try:
                trap, *args = self.gen.send(self._next_value)
            except StopIteration as e:
                self._state = State._state_end
                self.set_result(e.value)
                return
            except Exception:
                self._state = State._state_end
                tb = sys.exc_info()[2]
                raise ParseError(f"{self._next_value!r}").with_traceback(tb)
            else:
                if not isinstance(trap, Traps):
                    self._state = State._state_end
                    raise RuntimeError(f"Expect Traps object, but got: {trap}")
        else:
            trap, *args = self._last_trap
        result = getattr(self, trap.name)(*args)
        if result is _wait:
            self._state = State._state_wait
            self._last_trap = (trap, *args)
        else:
            self._state = State._state_next
            self._next_value = result
            self._last_trap = None

    def readall(self) -> bytes:
        """
        retrieve data from input back
        """
        return self._read(0)

    def has_more_data(self) -> bool:
        "indicate whether input has some bytes left"
        return len(self._input) > 0

    def send_event(self, event: typing.Any) -> None:
        self._input_events.append(event)
        self._process()

    def _wait_event(self):
        if self._input_events:
            return self._input_events.popleft()
        return _wait

    def _wait(self) -> typing.Optional[object]:
        if not getattr(self, "_waiting", False):
            self._waiting = True
            return _wait
        self._waiting = False
        return None

    def _read(self, nbytes: int = 0, from_=None) -> bytes:
        buf = self._input if from_ is None else from_
        if nbytes == 0:
            data = bytes(buf)
            del buf[:]
            return data
        if len(buf) < nbytes:
            return _wait
        data = bytes(buf[:nbytes])
        del buf[:nbytes]
        return data

    def _read_more(self, nbytes: int = 1, from_=None) -> typing.Union[object, bytes]:
        buf = self._input if from_ is None else from_
        if len(buf) < nbytes:
            return _wait
        data = bytes(buf)
        del buf[:]
        return data

    def _read_until(
        self, data: bytes, return_tail: bool = True, from_=None
    ) -> typing.Union[object, bytes]:
        buf = self._input if from_ is None else from_
        index = buf.find(data, self._pos)
        if index == -1:
            self._pos = len(buf) - len(data) + 1
            self._pos = self._pos if self._pos > 0 else 0
            return _wait
        size = index + len(data)
        if return_tail:
            data = bytes(buf[:size])
        else:
            data = bytes(buf[:index])
        del buf[:size]
        self._pos = 0
        return data

    def _read_struct(
        self, struct_obj: Struct, from_=None
    ) -> typing.Union[object, tuple]:
        buf = self._input if from_ is None else from_
        size = struct_obj.size
        if len(buf) < size:
            return _wait
        result = struct_obj.unpack_from(buf)
        del buf[:size]
        return result

    def _read_int(
        self, nbytes: int, byteorder: str = "big", signed: bool = False, from_=None
    ) -> typing.Union[object, int]:
        buf = self._input if from_ is None else from_
        if len(buf) < nbytes:
            return _wait
        data = self._read(nbytes)
        return int.from_bytes(data, byteorder, signed=signed)

    def _peek(self, nbytes: int = 1, from_=None) -> typing.Union[object, bytes]:
        buf = self._input if from_ is None else from_
        if len(buf) < nbytes:
            return _wait
        return bytes(buf[:nbytes])

    def _get_parser(self) -> "Parser":
        return self


class LinkedNode:
    __slots__ = ("parser", "next")

    def __init__(self, parser: Parser, next_: typing.Optional["LinkedNode"]):
        self.parser = parser
        self.next = next_


class ParserChain:
    def __init__(self, *parsers: Parser):
        nxt = None
        for parser in reversed(parsers):
            node = LinkedNode(parser, nxt)
            nxt = node
        self.first = node

    def send(self, data: bytes) -> None:
        self.first.parser.send(data)

    def __iter__(self):
        return self._get_events(self.first)

    def _get_events(self, node: LinkedNode) -> typing.Generator[
        typing.Tuple[
            typing.Optional[bytes],
            typing.Optional[bool],
            typing.Optional[Exception],
            typing.Any,
        ],
        None,
        None,
    ]:
        for data, close, exc, result in node.parser:
            if result is not _no_result and node.next:
                node.next.parser.send(result)
                yield (data, close, exc, _no_result)
            else:
                yield (data, close, exc, result)
        if node.next:
            yield from self._get_events(node.next)


def read(nbytes: int = 0, *, from_=None) -> typing.Generator[tuple, bytes, bytes]:
    """
    if nbytes = 0, read as many as possible, empty bytes is valid;
    if nbytes > 0, read *exactly* ``nbytes``
    """
    return (yield (Traps._read, nbytes, from_))


def read_more(nbytes: int = 1, *, from_=None) -> typing.Generator[tuple, bytes, bytes]:
    """
    read *at least* ``nbytes``
    """
    if nbytes <= 0:
        raise ValueError(f"nbytes must > 0, but got {nbytes}")
    return (yield (Traps._read_more, nbytes, from_))


def read_until(
    data: bytes, *, return_tail: bool = True, from_=None
) -> typing.Generator[tuple, bytes, bytes]:
    """
    read until some bytes appear
    """
    return (yield (Traps._read_until, data, return_tail, from_))


def read_struct(fmt: str, *, from_=None) -> typing.Generator[tuple, tuple, tuple]:
    """
    read specific formatted data
    """
    return (yield (Traps._read_struct, Struct(fmt), from_))


def read_raw_struct(
    struct_obj: Struct, *, from_=None
) -> typing.Generator[tuple, tuple, tuple]:
    """
    read raw struct formatted data
    """
    return (yield (Traps._read_struct, struct_obj, from_))


def read_int(
    nbytes: int, byteorder: str = "big", *, signed: bool = False, from_=None
) -> typing.Generator[tuple, int, int]:
    """
    read some bytes as integer
    """
    if nbytes <= 0:
        raise ValueError(f"nbytes must > 0, but got {nbytes}")
    return (yield (Traps._read_int, nbytes, byteorder, signed, from_))


def wait() -> typing.Generator[tuple, bytes, typing.Optional[object]]:
    """
    wait for next send event
    """
    return (yield (Traps._wait,))


def peek(nbytes: int = 1, *, from_=None) -> typing.Generator[tuple, bytes, bytes]:
    """
    peek many bytes without taking them away from buffer
    """
    if nbytes <= 0:
        raise ValueError(f"nbytes must > 0, but got {nbytes}")
    return (yield (Traps._peek, nbytes, from_))


def wait_event() -> typing.Generator[tuple, typing.Any, typing.Any]:
    """
    wait for an event
    """
    return (yield (Traps._wait_event,))


def get_parser() -> typing.Generator[tuple, Parser, Parser]:
    "get current parser object"
    return (yield (Traps._get_parser,))


def parser(generator_func: typing.Callable) -> typing.Callable:
    "decorator function to wrap a generator"

    def create_parser(*args, **kwargs) -> Parser:
        return Parser(generator_func(*args, **kwargs))

    generator_func.parser = create_parser
    return generator_func
