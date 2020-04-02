# iofree

[![Build Status](https://travis-ci.org/guyingbo/iofree.svg?branch=master)](https://travis-ci.org/guyingbo/iofree)
[![Python Version](https://img.shields.io/pypi/pyversions/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![Version](https://img.shields.io/pypi/v/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![Format](https://img.shields.io/pypi/format/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![License](https://img.shields.io/pypi/l/iofree.svg)](https://pypi.python.org/pypi/iofree)
[![codecov](https://codecov.io/gh/guyingbo/iofree/branch/master/graph/badge.svg)](https://codecov.io/gh/guyingbo/iofree)

io-free stream parser inspired by [ohneio](https://github.com/acatton/ohneio).

## Installation

~~~
pip install iofree
~~~

## Advantages

Using iofree, you can:

* define network protocols and file format in a clear and precise manner
* parse both binary streams and files


## Tutorial 1: write a simple parser

```python
>>> from iofree import schema
>>> schema.uint8(1)
b'\x01'
>>> schema.uint32be(3)
b'\x00\x00\x00\x03'
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

## Built-in units:

commonly used number units:
* int8 uint8
* int16 int16be uint16 uint16be
* int24 int24be uint24 uint24be
* int32 int32be uint32 uint32be
* int64 int64be uint64 uint64be
* float32 float32be float64 float64be

and also:
* Bytes
* String
* MustEqual
* EndWith
* LengthPrefixedBytes
* LengthPrefixedString
* LengthPrefixedObjectList
* LengthPrefixedObject
* Switch
* SizedIntEnum
* Convert
* Group

Here is a real life example [definition](https://github.com/guyingbo/iofree/blob/master/iofree/contrib/socks5.py) of socks5 client request, you can see the following code snippet:

```python
class Socks5ClientRequest(schema.BinarySchema):
    auth_ver = schema.MustEqual(schema.uint8, 1)
    username = schema.LengthPrefixedString(schema.uint8)
    password = schema.LengthPrefixedString(schema.uint8)
    ver = schema.MustEqual(schema.uint8, 5)
    cmd = schema.SizedIntEnum(schema.uint8, Cmd)
    rsv = schema.MustEqual(schema.uint8, 0)
    addr = Addr
```

## Tutorial 2: customize your struct unit

```python
In [1]: import socket
   ...: from struct import Struct
   ...: from iofree import schema
   ...: from iofree import read_raw_struct
   ...:
   ...:
   ...: class IPv4(schema.Unit):
   ...:     def __init__(self):
   ...:         self._struct = Struct("4s")
   ...:
   ...:     def get_value(self):
   ...:         (result,) = yield from read_raw_struct(self._struct)
   ...:         return socket.inet_ntoa(result)
   ...:
   ...:     def __call__(self, obj: str) -> bytes:
   ...:         return self._struct.pack(socket.inet_aton(obj))
   ...:

In [2]: ipv4 = IPv4()

In [3]: ipv4('192.168.0.1')
Out[3]: b'\xc0\xa8\x00\x01'
```

A complete socks5 Addr [definition](https://github.com/guyingbo/iofree/blob/master/iofree/contrib/common.py)

## Usage Examples:

* [shadowsocks parser](https://github.com/guyingbo/shadowproxy/blob/master/shadowproxy/proxies/shadowsocks/parser.py)
* [shadowsocks aead parser](https://github.com/guyingbo/shadowproxy/blob/master/shadowproxy/proxies/aead/parser.py)
* [socks5 models](https://github.com/guyingbo/iofree/blob/master/iofree/contrib/socks5.py)
* [socks5 parser](https://github.com/guyingbo/shadowproxy/blob/master/shadowproxy/proxies/socks/parser.py)
* [simple http parser](https://github.com/guyingbo/shadowproxy/blob/master/shadowproxy/proxies/http/parser.py)
* TLS1.3 [models](https://github.com/guyingbo/tls1.3/blob/master/tls/models.py) and [parser](https://github.com/guyingbo/tls1.3/blob/0e329c44152bd31859668b929a0836eea439d07c/tls/session.py#L227)
