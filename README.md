# iofree

[![Build Status](https://travis-ci.org/guyingbo/iofree.svg?branch=master)](https://travis-ci.org/guyingbo/iofree)
[![Documentation Status](https://readthedocs.org/projects/iofree/badge/?version=latest)](https://iofree.readthedocs.io/en/latest/?badge=latest)
[![Python Version](https://img.shields.io/pypi/pyversions/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![Version](https://img.shields.io/pypi/v/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![Format](https://img.shields.io/pypi/format/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![License](https://img.shields.io/pypi/l/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![codecov](https://codecov.io/gh/guyingbo/iofree/branch/master/graph/badge.svg)](https://codecov.io/gh/guyingbo/iofree)

`iofree` is an easy-to-use and powerful library to help you implement network protocols and binary parsers.

## Installation

~~~
pip install iofree
~~~

## Advantages

Using iofree, you can:

* define network protocols and file format in a clear and precise manner
* parse both binary streams and files

## Documentation

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

commonly used number units:

* int8 uint8
* int16 int16be uint16 uint16be
* int24 int24be uint24 uint24be
* int32 int32be uint32 uint32be
* int64 int64be uint64 uint64be
* float16 float16be
* float32 float32be
* float64 float64be

simple units:

* Bytes
* String
* EndWith

composite units:

* LengthPrefixedBytes
* LengthPrefixedString
* LengthPrefixedObjectList
* LengthPrefixedObject
* MustEqual
* Switch
* SizedIntEnum
* Convert
* Group

[API docs](https://iofree.readthedocs.io/en/latest/index.html)

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
