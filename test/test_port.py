import pytest
from port import *

def test_port():
    A = Port()
    assert A.val == 0

    B = A
    A.write(0x42)
    assert B.read() == 0x42

def test_portx():
    init = {'one':1, 'two':2, 'three':3}

    # Test init
    A = PortX(init)
    assert A.val == init

    # Test reading all subports
    ret = A.read()
    assert ret == init

    # Test reading one subport
    ret = A.read('one')
    assert ret == 1

    # Test reading another subport
    ret = A.read('three')
    assert ret == 3

    # Test write
    A.write({'one':42, 'two':45})
    assert A.val == {'one':42, 'two':45, 'three':3}

