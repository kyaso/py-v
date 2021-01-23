import pytest
from port import *

def test_port():
    A = Port()
    assert A.val == 0

    B = A
    A.write(0x42)
    assert B.read() == 0x42

def test_portx():
    init = {'one':0, 'two':0, 'three':0}

    # Test init
    A = PortX('one', 'two', 'three')
    assert A.val == init

    # Test write
    A.write('one', 42, 'two', 45)
    assert A.val == {'one':42, 'two':45, 'three':0}

    # Test reading all subports
    ret = A.read()
    assert ret == {'one':42, 'two':45, 'three':0}

    # Test reading one subport
    ret = A.read('one')
    assert ret == 42

    # Test reading another subport
    ret = A.read('two')
    assert ret == 45

    # Test reading multiple subports
    val1, val2 = A.read('two', 'one')
    assert val1 == 45
    assert val2 == 42

    # Test writing to all subports using dict
    new = {'one':99, 'two':34, 'three':135}
    A.write(new)
    assert A.val == new
