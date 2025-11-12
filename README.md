# iofree: Effortless Network Protocol and Binary Parser Implementation

[![Python package](https://github.com/guyingbo/iofree/actions/workflows/pythonpackage.yml/badge.svg)](https://github.com/guyingbo/iofree/actions/workflows/pythonpackage.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![Version](https://img.shields.io/pypi/v/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![Format](https://img.shields.io/pypi/format/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![License](https://img.shields.io/pypi/l/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![codecov](https://codecov.io/gh/guyingbo/iofree/branch/master/graph/badge.svg)](https://codecov.io/gh/guyingbo/iofree)

`iofree` is a powerful and easy-to-use Python library designed to simplify the implementation of network protocols and binary parsers. It allows developers to define complex data structures and parsing logic in a clear, declarative, and Pythonic way.

## Installation

To install `iofree`, simply use pip:

```bash
pip install iofree
```

It is recommended to install `iofree` in a virtual environment.

## Documentation

For more in-depth examples and API reference, please refer to the [official documentation](https://iofree.readthedocs.io/en/latest/) (link coming soon).

### Basic Usage

```python
>>> from iofree import schema
>>> schema.uint8(1)
b'\x01'
>>> schema.uint32be(3)
b'\x00\x00\x00\x03'
>>> schema.uint32be.parse(b'\x00\x00\x00\x03')
3
```

### Tutorial 1: a simple parser

```python
>>> class Simple(schema.BinarySchema):
...     a = schema.uint8
...     b = schema.uint32be # "be" for big-endian
... 
>>> Simple(1, 3).binary
b'\x01\x00\x00\x00\x03'
>>> binary = _
>>> Simple.parse(binary)
<Simple(a=1, b=3)>
```

### Built-in units:

`iofree` provides a rich set of built-in units to define various data types and structures:

**Commonly used number units:**

*   `int8`, `uint8`: Signed/unsigned 8-bit integers.
*   `int16`, `int16be`, `uint16`, `uint16be`: Signed/unsigned 16-bit integers (with big-endian variants).
*   `int24`, `int24be`, `uint24`, `uint24be`: Signed/unsigned 24-bit integers (with big-endian variants).
*   `int32`, `int32be`, `uint32`, `uint32be`: Signed/unsigned 32-bit integers (with big-endian variants).
*   `int64`, `int64be`, `uint64`, `uint64be`: Signed/unsigned 64-bit integers (with big-endian variants).
*   `float16`, `float16be`: 16-bit floating-point numbers.
*   `float32`, `float32be`: 32-bit floating-point numbers.
*   `float64`, `float64be`: 64-bit floating-point numbers.

**Simple units:**

*   `Bytes`: A fixed-length sequence of bytes.
*   `String`: A fixed-length string (decoded from bytes).
*   `EndWith`: Reads until a specific byte sequence is encountered.

**Composite units:**

*   `LengthPrefixedBytes`: Bytes prefixed by their length.
*   `LengthPrefixedString`: String prefixed by its length.
*   `LengthPrefixedObjectList`: A list of objects prefixed by their total length.
*   `LengthPrefixedObject`: An object prefixed by its length.
*   `MustEqual`: Ensures a field's value matches a specific constant.
*   `Switch`: Defines a field whose schema depends on the value of another field.
*   `SizedIntEnum`: An integer-backed enumeration.
*   `Convert`: Applies encoding/decoding functions to a field's value.
*   `Group`: Groups multiple fields together, often used for reusability.

Here is a real life example [definition](https://github.com/guyingbo/iofree/blob/master/iofree/contrib/socks5.py) of socks5 client request, you can see the following code snippet:
```python
class Socks5ClientRequest(schema.BinarySchema):
    ver = schema.MustEqual(schema.uint8, 5)
    cmd = schema.SizedIntEnum(schema.uint8, Cmd)
    rsv = schema.MustEqual(schema.uint8, 0)
    addr = Addr
```

### Tutorial 2: define socks5 address format

```python
In [1]: import socket
   ...: from iofree import schema
   ...:
   ...:
   ...: class Addr(schema.BinarySchema):
   ...:     atyp: int = schema.uint8
   ...:     host: str = schema.Switch(
   ...:         "atyp",
   ...:         {
   ...:             1: schema.Convert(
   ...:                 schema.Bytes(4), encode=socket.inet_aton, decode=socket.inet_ntoa
   ...:
   ...:             ),
   ...:             4: schema.Convert(
   ...:                 schema.Bytes(16),
   ...:                 encode=lambda x: socket.inet_pton(socket.AF_INET6, x),
   ...:                 decode=lambda x: socket.inet_ntop(socket.AF_INET6, x),
   ...:             ),
   ...:             3: schema.LengthPrefixedString(schema.uint8),
   ...:         },
   ...:     )
   ...:     port: int = schema.uint16be
   ...:

In [2]: addr = Addr(1, '172.16.1.20', 80)

In [3]: addr
Out[3]: <Addr(atyp=1, host='172.16.1.20', port=80)>

In [4]: addr.binary
Out[4]: b'\x01\xac\x10\x01\x14\x00P'

In [5]: Addr.parse(addr.binary)
Out[5]: <Addr(atyp=1, host='172.16.1.20', port=80)>
```

A complete socks5 Addr [definition](https://github.com/guyingbo/iofree/blob/master/iofree/contrib/common.py)

## Projects using iofree

* [Shadowproxy](https://github.com/guyingbo/shadowproxy)
    * [socks5 models](https://github.com/guyingbo/iofree/blob/master/iofree/contrib/socks5.py) and [socks5 protocol](https://github.com/guyingbo/shadowproxy/blob/master/shadowproxy/protocols/socks5.py)
    * [shadowsocks parser](https://github.com/guyingbo/shadowproxy/blob/master/shadowproxy/proxies/shadowsocks/parser.py)
    * [shadowsocks aead parser](https://github.com/guyingbo/shadowproxy/blob/master/shadowproxy/proxies/aead/parser.py)
* [python tls1.3](https://github.com/guyingbo/tls1.3)
    * [TLS1.3 models](https://github.com/guyingbo/tls1.3/blob/master/tls/models.py) and [protocol](https://github.com/guyingbo/tls1.3/blob/master/tls/session.py)

## References

`iofree` parser is inspired by project [ohneio](https://github.com/acatton/ohneio).

## Contributing

Contributions are welcome! Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

`iofree` is released under the [MIT License](LICENSE).
