from collections import deque
import pytest
from pyv.port import Port, PortX, Wire
from pyv.defines import *
from pyv.module import Module
from pyv.simulator import Simulator

class TestPort:
    def test_init(self):
        class mod(Module):
            pass

        foo = mod()

        A = Port(IN, foo)
        assert A._direction == IN
        assert A._module == foo
        assert A._val is 0

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

    def test_defaultVal(self):
        # This tests checks whether the forced propagation on the
        # very first write works.
        sim = Simulator()
        class modA(Module):
            def __init__(self):
                self.pi = Port(IN, self, sensitive_methods=[self.process]) # Default value: 0
                self.po = Port(OUT, self)

            def process(self):
                # Simply add 3 to the input
                self.po.write(self.pi.read()+3)

        # Initialize module
        A_i = modA()
        A_i.name = 'A_i'
        A_i.init()

        # Write 0. The port has the same default value.
        # However, since this is the first write, the
        # propagation should be forced.
        A_i.pi.write(0)
        sim.run(1)
        assert A_i.po.read() == 3

        # Now, we write the same value again, but this time
        # the output shouldn't change.
        A_i.pi.write(0)
        sim.run(1)
        assert A_i.po.read() == 3

    def test_readOutput(self):
        p = Port(OUT)
        p.write(4)

        with pytest.warns(UserWarning):
            p.read()

    def test_sensitive_methods(self, caplog):
        def foo():
            pass
        def bar():
            pass

        # (also don't allow any duplicates)
        p = Port(IN, sensitive_methods=[foo, bar, bar])
        assert p._processMethods == [foo, bar]

        # Output ports shouldn't have any sensitive methods
        with pytest.raises(Exception):
            p2 = Port(OUT, sensitive_methods=[foo])

        # Default sensitive method
        class modA(Module):
            def process(self):
                pass

        A = modA()
        # When no sens list, default to parent module's process method
        p3 = Port(IN, A)
        assert p3._processMethods == [A.process]

        # When sens list AND module given, only take the sens list
        p4 = Port(IN, A, sensitive_methods=[bar, foo])
        assert p4._processMethods == [bar, foo]


    def test_onChange(self):
        def foo():
            pass
        def bar():
            pass

        p = Port(IN, sensitive_methods = [foo, bar])

        sim = Simulator()

        p.write(42)
        assert sim._queue == deque([foo, bar])

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

    def test_sensitive_methods(self, caplog):
        def foo():
            pass
        def bar():
            pass

        A = PortX(IN, None, 'one', 'two', sensitive_methods = [foo, bar])
        assert A._val['one']._processMethods == [foo, bar]
        assert A._val['two']._processMethods == [foo, bar]

        # Output PortX shouldn't have sensitive methods
        B = PortX(OUT, None, 'one', 'two', sensitive_methods = [foo, bar])
        assert "Ignoring sensitive methods for PortX 'noName' with direction OUT" in caplog.text
        # In case a non-empty sensitivity list got passed in, this shouldn't be
        # propagated to the sub-ports
        assert "Ignoring sensitive methods for port 'noName' with direction OUT" not in caplog.text

