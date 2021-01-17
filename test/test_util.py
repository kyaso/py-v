import pytest
from util import *

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

