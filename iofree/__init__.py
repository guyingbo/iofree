"io-free stream parser which helps implementing network protocols the `Sans-IO` way"
import typing
import warnings
from struct import Struct
from enum import IntEnum, auto
from collections import deque
from .exceptions import NoResult, ParseError

__version__ = "0.2.2"
_wait = object()


class Traps(IntEnum):
    _read = auto()
    _read_more = auto()
    _read_until = auto()
    _read_struct = auto()
    _read_int = auto()
    _write = auto()
    _wait = auto()
    _peek = auto()
    _get_parser = auto()


class State(IntEnum):
    _state_wait = auto()
    _state_next = auto()
    _state_end = auto()


class Parser:
    def __init__(self, gen: typing.Generator):
        self.gen = gen
        self.input = bytearray()
        self.output = bytearray()
        self.res_queue = deque()
        self._next_value = None
        self._last_trap = None
        self._pos = 0
        self._state = State._state_wait
        self._process()

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
        self.input.extend(data)
        self._process()

    def read_output(self, nbytes: int = 0) -> bytes:
        """
        read *at most* ``nbytes``
        """
        if nbytes == 0 or len(self.output) <= nbytes:
            data = bytes(self.output)
            del self.output[:]
            return data
        data = bytes(self.output[:nbytes])
        del self.output[:nbytes]
        return data

    def read(self, nbytes: int = 0) -> bytes:
        "backward-compatible for v0.1.x"
        warnings.warn(
            "backward-compatible for v0.1.x, use read_output instead",
            DeprecationWarning,
        )
        return self.read_output(nbytes)

    @property
    def has_result(self) -> bool:
        return len(self.res_queue) > 0

    def get_result(self):
        """
        raises *NoResult* exception if no result has been set
        """
        self._process()
        if not self.has_result:
            raise NoResult("no result")
        return self.res_queue.popleft()

    def set_result(self, result):
        self.res_queue.append(result)

    def finished(self) -> bool:
        return self._state is State._state_end

    def _process(self):
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
                raise ParseError(
                    f"on value {self._next_value!r}"
                )
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
        return len(self.input) > 0

    def write(self, data: bytes) -> None:
        self.output.extend(data)

    def _write(self, data: bytes) -> None:
        self.output.extend(data)

    def _wait(self) -> None:
        if not getattr(self, "_waiting", False):
            self._waiting = True
            return _wait
        self._waiting = False
        return

    def _read(self, nbytes: int = 0, from_=None) -> bytes:
        buf = self.input if from_ is None else from_
        if nbytes == 0:
            data = bytes(buf)
            del buf[:]
            return data
        if len(buf) < nbytes:
            return _wait
        data = bytes(buf[:nbytes])
        del buf[:nbytes]
        return data

    def _read_more(self, nbytes: int = 1, from_=None) -> bytes:
        buf = self.input if from_ is None else from_
        if len(buf) < nbytes:
            return _wait
        data = bytes(buf)
        del buf[:]
        return data

    def _read_until(self, data: bytes, return_tail: bool = True, from_=None) -> bytes:
        buf = self.input if from_ is None else from_
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

    def _read_struct(self, struct_obj: Struct, from_=None) -> tuple:
        buf = self.input if from_ is None else from_
        size = struct_obj.size
        if len(buf) < size:
            return _wait
        result = struct_obj.unpack_from(buf)
        del buf[:size]
        return result

    def _read_int(self, nbytes: int, byteorder: str = "big", from_=None) -> int:
        buf = self.input if from_ is None else from_
        if len(buf) < nbytes:
            return _wait
        data = self._read(nbytes)
        return int.from_bytes(data, byteorder)

    def _peek(self, nbytes: int = 1, from_=None) -> bytes:
        buf = self.input if from_ is None else from_
        if len(buf) < nbytes:
            return _wait
        return bytes(buf[:nbytes])

    def _get_parser(self) -> "Parser":
        return self


def read(nbytes: int = 0, *, from_=None) -> bytes:
    """
    if nbytes = 0, read as many as it can, empty bytes is valid;
    if nbytes > 0, read *exactly* ``nbytes``
    """
    return (yield (Traps._read, nbytes, from_))


def read_more(nbytes: int = 1, *, from_=None) -> bytes:
    """
    read *at least* ``nbytes``
    """
    if nbytes <= 0:
        raise ValueError(f"nbytes must > 0, but got {nbytes}")
    return (yield (Traps._read_more, nbytes, from_))


def read_until(data: bytes, *, return_tail: bool = True, from_=None) -> bytes:
    """
    read until some bytes appear
    """
    return (yield (Traps._read_until, data, return_tail, from_))


def read_struct(fmt: str, *, from_=None) -> tuple:
    """
    read specific formatted data
    """
    return (yield (Traps._read_struct, Struct(fmt), from_))


def read_raw_struct(struct_obj: Struct, *, from_=None) -> tuple:
    """
    read raw struct formatted data
    """
    return (yield (Traps._read_struct, struct_obj, from_))


def read_int(nbytes: int, *, byteorder: str = "big", from_=None) -> int:
    """
    read some bytes as integer
    """
    if nbytes <= 0:
        raise ValueError(f"nbytes must > 0, but got {nbytes}")
    return (yield (Traps._read_int, nbytes, byteorder, from_))


def write(data: bytes) -> None:
    """
    write some bytes to the output buffer
    """
    return (yield (Traps._write, data))


def wait() -> None:
    """
    wait for next send or get_result event
    """
    return (yield (Traps._wait,))


def peek(nbytes: int = 1, *, from_=None) -> bytes:
    """
    peek many bytes without taking them away from buffer
    """
    if nbytes <= 0:
        raise ValueError(f"nbytes must > 0, but got {nbytes}")
    return (yield (Traps._peek, nbytes, from_))


def get_parser() -> Parser:
    return (yield (Traps._get_parser,))


def parser(generator_func: typing.Generator) -> typing.Generator:
    def create_parser(*args, **kwargs) -> Parser:
        return Parser(generator_func(*args, **kwargs))

    generator_func.parser = create_parser
    return generator_func
