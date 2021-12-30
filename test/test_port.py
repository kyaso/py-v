import pytest
from pyv.port import Port, PortX, Wire
from pyv.defines import *
from pyv.module import Module

class TestPort:
    def test_constructor(self):
        class mod(Module):
            pass

        foo = mod()

        A = Port(IN, foo)
        assert A._direction == IN
        assert A._module == foo
        assert A._val is None

        A = Port(OUT, initVal=42)
        assert A._direction == OUT
        assert A._val == 42
        assert A._module is None

    def test_read(self):
        A = Port()
        A._val = 42
        assert A.read() == 42
    
    def test_write(self):
        A = Port()
        A.write(123)
        assert A._val == 123
    
    def test_connect(self):
        A = Port()
        B = Port()
        C = Port()
        D = Port()
        B.connect(A)
        C.connect(B)
        D.connect(B)

        # Check children
        assert A._children == [B]
        assert B._children == [C, D]
        assert C._children == []
        assert D._children == []
        
        # Check parents
        assert A._parent is None
        assert B._parent == A
        assert C._parent == B
        assert D._parent == B

        # Check root driver attribute
        assert A._is_root_driver == True
        assert B._is_root_driver == False
        assert C._is_root_driver == False
        assert D._is_root_driver == False

        # Write to A
        A.write(410)
        assert B.read() == 410
        assert C.read() == 410
        assert D.read() == 410

        # Test reverse connect order
        A = Port()
        B = Port()
        C = Port()
        C.connect(B)
        B.connect(A)
        assert A._children == [B]
        assert B._children == [C]
        A.write(420)
        assert B.read() == 420
        assert C.read() == 420 

    def test_wire(self):
        A = Port()
        B = Port()
        C = Port()
        D = Port()
        W = Wire()

        # Connect wire W to port A
        W.connect(A)

        # The other ports are connected to wire W
        B.connect(W)
        C.connect(W)
        D.connect(W)

        # Write a value to A
        A.write(42)
        # Read the other ports
        assert B.read() == 42
        assert C.read() == 42
        assert D.read() == 42

    def test_errors(self):
        A = Port()

        # Connecting a port to two parents
        B = Port()
        C = Port()
        A.connect(B)
        with pytest.raises(Exception):
            A.connect(C)
        
        # Non-root port calls write
        with pytest.raises(Exception):
            A.write(42)

class TestPortX:
    def test_portx(self):
        # Init
        A = PortX(IN, None, 'one', 'two', 'three')

        # Test write
        A.write('one', 42, 'two', 45, 'three', 1)
        assert A._val['one']._val == 42
        assert A._val['two']._val == 45
        assert A._val['three']._val == 1

        # Test reading all subports
        ret = A.read()
        assert ret['one'] == 42
        assert ret['two'] == 45
        assert ret['three'] == 1

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
        B = PortX(IN, None, 'one', 'two', 'three')
        new = {'one':89, 'two':12, 'three':90}
        B.write(new)
        assert B._val['one']._val == 89
        assert B._val['two']._val == 12
        assert B._val['three']._val == 90

        # Test reading with square brackets operator
        for key, val in A._val.items():
            assert A[key] is A._val[key]

        # Test connecting other port to sub-port
        B = Port()
        A['two'].connect(B)
        B.write(5678)
        assert A._val['two'].read() == 5678

    def test_errors(self):
        A = PortX(IN, None, 'one', 'two', 'three') 

        # Test invalid sq. brackets assignment
        with pytest.raises(TypeError):
            A['three'] = 3

        # Test connecting non-PortX
        with pytest.raises(TypeError):
            A.connect(42) # Just pass an integer as "driver"
        

