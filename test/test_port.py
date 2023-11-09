from collections import deque
from unittest.mock import MagicMock
import pytest
from pyv.port import Input, Output, Wire
from pyv.defines import *
from pyv.module import Module
from pyv.simulator import Simulator

class TestPort:
    def test_init(self):
        A = Input(int)
        assert A._direction == IN
        assert type(A._val) == int
        assert A._val == 0
        assert A._processMethods == []

        A = Output(float)
        assert A._direction == OUT
        assert type(A._val) == float
        assert A._val == 0
        assert A._processMethods == []

    def test_read(self):
        A = Input(int)
        A._val = 42
        assert A.read() == 42

    def test_write(self):
        A = Input(int)
        A.write(123)
        assert A._val == 123

    def test_connect(self):
        A = Input(int)
        B = Input(int)
        C = Input(int)
        D = Input(int)
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
        A = Input(int)
        B = Input(int)
        C = Input(int)
        C.connect(B)
        B.connect(A)
        assert A._children == [B]
        assert B._children == [C]
        A.write(420)
        assert B.read() == 420
        assert C.read() == 420

    def test_wire(self):
        A = Input(int)
        B = Input(int)
        C = Input(int)
        D = Input(int)
        W = Wire(int)

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
        A = Input(int)

        # Connecting a port to two parents
        B = Input(int)
        C = Input(int)
        A.connect(B)
        with pytest.raises(Exception):
            A.connect(C)

        # Non-root port calls write
        with pytest.raises(Exception):
            A.write(42)

        # Wrong type write
        D = Input(float)
        with pytest.raises(TypeError):
            D.write("hello")

        # Connect port to itself
        with pytest.raises(Exception):
            D.connect(D)

        # Invalid driver type
        with pytest.raises(Exception):
            D.connect("foo")

    def test_connect_wrong_type(self):
        A = Input(int)
        B = Input(float)

        with pytest.raises(Exception):
            B.connect(A)

    def test_defaultVal(self):
        # This tests checks whether the forced propagation on the
        # very first write works.
        sim = Simulator()
        class modA(Module):
            def __init__(self):
                self.pi = Input(int) # Default value: 0
                self.po = Output(int)

            def process(self):
                # Simply add 3 to the input
                self.po.write(self.pi.read()+3)

        # Initialize module
        A = modA()
        A.name = 'A'
        A.init()

        # Write 0. The port has the same default value.
        # However, since this is the first write, the
        # propagation should be forced.
        A.pi.write(0)
        sim.step()
        assert A.po.read() == 3

        # Now, we write the same value again, but this time
        # the process method shouldn't have been called.
        A.process = MagicMock()
        A.pi.write(0)
        sim.step()
        A.process.assert_not_called()

    def test_readOutput(self):
        p = Output(int)
        p.write(4)

        with pytest.warns(UserWarning):
            p.read()

    def test_sensitive_methods(self, caplog):
        def foo():
            pass
        def bar():
            pass

        # (also don't allow any duplicates)
        p = Input(int, sensitive_methods=[foo, bar, bar])
        assert p._processMethods == [foo, bar]

        # Output ports shouldn't have any sensitive methods
        with pytest.raises(Exception):
            p2 = Output(int, sensitive_methods=[foo])

    def test_onChange(self):
        def foo():
            pass
        def bar():
            pass

        p = Input(int, sensitive_methods=[foo, bar])

        sim = Simulator()

        p.write(42)
        assert sim._process_q == deque([foo, bar])
