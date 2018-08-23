"io-free stream parser which helps implementing network protocols the `Sans-IO` way"
import struct
from enum import IntEnum, auto

__version__ = "0.1.1"

_no_result = object()
_wait = object()


class NoResult(RuntimeError):
    ""


class Traps(IntEnum):
    _read = auto()
    _read_more = auto()
    _read_until = auto()
    _read_struct = auto()
    _read_int = auto()
    _write = auto()
    _wait = auto()
    _peek = auto()


class State(IntEnum):
    _state_wait = auto()
    _state_next = auto()
    _state_end = auto()


class Parser:
    def __init__(self, gen):
        self.gen = gen
        self.input = bytearray()
        self.output = bytearray()
        self.res = _no_result
        self._next_value = None
        self._last_trap = None
        self._pos = 0
        self._state = State._state_wait
        self._process()

    def send(self, data: bytes = b""):
        """
        send data for parsing
        """
        self.input.extend(data)
        self._process()

    def read(self, nbytes: int = 0) -> bytes:
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

    @property
    def has_result(self) -> bool:
        return self.res is not _no_result

    def get_result(self):
        """
        raises *NoResult* exception if no result has been set
        """
        self._process()
        if not self.has_result:
            raise NoResult
        return self.res

    def _process(self):
        if self.has_result or self._state is State._state_end:
            return
        self._state = State._state_next
        while self._state is State._state_next:
            self._next_state()

    def _next_state(self):
        if self._last_trap is None:
            try:
                trap, *args = self.gen.send(self._next_value)
            except StopIteration as e:
                self._state = State._state_end
                self.res = e.value
                return
            except Exception as e:
                self._state = State._state_end
                raise
            else:
                if not isinstance(trap, Traps):
                    self._state = State._state_end
                    raise RuntimeError(f"Expect Traps object, but got: {trap}")
        else:
            trap, *args = self._last_trap
        r = getattr(self, trap.name)(*args)
        if r is _wait:
            self._state = State._state_wait
            self._last_trap = (trap, *args)
        else:
            self._state = State._state_next
            self._next_value = r
            self._last_trap = None

    def readall(self) -> bytes:
        """
        retrieve data from input back
        """
        return self._read(0)

    def _read(self, nbytes: int = 0) -> bytes:
        if nbytes == 0:
            data = bytes(self.input)
            del self.input[:]
            return data
        if len(self.input) < nbytes:
            return _wait
        data = bytes(self.input[:nbytes])
        del self.input[:nbytes]
        return data

    def _read_more(self, nbytes: int = 1) -> bytes:
        assert nbytes > 0, "nbytes must > 0"
        if len(self.input) < nbytes:
            return _wait
        data = bytes(self.input)
        del self.input[:]
        return data

    def _read_until(self, data: bytes, return_tail: bool = True) -> bytes:
        index = self.input.find(data, self._pos)
        if index == -1:
            self._pos = len(self.input) - len(data) + 1
            self._pos = self._pos if self._pos > 0 else 0
            return _wait
        size = index + len(data)
        if return_tail:
            data = bytes(self.input[:size])
        else:
            data = bytes(self.input[:index])
        del self.input[:size]
        self._pos = 0
        return data

    def _read_struct(self, fmt: str) -> tuple:
        size = struct.calcsize(fmt)
        if len(self.input) < size:
            return _wait
        result = struct.unpack_from(fmt, self.input)
        del self.input[:size]
        return result

    def _read_int(self, nbytes: int, byteorder: str = "big") -> int:
        assert nbytes > 0, "nbytes must > 0"
        if len(self.input) < nbytes:
            return _wait
        data = self._read(nbytes)
        return int.from_bytes(data, byteorder)

    def _write(self, data: bytes):
        self.output.extend(data)

    def _wait(self):
        if not getattr(self, "_waiting", False):
            self._waiting = True
            return _wait
        self._waiting = False
        return

    def _peek(self, nbytes: int = 1) -> bytes:
        assert nbytes > 0, "nbytes must > 0"
        if len(self.input) < nbytes:
            return _wait
        return bytes(self.input[:nbytes])


def read(nbytes: int = 0) -> bytes:
    """
    if nbytes = 0, read as many as it can, empty bytes is valid;
    if nbytes > 0, read *exactly* ``nbytes``
    """
    return (yield (Traps._read, nbytes))


def read_more(nbytes: int = 1) -> bytes:
    """
    read *at least* ``nbytes``
    """
    return (yield (Traps._read_more, nbytes))


def read_until(data: bytes, return_tail: bool = True) -> bytes:
    """
    read until some bytes appear
    """
    return (yield (Traps._read_until, data, return_tail))


def read_struct(fmt: str) -> tuple:
    """
    read specific formated data
    """
    return (yield (Traps._read_struct, fmt))


def read_int(nbytes: int, byteorder: str = "big") -> int:
    """
    read some bytes as integer
    """
    return (yield (Traps._read_int, nbytes, byteorder))


def write(data: bytes):
    """
    write some bytes to the output buffer
    """
    return (yield (Traps._write, data))


def wait():
    """
    wait for next send or get_result event
    """
    return (yield (Traps._wait,))


def peek(nbytes: int = 1) -> bytes:
    """
    peek many bytes without taking them away from buffer
    """
    return (yield (Traps._peek, nbytes))


def parser(generator_func):

    def create_parser(*args, **kwargs):
        return Parser(generator_func(*args, **kwargs))

    generator_func.parser = create_parser
    return generator_func
