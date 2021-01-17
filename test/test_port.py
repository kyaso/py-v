import pytest
from port import *

def test_port():
    A = Port()
    assert A.val == 0

    B = A
    A.val = 0x42
    assert B.val == 0x42
