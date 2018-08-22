"io-free stream parser which helps implementing network protocols the `Sans-IO` way"
import struct
from enum import IntEnum

__version__ = "0.1.0"

_no_result = object()
_wait = object()


class NoResult(RuntimeError):
    ""


class Traps(IntEnum):
    _read = 0
    _read_more = 1
    _read_until = 2
    _read_struct = 3
    _write = 4
    _wait = 5
    _peek = 6


class State(IntEnum):
    _state_wait = 0
    _state_next = 1
    _state_end = 2


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
        self.input.extend(data)
        self._process()

    def read(self, nbytes: int = 0) -> bytes:
        "read *at most* ``nbytes``"
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
        return self._read()

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

    def _write(self, data: bytes):
        self.output.extend(data)

    def _wait(self):
        if not getattr(self, '_waiting', False):
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
    return (yield (Traps._read, nbytes))


def read_more(nbytes: int = 1) -> bytes:
    return (yield (Traps._read_more, nbytes))


def read_until(data: bytes, return_tail: bool = True) -> bytes:
    return (yield (Traps._read_until, data, return_tail))


def read_struct(fmt: str) -> tuple:
    return (yield (Traps._read_struct, fmt))


def write(data: bytes):
    return (yield (Traps._write, data))


def wait():
    return (yield (Traps._wait,))


def peek(nbytes: int = 1) -> bytes:
    return (yield (Traps._peek, nbytes))
