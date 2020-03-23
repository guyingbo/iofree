import abc
import enum
import struct
import typing
from struct import Struct
from . import read_raw_struct, read, read_until, read_struct, Parser


class Unit(abc.ABC):
    @abc.abstractmethod
    def get_value(self, namespace: typing.Mapping) -> typing.Generator:
        "get object you want from bytes"

    @abc.abstractmethod
    def __call__(self, obj: typing.Any) -> bytes:
        "convert your object to bytes"


class StructUnit(Unit):
    def __init__(self, format_: str):
        self._struct = Struct(format_)

    def __str__(self):
        return f"{self.__class__.__name__}({self._struct.format})"

    def get_value(self, namespace):
        return (yield from read_raw_struct(self._struct))[0]

    def __call__(self, obj) -> bytes:
        return self._struct.pack(obj)


int8 = StructUnit("b")
uint8 = StructUnit("B")
int16 = StructUnit("h")
int16be = StructUnit(">h")
uint16 = StructUnit("H")
uint16be = StructUnit(">H")
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

    def get_value(self, namespace):
        if self.length >= 0:
            return (yield from read_raw_struct(self._struct))[0]
        else:
            return (yield from read())

    def __call__(self, obj) -> bytes:
        if self.length >= 0:
            return self._struct.pack(obj)
        else:
            return obj


class String(Bytes):
    def __init__(self, length, encoding="utf-8"):
        super().__init__(length)
        self.encoding = encoding

    def __str__(self):
        return f"{self.__class__.__name__}({self.length})"

    def get_value(self, namespace):
        v, = yield from read_raw_struct(self._struct)
        return v.decode(self.encoding)

    def __call__(self, obj: str) -> bytes:
        return super().__call__(obj.encode(self.encoding))


class MustEqual(Unit):
    def __init__(self, unit, value):
        self.unit = unit
        self.value = value

    def __str__(self):
        return f"{self.__class__.__name__}({self.unit}, {self.value})"

    def get_value(self, namespace):
        result = yield from self.unit.get_value(namespace)
        assert self.value == result
        return result

    def __call__(self, obj) -> bytes:
        assert self.value == obj
        return self.unit(obj)


class EndWith(Unit):
    def __init__(self, _bytes):
        self._bytes = _bytes

    def __str__(self):
        return f"{self.__class__.__name__}({self._bytes})"

    def get_value(self, namespace):
        return (yield from read_until(self._bytes, return_tail=False))

    def __call__(self, obj: bytes) -> bytes:
        return obj + self._bytes


class LengthPrefixedBytes(Unit):
    def __init__(self, unit: StructUnit):
        self.unit = unit

    def __str__(self):
        return f"{self.__class__.__name__}({self.unit})"

    def get_value(self, namespace):
        length = yield from self.unit.get_value(namespace)
        return (yield from read_struct(f"{length}s"))[0]

    def __call__(self, obj: bytes) -> bytes:
        length = len(obj)
        return self.unit(length) + struct.pack(f"{length}s", obj)


class LengthPrefixedString(Unit):
    def __init__(self, unit: StructUnit, encoding="utf-8"):
        self.unit = unit
        self.encoding = encoding

    def __str__(self):
        return f"{self.__class__.__name__}({self.unit}, {self.encoding})"

    def get_value(self, namespace):
        length = yield from self.unit.get_value(namespace)
        v = (yield from read_struct(f"{length}s"))[0]
        return v.decode(self.encoding)

    def __call__(self, obj: str) -> bytes:
        length = len(obj)
        return self.unit(length) + struct.pack(f"{length}s", obj.encode(self.encoding))


class Switch(Unit):
    def __init__(self, ref, cases):
        self.ref = ref
        self.cases = cases

    def __str__(self):
        return f"{self.__class__.__name__}({self.ref}, {self.cases})"

    def get_value(self, namespace):
        unit = self.cases[namespace[self.ref]]
        if isinstance(unit, Unit):
            return (yield from unit.get_value(namespace))
        else:
            return (yield from unit.get_value())

    def __call__(self, parent, obj) -> bytes:
        if isinstance(obj, BinarySchema):
            return obj.binary
        return self.cases[getattr(parent, self.ref)](obj)


class SizedIntEnum(Unit):
    def __init__(self, unit: StructUnit, enum_class):
        self.unit = unit
        self.enum_class = enum_class

    def __str__(self):
        return f"{self.__class__.__name__}({self.unit}, {self.enum_class})"

    def get_value(self, namespace):
        v = yield from self.unit.get_value(namespace)
        return self.enum_class(v)

    def __call__(self, obj: enum.IntEnum) -> bytes:
        return self.unit(obj.value)


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


class BinarySchema(metaclass=BinarySchemaMetaclass):
    def __init__(self, *args):
        if len(args) != len(self.__class__._fields):
            raise ValueError(
                f"need {len(self.__class__._fields)} args, got {len(args)}"
            )
        binary_list = []
        for arg, (name, field) in zip(args, self.__class__._fields.items()):
            if isinstance(field, Switch):
                binary = field(self, arg)
            elif isinstance(arg, BinarySchema):
                binary = arg.binary
            else:
                binary = field(arg)
            setattr(self, name, arg)
            binary_list.append(binary)
        self.binary = b"".join(binary_list)

    def __str__(self):
        sl = []
        for name in self.__class__._fields:
            value = getattr(self, name)
            sl.append(f"{name}={value}")
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
    def get_value(cls, namespace=None):
        namespace = {}
        for name, field in cls._fields.items():
            namespace[name] = yield from field.get_value(namespace)
        return cls(*namespace.values())

    @classmethod
    def get_parser(cls):
        return Parser(cls.get_value())

    @classmethod
    def parse(cls, data: bytes):
        return cls.get_parser().parse(data)
