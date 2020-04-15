import abc
import enum
import struct
import typing
from struct import Struct
from collections import deque
from .exceptions import ParseError
from . import (
    read_raw_struct,
    read,
    read_until,
    read_struct,
    Parser,
    get_parser,
    wait,
    read_int,
)

_parent_stack = deque()


class Unit(abc.ABC):
    """Unit is the base class of all units. \
    If you can build your own unit class, you must inherit from it"""

    def __iter__(self):
        return self.get_value()

    @abc.abstractmethod
    def get_value(self) -> typing.Generator:
        "get object you want from bytes"

    @abc.abstractmethod
    def __call__(self, obj: typing.Any) -> bytes:
        "convert user-given object to bytes"

    def parse(self, data: bytes, *, strict=True):
        "a convenient function to help you parse fixed bytes"
        return Parser(self.get_value()).parse(data, strict=strict)


class BinarySchemaMetaclass(type):
    # def __new__(mcls, name, bases, namespace, **kwargs):
    #     fields = {}
    #     for key, value in namespace.items():
    #         if isinstance(value, (Unit, mcls)):
    #             fields[key] = value
    #     namespace["_fields"] = fields
    #     return super().__new__(mcls, name, bases, namespace)

    def __init__(cls, name, bases, namespace):
        fields = {}
        for key, value in namespace.items():
            if isinstance(value, (Unit, BinarySchemaMetaclass)):
                fields[key] = value
        cls._fields = fields
        super().__init__(name, bases, namespace)

    def __str__(cls):
        sl = []
        for name, field in cls._fields.items():
            sl.append(f"{name}={field}")
        s = ", ".join(sl)
        return f"{cls.__name__}({s})"

    def __iter__(cls):
        return cls.get_value()


class BinarySchema(metaclass=BinarySchemaMetaclass):
    "The main class for users to define their own binary structures"

    def __init__(self, *args):
        if len(args) != len(self.__class__._fields):
            raise ValueError(
                f"need {len(self.__class__._fields)} args, got {len(args)}"
            )
        _parent_stack.append(self)
        try:
            self.bins = {}
            for arg, (name, field) in zip(args, self.__class__._fields.items()):
                if isinstance(field, BinarySchemaMetaclass):
                    binary = arg.binary
                elif isinstance(field, Unit):
                    binary = field(arg)
                if arg is ...:
                    arg = field.get_default()
                setattr(self, name, arg)
                self.bins[name] = binary
            self.binary = b"".join(self.bins.values())
        finally:
            _parent_stack.pop()

        if hasattr(self, "__post_init__"):
            self.__post_init__()

    def __str__(self):
        sl = []
        for name in self.__class__._fields:
            value = getattr(self, name)
            sl.append(f"{name}={value!r}")
        s = ", ".join(sl)
        return f"{self.__class__.__name__}({s})"

    def __repr__(self):
        return f"<{self}>"

    def __eq__(self, other: "BinarySchema") -> bool:
        if not isinstance(other, self.__class__):
            return False
        for name in self.__class__._fields:
            if getattr(self, name) != getattr(other, name):
                return False
        return True

    @classmethod
    def get_value(cls) -> typing.Generator:
        "get `BinarySchema` object from bytes"
        mapping = {}
        parser = yield from get_parser()
        parser._mapping_stack.append(mapping)
        try:
            for name, field in cls._fields.items():
                mapping[name] = yield from field.get_value()
        except Exception:
            raise ParseError(mapping)
        finally:
            parser._mapping_stack.pop()
        return cls(*mapping.values())

    @classmethod
    def get_parser(cls) -> Parser:
        return Parser(cls.get_value())

    @classmethod
    def parse(cls, data: bytes, *, strict=True) -> "BinarySchema":
        return cls.get_parser().parse(data, strict=strict)


FieldType = typing.Union[BinarySchemaMetaclass, Unit]


class StructUnit(Unit):
    def __init__(self, format_: str):
        self._struct = Struct(format_)

    def __str__(self):
        return f"{self.__class__.__name__}({self._struct.format})"

    def get_value(self):
        return (yield from read_raw_struct(self._struct))[0]

    def __call__(self, obj) -> bytes:
        return self._struct.pack(obj)


class IntUnit(Unit):
    def __init__(self, length: int, byteorder: str, signed: bool = False):
        self.length = length
        self.byteorder = byteorder
        self.signed = signed

    def get_value(self):
        return (
            yield from read_int(
                self.length, byteorder=self.byteorder, signed=self.signed
            )
        )

    def __call__(self, obj: int) -> bytes:
        return obj.to_bytes(self.length, self.byteorder, signed=self.signed)


int8 = StructUnit("b")
uint8 = StructUnit("B")
int16 = StructUnit("h")
int16be = StructUnit(">h")
uint16 = StructUnit("H")
uint16be = StructUnit(">H")
int24 = IntUnit(3, "little", signed=True)
int24be = IntUnit(3, "big", signed=True)
uint24 = IntUnit(3, "little", signed=False)
uint24be = IntUnit(3, "big", signed=False)
int32 = StructUnit("i")
int32be = StructUnit(">i")
uint32 = StructUnit("I")
uint32be = StructUnit(">I")
int64 = StructUnit("q")
int64be = StructUnit(">q")
uint64 = StructUnit("Q")
uint64be = StructUnit(">Q")
float32 = StructUnit("f")
float32be = StructUnit(">f")
float64 = StructUnit("d")
float64be = StructUnit(">d")


