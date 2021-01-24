import pytest
from port import *

def test_port():
    A = Port()
    assert A.val == 0

    B = A
    A.write(0x42)
    assert B.read() == 0x42

def test_portx():
    # Init
    A = PortX('one', 'two', 'three')

    # Test write
    A.write('one', 42, 'two', 45)
    assert A.val['one'].val == 42
    assert A.val['two'].val == 45
    assert A.val['three'].val == 0

    # Test reading all subports
    ret = A.read()
    assert ret['one'] == 42
    assert ret['two'] == 45
    assert ret['three'] == 0

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
    new = {'one':89, 'two':12, 'three':90}
    A.write(new)
    assert A.val['one'].val == 89
    assert A.val['two'].val == 12
    assert A.val['three'].val == 90
