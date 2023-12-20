import pytest
from pyv.util import getBit, getBits, getBitVector


def test_getBit():
    assert getBit(1, 0) == 1
    assert getBit(1, 1) == 0
    assert getBit(8, 3) == 1


def test_getBits():
    assert getBits(3, 1, 0) == 3
    assert getBits(3, 1, 1) == 1
    assert getBits(3, 0, 0) == 1
    assert getBits(15, 3, 2) == 3
    assert getBits(0xdeadbeef, 31, 1) == 0x6F56DF77

def test_getBitVector():
    assert getBitVector(0xAA, 0) == [1, 0, 1, 0, 1, 0, 1, 0]
    assert getBitVector(0xAA, 11) == [0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    with pytest.warns(UserWarning):
        assert getBitVector(0x39, 4) == [1, 0, 0, 1]
