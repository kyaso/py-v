import pytest
from mem import *

def test_load():
    mem = Memory()
    mem.mem = [0xef, 0xbe, 0xad, 0xde]

    # Load byte
    val = mem.read(0, 1)
    assert val == 0xef

    # Load half word
    val = mem.read(0, 2)
    assert val == 0xbeef

    # Load word
    val = mem.read(0, 4)
    assert val == 0xdeadbeef

    # TODO: Test misaligned loads
    val = mem.read(1, 2)
    assert val == 0xadbe

    # Test invalid width
    with pytest.raises(Exception):
        mem.read(0, 5)

def test_store():
    mem = Memory()
    
    # Store byte
    mem.write(0, 0xaf, 1)
    assert mem.mem[0] == 0xaf

    # Store half word
    mem.write(0, 0xbabe, 2)
    assert mem.mem[0] == 0xbe
    assert mem.mem[1] == 0xba

    # Store word
    mem. write(0, 0xaffedead, 4)
    assert mem.mem[0] == 0xad
    assert mem.mem[1] == 0xde
    assert mem.mem[2] == 0xfe
    assert mem.mem[3] == 0xaf

    # Test invalid width
    with pytest.raises(Exception):
        mem.write(0, 6)