class Bytes(Unit):
    def __init__(self, length):
        self.length = length
        if length >= 0:
            self._struct = Struct(f"{length}s")

    def __str__(self):
        return f"{self.__class__.__name__}({self.length})"

    def get_value(self):
        if self.length >= 0:
            return (yield from read_raw_struct(self._struct))[0]
        else:
            return (yield from read())

    def __call__(self, obj) -> bytes:
        if self.length >= 0:
            return self._struct.pack(obj)
        else:
            return obj


class MustEqual(Unit):
    def __init__(self, unit, value):
        self.unit = unit
        self.value = value

    def __str__(self):
        return f"{self.__class__.__name__}({self.unit}, {self.value})"

    def get_value(self):
        result = yield from self.unit.get_value()
        if self.value != result:
            raise ValueError(f"expect {self.value}, got {result}")
        return result

    def get_default(self):
        return self.value

    def __call__(self, obj) -> bytes:
        if obj is not ...:
            if self.value != obj:
                raise ValueError(f"expect {self.value}, got {obj}")
        return self.unit(self.value)


class EndWith(Unit):
    def __init__(self, bytes_):
        self.bytes_ = bytes_

    def __str__(self):
        return f"{self.__class__.__name__}({self.bytes_})"

    def get_value(self):
        return (yield from read_until(self.bytes_, return_tail=False))

    def __call__(self, obj: bytes) -> bytes:
        return obj + self.bytes_


class LengthPrefixedBytes(Unit):
    def __init__(self, length_unit: StructUnit):
        self.length_unit = length_unit

    def __str__(self):
        return f"{self.__class__.__name__}({self.length_unit})"

    def get_value(self):
        length = yield from self.length_unit.get_value()
        return (yield from read_struct(f"{length}s"))[0]

    def __call__(self, obj: bytes) -> bytes:
        length = len(obj)
        return self.length_unit(length) + struct.pack(f"{length}s", obj)


class LengthPrefixedObjectList(Unit):
    def __init__(self, length_unit: StructUnit, object_unit: FieldType):
        self.length_unit = length_unit
        self.object_unit = object_unit

    def __str__(self):
        return f"{self.__class__.__name__}({self.length_unit}, {self.object_unit})"

    def get_value(self):
        length = yield from self.length_unit.get_value()
        data, = yield from read_struct(f"{length}s")
        parser = Parser(self._gen())
        return parser.parse(data)

    def _gen(self):
        parser = yield from get_parser()
        lst = []
        yield from wait()
        while parser.has_more_data():
            lst.append((yield from self.object_unit.get_value()))
        return lst

    def __call__(self, obj_list: typing.List[FieldType]) -> bytes:
        if isinstance(self.object_unit, BinarySchemaMetaclass):
            bytes_ = b"".join(bs.binary for bs in obj_list)
        elif isinstance(self.object_unit, Unit):
            bytes_ = b"".join(self.object_unit(bs) for bs in obj_list)
        return self.length_unit(len(bytes_)) + bytes_


class LengthPrefixedObject(LengthPrefixedObjectList):
    def _gen(self):
        parser = yield from get_parser()
        v = yield from self.object_unit.get_value()
        if parser.has_more_data():
            raise ValueError("extra bytes left")
        return v

    def __call__(self, obj: FieldType) -> bytes:
        bytes_ = (
            obj.binary
            if isinstance(self.object_unit, BinarySchemaMetaclass)
            else self.object_unit(obj)
        )
        return self.length_unit(len(bytes_)) + bytes_


class Switch(Unit):
    def __init__(self, ref: str, cases: typing.Mapping[typing.Any, FieldType]):
        self.ref = ref
        self.cases = cases

    def __str__(self):
        return f"{self.__class__.__name__}({self.ref}, {self.cases})"

    def get_value(self):
        parser = yield from get_parser()
        mapping = parser._mapping_stack[-1]
        unit = self.cases[mapping[self.ref]]
        return (yield from unit.get_value())

    def __call__(self, obj) -> bytes:
        parent = _parent_stack[-1]
        real_field = self.cases[getattr(parent, self.ref)]
        return real_field(obj) if isinstance(real_field, Unit) else obj.binary


class SizedIntEnum(Unit):
    def __init__(self, size_unit: StructUnit, enum_class):
        self.size_unit = size_unit
        self.enum_class = enum_class

    def __str__(self):
        return f"{self.__class__.__name__}({self.size_unit}, {self.enum_class})"

    def get_value(self):
        v = yield from self.size_unit.get_value()
        return self.enum_class(v)

    def __call__(self, obj: enum.IntEnum) -> bytes:
        return self.size_unit(obj.value)


class Convert(Unit):
    def __init__(
        self, unit: FieldType, *, encode: typing.Callable, decode: typing.Callable
    ):
        self.unit = unit
        self.encode = encode
        self.decode = decode

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            f"({self.unit}, encode={self.encode}, decode={self.decode})"
        )

    def get_value(self):
        v = yield from self.unit.get_value()
        return self.decode(v)

    def __call__(self, obj) -> bytes:
        return self.unit(self.encode(obj))


class String(Convert):
    def __init__(self, length, encoding="utf-8"):
        super().__init__(
            Bytes(length),
            encode=lambda x: x.encode(encoding),
            decode=lambda x: x.decode(encoding),
        )


class LengthPrefixedString(Convert):
    def __init__(self, length_unit: StructUnit, encoding="utf-8"):
        super().__init__(
            LengthPrefixedBytes(length_unit),
            encode=lambda x: x.encode(encoding),
            decode=lambda x: x.decode(encoding),
        )


def Group(**fields: typing.Dict[str, FieldType]) -> BinarySchema:
    return type("Group", (BinarySchema,), fields)
