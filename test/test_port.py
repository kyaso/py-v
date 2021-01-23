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

