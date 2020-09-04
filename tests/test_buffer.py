from iofree.buffer import Buffer, float64


def test_buffer():
    buf = Buffer(16)
    buf.pprint()
    buf.push(b"0" * 15)
    buf.pprint()
    buf.pull(10)
    buf.pprint()
    buf.push(b"1" * 4)
    buf.pprint()
    buf.resize(32)
    buf.push_struct(float64, 100)
